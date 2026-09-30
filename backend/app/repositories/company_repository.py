from sqlalchemy.orm import Session

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self):
        super().__init__(Company)

    def get_by_code(self, db: Session, stock_code: str) -> Company | None:
        return db.query(Company).filter(Company.stock_code == stock_code).first()


company_repository = CompanyRepository()
