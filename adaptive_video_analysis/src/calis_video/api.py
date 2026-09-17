from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .config import PACKAGE_ROOT, Settings
from .env import load_env_file
from .factory import make_provider
from .pipeline import AdaptiveVideoAnalyzer
from .providers.base import ProviderError
from .schemas import AnalysisResult, ExerciseId
from .video import VideoValidationError


load_env_file(PACKAGE_ROOT / ".env")
app = FastAPI(
    title="Calis Adaptive Video Analysis",
    version="0.1.0",
    description=(
        "Local pose/timeline extraction with selective free-tier VLM escalation."
    ),
)

ALLOWED_SUFFIXES = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".mpeg", ".mpg"}


@app.get("/health")
def health() -> dict[str, object]:
    settings = Settings.from_env()
    return {
        "ok": True,
        "pose_model_present": settings.pose_model_path.is_file(),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "supported_exercises": [exercise.value for exercise in ExerciseId],
    }


@app.post("/v1/analyze", response_model=AnalysisResult)
def analyze(
    video: Annotated[UploadFile, File(description="A short exercise video")],
    exercise: Annotated[ExerciseId, Form()],
    provider: Annotated[
        Literal["auto", "gemini", "groq", "local"], Form()
    ] = "auto",
    mode: Annotated[
        Literal["coarse-to-fine", "single", "local"], Form()
    ] = "coarse-to-fine",
) -> AnalysisResult:
    settings = Settings.from_env()
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported video extension: {suffix or '(none)'}",
        )

    try:
        with tempfile.TemporaryDirectory(prefix="calis-analysis-") as temp:
            path = Path(temp) / f"upload{suffix}"
            with path.open("wb") as destination:
                shutil.copyfileobj(
                    video.file,
                    destination,
                    length=1024 * 1024,
                )
            if path.stat().st_size > settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="Upload is too large")
            analyzer = AdaptiveVideoAnalyzer(
                settings=settings,
                provider=make_provider(provider, settings),
            )
            return analyzer.analyze(path, exercise, mode=mode)
    except HTTPException:
        raise
    except VideoValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


def main() -> None:
    import uvicorn

    uvicorn.run("calis_video.api:app", host="127.0.0.1", port=8000)

