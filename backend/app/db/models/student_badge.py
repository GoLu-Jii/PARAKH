from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.badge import Badge
    from app.db.models.student import Student


class StudentBadge(Base):
    __tablename__ = "student_badges"

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("students.id", ondelete="CASCADE"),primary_key=True,)
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="badges")
    badge: Mapped["Badge"] = relationship("Badge", back_populates="student_badges")
