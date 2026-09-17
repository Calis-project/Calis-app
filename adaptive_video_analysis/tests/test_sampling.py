from __future__ import annotations

from calis_video.exercises import detect_repetitions
from calis_video.sampling import (
    local_candidate_intervals,
    select_detail_frames,
    select_overview_frames,
)
from calis_video.schemas import ExerciseId


def test_overview_selection_respects_budget_and_time_order(frame_factory) -> None:
    frames = frame_factory(
        [170, 168, 150, 120, 90, 105, 135, 160, 170, 165, 140, 100, 90, 120, 160]
    )
    reps = detect_repetitions(frames, ExerciseId.PUSH_UP)
    selected = select_overview_frames(
        frames, ExerciseId.PUSH_UP, reps, budget=6
    )
    assert 1 <= len(selected) <= 6
    assert selected == sorted(selected, key=lambda item: item.timestamp_seconds)
    assert any(
        any("rep_bottom" in reason for reason in item.reasons)
        for item in selected
    )


def test_detail_selection_focuses_on_candidate_intervals(frame_factory) -> None:
    frames = frame_factory([170] * 30, step=0.1)
    overview = select_overview_frames(
        frames, ExerciseId.PUSH_UP, [], budget=8
    )
    intervals = local_candidate_intervals(
        overview, duration_seconds=3.0, radius_seconds=0.4
    )
    # Timeline-only frames do not trigger escalation.
    assert intervals == []


def test_detail_selection_respects_budget(frame_factory) -> None:
    from calis_video.schemas import CandidateInterval

    frames = frame_factory([170] * 40, step=0.1)
    selected = select_detail_frames(
        frames,
        [
            CandidateInterval(start_seconds=0.5, end_seconds=1.0, reason="one"),
            CandidateInterval(start_seconds=2.0, end_seconds=2.5, reason="two"),
        ],
        budget=5,
    )
    assert len(selected) <= 5
    assert all(
        0.5 <= item.timestamp_seconds <= 1.0
        or 2.0 <= item.timestamp_seconds <= 2.5
        for item in selected
    )

