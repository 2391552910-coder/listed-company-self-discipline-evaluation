"""
公司管理接口（控制层）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.company import CompanyCreate
from app.services.company_service import company_service
from app.utils.response import ok, Response

router = APIRouter()


@router.post("")
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Response:
    return ok(company_service.create(db, payload).id, "创建成功")


@router.get("/{stock_code}")
def get_company(stock_code: str, db: Session = Depends(get_db)) -> Response:
    return ok(company_service.get_by_code(db, stock_code))


@router.get("")
def list_companies(industry: str | None = None, page: int = Query(1, ge=1),
                   size: int = Query(20, ge=1, le=200),
                   db: Session = Depends(get_db)) -> Response:
    return ok(company_service.list(db, industry, page, size))


@router.delete("/{stock_code}")
def delete_company(stock_code: str, db: Session = Depends(get_db)) -> Response:
    company_service.delete(db, stock_code)
    return ok(message="删除成功")
