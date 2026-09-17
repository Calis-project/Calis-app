from __future__ import annotations

from collections.abc import Iterable

import pytest

from calis_video.schemas import FrameEvidence


@pytest.fixture
def frame_factory():
    def make(
        angles: Iterable[float],
        *,
        metric: str = "elbow_angle",
        confidence: float = 0.9,
        step: float = 0.125,
    ) -> list[FrameEvidence]:
        frames: list[FrameEvidence] = []
        for index, angle in enumerate(angles):
            metrics = {
                "elbow_angle": 175.0,
                "body_line_angle": 175.0,
                "knee_angle": 175.0,
                "knee_angle_asymmetry": 2.0,
                "torso_deviation_vertical": 20.0,
            }
            metrics[metric] = float(angle)
            frames.append(
                FrameEvidence(
                    index=index,
                    timestamp_seconds=index * step,
                    pose_confidence=confidence,
                    motion_score=0.02,
                    metrics=metrics,
                    jpeg=b"jpeg",
                )
            )
        return frames

    return make
