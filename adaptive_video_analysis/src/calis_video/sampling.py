from __future__ import annotations

from collections import defaultdict

import numpy as np

from .exercises import frame_rule_signals
from .schemas import (
    CandidateFrame,
    CandidateInterval,
    ExerciseId,
    FrameEvidence,
    RepEvidence,
)


def _nearest_frame_index(
    frames: list[FrameEvidence], timestamp_seconds: float
) -> int:
    return min(
        range(len(frames)),
        key=lambda index: abs(frames[index].timestamp_seconds - timestamp_seconds),
    )


def select_overview_frames(
    frames: list[FrameEvidence],
    exercise: ExerciseId,
    repetitions: list[RepEvidence],
    budget: int,
) -> list[CandidateFrame]:
    if not frames or budget <= 0:
        return []
    reasons: dict[int, set[str]] = defaultdict(set)
    scores: dict[int, float] = defaultdict(float)

    even_count = min(budget, max(3, budget // 2))
    for index in np.linspace(0, len(frames) - 1, even_count, dtype=int):
        reasons[int(index)].add("timeline_coverage")
        scores[int(index)] += 0.5

    for rep in repetitions:
        for timestamp, reason, score in (
            (rep.start_seconds, "rep_start", 1.0),
            (rep.bottom_seconds, "rep_bottom", 2.0),
            (rep.end_seconds, "rep_end", 1.0),
        ):
            index = _nearest_frame_index(frames, timestamp)
            reasons[index].add(f"{reason}_{rep.index}")
            scores[index] += score

    for index, frame in enumerate(frames):
        for reason, score in frame_rule_signals(frame, exercise):
            reasons[index].add(reason)
            scores[index] += score

    ranked = sorted(
        reasons,
        key=lambda index: (
            -scores[index],
            frames[index].timestamp_seconds,
        ),
    )
    selected: list[int] = []
    minimum_gap = 0.20
    for index in ranked:
        timestamp = frames[index].timestamp_seconds
        if all(
            abs(timestamp - frames[other].timestamp_seconds) >= minimum_gap
            for other in selected
        ):
            selected.append(index)
        if len(selected) >= budget:
            break

    selected.sort(key=lambda index: frames[index].timestamp_seconds)
    return [
        CandidateFrame(
            timestamp_seconds=frames[index].timestamp_seconds,
            score=scores[index],
            reasons=sorted(reasons[index]),
            source_index=index,
        )
        for index in selected
    ]


def local_candidate_intervals(
    candidates: list[CandidateFrame],
    duration_seconds: float,
    radius_seconds: float,
    limit: int = 4,
) -> list[CandidateInterval]:
    ranked = sorted(candidates, key=lambda candidate: candidate.score, reverse=True)
    result: list[CandidateInterval] = []
    for candidate in ranked:
        if candidate.score < 1.0:
            continue
        start = max(0.0, candidate.timestamp_seconds - radius_seconds)
        end = min(duration_seconds, candidate.timestamp_seconds + radius_seconds)
        if any(
            not (end < existing.start_seconds or start > existing.end_seconds)
            for existing in result
        ):
            continue
        result.append(
            CandidateInterval(
                start_seconds=start,
                end_seconds=end,
                reason=", ".join(candidate.reasons),
            )
        )
        if len(result) >= limit:
            break
    return sorted(result, key=lambda item: item.start_seconds)


def merge_intervals(
    local: list[CandidateInterval],
    remote: list[CandidateInterval],
    duration_seconds: float,
    limit: int = 4,
) -> list[CandidateInterval]:
    combined = sorted(
        [*remote, *local],
        key=lambda item: (item.start_seconds, item.end_seconds),
    )
    merged: list[CandidateInterval] = []
    for interval in combined:
        start = max(0.0, min(duration_seconds, interval.start_seconds))
        end = max(start, min(duration_seconds, interval.end_seconds))
        if merged and start <= merged[-1].end_seconds + 0.15:
            previous = merged[-1]
            merged[-1] = CandidateInterval(
                start_seconds=previous.start_seconds,
                end_seconds=max(previous.end_seconds, end),
                reason=f"{previous.reason}; {interval.reason}"[:240],
                confidence=previous.confidence,
            )
        else:
            merged.append(
                CandidateInterval(
                    start_seconds=start,
                    end_seconds=end,
                    reason=interval.reason,
                    confidence=interval.confidence,
                )
            )
    return merged[:limit]


def select_detail_frames(
    frames: list[FrameEvidence],
    intervals: list[CandidateInterval],
    budget: int,
) -> list[CandidateFrame]:
    if not frames or not intervals or budget <= 0:
        return []
    per_interval = max(1, budget // len(intervals))
    indices: set[int] = set()
    reasons: dict[int, set[str]] = defaultdict(set)
    for interval in intervals:
        timestamps = np.linspace(
            interval.start_seconds, interval.end_seconds, per_interval
        )
        for timestamp in timestamps:
            index = _nearest_frame_index(frames, float(timestamp))
            indices.add(index)
            reasons[index].add(f"detail:{interval.reason}")
    ordered = sorted(indices, key=lambda index: frames[index].timestamp_seconds)
    if len(ordered) > budget:
        ordered = ordered[:budget]
    return [
        CandidateFrame(
            timestamp_seconds=frames[index].timestamp_seconds,
            score=2.0,
            reasons=sorted(reasons[index]),
            source_index=index,
        )
        for index in ordered
    ]

