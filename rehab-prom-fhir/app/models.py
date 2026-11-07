"""Database model. One row per completed questionnaire response."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class ResponseRow(Base):
    __tablename__ = "questionnaire_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_ref: Mapped[str] = mapped_column(String(64), index=True)
    questionnaire_id: Mapped[str] = mapped_column(String(64))
    authored: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    answers: Mapped[dict] = mapped_column(JSON)
    total_score: Mapped[int] = mapped_column(Integer)
    needs_review: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (Index("ix_patient_authored", "patient_ref", "authored"),)
