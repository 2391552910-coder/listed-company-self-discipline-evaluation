"""
年报上传与解析接口（控制层，5.4.1 / 4.1）
"""
from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.annual_report_service import annual_report_service
from app.utils.response import ok, Response

router = APIRouter()


@router.post("/upload")
async def upload_report(stock_code: str = Form(...), year: int = Form(...),
                        file: UploadFile = Form(...),
                        db: Session = Depends(get_db)) -> Response:
    """年报 PDF 上传"""
    report = annual_report_service.upload(db, stock_code, year, file.filename, await file.read())
    return ok({"id": report.id}, "上传成功，待解析")


@router.post("/parse/{report_id}")
def parse_report(report_id: int, db: Session = Depends(get_db)) -> Response:
    """触发 MinerU 解析 + 章节识别 + 段落切分"""
    report = annual_report_service.parse(db, report_id)
    return ok({"status": report.parse_status, "chapters": report.chapter_count,
               "chunks": report.chunk_count}, "解析完成")


@router.get("/chunks/{report_id}")
def list_chunks(report_id: int, db: Session = Depends(get_db)) -> Response:
    return ok(annual_report_service.list_chunks(db, report_id))
