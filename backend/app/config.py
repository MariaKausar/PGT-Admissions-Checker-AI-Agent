"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    agent_temperature: float = 0.0
    frontend_origin: str = "http://localhost:5173"
    intake_years_ahead: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
