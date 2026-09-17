from __future__ import annotations

from typing import Any

from calis_video.schemas import VLMObservation

from .base import ImageInput, VisionProvider


class LocalOnlyProvider(VisionProvider):
    name = "local"
    model = "none"
    max_images_per_request = 0

    def observe(
        self,
        *,
        prompt: str,
        images: list[ImageInput],
        context: dict[str, Any],
    ) -> VLMObservation:
        return VLMObservation(
            exercise_matches=True,
            overview=(
                "Local pose and timeline extraction completed. No VLM was "
                "called, so qualitative form findings were intentionally omitted."
            ),
            uncertainty=["Visual-language analysis was disabled."],
        )

