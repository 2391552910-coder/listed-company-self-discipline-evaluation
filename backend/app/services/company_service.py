"""
公司业务逻辑层：上市公司主体的增删改查
"""
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException, NotFoundException
from app.models.company import Company
from app.repositories.company_repository import company_repository
from app.schemas.company import CompanyCreate


class CompanyService:
    def create(self, db: Session, payload: CompanyCreate) -> Company:
        if company_repository.get_by_code(db, payload.stock_code):
            raise BusinessException(f"股票代码 {payload.stock_code} 已存在")
        return company_repository.create(db, Company(**payload.model_dump()))

    def get_by_code(self, db: Session, stock_code: str) -> Company:
        company = company_repository.get_by_code(db, stock_code)
        if not company:
            raise NotFoundException(f"公司 {stock_code} 不存在")
        return company

    def list(self, db: Session, industry: str | None = None, page: int = 1, size: int = 20):
        total = db.query(Company).count()
        items = company_repository.list(
            db, offset=(page - 1) * size, limit=size,
            **({"industry": industry} if industry else {}),
        )
        return {"total": total, "items": items}

    def delete(self, db: Session, stock_code: str) -> None:
        company = self.get_by_code(db, stock_code)
        company_repository.delete(db, company.id)


company_service = CompanyService()
