import asyncio
import sys
import uuid
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select

from app.db.models.student import Student
from app.db.models.student_topic_progress import StudentTopicProgress
from app.db.models.topic import Topic
from app.db.repositories.progress import ProgressRepository
from app.db.repositories.students import StudentRepository
from app.db.session import AsyncSessionLocal
from app.main import app
from app.schemas.onboarding import OnboardingRequestSchema

client = TestClient(app)


def test_unauthenticated_requests():
    # 1. GET /topics without token -> 403 or 401
    r_topics = client.get("/topics")
    assert r_topics.status_code in (401, 403), f"Expected 401/403, got {r_topics.status_code}"

    # 2. POST /onboarding without token -> 401/403
    r_onboard = client.post("/onboarding", json={})
    assert r_onboard.status_code in (401, 403), f"Expected 401/403, got {r_onboard.status_code}"
    print("Unauthenticated protection test PASSED.")


def test_pydantic_onboarding_validation():
    # Fewer than 3 topics should raise ValidationError
    try:
        OnboardingRequestSchema(
            topic_selections=[
                {"topic_id": 1, "self_assessment": "beginner"},
                {"topic_id": 2, "self_assessment": "intermediate"},
            ],
            academic_info={"college_year": "3rd Year", "stream": "CSE"},
            timezone="Asia/Kolkata",
        )
        assert False, "Should have raised ValidationError for < 3 topics"
    except ValidationError as e:
        assert "at least 3 topics" in str(e)
        print("Pydantic validation for < 3 topics PASSED.")


async def test_repository_and_database_flow():
    async with AsyncSessionLocal() as session:
        # Check topic IDs exist
        stmt = select(Topic).order_by(Topic.id)
        res = await session.execute(stmt)
        topics = list(res.scalars().all())
        assert len(topics) == 5, f"Expected 5 topics, found {len(topics)}"
        print(f"Database topic check PASSED (found {len(topics)} topics).")

        # Test StudentRepository get_or_create
        test_uuid = uuid.uuid4()
        test_email = f"test_{test_uuid.hex[:6]}@example.com"

        student = await StudentRepository.get_or_create(
            session=session,
            user_id=test_uuid,
            email=test_email,
            user_metadata={"name": "Test Student"},
            timezone="Asia/Kolkata",
        )
        assert student.id == test_uuid
        assert student.email == test_email
        assert student.timezone == "Asia/Kolkata"
        print("StudentRepository get_or_create PASSED.")

        # Test ProgressRepository create_or_update_progress
        topic_ids_to_select = [topics[0].id, topics[1].id, topics[2].id]
        progress_rows = await ProgressRepository.create_or_update_progress(
            session=session,
            student_id=student.id,
            topic_ids=topic_ids_to_select,
        )
        assert len(progress_rows) == 3
        for p in progress_rows:
            assert p.current_level == 1
        print("ProgressRepository create_or_update_progress PASSED.")

        # Test Idempotency (running second time)
        progress_rows_second = await ProgressRepository.create_or_update_progress(
            session=session,
            student_id=student.id,
            topic_ids=topic_ids_to_select,
        )
        assert len(progress_rows_second) == 3
        print("ProgressRepository Idempotency check PASSED.")

        # Cleanup test student
        await session.delete(student)
        await session.commit()
        print("Database cleanup PASSED.")


if __name__ == "__main__":
    test_unauthenticated_requests()
    test_pydantic_onboarding_validation()
    asyncio.run(test_repository_and_database_flow())
