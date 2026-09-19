from typing import Any
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.attempt import Attempt


class AttemptRepository:
    @staticmethod
    async def create_attempt(
        session: AsyncSession,
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        question_id: int,
        transcript: str,
        addressed_concepts: list[str],
        gaps: list[str],
        score: float,
        follow_up_id_used: int | None = None,
    ) -> Attempt:
        attempt = Attempt(
            session_id=session_id,
            student_id=student_id,
            question_id=question_id,
            transcript=transcript,
            addressed_concepts=addressed_concepts,
            gaps=gaps,
            score=score,
            follow_up_id_used=follow_up_id_used,
        )
        session.add(attempt)
        await session.flush()
        return attempt

    @staticmethod
    async def get_attempts_by_session_id(
        session: AsyncSession, session_id: uuid.UUID
    ) -> list[Attempt]:
        stmt = (
            select(Attempt)
            .options(
                selectinload(Attempt.question),
                selectinload(Attempt.follow_up_used),
            )
            .where(Attempt.session_id == session_id)
            .order_by(Attempt.timestamp.asc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_attempt_by_id(
        session: AsyncSession, attempt_id: uuid.UUID
    ) -> Attempt | None:
        stmt = select(Attempt).where(Attempt.id == attempt_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_attempt_followup(
        session: AsyncSession,
        attempt_id: uuid.UUID,
        follow_up_transcript: str,
        follow_up_addressed: Any,
        follow_up_score: float,
    ) -> Attempt | None:
        attempt = await AttemptRepository.get_attempt_by_id(session, attempt_id)
        if attempt:
            attempt.follow_up_transcript = follow_up_transcript
            attempt.follow_up_addressed = follow_up_addressed
            attempt.follow_up_score = follow_up_score
            await session.flush()
        return attempt
