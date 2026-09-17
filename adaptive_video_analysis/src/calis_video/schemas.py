from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExerciseId(StrEnum):
    PUSH_UP = "push_up"
    SQUAT = "squat"
    PLANK = "plank"
    LUNGE = "lunge"
    HOLLOW_HOLD = "hollow_hold"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VideoMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_seconds: float = Field(ge=0)
    fps: float = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    total_frames: int = Field(ge=0)
    processed_frames: int = Field(ge=0, default=0)


class Landmark(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    z: float
    visibility: float = Field(ge=0, le=1)


class FrameEvidence(BaseModel):
    """Compact local evidence for one sampled video frame."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    timestamp_seconds: float = Field(ge=0)
    pose_confidence: float = Field(ge=0, le=1)
    motion_score: float = Field(ge=0)
    metrics: dict[str, float | None] = Field(default_factory=dict)
    jpeg: bytes = Field(exclude=True, repr=False)


class RepEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=1)
    start_seconds: float = Field(ge=0)
    bottom_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    range_of_motion_degrees: float = Field(ge=0)
    minimum_primary_angle: float | None = None
    confidence: Confidence


class CandidateFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp_seconds: float = Field(ge=0)
    score: float = Field(ge=0)
    reasons: list[str] = Field(default_factory=list)
    source_index: int = Field(ge=0)


class CandidateInterval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    reason: str = Field(min_length=1, max_length=240)
    confidence: Confidence = Confidence.MEDIUM

    @model_validator(mode="after")
    def end_must_not_precede_start(self) -> "CandidateInterval":
        if self.end_seconds < self.start_seconds:
            raise ValueError("end_seconds must be greater than or equal to start_seconds")
        return self


class MediaQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usable: bool
    confidence: Confidence
    visibility_fraction: float = Field(ge=0, le=1)
    problems: list[str] = Field(default_factory=list)
    retry_guidance: list[str] = Field(default_factory=list)


class LocalTimeline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise: ExerciseId
    metadata: VideoMetadata
    media_quality: MediaQuality
    repetitions: list[RepEvidence] = Field(default_factory=list)
    aggregate_metrics: dict[str, float | int | None] = Field(default_factory=dict)
    candidate_frames: list[CandidateFrame] = Field(default_factory=list)


class VLMFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=100)
    timestamp_seconds: float | None = Field(default=None, ge=0)
    severity: Severity
    confidence: Confidence
    visible_evidence: str = Field(min_length=1, max_length=500)
    correction_cue: str = Field(min_length=1, max_length=300)


class VLMObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise_matches: bool
    overview: str = Field(min_length=1, max_length=800)
    positive_observations: list[str] = Field(default_factory=list, max_length=5)
    findings: list[VLMFinding] = Field(default_factory=list, max_length=8)
    candidate_intervals: list[CandidateInterval] = Field(
        default_factory=list, max_length=8
    )
    uncertainty: list[str] = Field(default_factory=list, max_length=8)


class AnalysisDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    passes: int = Field(ge=0)
    processed_local_frames: int = Field(ge=0)
    images_sent: int = Field(ge=0)
    estimated_full_video_frames: int = Field(ge=0)
    context_reduction_ratio: float = Field(ge=0, le=1)
    elapsed_ms: int = Field(ge=0)
    notes: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    status: str
    exercise: ExerciseId
    summary: str
    media_quality: MediaQuality
    repetitions: list[RepEvidence] = Field(default_factory=list)
    positive_observations: list[str] = Field(default_factory=list)
    prioritized_findings: list[VLMFinding] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    aggregate_metrics: dict[str, Any] = Field(default_factory=dict)
    diagnostics: AnalysisDiagnostics
    safety_notice: str = (
        "This app provides general fitness guidance, not medical or "
        "physiotherapy advice. Stop if you feel pain, dizziness, or unusual "
        "discomfort."
    )
