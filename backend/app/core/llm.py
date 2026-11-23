"""Proveedor de LLM para el ReportingAgent.

Gemini es el proveedor preferido; OpenAI permanece como fallback y, si no hay
credenciales, se devuelve un texto explícitamente marcado como stub.
"""

from __future__ import annotations

from typing import Any

from .config import settings


class LLMProvider:
    def __init__(self) -> None:
        self.provider = "stub"
        self._client: Any = None
        self._model: Any = None

        if settings.llm_provider == "gemini" and settings.gemini_api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=settings.gemini_api_key)
                self._model = genai.GenerativeModel(settings.gemini_model)
                self.provider = "gemini"
            except Exception:  # pragma: no cover - depende del entorno
                self.provider = "stub"
        elif settings.openai_api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=settings.openai_api_key)
                self.provider = "openai"
            except Exception:  # pragma: no cover
                self.provider = "stub"

    def generate(self, prompt: str) -> str:
        if self.provider == "gemini":
            return self._model.generate_content(prompt).text
        if self.provider == "openai":
            completion = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            return completion.choices[0].message.content or ""
        return f"[stub:${self.provider}] {prompt[:200]}"


llm_provider = LLMProvider()
