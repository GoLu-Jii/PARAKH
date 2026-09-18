from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.attempt import Attempt
    from app.db.models.student import Student
    from app.db.models.topic import Topic


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    target_level: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    question_ids_asked: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="interview_sessions")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="interview_sessions")
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="session", cascade="all, delete-orphan")
