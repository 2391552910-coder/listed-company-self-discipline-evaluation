"""
年报解析服务（论文 4.1：基于 MinerU 的年报 PDF 解析与文本切分）

流程：PDF 上传 → MinerU 解析（文本/表格/图片）→ 章节识别 → 治理段落切分 → 维度标注入库
"""
import os
import re
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.annual_report import AnnualReport, ReportChunk
from app.rag.prompts import CHUNK_OVERLAP, CHUNK_SIZE, GOVERNANCE_CHAPTER_KEYWORDS
from app.repositories.annual_report_repository import annual_report_repository, report_chunk_repository
from app.services.company_service import company_service

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 年报章节识别正则（4.1.2）
CHAPTER_PATTERNS = [
    r"第[一二三四五六七八九十]+节\s*([^\\n]{2,30})",
    r"^(董事会报告|公司治理|内部控制|环境与社会责任|重要事项|审计报告|财务报告)\s*$",
]


class AnnualReportService:
    def upload(self, db: Session, stock_code: str, year: int, filename: str,
               file_bytes: bytes) -> AnnualReport:
        """年报 PDF 上传入库"""
        company = company_service.get_by_code(db, stock_code)
        if not filename.lower().endswith(".pdf"):
            raise BusinessException("仅支持 PDF 格式年报")
        existing = annual_report_repository.get_by_company_year(db, company.id, year)
        if existing:
            annual_report_repository.delete(db, existing.id)

        saved = UPLOAD_DIR / f"{stock_code}_{year}_{uuid.uuid4().hex[:8]}.pdf"
        saved.write_bytes(file_bytes)
        return annual_report_repository.create(db, AnnualReport(
            company_id=company.id, year=year, file_path=str(saved), parse_status="pending",
        ))

    def parse(self, db: Session, report_id: int) -> AnnualReport:
        """
        解析年报：MinerU 提取全文 → 章节识别 → 治理段落切分与维度标注（4.1.3）
        """
        report = annual_report_repository.get(db, report_id)
        if not report:
            raise BusinessException("年报记录不存在")
        report.parse_status = "parsing"
        db.commit()

        try:
            full_text = self._extract_text(report.file_path)
            chapters = self._recognize_chapters(full_text)
            chunks = self._split_and_tag(chapters)
            report_chunk_repository.delete_by_report(db, report_id)
            objs = [
                ReportChunk(report_id=report_id, chapter=c["chapter"], content=c["content"],
                            dimension_tag=c["dimension"], seq=i)
                for i, c in enumerate(chunks)
            ]
            report_chunk_repository.bulk_create(db, objs)
            report.chapter_count = len(chapters)
            report.chunk_count = len(objs)
            report.parse_status = "done"
        except Exception as e:
            report.parse_status = "failed"
            db.commit()
            raise BusinessException(f"年报解析失败：{e}")
        db.commit()
        return report

    @staticmethod
    def _extract_text(pdf_path: str) -> str:
        """MinerU PDF 解析（4.1.1）"""
        try:
            from mineru.cli import do_parse  # MinerU 官方解析入口
            do_parse(
                output_dir=str(UPLOAD_DIR / "mineru_output"),
                pdf_file_names=[pdf_path],
                lang="ch",
            )
            md_path = Path(pdf_path).with_suffix(".md")
            if md_path.exists():
                return md_path.read_text(encoding="utf-8")
        except ImportError:
            pass  # 未安装 mineru 时降级为纯文本提取
        import pdfplumber
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages)

    @staticmethod
    def _recognize_chapters(text: str) -> list[dict]:
        """章节识别：按年报标准章节切分（4.1.2）"""
        pattern = re.compile("|".join(f"({p})" for p in CHAPTER_PATTERNS), re.MULTILINE)
        matches = list(pattern.finditer(text))
        chapters = []
        for i, m in enumerate(matches):
            title = m.group(1) or m.group(0)
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chapters.append({"chapter": title.strip(), "content": text[start:end].strip()})
        if not chapters:
            chapters.append({"chapter": "全文", "content": text})
        return chapters

    @staticmethod
    def _tag_dimension(chapter: str, content: str) -> str | None:
        """按关键词标注关联自律维度（4.1.3）"""
        text = chapter + content[:200]
        for dim, keywords in GOVERNANCE_CHAPTER_KEYWORDS.items():
            if any(k in text for k in keywords):
                return dim
        return None

    def _split_and_tag(self, chapters: list[dict]) -> list[dict]:
        """长章节按固定窗口切分并标注维度"""
        chunks = []
        for ch in chapters:
            dim = self._tag_dimension(ch["chapter"], ch["content"])
            content = ch["content"]
            if len(content) <= CHUNK_SIZE:
                chunks.append({"chapter": ch["chapter"], "content": content, "dimension": dim})
                continue
            step = CHUNK_SIZE - CHUNK_OVERLAP
            for i in range(0, len(content), step):
                piece = content[i:i + CHUNK_SIZE]
                if piece.strip():
                    chunks.append({"chapter": ch["chapter"], "content": piece, "dimension": dim})
        return chunks

    def list_chunks(self, db: Session, report_id: int) -> list[ReportChunk]:
        return report_chunk_repository.list_by_report(db, report_id)


annual_report_service = AnnualReportService()
