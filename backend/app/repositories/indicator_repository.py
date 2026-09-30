from sqlalchemy.orm import Session

from app.models.indicator import Dimension, Indicator, IndicatorValue, IndexResult
from app.repositories.base import BaseRepository


class DimensionRepository(BaseRepository[Dimension]):
    def __init__(self):
        super().__init__(Dimension)

    def get_by_code(self, db: Session, code: str) -> Dimension | None:
        return db.query(Dimension).filter(Dimension.code == code).first()


class IndicatorRepository(BaseRepository[Indicator]):
    def __init__(self):
        super().__init__(Indicator)

    def get_by_code(self, db: Session, code: str) -> Indicator | None:
        return db.query(Indicator).filter(Indicator.code == code).first()

    def list_with_dimension(self, db: Session) -> list[Indicator]:
        return db.query(Indicator).order_by(Indicator.code).all()


class IndicatorValueRepository(BaseRepository[IndicatorValue]):
    def __init__(self):
        super().__init__(IndicatorValue)

    def get_matrix(self, db: Session, year: int) -> list[IndicatorValue]:
        """取某年度全部指标值，供标准化与 Transformer 赋权使用"""
        return db.query(IndicatorValue).filter(IndicatorValue.year == year).all()

    def delete_by_year(self, db: Session, year: int) -> None:
        db.query(IndicatorValue).filter(IndicatorValue.year == year).delete()
        db.commit()


class IndexResultRepository(BaseRepository[IndexResult]):
    def __init__(self):
        super().__init__(IndexResult)

    def get_by_company_year(self, db: Session, company_id: int, year: int) -> IndexResult | None:
        return (
            db.query(IndexResult)
            .filter(IndexResult.company_id == company_id, IndexResult.year == year)
            .first()
        )


dimension_repository = DimensionRepository()
indicator_repository = IndicatorRepository()
indicator_value_repository = IndicatorValueRepository()
index_result_repository = IndexResultRepository()
