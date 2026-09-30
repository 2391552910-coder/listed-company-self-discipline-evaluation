"""
监管知识库元数据表（向量数据存于 Milvus，本表存业务元数据）
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "t_knowledge_document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_type = Column(String(32), nullable=False, comment="regulation:监管规则 penalty:处罚案例 announcement:历史公告")
    title = Column(String(255), nullable=False, comment="标题")
    source = Column(String(128), comment="发文机关/来源")
    publish_date = Column(String(16), comment="发布日期")
    content = Column(Text, comment="全文文本")
    milvus_pk = Column(String(64), comment="Milvus 主键")
    created_at = Column(DateTime, server_default=func.now())
