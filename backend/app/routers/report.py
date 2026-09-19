import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthenticatedUser, get_current_user
from app.db.models.topic import Topic
from app.db.repositories.attempts import AttemptRepository
from app.db.repositories.sessions import SessionRepository
from app.db.session import get_db
from app.llm.generate_report import generate_interview_report
from app.schemas.interview import ReportResponse

router = APIRouter(prefix="/interview", tags=["Reports"])


@router.get("/{session_id}/report", response_model=ReportResponse)
async def get_session_report(
    session_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch & authorize session
    session_obj = await SessionRepository.get_session_by_id(db, session_id)
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_obj.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if session_obj.ended_at is None or session_obj.outcome is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not available for an incomplete session",
        )

    # 2. Fetch attempts & validate 4 attempts
    attempts = await AttemptRepository.get_attempts_by_session_id(db, session_id)
    if len(attempts) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session does not contain 4 complete attempts",
        )

    # 3. Fetch topic name
    stmt = select(Topic.name).where(Topic.id == session_obj.topic_id)
    res = await db.execute(stmt)
    topic_name = res.scalar_one_or_none() or f"Topic #{session_obj.topic_id}"

    # 4. Prepare structured data for report generation (NO raw transcripts)
    attempt_summaries = [
        {
            "question_id": a.question_id,
            "score": a.score or 0.0,
            "addressed_concepts": a.addressed_concepts or [],
            "gaps": a.gaps or [],
            "follow_up_used": a.follow_up_id_used is not None,
            "follow_up_addressed": a.follow_up_addressed,
            "follow_up_score": a.follow_up_score,
        }
        for a in attempts
    ]

    # 5. Generate narrative report
    report_markdown = generate_interview_report(
        topic_name=topic_name,
        target_level=session_obj.target_level,
        outcome=session_obj.outcome,
        attempt_summaries=attempt_summaries,
    )

    return ReportResponse(
        session_id=str(session_obj.id),
        topic_name=topic_name,
        target_level=session_obj.target_level,
        outcome=session_obj.outcome,
        report_markdown=report_markdown,
    )
