from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.attempt import Attempt
    from app.db.models.interview_session import InterviewSession
    from app.db.models.student_badge import StudentBadge
    from app.db.models.student_concept_state import StudentConceptState
    from app.db.models.student_topic_progress import StudentTopicProgress


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    avatar: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    topic_progress: Mapped[list["StudentTopicProgress"]] = relationship("StudentTopicProgress", back_populates="student", cascade="all, delete-orphan")
    concept_states: Mapped[list["StudentConceptState"]] = relationship("StudentConceptState", back_populates="student", cascade="all, delete-orphan")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship("InterviewSession", back_populates="student", cascade="all, delete-orphan")
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="student", cascade="all, delete-orphan")
    badges: Mapped[list["StudentBadge"]] = relationship("StudentBadge", back_populates="student", cascade="all, delete-orphan")
