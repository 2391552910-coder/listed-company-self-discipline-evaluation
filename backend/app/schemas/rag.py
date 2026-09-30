from pydantic import BaseModel


class KnowledgeIn(BaseModel):
    """监管知识入库"""
    doc_type: str  # regulation / penalty / announcement
    title: str
    source: str | None = None
    publish_date: str | None = None
    content: str


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    doc_type: str | None = None


class SearchHit(BaseModel):
    doc_id: int | None
    doc_type: str | None
    title: str
    source: str | None
    content: str
    score: float
