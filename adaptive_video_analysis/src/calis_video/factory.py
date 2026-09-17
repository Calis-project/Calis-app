from __future__ import annotations

import os
from typing import Literal

from .config import Settings
from .providers import GeminiProvider, GroqProvider, LocalOnlyProvider, VisionProvider


ProviderChoice = Literal["auto", "gemini", "groq", "local"]


def make_provider(
    choice: ProviderChoice, settings: Settings
) -> VisionProvider:
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if choice == "auto":
        choice = "gemini" if gemini_key else "groq" if groq_key else "local"
    if choice == "gemini":
        return GeminiProvider(
            gemini_key,
            settings.gemini_model,
            fallback_model=settings.gemini_fallback_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    if choice == "groq":
        return GroqProvider(
            groq_key,
            settings.groq_vision_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    return LocalOnlyProvider()

