"""
自律评价指标体系与指数结果表
- t_dimension：四个一级维度（信息披露质量/董事会治理有效性/内部控制与合规性/第三方声誉）
- t_indicator：十二项二级指标
- t_indicator_value：指标原始值（来源 CSMAR）
- t_index_result：主体自律指数评分结果
"""
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, DateTime, func

from app.core.database import Base


class Dimension(Base):
    __tablename__ = "t_dimension"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), unique=True, nullable=False, comment="维度编码 D1-D4")
    name = Column(String(64), nullable=False, comment="维度名称")
    description = Column(Text, comment="维度说明")


class Indicator(Base):
    __tablename__ = "t_indicator"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), unique=True, nullable=False, comment="指标编码 I1-I12")
    name = Column(String(64), nullable=False, comment="指标名称")
    dimension_id = Column(Integer, ForeignKey("t_dimension.id"), nullable=False, comment="所属维度")
    direction = Column(String(8), nullable=False, default="positive", comment="正向/负向指标")
    unit = Column(String(16), comment="计量单位")
    data_source = Column(String(64), comment="数据来源：CSMAR/年报文本/舆情")


class IndicatorValue(Base):
    __tablename__ = "t_indicator_value"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("t_company.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("t_indicator.id"), nullable=False)
    year = Column(Integer, nullable=False, comment="会计年度")
    raw_value = Column(Float, comment="原始值")
    std_value = Column(Float, comment="标准化值 0-100")
    created_at = Column(DateTime, server_default=func.now())


class IndexResult(Base):
    __tablename__ = "t_index_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("t_company.id"), nullable=False)
    year = Column(Integer, nullable=False)
    score = Column(Float, nullable=False, comment="主体自律指数 0-100")
    level = Column(String(8), nullable=False, comment="等级：A/B/C/D")
    d1_score = Column(Float, comment="信息披露质量得分")
    d2_score = Column(Float, comment="董事会治理有效性得分")
    d3_score = Column(Float, comment="内部控制与合规性得分")
    d4_score = Column(Float, comment="第三方声誉得分")
    weight_scheme = Column(String(32), default="ahp_transformer", comment="赋权方案")
    created_at = Column(DateTime, server_default=func.now())
