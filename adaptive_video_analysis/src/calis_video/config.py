from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PACKAGE_ROOT / "models" / "pose_landmarker_lite.task"


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


@dataclass(frozen=True, slots=True)
class Settings:
    max_video_seconds: float = 30.0
    max_upload_bytes: int = 40 * 1024 * 1024
    analysis_fps: float = 8.0
    max_dimension: int = 640
    jpeg_quality: int = 78
    min_landmark_visibility: float = 0.50
    max_overview_frames: int = 8
    max_detail_frames: int = 12
    detail_radius_seconds: float = 0.65
    pose_model_path: Path = DEFAULT_MODEL_PATH
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"
    groq_vision_model: str = "qwen/qwen3.6-27b"
    request_timeout_seconds: float = 90.0

    @classmethod
    def from_env(cls) -> "Settings":
        pose_path = os.getenv("CALIS_POSE_MODEL")
        return cls(
            max_video_seconds=_float_env("CALIS_MAX_VIDEO_SECONDS", 30.0),
            max_upload_bytes=_int_env("CALIS_MAX_UPLOAD_MB", 40) * 1024 * 1024,
            analysis_fps=_float_env("CALIS_ANALYSIS_FPS", 8.0),
            max_dimension=_int_env("CALIS_MAX_DIMENSION", 640),
            jpeg_quality=_int_env("CALIS_JPEG_QUALITY", 78),
            min_landmark_visibility=_float_env(
                "CALIS_MIN_LANDMARK_VISIBILITY", 0.50
            ),
            max_overview_frames=_int_env("CALIS_MAX_OVERVIEW_FRAMES", 8),
            max_detail_frames=_int_env("CALIS_MAX_DETAIL_FRAMES", 12),
            detail_radius_seconds=_float_env(
                "CALIS_DETAIL_RADIUS_SECONDS", 0.65
            ),
            pose_model_path=Path(pose_path) if pose_path else DEFAULT_MODEL_PATH,
            gemini_model=os.getenv("CALIS_GEMINI_MODEL", "gemini-3.6-flash"),
            gemini_fallback_model=os.getenv(
                "CALIS_GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite"
            ),
            groq_vision_model=os.getenv(
                "CALIS_GROQ_VISION_MODEL", "qwen/qwen3.6-27b"
            ),
            request_timeout_seconds=_float_env(
                "CALIS_REQUEST_TIMEOUT_SECONDS", 90.0
            ),
        )

