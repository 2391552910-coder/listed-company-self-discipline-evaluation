"""
大模型多维度评价接口（控制层，4.3 / 5.4.3）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.evaluation import EvaluationCreate
from app.services.evaluation_service import evaluation_service
from app.utils.response import ok, Response

router = APIRouter()


@router.post("/run")
def run_evaluation(payload: EvaluationCreate, db: Session = Depends(get_db)) -> Response:
    """执行四维度评价任务（抽取→RAG 增强→评价生成）"""
    evaluation = evaluation_service.run(db, payload.stock_code, payload.year, payload.rag_enabled)
    return ok({"id": evaluation.id, "status": evaluation.status, "score": evaluation.score},
              "评价完成")


@router.get("/{stock_code}/{year}")
def get_evaluation(stock_code: str, year: int, db: Session = Depends(get_db)) -> Response:
    """评价结果 + 证据溯源"""
    return ok(evaluation_service.get_with_evidence(db, stock_code, year))
