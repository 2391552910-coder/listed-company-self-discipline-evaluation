from pydantic import BaseModel, ConfigDict


class AnnualReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    year: int
    file_path: str | None
    parse_status: str
    chapter_count: int
    chunk_count: int


class ReportChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: int
    chapter: str | None
    content: str
    dimension_tag: str | None
    seq: int | None
