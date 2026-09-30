"""
上市公司主体信息表（t_company）
"""
from sqlalchemy import Column, Integer, String, DateTime, func

from app.core.database import Base


class Company(Base):
    __tablename__ = "t_company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(16), unique=True, nullable=False, comment="股票代码")
    stock_name = Column(String(64), nullable=False, comment="股票简称")
    industry = Column(String(64), comment="所属行业")
    market = Column(String(8), comment="上市板块：SH/SZ/BJ")
    listed_date = Column(String(16), comment="上市日期")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
