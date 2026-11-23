"""Configuración del backend a partir de variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    event_backend: str = os.getenv("EVENT_BACKEND", "local")
    event_dir: str = os.getenv("EVENT_DIR", "data/events")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )


settings = Settings()
