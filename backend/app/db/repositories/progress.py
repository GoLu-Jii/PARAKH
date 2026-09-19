import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.student_topic_progress import StudentTopicProgress


class ProgressRepository:
    @staticmethod
    async def get_student_topic_progress(
        session: AsyncSession, student_id: uuid.UUID
    ) -> list[StudentTopicProgress]:
        stmt = select(StudentTopicProgress).where(
            StudentTopicProgress.student_id == student_id
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_or_update_progress(
        session: AsyncSession, student_id: uuid.UUID, topic_ids: list[int]
    ) -> list[StudentTopicProgress]:
        existing_progress = await ProgressRepository.get_student_topic_progress(
            session, student_id
        )
        existing_topic_ids = {p.topic_id for p in existing_progress}

        new_progress_rows = []
        for topic_id in topic_ids:
            if topic_id not in existing_topic_ids:
                row = StudentTopicProgress(
                    student_id=student_id,
                    topic_id=topic_id,
                    current_level=1,
                )
                session.add(row)
                new_progress_rows.append(row)

        if new_progress_rows:
            await session.flush()

        return await ProgressRepository.get_student_topic_progress(
            session, student_id
        )
