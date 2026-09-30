"""
RAG 监管知识检索服务（论文 4.4：知识库构建、混合检索、证据溯源）

知识入库：切分 → BGE-M3 向量化 → Milvus 存储 + PostgreSQL 元数据
评价增强：混合检索法规/案例 → 注入提示词 → 评价证据落库（证据溯源）
"""
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import BusinessException
from app.models.knowledge import KnowledgeDocument
from app.rag.embeddings import get_embedding_model
from app.rag.prompts import CHUNK_OVERLAP, CHUNK_SIZE
from app.rag.retriever import HybridRetriever, hybrid_retriever
from app.rag.vector_store import milvus_store
from app.repositories.knowledge_repository import knowledge_repository
from app.schemas.rag import KnowledgeIn


class RAGService:
    # ---------- 知识库构建（4.4.1） ----------
    def ingest(self, db: Session, payload: KnowledgeIn) -> KnowledgeDocument:
        """监管规则/处罚案例入库：PG 存元数据，Milvus 存向量"""
        if knowledge_repository.get_by_title(db, payload.title):
            raise BusinessException(f"知识条目《{payload.title}》已存在")
        doc = knowledge_repository.create(db, KnowledgeDocument(**payload.model_dump()))

        chunks = self._chunk(payload.content)
        embedder = get_embedding_model(settings.EMBEDDING_MODEL, settings.EMBEDDING_DEVICE)
        vectors = embedder.embed_documents(chunks)
        pks = milvus_store.insert(vectors, payload.doc_type, payload.title,
                                  payload.source or "", chunks)
        doc.milvus_pk = pks[0] if pks else None
        db.commit()

        # 同步刷新 BM25 语料
        self._refresh_corpus(db)
        return doc

    def _refresh_corpus(self, db: Session):
        docs = knowledge_repository.list(db, limit=10000)
        hybrid_retriever._corpus = [
            {"title": d.title, "content": d.content, "doc_type": d.doc_type, "source": d.source}
            for d in docs
        ]
        hybrid_retriever._bm25_ready = False

    @staticmethod
    def _chunk(content: str) -> list[str]:
        if len(content) <= CHUNK_SIZE:
            return [content]
        step = CHUNK_SIZE - CHUNK_OVERLAP
        return [content[i:i + CHUNK_SIZE] for i in range(0, len(content), step)]

    # ---------- 混合检索（4.4.2） ----------
    def search(self, db: Session, query: str, top_k: int = 5,
               doc_type: str | None = None) -> list[dict]:
        if not hybrid_retriever._corpus:
            self._refresh_corpus(db)
        hits = hybrid_retriever.hybrid_search(query, top_k=top_k, doc_type=doc_type)
        # 关联 PG 元数据，便于证据溯源展示
        by_title = {d.title: d for d in knowledge_repository.list(db, limit=10000)}
        for h in hits:
            doc = by_title.get(h.get("title"))
            h["doc_id"] = doc.id if doc else None
        return hits

    # ---------- 检索结果格式化（注入提示词用） ----------
    @staticmethod
    def format_regulations(hits: list[dict]) -> str:
        lines = []
        for i, h in enumerate(hits, 1):
            lines.append(
                f"[{i}] 《{h['title']}》（{h.get('source') or '未知来源'}）\n{h['content'][:300]}"
            )
        return "\n\n".join(lines) if lines else "无相关法规依据。"


rag_service = RAGService()
