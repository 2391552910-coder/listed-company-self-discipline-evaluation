from pydantic import BaseModel, ConfigDict


class CompanyCreate(BaseModel):
    stock_code: str
    stock_name: str
    industry: str | None = None
    market: str | None = None
    listed_date: str | None = None


class CompanyOut(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
