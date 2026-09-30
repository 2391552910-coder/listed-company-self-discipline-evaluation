"""
年报文件与解析切分表（MinerU 解析结果）
- t_annual_report：年报 PDF 元数据
- t_report_chunk：治理相关段落切分结果
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey

from app.core.database import Base


class AnnualReport(Base):
    __tablename__ = "t_annual_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("t_company.id"), nullable=False)
    year = Column(Integer, nullable=False)
    file_path = Column(String(255), comment="PDF 存储路径")
    parse_status = Column(String(16), default="pending", comment="pending/parsing/done/failed")
    chapter_count = Column(Integer, default=0, comment="识别章节数")
    chunk_count = Column(Integer, default=0, comment="切分段落数")
    created_at = Column(DateTime, server_default=func.now())


class ReportChunk(Base):
    __tablename__ = "t_report_chunk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("t_annual_report.id"), nullable=False)
    chapter = Column(String(64), comment="所属章节：董事会报告/公司治理/内部控制...")
    content = Column(Text, nullable=False, comment="段落文本")
    dimension_tag = Column(String(16), comment="关联自律维度 D1-D4")
    seq = Column(Integer, comment="段内序号")
    created_at = Column(DateTime, server_default=func.now())
