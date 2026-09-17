from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from .pipeline import AdaptiveVideoAnalyzer, AnalysisMode
from .schemas import AnalysisResult, ExerciseId


class ExpectedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    timestamp_seconds: float | None = Field(default=None, ge=0)


class LabelledClip(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    video: Path
    exercise: ExerciseId
    expected_reps: int | None = Field(default=None, ge=0)
    expected_usable: bool = True
    expected_findings: list[ExpectedFinding] = Field(default_factory=list)
    notes: str = ""


class ClipEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    video: str
    status: str
    error: str | None = None
    expected_reps: int | None = None
    predicted_reps: int | None = None
    expected_usable: bool
    predicted_usable: bool | None = None
    expected_labels: list[str] = Field(default_factory=list)
    predicted_labels: list[str] = Field(default_factory=list)
    images_sent: int = 0
    context_reduction_ratio: float = 0.0
    elapsed_ms: int = 0


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_clips: int
    completed_clips: int
    failed_clips: int
    rep_count_mae: float | None
    rep_exact_accuracy: float | None
    usability_accuracy: float | None
    finding_precision: float | None
    finding_recall: float | None
    mean_images_sent: float
    mean_context_reduction_ratio: float
    mean_elapsed_ms: float
    clips: list[ClipEvaluation]


def load_manifest(path: Path) -> list[LabelledClip]:
    base = path.resolve().parent
    clips: list[LabelledClip] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), 1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            data = json.loads(line)
            clip = LabelledClip.model_validate(data)
        except Exception as error:
            raise ValueError(
                f"Invalid manifest line {line_number}: {error}"
            ) from error
        if not clip.video.is_absolute():
            clip = clip.model_copy(update={"video": base / clip.video})
        clips.append(clip)
    return clips


def evaluate_manifest(
    analyzer: AdaptiveVideoAnalyzer,
    clips: list[LabelledClip],
    *,
    mode: AnalysisMode = "coarse-to-fine",
    limit: int | None = None,
) -> EvaluationReport:
    records: list[ClipEvaluation] = []
    for clip in clips[:limit]:
        try:
            result = analyzer.analyze(clip.video, clip.exercise, mode=mode)
            records.append(_record_from_result(clip, result))
        except Exception as error:
            records.append(
                ClipEvaluation(
                    id=clip.id,
                    video=str(clip.video),
                    status="error",
                    error=f"{type(error).__name__}: {error}",
                    expected_reps=clip.expected_reps,
                    expected_usable=clip.expected_usable,
                    expected_labels=[
                        _normalize_label(item.label)
                        for item in clip.expected_findings
                    ],
                )
            )
    return score_records(records)


def _record_from_result(
    clip: LabelledClip, result: AnalysisResult
) -> ClipEvaluation:
    return ClipEvaluation(
        id=clip.id,
        video=str(clip.video),
        status=result.status,
        expected_reps=clip.expected_reps,
        predicted_reps=len(result.repetitions),
        expected_usable=clip.expected_usable,
        predicted_usable=result.media_quality.usable,
        expected_labels=[
            _normalize_label(item.label) for item in clip.expected_findings
        ],
        predicted_labels=[
            _normalize_label(item.label) for item in result.prioritized_findings
        ],
        images_sent=result.diagnostics.images_sent,
        context_reduction_ratio=result.diagnostics.context_reduction_ratio,
        elapsed_ms=result.diagnostics.elapsed_ms,
    )


def score_records(records: list[ClipEvaluation]) -> EvaluationReport:
    successful = [record for record in records if record.error is None]
    rep_records = [
        record
        for record in successful
        if record.expected_reps is not None and record.predicted_reps is not None
    ]
    rep_errors = [
        abs(record.expected_reps - record.predicted_reps)
        for record in rep_records
        if record.expected_reps is not None and record.predicted_reps is not None
    ]
    usability = [
        record.expected_usable == record.predicted_usable
        for record in successful
        if record.predicted_usable is not None
    ]

    true_positive = 0
    false_positive = 0
    false_negative = 0
    for record in successful:
        expected = set(record.expected_labels)
        predicted = set(record.predicted_labels)
        true_positive += len(expected & predicted)
        false_positive += len(predicted - expected)
        false_negative += len(expected - predicted)

    return EvaluationReport(
        total_clips=len(records),
        completed_clips=len(successful),
        failed_clips=len(records) - len(successful),
        rep_count_mae=float(np.mean(rep_errors)) if rep_errors else None,
        rep_exact_accuracy=(
            sum(error == 0 for error in rep_errors) / len(rep_errors)
            if rep_errors
            else None
        ),
        usability_accuracy=(
            sum(usability) / len(usability) if usability else None
        ),
        finding_precision=(
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else None
        ),
        finding_recall=(
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else None
        ),
        mean_images_sent=(
            float(np.mean([record.images_sent for record in successful]))
            if successful
            else 0.0
        ),
        mean_context_reduction_ratio=(
            float(
                np.mean(
                    [record.context_reduction_ratio for record in successful]
                )
            )
            if successful
            else 0.0
        ),
        mean_elapsed_ms=(
            float(np.mean([record.elapsed_ms for record in successful]))
            if successful
            else 0.0
        ),
        clips=records,
    )


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def example_manifest() -> str:
    example: dict[str, Any] = {
        "id": "pushup_001",
        "video": "videos/pushup_001.mp4",
        "exercise": "push_up",
        "expected_reps": 5,
        "expected_usable": True,
        "expected_findings": [
            {"label": "body_line_deviation", "timestamp_seconds": 6.2}
        ],
        "notes": "Side view; form reviewed by coach initials AB.",
    }
    return json.dumps(example, separators=(",", ":"))

