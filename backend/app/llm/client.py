from groq import Groq
from app.config import settings


def get_groq_client() -> Groq:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing")
    return Groq(api_key=settings.groq_api_key)


groq_client = get_groq_client()
MODEL_NAME = "llama-3.3-70b-versatile"
