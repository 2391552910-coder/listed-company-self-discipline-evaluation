from pydantic import BaseModel, ConfigDict


class EvaluationCreate(BaseModel):
    stock_code: str
    year: int
    rag_enabled: bool = True


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    year: int
    status: str
    model_name: str | None
    rag_enabled: int
    d1_evaluation: str | None
    d2_evaluation: str | None
    d3_evaluation: str | None
    d4_evaluation: str | None
    overall_summary: str | None
    score: float | None


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    evaluation_id: int
    dimension_code: str | None
    regulation_title: str | None
    regulation_source: str | None
    clause: str | None
    similarity: float | None
