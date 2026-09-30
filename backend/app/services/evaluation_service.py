"""
大模型多维度评价编排服务（论文 4.3 + 4.4：抽取 → RAG 增强 → 评价生成 → 证据溯源）

主流程：
1. 读取年报解析切分结果，按维度聚合文本
2. 逐维度：大模型抽取事实 → RAG 检索法规 → 生成维度评价（结构化 JSON）
3. 生成总体评价摘要
4. 评价与证据落库，支持证据溯源查询（4.4.3）
"""
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import BusinessException
from app.models.evaluation import Evaluation, EvaluationEvidence
from app.models.indicator import Dimension
from app.repositories.evaluation_repository import (
    evaluation_evidence_repository, evaluation_repository,
)
from app.repositories.knowledge_repository import knowledge_repository
from app.services.company_service import company_service
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.repositories.annual_report_repository import annual_report_repository, report_chunk_repository


class EvaluationService:
    def run(self, db: Session, stock_code: str, year: int, rag_enabled: bool = True) -> Evaluation:
        """执行一次完整的四维度评价任务"""
        company = company_service.get_by_code(db, stock_code)
        report = annual_report_repository.get_by_company_year(db, company.id, year)
        if not report:
            raise BusinessException(f"{stock_code} {year} 年报未上传，请先上传并解析年报")
        chunks = report_chunk_repository.list_by_report(db, report.id)
        if not chunks:
            raise BusinessException("年报尚未解析或无可用的治理段落，请先执行解析")

        evaluation = evaluation_repository.create(db, Evaluation(
            company_id=company.id, year=year, status="running",
            model_name=settings.LLM_MODEL, rag_enabled=1 if rag_enabled else 0,
        ))
        evaluation_evidence_repository.delete_by_evaluation(db, evaluation.id)

        try:
            # 按维度聚合年报文本（未标注维度的段落并入 D3 内控合规）
            dim_texts: dict[str, str] = {}
            untagged = [c.content for c in chunks if not c.dimension_tag]
            for dim in ("D1", "D2", "D3", "D4"):
                dim_chunks = [c.content for c in chunks if c.dimension_tag == dim]
                if dim == "D3" and untagged:
                    dim_chunks += untagged
                if not dim_chunks:
                    continue
                dim_texts[dim] = "\n".join(dim_chunks)[:12000]

            eval_texts: dict[str, str] = {}
            scores: list[float] = []
            for dim in ("D1", "D2", "D3", "D4"):
                if dim not in dim_texts:
                    continue
                dim_obj = db.query(Dimension).filter(Dimension.code == dim).first()
                dim_name = dim_obj.name if dim_obj else dim

                # 1) 事实抽取（4.3.1）
                facts_resp = llm_service.extract_facts(dim_name, dim_texts[dim])
                facts = "\n".join(
                    f"- {f.get('content')}（{f.get('chapter', '')}）"
                    for f in facts_resp.get("facts", [])
                ) or "未抽取到有效事实。"

                # 2) RAG 检索法规依据（4.4.2）
                regulations, hits = "", []
                if rag_enabled:
                    query = f"{dim_name} 上市公司 年报 监管要求 自律"
                    hits = rag_service.search(db, query, top_k=settings.RAG_TOP_K)
                    regulations = rag_service.format_regulations(hits)

                # 3) 维度评价生成（4.3.2）
                result = llm_service.evaluate_dimension(
                    company.stock_name, company.stock_code, year,
                    dim_name, dim_obj.description if dim_obj else "",
                    facts, regulations,
                )
                eval_texts[dim] = result.get("evaluation", "")
                if result.get("score") is not None:
                    scores.append(float(result["score"]))

                # 4) 证据溯源落库（4.4.3）
                self._save_evidence(db, evaluation.id, dim, hits,
                                    result.get("evidence_titles", []))

            # 总体摘要
            joined = "\n".join(f"{d}：{t}" for d, t in eval_texts.items())
            summary_resp = llm_service.summarize(
                company.stock_name, company.stock_code, year, joined
            )

            evaluation.d1_evaluation = eval_texts.get("D1")
            evaluation.d2_evaluation = eval_texts.get("D2")
            evaluation.d3_evaluation = eval_texts.get("D3")
            evaluation.d4_evaluation = eval_texts.get("D4")
            evaluation.overall_summary = summary_resp.get("summary")
            evaluation.score = sum(scores) / len(scores) if scores else None
            evaluation.status = "done"
        except Exception as e:
            evaluation.status = "failed"
            db.commit()
            raise BusinessException(f"评价生成失败：{e}")
        db.commit()
        return evaluation

    def _save_evidence(self, db: Session, evaluation_id: int, dim: str,
                       hits: list[dict], cited_titles: list[str]) -> None:
        """将检索命中且被模型引用的法规/案例保存为评价证据"""
        cited = set(cited_titles or [])
        for h in hits:
            title = h.get("title", "")
            if cited and title not in cited:
                continue
            doc = knowledge_repository.get_by_title(db, title)
            evaluation_evidence_repository.create(db, EvaluationEvidence(
                evaluation_id=evaluation_id, dimension_code=dim,
                knowledge_id=doc.id if doc else None,
                regulation_title=title, regulation_source=h.get("source"),
                clause=h.get("content", "")[:500], similarity=h.get("score"),
            ))

    def get_with_evidence(self, db: Session, stock_code: str, year: int) -> dict:
        """评价结果 + 证据溯源联合查询（5.4.4 证据追溯）"""
        company = company_service.get_by_code(db, stock_code)
        evaluation = evaluation_repository.get_by_company_year(db, company.id, year)
        if not evaluation:
            raise BusinessException(f"{stock_code} {year} 暂无评价结果")
        evidence = evaluation_evidence_repository.list_by_evaluation(db, evaluation.id)
        return {"evaluation": evaluation, "evidence": evidence}


evaluation_service = EvaluationService()
