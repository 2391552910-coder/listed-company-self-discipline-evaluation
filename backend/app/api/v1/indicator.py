"""
指标体系与指数计算接口（控制层）
"""
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.indicator import AHPJudgmentMatrixIn
from app.services.import_service import import_service
from app.services.index_service import index_service
from app.services.company_service import company_service
from app.repositories.indicator_repository import index_result_repository
from app.utils.response import ok, Response

router = APIRouter()


@router.post("/import")
async def import_indicators(file: UploadFile, db: Session = Depends(get_db)) -> Response:
    """CSMAR 指标数据批量导入（Excel/CSV）"""
    result = import_service.import_indicator_file(db, await file.read(), file.filename)
    return ok(result, "导入完成")


@router.post("/index/compute")
def compute_index(payload: AHPJudgmentMatrixIn | None, year: int,
                  db: Session = Depends(get_db)) -> Response:
    """AHP-Transformer 混合赋权指数计算"""
    matrix = payload.matrix if payload else None
    return ok(index_service.compute(db, year, matrix), "计算完成")


@router.get("/index/{stock_code}/{year}")
def get_index(stock_code: str, year: int, db: Session = Depends(get_db)) -> Response:
    company = company_service.get_by_code(db, stock_code)
    result = index_result_repository.get_by_company_year(db, company.id, year)
    return ok(result)
