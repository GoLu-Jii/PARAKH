from datetime import datetime
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.interview_session import InterviewSession


class SessionRepository:
    @staticmethod
    async def create_session(
        session: AsyncSession,
        student_id: uuid.UUID,
        topic_id: int,
        target_level: int,
    ) -> InterviewSession:
        new_session = InterviewSession(
            student_id=student_id,
            topic_id=topic_id,
            target_level=target_level,
            started_at=datetime.now(),
            question_ids_asked=[],
            outcome=None,
        )
        session.add(new_session)
        await session.flush()
        return new_session

    @staticmethod
    async def get_session_by_id(
        session: AsyncSession, session_id: uuid.UUID
    ) -> InterviewSession | None:
        stmt = select(InterviewSession).where(InterviewSession.id == session_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_session_question_ids(
        session: AsyncSession,
        session_id: uuid.UUID,
        question_ids_asked: list[int],
    ) -> InterviewSession | None:
        interview_session = await SessionRepository.get_session_by_id(
            session, session_id
        )
        if interview_session:
            interview_session.question_ids_asked = question_ids_asked
            await session.flush()
        return interview_session

    @staticmethod
    async def complete_session(
        session: AsyncSession,
        session_id: uuid.UUID,
        outcome: str,
    ) -> InterviewSession | None:
        interview_session = await SessionRepository.get_session_by_id(
            session, session_id
        )
        if interview_session:
            interview_session.ended_at = datetime.now()
            interview_session.outcome = outcome
            await session.flush()
        return interview_session

    @staticmethod
    async def count_non_dismissed_sessions_in_window(
        session: AsyncSession,
        student_id: uuid.UUID,
        start_utc: datetime,
        end_utc: datetime,
    ) -> int:
        stmt = select(func.count(InterviewSession.id)).where(
            InterviewSession.student_id == student_id,
            InterviewSession.started_at >= start_utc,
            InterviewSession.started_at < end_utc,
            (InterviewSession.outcome == None) | (InterviewSession.outcome != "dismissed"),
        )
        res = await session.execute(stmt)
        return res.scalar() or 0
