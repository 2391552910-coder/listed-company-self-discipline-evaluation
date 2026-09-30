"""
Repository 基类：封装通用 CRUD
"""
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    def get(self, db: Session, pk: int) -> ModelType | None:
        return db.get(self.model, pk)

    def list(self, db: Session, offset: int = 0, limit: int = 100, **filters) -> list[ModelType]:
        query = db.query(self.model)
        for k, v in filters.items():
            if v is not None and hasattr(self.model, k):
                query = query.filter(getattr(self.model, k) == v)
        return query.offset(offset).limit(limit).all()

    def create(self, db: Session, obj: ModelType) -> ModelType:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def bulk_create(self, db: Session, objs: list[ModelType]) -> list[ModelType]:
        db.add_all(objs)
        db.commit()
        return objs

    def delete(self, db: Session, pk: int) -> None:
        obj = self.get(db, pk)
        if obj:
            db.delete(obj)
            db.commit()
