from pydantic import BaseModel


class ReportRequest(BaseModel):
    stock_code: str
    year: int
