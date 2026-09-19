from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.concept import Concept
from app.db.models.follow_up import FollowUp
from app.db.models.question import Question


class QuestionRepository:
    @staticmethod
    async def get_question_by_id(
        session: AsyncSession, question_id: int
    ) -> Question | None:
        stmt = (
            select(Question)
            .options(selectinload(Question.concept), selectinload(Question.follow_ups))
            .where(Question.id == question_id)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_candidate_questions_by_topic_and_level(
        session: AsyncSession, topic_id: int, target_level: int
    ) -> list[Question]:
        stmt = (
            select(Question)
            .join(Concept, Question.concept_id == Concept.id)
            .options(selectinload(Question.concept), selectinload(Question.follow_ups))
            .where(
                Concept.topic_id == topic_id,
                Concept.cognitive_level == target_level,
            )
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_follow_ups_by_question_id(
        session: AsyncSession, question_id: int
    ) -> list[FollowUp]:
        stmt = select(FollowUp).where(FollowUp.question_id == question_id)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_follow_up_by_id(
        session: AsyncSession, follow_up_id: int
    ) -> FollowUp | None:
        stmt = select(FollowUp).where(FollowUp.id == follow_up_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()
