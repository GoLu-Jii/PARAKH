from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthenticatedUser, get_current_user
from app.db.models.topic import Topic
from app.db.repositories.progress import ProgressRepository
from app.db.session import get_db
from app.schemas.topic import TopicOut

router = APIRouter(prefix="", tags=["Topics"])


@router.get(
    "/topics",
    response_model=list[TopicOut],
)
async def get_topics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch all topics
    stmt = select(Topic).order_by(Topic.id)
    res = await db.execute(stmt)
    all_topics = res.scalars().all()

    # Fetch student's current progress
    progress_rows = await ProgressRepository.get_student_topic_progress(
        db, current_user.id
    )
    progress_map = {p.topic_id: p.current_level for p in progress_rows}

    results = []
    for t in all_topics:
        level = progress_map.get(t.id)
        results.append(
            TopicOut(
                id=t.id,
                name=t.name,
                current_level=level,
            )
        )

    return results
