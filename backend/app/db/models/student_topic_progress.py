from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.student import Student
    from app.db.models.topic import Topic


class StudentTopicProgress(Base):
    __tablename__ = "student_topic_progress"

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("students.id", ondelete="CASCADE"),primary_key=True,)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    current_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_interview_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="topic_progress")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="student_progress")
