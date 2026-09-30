from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation, EvaluationEvidence
from app.repositories.base import BaseRepository


class EvaluationRepository(BaseRepository[Evaluation]):
    def __init__(self):
        super().__init__(Evaluation)

    def get_by_company_year(self, db: Session, company_id: int, year: int) -> Evaluation | None:
        return (
            db.query(Evaluation)
            .filter(Evaluation.company_id == company_id, Evaluation.year == year)
            .order_by(Evaluation.id.desc())
            .first()
        )


class EvaluationEvidenceRepository(BaseRepository[EvaluationEvidence]):
    def __init__(self):
        super().__init__(EvaluationEvidence)

    def list_by_evaluation(self, db: Session, evaluation_id: int) -> list[EvaluationEvidence]:
        return (
            db.query(EvaluationEvidence)
            .filter(EvaluationEvidence.evaluation_id == evaluation_id)
            .all()
        )

    def delete_by_evaluation(self, db: Session, evaluation_id: int) -> None:
        db.query(EvaluationEvidence).filter(
            EvaluationEvidence.evaluation_id == evaluation_id
        ).delete()
        db.commit()


evaluation_repository = EvaluationRepository()
evaluation_evidence_repository = EvaluationEvidenceRepository()
