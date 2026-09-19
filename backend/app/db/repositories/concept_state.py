from datetime import datetime
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.student_concept_state import StudentConceptState


class ConceptStateRepository:
    @staticmethod
    async def get_student_concept_states(
        session: AsyncSession, student_id: uuid.UUID
    ) -> dict[int, str]:
        stmt = select(StudentConceptState).where(
            StudentConceptState.student_id == student_id
        )
        res = await session.execute(stmt)
        rows = res.scalars().all()
        return {r.concept_id: r.status for r in rows}

    @staticmethod
    async def update_concept_states(
        session: AsyncSession,
        student_id: uuid.UUID,
        concept_updates: dict[int, str],
    ) -> None:
        if not concept_updates:
            return

        stmt = select(StudentConceptState).where(
            StudentConceptState.student_id == student_id,
            StudentConceptState.concept_id.in_(list(concept_updates.keys())),
        )
        res = await session.execute(stmt)
        existing_rows = {r.concept_id: r for r in res.scalars().all()}

        now = datetime.now()
        for concept_id, new_status in concept_updates.items():
            if concept_id in existing_rows:
                row = existing_rows[concept_id]
                # 'weak' takes precedence if already marked weak or updated to weak
                if new_status == "weak" or row.status != "weak":
                    row.status = new_status
                row.last_attempt_date = now
            else:
                row = StudentConceptState(
                    student_id=student_id,
                    concept_id=concept_id,
                    status=new_status,
                    last_attempt_date=now,
                )
                session.add(row)

        await session.flush()
