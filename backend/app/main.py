"""
FastAPI 应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.database import init_db
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # 启动时初始化 PostgreSQL 表结构
    yield


app = FastAPI(
    title="基于大模型的上市公司主体自律评价系统",
    description="AHP-Transformer 混合赋权指数 + 大模型多维度评价 + RAG 监管知识增强",
    version="1.0.0",
    lifespan=lifespan,
)

# 前后端分离：允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
