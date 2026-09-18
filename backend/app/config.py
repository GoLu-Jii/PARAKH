"""Configuration management (Supabase/Groq keys, env loading)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    groq_api_key: str = ""
    database_url: str = ""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        extra="ignore",
    )


settings = Settings()