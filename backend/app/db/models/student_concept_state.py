from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.concept import Concept
    from app.db.models.student import Student


class StudentConceptState(Base):
    __tablename__ = "student_concept_state"

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("students.id", ondelete="CASCADE"),primary_key=True,)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="not_seen", nullable=False)
    last_attempt_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="concept_states")
    concept: Mapped["Concept"] = relationship("Concept", back_populates="student_states")
