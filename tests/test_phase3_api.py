import asyncio
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.auth.deps import AuthenticatedUser, get_current_user
from app.db.models.concept import Concept
from app.db.models.follow_up import FollowUp
from app.db.models.question import Question
from app.db.models.student import Student
from app.db.repositories.progress import ProgressRepository
from app.db.repositories.questions import QuestionRepository
from app.db.repositories.students import StudentRepository
from app.db.session import AsyncSessionLocal
from app.llm.evaluate_answer import AnswerEvaluationResult
from app.llm.evaluate_followup import FollowUpEvaluationResult
from app.main import app

# Create mock authenticated user
mock_user_id = uuid.uuid4()
mock_user = AuthenticatedUser(
    id=mock_user_id,
    email="phase3_test@example.com",
    user_metadata={"name": "Phase 3 Tester"},
)

# Override auth dependency for testing
app.dependency_overrides[get_current_user] = lambda: mock_user

created_test_question_ids = []


async def setup_test_data(session):
    global created_test_question_ids
    created_test_question_ids.clear()

    # Create student record
    student = await StudentRepository.get_or_create(
        session=session,
        user_id=mock_user.id,
        email=mock_user.email,
        timezone="Asia/Kolkata",
    )
    # Create topic progress at Level 2 for DSA (topic_id=1)
    await ProgressRepository.create_or_update_progress(
        session=session, student_id=student.id, topic_ids=[1]
    )

    # Ensure Concept at Level 2 exists
    stmt = select(Concept).where(Concept.topic_id == 1, Concept.cognitive_level == 2)
    res = await session.execute(stmt)
    concept_level2 = res.scalars().first()
    if not concept_level2:
        concept_level2 = Concept(topic_id=1, name="Test Array Concept", cognitive_level=2)
        session.add(concept_level2)
        await session.flush()

    # Create 4 test questions at Level 2
    for i in range(1, 5):
        q_text = f"Phase 3 Test Question {i} for Level 2"
        stmt_q = select(Question).where(
            Question.concept_id == concept_level2.id,
            Question.question_text == q_text,
        )
        res_q = await session.execute(stmt_q)
        q_obj = res_q.scalar_one_or_none()
        if not q_obj:
            q_obj = Question(
                concept_id=concept_level2.id,
                question_text=q_text,
                expected_concepts=[f"Concept Point {i}.1", f"Concept Point {i}.2"],
                is_llm_generated=False,
            )
            session.add(q_obj)
            await session.flush()

            # Add follow-up for Question 2
            fu = FollowUp(
                question_id=q_obj.id,
                follow_up_text=f"Follow-up for Question {i}",
                targets_gap=f"Concept Point {i}.2",
            )
            session.add(fu)

        created_test_question_ids.append(q_obj.id)

    await session.commit()


async def cleanup_test_data(session):
    stmt = select(Student).where(Student.id == mock_user.id)
    res = await session.execute(stmt)
    student = res.scalar_one_or_none()
    if student:
        await session.delete(student)

    if created_test_question_ids:
        stmt_del = select(Question).where(Question.id.in_(created_test_question_ids))
        res_del = await session.execute(stmt_del)
        for q in res_del.scalars().all():
            await session.delete(q)

    await session.commit()


@patch("app.routers.interview.evaluate_main_answer")
@patch("app.routers.interview.evaluate_followup_answer")
@patch("app.routers.report.generate_interview_report")
async def run_phase3_api_tests(mock_report, mock_eval_fu, mock_eval_main):
    async with AsyncSessionLocal() as session:
        await setup_test_data(session)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Setup LLM mocks
            mock_eval_main.return_value = AnswerEvaluationResult(
                addressed_concepts=["Concept Point 1.1"],
                score=8.5,
                gaps=[],
                ask_follow_up=False,
                follow_up_id=None,
            )
            mock_eval_fu.return_value = FollowUpEvaluationResult(
                addressed=True,
                score=9.0,
                feedback="Great job!",
            )
            mock_report.return_value = "# Report\nGreat interview performance!"

            # 1. Start Interview
            start_resp = await client.post("/interview/start", json={"topic_id": 1, "target_level": 2})
            assert start_resp.status_code == 200, f"Start failed: {start_resp.text}"
            data = start_resp.json()
            session_id = data["session_id"]
            first_q_id = data["first_question"]["id"]
            assert data["target_level"] == 2
            assert data["total_questions"] == 4
            print("Start interview PASSED.")

            # 2. Answer Question 1
            ans1_resp = await client.post(
                f"/interview/{session_id}/answer",
                json={"question_id": first_q_id, "transcript": "A hash map uses a hash function to map keys to bucket indices."},
            )
            assert ans1_resp.status_code == 200, f"Ans 1 failed: {ans1_resp.text}"
            ans1_data = ans1_resp.json()
            assert ans1_data["score"] == 8.5
            assert not ans1_data["is_session_complete"]
            q2_id = ans1_data["next_question"]["id"]
            print("Answer question 1 PASSED.")

            # 3. Answer Question 2 with follow-up request
            # Get follow-up ID for question 2
            async with AsyncSessionLocal() as session:
                q2_obj = await QuestionRepository.get_question_by_id(session, q2_id)
                q2_fu_id = q2_obj.follow_ups[0].id if q2_obj and q2_obj.follow_ups else 1

            mock_eval_main.return_value = AnswerEvaluationResult(
                addressed_concepts=["Concept Point 2.1"],
                score=6.0,
                gaps=["Concept Point 2.2"],
                ask_follow_up=True,
                follow_up_id=q2_fu_id,
            )

            ans2_resp = await client.post(
                f"/interview/{session_id}/answer",
                json={"question_id": q2_id, "transcript": "Two pointers move inwards based on sum."},
            )
            assert ans2_resp.status_code == 200, f"Ans 2 failed: {ans2_resp.text}"
            ans2_data = ans2_resp.json()
            assert ans2_data["ask_follow_up"]
            assert ans2_data["follow_up_prompt"] is not None

            # 4. Answer Follow-up for Question 2
            fu_resp = await client.post(
                f"/interview/{session_id}/followup-answer",
                json={"transcript": "The array must be sorted so pointer movements guarantee correct bounds."},
            )
            assert fu_resp.status_code == 200, f"Followup failed: {fu_resp.text}"
            fu_data = fu_resp.json()
            assert fu_data["follow_up_addressed"]
            q3_id = fu_data["next_question"]["id"]
            print("Answer question 2 + follow-up PASSED.")

            # Reset mock to normal answers for remaining questions
            mock_eval_main.return_value = AnswerEvaluationResult(
                addressed_concepts=["Concept Point 3.1"],
                score=8.0,
                gaps=[],
                ask_follow_up=False,
                follow_up_id=None,
            )

            # 5. Answer Question 3
            ans3_resp = await client.post(
                f"/interview/{session_id}/answer",
                json={"question_id": q3_id, "transcript": "In-place algorithms modify memory directly."},
            )
            assert ans3_resp.status_code == 200, f"Ans 3 failed: {ans3_resp.text}"
            q4_id = ans3_resp.json()["next_question"]["id"]

            # 6. Answer Question 4 (Final main question)
            ans4_resp = await client.post(
                f"/interview/{session_id}/answer",
                json={"question_id": q4_id, "transcript": "Final question answer covering trade-offs."},
            )
            assert ans4_resp.status_code == 200, f"Ans 4 failed: {ans4_resp.text}"
            ans4_data = ans4_resp.json()
            assert ans4_data["is_session_complete"]
            assert ans4_data["session_outcome"] == "level_up"
            print("Completed 4-question session PASSED (outcome = level_up).")

            # 7. Fetch Report
            report_resp = await client.get(f"/interview/{session_id}/report")
            assert report_resp.status_code == 200, f"Report failed: {report_resp.text}"
            report_data = report_resp.json()
            assert report_data["outcome"] == "level_up"
            assert "Great interview performance!" in report_data["report_markdown"]
            print("Fetch report PASSED.")

            # 8. Test Session Ownership Security
            other_user = AuthenticatedUser(id=uuid.uuid4(), email="hacker@example.com")
            app.dependency_overrides[get_current_user] = lambda: other_user

            stolen_resp = await client.post(
                f"/interview/{session_id}/answer",
                json={"question_id": 1, "transcript": "Hacking attempt"},
            )
            assert stolen_resp.status_code == 403, f"Expected 403, got {stolen_resp.status_code}"
            print("Session ownership security test PASSED.")

    finally:
        async with AsyncSessionLocal() as session:
            await cleanup_test_data(session)


if __name__ == "__main__":
    asyncio.run(run_phase3_api_tests())
