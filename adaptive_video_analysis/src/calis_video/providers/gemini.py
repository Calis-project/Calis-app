from __future__ import annotations

import base64
import json
from typing import Any

import httpx
from pydantic import ValidationError

from calis_video.schemas import VLMObservation

from .base import ImageInput, ProviderError, VisionProvider
from .http import with_retries


class GeminiProvider(VisionProvider):
    name = "gemini"
    max_images_per_request = 24

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        fallback_model: str | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model
        self.client = httpx.Client(timeout=timeout_seconds)

    def observe(
        self,
        *,
        prompt: str,
        images: list[ImageInput],
        context: dict[str, Any],
    ) -> VLMObservation:
        if len(images) > self.max_images_per_request:
            raise ProviderError(
                f"Gemini image budget exceeded: {len(images)} > "
                f"{self.max_images_per_request}"
            )
        try:
            return self._observe_model(self.model, prompt, images)
        except ProviderError:
            if not self.fallback_model or self.fallback_model == self.model:
                raise
            observation = self._observe_model(self.fallback_model, prompt, images)
            self.model = self.fallback_model
            return observation

    def _observe_model(
        self, model: str, prompt: str, images: list[ImageInput]
    ) -> VLMObservation:
        parts: list[dict[str, Any]] = [{"text": prompt}]
        for number, image in enumerate(images, 1):
            parts.append(
                {
                    "text": (
                        f"Frame {number}: timestamp "
                        f"{image.timestamp_seconds:.3f}s; selection reasons: "
                        f"{', '.join(image.reasons) or 'timeline coverage'}"
                    )
                }
            )
            parts.append(
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": base64.b64encode(image.jpeg).decode("ascii"),
                    }
                }
            )
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": VLMObservation.model_json_schema(),
                "maxOutputTokens": 2500,
            },
        }

        def request() -> httpx.Response:
            response = self.client.post(
                (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent"
                ),
                headers={"x-goog-api-key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
            return response

        response = with_retries(request)
        try:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return VLMObservation.model_validate(json.loads(text))
        except (KeyError, IndexError, ValueError, ValidationError) as error:
            raise ProviderError(
                f"Gemini returned an invalid structured observation: {error}"
            ) from error

