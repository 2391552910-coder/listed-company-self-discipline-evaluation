from sqlalchemy.orm import Session

from app.models.annual_report import AnnualReport, ReportChunk
from app.repositories.base import BaseRepository


class AnnualReportRepository(BaseRepository[AnnualReport]):
    def __init__(self):
        super().__init__(AnnualReport)

    def get_by_company_year(self, db: Session, company_id: int, year: int) -> AnnualReport | None:
        return (
            db.query(AnnualReport)
            .filter(AnnualReport.company_id == company_id, AnnualReport.year == year)
            .first()
        )


class ReportChunkRepository(BaseRepository[ReportChunk]):
    def __init__(self):
        super().__init__(ReportChunk)

    def list_by_report(self, db: Session, report_id: int) -> list[ReportChunk]:
        return (
            db.query(ReportChunk)
            .filter(ReportChunk.report_id == report_id)
            .order_by(ReportChunk.seq)
            .all()
        )

    def delete_by_report(self, db: Session, report_id: int) -> None:
        db.query(ReportChunk).filter(ReportChunk.report_id == report_id).delete()
        db.commit()


annual_report_repository = AnnualReportRepository()
report_chunk_repository = ReportChunkRepository()
