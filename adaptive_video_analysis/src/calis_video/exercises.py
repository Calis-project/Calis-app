from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .geometry import moving_median
from .schemas import Confidence, ExerciseId, FrameEvidence, RepEvidence


@dataclass(frozen=True, slots=True)
class ExerciseSpec:
    dynamic: bool
    primary_metric: str
    top_angle: float
    bottom_angle: float
    minimum_rom: float
    required_metrics: tuple[str, ...]


EXERCISE_SPECS: dict[ExerciseId, ExerciseSpec] = {
    ExerciseId.PUSH_UP: ExerciseSpec(
        dynamic=True,
        primary_metric="elbow_angle",
        top_angle=145.0,
        bottom_angle=120.0,
        minimum_rom=28.0,
        required_metrics=("elbow_angle", "body_line_angle", "knee_angle"),
    ),
    ExerciseId.SQUAT: ExerciseSpec(
        dynamic=True,
        primary_metric="knee_angle",
        top_angle=150.0,
        bottom_angle=125.0,
        minimum_rom=30.0,
        required_metrics=("knee_angle", "torso_deviation_vertical"),
    ),
    ExerciseId.LUNGE: ExerciseSpec(
        dynamic=True,
        primary_metric="knee_angle",
        top_angle=145.0,
        bottom_angle=120.0,
        minimum_rom=28.0,
        required_metrics=("left_knee_angle", "right_knee_angle"),
    ),
    ExerciseId.PLANK: ExerciseSpec(
        dynamic=False,
        primary_metric="body_line_angle",
        top_angle=0.0,
        bottom_angle=0.0,
        minimum_rom=0.0,
        required_metrics=("body_line_angle", "knee_angle"),
    ),
    ExerciseId.HOLLOW_HOLD: ExerciseSpec(
        dynamic=False,
        primary_metric="body_line_angle",
        top_angle=0.0,
        bottom_angle=0.0,
        minimum_rom=0.0,
        required_metrics=("body_line_angle", "knee_angle"),
    ),
}


def detect_repetitions(
    frames: list[FrameEvidence], exercise: ExerciseId
) -> list[RepEvidence]:
    spec = EXERCISE_SPECS[exercise]
    if not spec.dynamic or len(frames) < 5:
        return []

    raw = [frame.metrics.get(spec.primary_metric) for frame in frames]
    smoothed = moving_median(raw, window=3)
    reps: list[RepEvidence] = []
    state = "top"
    start_index: int | None = None
    bottom_index: int | None = None
    recent_top = spec.top_angle
    running_min = 180.0

    for index, angle in enumerate(smoothed):
        if angle is None:
            continue
        recent_top = max(recent_top, angle)

        if state == "top":
            if angle <= recent_top - 12.0:
                start_index = max(0, index - 1)
                bottom_index = index
                running_min = angle
                state = "descending"
        elif state == "descending":
            if angle < running_min:
                running_min = angle
                bottom_index = index
            elif angle >= running_min + 7.0 and running_min <= spec.bottom_angle:
                state = "ascending"
            elif angle >= recent_top - 5.0:
                state = "top"
                start_index = None
                bottom_index = None
        else:
            if angle < running_min - 3.0:
                running_min = angle
                bottom_index = index
                state = "descending"
            elif angle >= max(spec.top_angle, recent_top - 12.0):
                if start_index is not None and bottom_index is not None:
                    rom = max(0.0, recent_top - running_min)
                    if rom >= spec.minimum_rom:
                        visible = np.mean(
                            [
                                frames[i].pose_confidence
                                for i in range(start_index, index + 1)
                            ]
                        )
                        confidence = (
                            Confidence.HIGH
                            if visible >= 0.75
                            else Confidence.MEDIUM
                            if visible >= 0.50
                            else Confidence.LOW
                        )
                        reps.append(
                            RepEvidence(
                                index=len(reps) + 1,
                                start_seconds=frames[
                                    start_index
                                ].timestamp_seconds,
                                bottom_seconds=frames[
                                    bottom_index
                                ].timestamp_seconds,
                                end_seconds=frames[index].timestamp_seconds,
                                range_of_motion_degrees=rom,
                                minimum_primary_angle=running_min,
                                confidence=confidence,
                            )
                        )
                state = "top"
                recent_top = angle
                start_index = None
                bottom_index = None
                running_min = 180.0
    return reps


def frame_rule_signals(
    frame: FrameEvidence, exercise: ExerciseId
) -> list[tuple[str, float]]:
    """Return conservative candidate signals, not user-facing diagnoses."""
    metrics = frame.metrics
    signals: list[tuple[str, float]] = []

    if frame.pose_confidence < 0.45:
        signals.append(("low_pose_visibility", 1.5))
    if frame.motion_score > 0.10:
        signals.append(("high_motion", min(1.5, frame.motion_score * 8)))

    if exercise in {ExerciseId.PUSH_UP, ExerciseId.PLANK}:
        body_line = metrics.get("body_line_angle")
        knee = metrics.get("knee_angle")
        if body_line is not None and body_line < 155:
            signals.append(("body_line_deviation_candidate", (155 - body_line) / 18))
        if knee is not None and knee < 155:
            signals.append(("knee_flexion_candidate", (155 - knee) / 20))
    elif exercise == ExerciseId.SQUAT:
        asymmetry = metrics.get("knee_angle_asymmetry")
        torso = metrics.get("torso_deviation_vertical")
        if asymmetry is not None and asymmetry > 16:
            signals.append(("left_right_asymmetry_candidate", asymmetry / 20))
        if torso is not None and torso > 55:
            signals.append(("large_torso_inclination_candidate", torso / 60))
    elif exercise == ExerciseId.LUNGE:
        asymmetry = metrics.get("knee_angle_asymmetry")
        if asymmetry is not None and asymmetry < 8:
            # During a lunge, both knees staying similarly extended can mean the
            # sampled phase is not representative. Escalate; do not diagnose.
            signals.append(("unclear_lunge_phase", 0.6))

    return signals


def aggregate_metrics(
    frames: list[FrameEvidence], exercise: ExerciseId
) -> dict[str, float | int | None]:
    spec = EXERCISE_SPECS[exercise]
    values = [
        frame.metrics.get(spec.primary_metric)
        for frame in frames
        if frame.metrics.get(spec.primary_metric) is not None
    ]
    confidences = [frame.pose_confidence for frame in frames]
    return {
        "local_samples": len(frames),
        "pose_visible_fraction": (
            sum(confidence >= 0.50 for confidence in confidences) / len(confidences)
            if confidences
            else 0.0
        ),
        "mean_pose_confidence": (
            float(np.mean(confidences)) if confidences else 0.0
        ),
        "primary_angle_min": float(np.min(values)) if values else None,
        "primary_angle_max": float(np.max(values)) if values else None,
        "primary_angle_median": float(np.median(values)) if values else None,
    }

