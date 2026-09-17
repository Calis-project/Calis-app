from __future__ import annotations

from pathlib import Path
from typing import Any

from calis_video.config import Settings
from calis_video.pipeline import AdaptiveVideoAnalyzer
from calis_video.providers.base import ImageInput, VisionProvider
from calis_video.schemas import (
    CandidateInterval,
    Confidence,
    ExerciseId,
    Severity,
    VLMFinding,
    VLMObservation,
    VideoMetadata,
)


class FakeExtractor:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> None:
        pass


class FakeProvider(VisionProvider):
    name = "fake"
    model = "fake-vision"
    max_images_per_request = 5

    def __init__(self) -> None:
        self.calls: list[list[ImageInput]] = []

    def observe(
        self,
        *,
        prompt: str,
        images: list[ImageInput],
        context: dict[str, Any],
    ) -> VLMObservation:
        self.calls.append(images)
        if len(self.calls) == 1:
            return VLMObservation(
                exercise_matches=True,
                overview="One push-up is visible.",
                candidate_intervals=[
                    CandidateInterval(
                        start_seconds=0.35,
                        end_seconds=0.95,
                        reason="bottom phase",
                    )
                ],
            )
        return VLMObservation(
            exercise_matches=True,
            overview="The sampled repetition is controlled.",
            positive_observations=["The top position appears stable."],
            findings=[
                VLMFinding(
                    label="Body-line deviation",
                    timestamp_seconds=0.75,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.MEDIUM,
                    visible_evidence="The hip is lower than the shoulder-to-ankle line.",
                    correction_cue="Brace your trunk before the next descent.",
                )
            ],
        )


def test_pipeline_uses_two_bounded_passes(monkeypatch, frame_factory, tmp_path) -> None:
    frames = frame_factory(
        [170, 165, 150, 130, 105, 90, 100, 125, 150, 165, 170],
        step=0.1,
    )
    provider = FakeProvider()
    settings = Settings(
        pose_model_path=Path("unused.task"),
        max_overview_frames=8,
        max_detail_frames=12,
    )
    monkeypatch.setattr("calis_video.pipeline.MediaPipePoseExtractor", FakeExtractor)
    monkeypatch.setattr(
        "calis_video.pipeline.validate_video",
        lambda *_: VideoMetadata(
            duration_seconds=1.1,
            fps=30,
            width=640,
            height=480,
            total_frames=33,
        ),
    )
    monkeypatch.setattr(
        "calis_video.pipeline.scan_video", lambda *_args, **_kwargs: iter(frames)
    )

    analyzer = AdaptiveVideoAnalyzer(settings=settings, provider=provider)
    result = analyzer.analyze(tmp_path / "input.mp4", ExerciseId.PUSH_UP)

    assert result.status == "completed"
    assert result.diagnostics.passes == 2
    assert len(provider.calls) == 2
    assert all(len(call) <= 5 for call in provider.calls)
    assert result.diagnostics.images_sent == sum(map(len, provider.calls))
    assert result.prioritized_findings[0].label == "Body-line deviation"

