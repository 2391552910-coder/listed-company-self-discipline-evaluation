"""
大模型多维度评价与证据溯源表
- t_evaluation：评价任务与四维度评价结果（含 RAG 法规引用）
- t_evaluation_evidence：评价引用的法规/案例证据（证据溯源）
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Float

from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "t_evaluation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("t_company.id"), nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(16), default="pending", comment="pending/running/done/failed")
    model_name = Column(String(64), comment="大模型名称")
    rag_enabled = Column(Integer, default=1, comment="是否启用 RAG 增强")
    d1_evaluation = Column(Text, comment="信息披露质量评价")
    d2_evaluation = Column(Text, comment="董事会治理有效性评价")
    d3_evaluation = Column(Text, comment="内部控制与合规性评价")
    d4_evaluation = Column(Text, comment="第三方声誉评价")
    overall_summary = Column(Text, comment="总体评价摘要")
    score = Column(Float, comment="模型给出的维度均分")
    created_at = Column(DateTime, server_default=func.now())


class EvaluationEvidence(Base):
    __tablename__ = "t_evaluation_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(Integer, ForeignKey("t_evaluation.id"), nullable=False)
    dimension_code = Column(String(8), comment="关联维度 D1-D4")
    knowledge_id = Column(Integer, ForeignKey("t_knowledge_document.id"), comment="引用知识条目")
    regulation_title = Column(String(255), comment="法规/案例标题")
    regulation_source = Column(String(255), comment="发文机关")
    clause = Column(Text, comment="引用条款原文")
    similarity = Column(Float, comment="检索相似度")
    created_at = Column(DateTime, server_default=func.now())
