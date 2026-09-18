from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.concept import Concept
    from app.db.models.interview_session import InterviewSession
    from app.db.models.student_topic_progress import StudentTopicProgress


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    concepts: Mapped[list["Concept"]] = relationship("Concept", back_populates="topic", cascade="all, delete-orphan")
    student_progress: Mapped[list["StudentTopicProgress"]] = relationship("StudentTopicProgress", back_populates="topic", cascade="all, delete-orphan")
    interview_sessions: Mapped[list["InterviewSession"]] = relationship("InterviewSession", back_populates="topic", cascade="all, delete-orphan")
