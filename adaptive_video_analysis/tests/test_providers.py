from __future__ import annotations

import json

import httpx

from calis_video.providers.base import ImageInput
from calis_video.providers.gemini import GeminiProvider
from calis_video.providers.groq import GroqProvider


OBSERVATION = {
    "exercise_matches": True,
    "overview": "A controlled repetition is visible.",
    "positive_observations": [],
    "findings": [],
    "candidate_intervals": [],
    "uncertainty": [],
}


def test_gemini_adapter_parses_structured_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["generationConfig"]["responseMimeType"] == "application/json"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": json.dumps(OBSERVATION)}]
                        }
                    }
                ]
            },
        )

    provider = GeminiProvider("key", "gemini-test")
    provider.client = httpx.Client(transport=httpx.MockTransport(handler))
    result = provider.observe(
        prompt="test",
        images=[ImageInput(jpeg=b"jpeg", timestamp_seconds=1.2)],
        context={},
    )
    assert result.exercise_matches


def test_groq_adapter_parses_json_mode_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["response_format"] == {"type": "json_object"}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": json.dumps(OBSERVATION)}}
                ]
            },
        )

    provider = GroqProvider("key", "qwen-test")
    provider.client = httpx.Client(transport=httpx.MockTransport(handler))
    result = provider.observe(
        prompt="test",
        images=[ImageInput(jpeg=b"jpeg", timestamp_seconds=1.2)],
        context={},
    )
    assert result.overview.startswith("A controlled")

