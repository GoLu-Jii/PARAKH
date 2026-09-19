import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.student import Student


class StudentRepository:
    @staticmethod
    async def get_by_id(session: AsyncSession, student_id: uuid.UUID) -> Student | None:
        stmt = select(Student).where(Student.id == student_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> Student | None:
        stmt = select(Student).where(Student.email == email)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        user_id: uuid.UUID,
        email: str,
        user_metadata: dict | None = None,
        timezone: str | None = None,
    ) -> Student:
        student = await StudentRepository.get_by_id(session, user_id)
        if student:
            if timezone and student.timezone != timezone:
                student.timezone = timezone
                await session.flush()
            return student

        # Generate deterministic & unique username from email/id
        email_prefix = email.split("@")[0] if email else "student"
        short_id = user_id.hex[:6]
        username = f"{email_prefix}_{short_id}"

        avatar = None
        if user_metadata:
            avatar = user_metadata.get("avatar_url") or user_metadata.get("picture")
        if not avatar:
            avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={username}"

        student = Student(
            id=user_id,
            email=email,
            username=username,
            avatar=avatar,
            timezone=timezone,
        )
        session.add(student)
        await session.flush()
        return student
