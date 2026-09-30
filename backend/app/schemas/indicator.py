from pydantic import BaseModel, ConfigDict


class IndicatorValueIn(BaseModel):
    """CSMAR 指标导入单行数据"""
    stock_code: str
    indicator_code: str
    year: int
    raw_value: float


class IndicatorValueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    indicator_id: int
    year: int
    raw_value: float | None
    std_value: float | None


class IndexResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    year: int
    score: float
    level: str
    d1_score: float | None
    d2_score: float | None
    d3_score: float | None
    d4_score: float | None
    weight_scheme: str | None


class AHPJudgmentMatrixIn(BaseModel):
    """专家 AHP 判断矩阵（12x12 或按维度）"""
    matrix: list[list[float]]
