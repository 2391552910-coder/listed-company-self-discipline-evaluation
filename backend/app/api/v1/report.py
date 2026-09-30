"""
评价报告导出接口（控制层，5.4.5）
"""
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, Response as HttpResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report import ReportRequest
from app.services.report_service import report_service
from app.utils.response import ok, Response

router = APIRouter()


@router.post("/preview")
def preview_report(payload: ReportRequest, db: Session = Depends(get_db)) -> Response:
    """报告数据预览（前端渲染用）"""
    return ok(jsonable_encoder(report_service.build_report_data(db, payload.stock_code, payload.year)))


@router.post("/export/html")
def export_html(payload: ReportRequest, db: Session = Depends(get_db)) -> HTMLResponse:
    return HTMLResponse(report_service.render_html(db, payload.stock_code, payload.year))


@router.post("/export/pdf")
def export_pdf(payload: ReportRequest, db: Session = Depends(get_db)) -> HttpResponse:
    pdf_bytes = report_service.render_pdf(db, payload.stock_code, payload.year)
    filename = f"{payload.stock_code}_{payload.year}_自律评价报告.pdf"
    return HttpResponse(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
