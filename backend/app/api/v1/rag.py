"""
RAG 知识库接口（控制层，4.4 / 5.4.4）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.rag import KnowledgeIn, SearchQuery
from app.services.rag_service import rag_service
from app.utils.response import ok, Response

router = APIRouter()


@router.post("/knowledge")
def ingest_knowledge(payload: KnowledgeIn, db: Session = Depends(get_db)) -> Response:
    """监管规则/处罚案例入库（切分→向量化→Milvus）"""
    doc = rag_service.ingest(db, payload)
    return ok({"id": doc.id}, "入库成功")


@router.post("/search")
def search_knowledge(payload: SearchQuery, db: Session = Depends(get_db)) -> Response:
    """混合检索（向量 + BM25 融合）"""
    return ok(rag_service.search(db, payload.query, payload.top_k, payload.doc_type))
