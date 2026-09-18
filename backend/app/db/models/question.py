from typing import TYPE_CHECKING, Any
from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.attempt import Attempt
    from app.db.models.concept import Concept
    from app.db.models.follow_up import FollowUp


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_concepts: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    is_llm_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    concept: Mapped["Concept"] = relationship("Concept", back_populates="questions")
    follow_ups: Mapped[list["FollowUp"]] = relationship("FollowUp", back_populates="question", cascade="all, delete-orphan")
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="question", cascade="all, delete-orphan")
