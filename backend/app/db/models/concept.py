from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.question import Question
    from app.db.models.student_concept_state import StudentConceptState
    from app.db.models.topic import Topic


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cognitive_level: Mapped[int] = mapped_column(Integer, nullable=False)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="concepts")
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="concept", cascade="all, delete-orphan")
    student_states: Mapped[list["StudentConceptState"]] = relationship("StudentConceptState", back_populates="concept", cascade="all, delete-orphan")
