from __future__ import annotations

import base64
import json
from typing import Any

import httpx
from pydantic import ValidationError

from calis_video.schemas import VLMObservation

from .base import ImageInput, ProviderError, VisionProvider
from .http import with_retries


class GroqProvider(VisionProvider):
    name = "groq"
    # qwen/qwen3.6-27b currently permits at most five images per request.
    max_images_per_request = 5

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        timeout_seconds: float = 90.0,
    ) -> None:
        if not api_key:
            raise ValueError("GROQ_API_KEY is required")
        self.api_key = api_key
        self.model = model
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
                f"Groq image budget exceeded: {len(images)} > "
                f"{self.max_images_per_request}"
            )
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for number, image in enumerate(images, 1):
            content.append(
                {
                    "type": "text",
                    "text": (
                        f"Frame {number}: {image.timestamp_seconds:.3f}s; "
                        f"reasons={','.join(image.reasons) or 'coverage'}"
                    ),
                }
            )
            encoded = base64.b64encode(image.jpeg).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded}",
                        "detail": "auto",
                    },
                }
            )
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 2500,
        }

        def request() -> httpx.Response:
            response = self.client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            return response

        response = with_retries(request)
        try:
            text = response.json()["choices"][0]["message"]["content"]
            return VLMObservation.model_validate(json.loads(text))
        except (KeyError, IndexError, ValueError, ValidationError) as error:
            raise ProviderError(
                f"Groq returned an invalid structured observation: {error}"
            ) from error

