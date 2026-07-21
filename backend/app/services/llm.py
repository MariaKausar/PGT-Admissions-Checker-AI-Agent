"""Shared Claude (Anthropic) chat model factory using LangChain."""
from __future__ import annotations

from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from app.config import get_settings


@lru_cache
def get_llm(temperature: float | None = None) -> ChatAnthropic:
    settings = get_settings()
    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=settings.agent_temperature if temperature is None else temperature,
        max_tokens=2048,
        timeout=120,
    )
