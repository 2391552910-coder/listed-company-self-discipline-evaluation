"""
API 路由聚合：/api/v1/*
"""
from fastapi import APIRouter

from app.api.v1 import annual_report, company, evaluation, indicator, rag, report

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(company.router, prefix="/companies", tags=["公司管理"])
api_router.include_router(indicator.router, prefix="/indicators", tags=["指标体系"])
api_router.include_router(annual_report.router, prefix="/reports", tags=["年报解析"])
api_router.include_router(evaluation.router, prefix="/evaluations", tags=["大模型评价"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG 知识库"])
api_router.include_router(report.router, prefix="/reports-export", tags=["报告导出"])
