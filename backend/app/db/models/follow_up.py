from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.attempt import Attempt
    from app.db.models.question import Question


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    follow_up_text: Mapped[str] = mapped_column(Text, nullable=False)
    targets_gap: Mapped[str] = mapped_column(String(255), nullable=False)

    question: Mapped["Question"] = relationship("Question", back_populates="follow_ups")
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="follow_up_used")
