from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.follow_up import FollowUp
    from app.db.models.interview_session import InterviewSession
    from app.db.models.question import Question
    from app.db.models.student import Student


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("interview_sessions.id", ondelete="CASCADE"),nullable=False,)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    addressed_concepts: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    gaps: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    follow_up_id_used: Mapped[int | None] = mapped_column(Integer, ForeignKey("follow_ups.id", ondelete="SET NULL"), nullable=True)
    follow_up_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_addressed: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    follow_up_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="attempts")
    student: Mapped["Student"] = relationship("Student", back_populates="attempts")
    question: Mapped["Question"] = relationship("Question", back_populates="attempts")
    follow_up_used: Mapped["FollowUp | None"] = relationship("FollowUp", back_populates="attempts")
