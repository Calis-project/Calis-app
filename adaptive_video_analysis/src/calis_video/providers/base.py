from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from calis_video.schemas import VLMObservation


@dataclass(frozen=True, slots=True)
class ImageInput:
    jpeg: bytes
    timestamp_seconds: float
    reasons: tuple[str, ...] = ()


class ProviderError(RuntimeError):
    pass


class VisionProvider(ABC):
    name: str
    model: str
    max_images_per_request: int

    @abstractmethod
    def observe(
        self,
        *,
        prompt: str,
        images: list[ImageInput],
        context: dict[str, Any],
    ) -> VLMObservation:
        raise NotImplementedError

