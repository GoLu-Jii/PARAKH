"""Interview router (start session, submit answer, next question)."""
from fastapi import APIRouter

router = APIRouter(prefix="/interview", tags=["interview"])
