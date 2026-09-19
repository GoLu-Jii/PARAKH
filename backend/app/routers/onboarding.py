from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthenticatedUser, get_current_user
from app.db.models.topic import Topic
from app.db.repositories.progress import ProgressRepository
from app.db.repositories.students import StudentRepository
from app.db.session import get_db
from app.schemas.onboarding import OnboardingRequestSchema, OnboardingResponseSchema

router = APIRouter(prefix="", tags=["Onboarding"])


@router.post(
    "/onboarding",
    response_model=OnboardingResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def complete_onboarding(
    payload: OnboardingRequestSchema,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Validate that topic IDs exist in the database
    requested_topic_ids = [t.topic_id for t in payload.topic_selections]
    stmt = select(Topic.id).where(Topic.id.in_(requested_topic_ids))
    res = await db.execute(stmt)
    existing_topic_ids = set(res.scalars().all())

    invalid_ids = set(requested_topic_ids) - existing_topic_ids
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid topic IDs provided: {sorted(list(invalid_ids))}",
        )

    # 2. Get or create student record with timezone
    student = await StudentRepository.get_or_create(
        session=db,
        user_id=current_user.id,
        email=current_user.email,
        user_metadata=current_user.user_metadata,
        timezone=payload.timezone,
    )

    # 3. Create or update student_topic_progress rows at Level 1
    progress_rows = await ProgressRepository.create_or_update_progress(
        session=db,
        student_id=student.id,
        topic_ids=requested_topic_ids,
    )

    await db.commit()

    return OnboardingResponseSchema(
        success=True,
        message="Onboarding completed successfully",
        student_id=str(student.id),
        topics_count=len(progress_rows),
    )
