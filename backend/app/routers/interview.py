import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthenticatedUser, get_current_user
from app.db.models.topic import Topic
from app.db.repositories.attempts import AttemptRepository
from app.db.repositories.concept_state import ConceptStateRepository
from app.db.repositories.progress import ProgressRepository
from app.db.repositories.questions import QuestionRepository
from app.db.repositories.sessions import SessionRepository
from app.db.repositories.students import StudentRepository
from app.db.session import get_db
from app.engine.leveling import compute_next_level, evaluate_level_outcome
from app.engine.selection import select_next_question
from app.engine.session_flow import get_interview_day_bounds
from app.llm.evaluate_answer import evaluate_main_answer
from app.llm.evaluate_followup import evaluate_followup_answer
from app.schemas.interview import (
    AnswerEvaluationOut,
    FollowUpEvaluationOut,
    FollowUpOut,
    QuestionOut,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitFollowUpRequest,
)

router = APIRouter(prefix="/interview", tags=["Interview Engine"])


@router.post("/start", response_model=StartInterviewResponse, status_code=status.HTTP_200_OK)
async def start_interview(
    payload: StartInterviewRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch student record
    student = await StudentRepository.get_or_create(
        session=db,
        user_id=current_user.id,
        email=current_user.email,
        user_metadata=current_user.user_metadata,
    )

    # 2. Validate topic exists
    stmt = select(Topic).where(Topic.id == payload.topic_id)
    res = await db.execute(stmt)
    topic = res.scalar_one_or_none()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with ID {payload.topic_id} not found",
        )

    # 3. Determine target level
    progress_rows = await ProgressRepository.get_student_topic_progress(db, student.id)
    progress_map = {p.topic_id: p.current_level for p in progress_rows}
    current_level = progress_map.get(payload.topic_id, 1)

    if payload.target_level and payload.target_level > current_level:
        target_level = payload.target_level
    else:
        target_level = payload.target_level or current_level

    # 4. Enforce Daily Limit (max 2 non-dismissed sessions per 4:00 AM interview day)
    start_utc, end_utc = get_interview_day_bounds(student.timezone)
    daily_count = await SessionRepository.count_non_dismissed_sessions_in_window(
        db, student.id, start_utc, end_utc
    )
    if daily_count >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily interview limit reached (maximum 2 sessions per interview day)",
        )

    # 5. Deterministically select first question
    candidates = await QuestionRepository.get_candidate_questions_by_topic_and_level(
        db, payload.topic_id, target_level
    )
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No questions available for topic '{topic.name}' at level {target_level}",
        )

    concept_states = await ConceptStateRepository.get_student_concept_states(db, student.id)
    first_question = select_next_question(candidates, [], concept_states)

    if not first_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No questions available for topic '{topic.name}' at level {target_level}",
        )

    # 6. Create interview_session row
    new_session = await SessionRepository.create_session(
        db,
        student_id=student.id,
        topic_id=payload.topic_id,
        target_level=target_level,
    )
    new_session.question_ids_asked = [first_question.id]
    await db.commit()

    return StartInterviewResponse(
        session_id=str(new_session.id),
        topic_id=payload.topic_id,
        target_level=target_level,
        current_question_index=1,
        total_questions=4,
        first_question=QuestionOut(
            id=first_question.id,
            question_text=first_question.question_text,
            concept_id=first_question.concept_id,
            cognitive_level=first_question.concept.cognitive_level,
        ),
    )


@router.post("/{session_id}/answer", response_model=AnswerEvaluationOut)
async def submit_main_answer(
    session_id: uuid.UUID,
    payload: SubmitAnswerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch & authorize session
    session_obj = await SessionRepository.get_session_by_id(db, session_id)
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_obj.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if session_obj.ended_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is already completed")

    asked_ids = session_obj.question_ids_asked or []
    if not asked_ids or asked_ids[-1] != payload.question_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question ID for current turn")

    # Check if attempt already exists for this question
    existing_attempts = await AttemptRepository.get_attempts_by_session_id(db, session_id)
    if any(a.question_id == payload.question_id for a in existing_attempts):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Answer already submitted for this question")

    # 2. Load Question & follow-ups
    question = await QuestionRepository.get_question_by_id(db, payload.question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    candidate_followups = [
        {"id": f.id, "text": f.follow_up_text, "targets_gap": f.targets_gap}
        for f in question.follow_ups
    ]

    # 3. Evaluate main answer via LLM
    eval_res = evaluate_main_answer(
        question_text=question.question_text,
        expected_concepts=question.expected_concepts or [],
        candidate_follow_ups=candidate_followups,
        transcript=payload.transcript,
    )

    # 4. Server-side validation of follow_up_id
    valid_followup_ids = {f.id for f in question.follow_ups}
    follow_up_id_to_use = None
    follow_up_obj = None

    if eval_res.ask_follow_up and eval_res.follow_up_id in valid_followup_ids:
        follow_up_id_to_use = eval_res.follow_up_id
        follow_up_obj = next((f for f in question.follow_ups if f.id == follow_up_id_to_use), None)
    else:
        eval_res.ask_follow_up = False
        eval_res.follow_up_id = None

    # 5. Save attempt row
    attempt = await AttemptRepository.create_attempt(
        session=db,
        session_id=session_id,
        student_id=current_user.id,
        question_id=payload.question_id,
        transcript=payload.transcript,
        addressed_concepts=eval_res.addressed_concepts,
        gaps=eval_res.gaps,
        score=eval_res.score,
        follow_up_id_used=follow_up_id_to_use,
    )

    # 6. Return follow-up prompt if requested
    if eval_res.ask_follow_up and follow_up_obj:
        await db.commit()
        return AnswerEvaluationOut(
            attempt_id=str(attempt.id),
            question_id=payload.question_id,
            addressed_concepts=eval_res.addressed_concepts,
            score=eval_res.score,
            gaps=eval_res.gaps,
            ask_follow_up=True,
            follow_up_id=follow_up_id_to_use,
            follow_up_prompt=FollowUpOut(
                id=follow_up_obj.id,
                follow_up_text=follow_up_obj.follow_up_text,
            ),
            is_session_complete=False,
        )

    # 7. If no follow-up, proceed to next question OR complete session
    all_attempts = await AttemptRepository.get_attempts_by_session_id(db, session_id)
    if len(all_attempts) >= 4:
        # Complete Session!
        outcome, next_q, is_complete = await _finalize_session(db, session_obj, current_user.id)
        await db.commit()
        return AnswerEvaluationOut(
            attempt_id=str(attempt.id),
            question_id=payload.question_id,
            addressed_concepts=eval_res.addressed_concepts,
            score=eval_res.score,
            gaps=eval_res.gaps,
            ask_follow_up=False,
            is_session_complete=is_complete,
            session_outcome=outcome,
        )

    # Select next question
    next_question = await _select_and_attach_next_question(db, session_obj, current_user.id)
    await db.commit()

    return AnswerEvaluationOut(
        attempt_id=str(attempt.id),
        question_id=payload.question_id,
        addressed_concepts=eval_res.addressed_concepts,
        score=eval_res.score,
        gaps=eval_res.gaps,
        ask_follow_up=False,
        next_question=QuestionOut(
            id=next_question.id,
            question_text=next_question.question_text,
            concept_id=next_question.concept_id,
            cognitive_level=next_question.concept.cognitive_level,
        ),
        is_session_complete=False,
    )


@router.post("/{session_id}/followup-answer", response_model=FollowUpEvaluationOut)
async def submit_followup_answer(
    session_id: uuid.UUID,
    payload: SubmitFollowUpRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch & authorize session
    session_obj = await SessionRepository.get_session_by_id(db, session_id)
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_obj.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if session_obj.ended_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is already completed")

    # 2. Find attempt needing follow-up evaluation
    attempts = await AttemptRepository.get_attempts_by_session_id(db, session_id)
    pending_attempt = next(
        (a for a in attempts if a.follow_up_id_used is not None and a.follow_up_transcript is None),
        None,
    )
    if not pending_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending follow-up question for this session",
        )

    # Load follow-up
    follow_up = await QuestionRepository.get_follow_up_by_id(db, pending_attempt.follow_up_id_used)
    question = await QuestionRepository.get_question_by_id(db, pending_attempt.question_id)

    # 3. Evaluate follow-up
    fu_eval = evaluate_followup_answer(
        question_text=question.question_text if question else "",
        target_gap=follow_up.targets_gap if follow_up else "",
        follow_up_text=follow_up.follow_up_text if follow_up else "",
        follow_up_transcript=payload.transcript,
    )

    # 4. Update attempt row
    await AttemptRepository.update_attempt_followup(
        session=db,
        attempt_id=pending_attempt.id,
        follow_up_transcript=payload.transcript,
        follow_up_addressed=fu_eval.addressed,
        follow_up_score=fu_eval.score,
    )

    # 5. Check if session is complete (4 main attempts)
    all_attempts = await AttemptRepository.get_attempts_by_session_id(db, session_id)
    if len(all_attempts) >= 4:
        outcome, _, is_complete = await _finalize_session(db, session_obj, current_user.id)
        await db.commit()
        return FollowUpEvaluationOut(
            attempt_id=str(pending_attempt.id),
            follow_up_addressed=fu_eval.addressed,
            follow_up_score=fu_eval.score,
            is_session_complete=is_complete,
            session_outcome=outcome,
        )

    # Next question
    next_question = await _select_and_attach_next_question(db, session_obj, current_user.id)
    await db.commit()

    return FollowUpEvaluationOut(
        attempt_id=str(pending_attempt.id),
        follow_up_addressed=fu_eval.addressed,
        follow_up_score=fu_eval.score,
        next_question=QuestionOut(
            id=next_question.id,
            question_text=next_question.question_text,
            concept_id=next_question.concept_id,
            cognitive_level=next_question.concept.cognitive_level,
        ),
        is_session_complete=False,
    )


async def _select_and_attach_next_question(db: AsyncSession, session_obj, student_id: uuid.UUID):
    candidates = await QuestionRepository.get_candidate_questions_by_topic_and_level(
        db, session_obj.topic_id, session_obj.target_level
    )
    concept_states = await ConceptStateRepository.get_student_concept_states(db, student_id)
    already_asked = session_obj.question_ids_asked or []

    next_q = select_next_question(candidates, already_asked, concept_states)
    if not next_q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No additional questions available for this level",
        )

    updated_asked = list(already_asked) + [next_q.id]
    await SessionRepository.update_session_question_ids(db, session_obj.id, updated_asked)
    return next_q


async def _finalize_session(db: AsyncSession, session_obj, student_id: uuid.UUID):
    attempts = await AttemptRepository.get_attempts_by_session_id(db, session_obj.id)
    scores = [a.score for a in attempts if a.score is not None]

    outcome = evaluate_level_outcome(scores)

    # Update Student Topic Progress
    progress_rows = await ProgressRepository.get_student_topic_progress(db, student_id)
    current_progress = next((p for p in progress_rows if p.topic_id == session_obj.topic_id), None)
    curr_level = current_progress.current_level if current_progress else 1

    new_level = compute_next_level(curr_level, session_obj.target_level, outcome)
    if current_progress and new_level != curr_level:
        current_progress.current_level = new_level
        await db.flush()

    # Update Concept States
    concept_updates = {}
    for a in attempts:
        q = a.question
        if not q:
            continue
        c_id = q.concept_id
        if a.gaps or (a.score and a.score < 6.0):
            concept_updates[c_id] = "weak"
        elif a.score and a.score >= 7.0:
            concept_updates[c_id] = "cleared"

    await ConceptStateRepository.update_concept_states(db, student_id, concept_updates)

    # Complete session in DB
    await SessionRepository.complete_session(db, session_obj.id, outcome)
    return outcome, None, True
