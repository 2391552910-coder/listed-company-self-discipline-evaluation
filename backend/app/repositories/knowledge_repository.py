from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDocument
from app.repositories.base import BaseRepository


class KnowledgeRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self):
        super().__init__(KnowledgeDocument)

    def get_by_title(self, db: Session, title: str) -> KnowledgeDocument | None:
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.title == title).first()

    def list_by_type(self, db: Session, doc_type: str) -> list[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_type == doc_type).all()


knowledge_repository = KnowledgeRepository()
