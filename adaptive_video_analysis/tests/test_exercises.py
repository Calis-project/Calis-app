from __future__ import annotations

from calis_video.exercises import aggregate_metrics, detect_repetitions
from calis_video.schemas import ExerciseId


def test_detects_complete_push_up_rep(frame_factory) -> None:
    frames = frame_factory(
        [170, 168, 160, 145, 125, 105, 90, 95, 110, 130, 150, 165, 170]
    )
    reps = detect_repetitions(frames, ExerciseId.PUSH_UP)
    assert len(reps) == 1
    assert reps[0].minimum_primary_angle <= 95
    assert reps[0].range_of_motion_degrees >= 70
    assert reps[0].start_seconds < reps[0].bottom_seconds < reps[0].end_seconds


def test_rejects_partial_push_up(frame_factory) -> None:
    frames = frame_factory([170, 168, 160, 154, 150, 154, 160, 168])
    assert detect_repetitions(frames, ExerciseId.PUSH_UP) == []


def test_detects_squat_with_knee_metric(frame_factory) -> None:
    frames = frame_factory(
        [170, 165, 150, 135, 115, 90, 100, 120, 145, 160, 170],
        metric="knee_angle",
    )
    reps = detect_repetitions(frames, ExerciseId.SQUAT)
    assert len(reps) == 1


def test_aggregate_metrics_reports_visibility(frame_factory) -> None:
    frames = frame_factory([170, 120, 90])
    metrics = aggregate_metrics(frames, ExerciseId.PUSH_UP)
    assert metrics["pose_visible_fraction"] == 1.0
    assert metrics["primary_angle_min"] == 90

