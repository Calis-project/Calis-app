from __future__ import annotations

import time
from pathlib import Path
from typing import Literal

from .artifacts import save_debug_artifacts
from .config import Settings
from .exercises import aggregate_metrics, detect_repetitions
from .pose import MediaPipePoseExtractor
from .providers.base import ImageInput, VisionProvider
from .providers.local import LocalOnlyProvider
from .providers.prompts import detail_prompt, overview_prompt
from .safety import validate_observation
from .sampling import (
    local_candidate_intervals,
    merge_intervals,
    select_detail_frames,
    select_overview_frames,
)
from .schemas import (
    AnalysisDiagnostics,
    AnalysisResult,
    Confidence,
    ExerciseId,
    LocalTimeline,
    MediaQuality,
    VLMObservation,
)
from .video import scan_video, validate_video


AnalysisMode = Literal["coarse-to-fine", "single", "local"]


class AdaptiveVideoAnalyzer:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        provider: VisionProvider | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.provider = provider or LocalOnlyProvider()

    def analyze(
        self,
        video_path: Path,
        exercise: ExerciseId,
        *,
        mode: AnalysisMode = "coarse-to-fine",
        keep_artifacts: Path | None = None,
    ) -> AnalysisResult:
        started = time.perf_counter()
        metadata = validate_video(video_path, self.settings)

        with MediaPipePoseExtractor(self.settings.pose_model_path) as extractor:
            frames = list(
                scan_video(video_path, self.settings, pose_extractor=extractor)
            )
        metadata = metadata.model_copy(update={"processed_frames": len(frames)})
        repetitions = detect_repetitions(frames, exercise)
        metrics = aggregate_metrics(frames, exercise)
        quality = self._media_quality(frames, metrics)
        overview_candidates = select_overview_frames(
            frames,
            exercise,
            repetitions,
            budget=min(
                self.settings.max_overview_frames,
                self.provider.max_images_per_request
                if self.provider.max_images_per_request
                else self.settings.max_overview_frames,
            ),
        )
        timeline = LocalTimeline(
            exercise=exercise,
            metadata=metadata,
            media_quality=quality,
            repetitions=repetitions,
            aggregate_metrics=metrics,
            candidate_frames=overview_candidates,
        )

        overview_images = self._candidate_images(frames, overview_candidates)
        detail_images: list[ImageInput] = []
        images_sent = 0
        passes = 0
        notes: list[str] = [
            (
                "Local scan frames do not consume VLM context; only images_sent "
                "were sent to the provider."
            )
        ]

        if mode == "local" or isinstance(self.provider, LocalOnlyProvider):
            observation = LocalOnlyProvider().observe(
                prompt="", images=[], context={}
            )
        elif not quality.usable:
            observation = VLMObservation(
                exercise_matches=True,
                overview="The clip did not pass the local media-quality gate.",
                uncertainty=[*quality.problems, *quality.retry_guidance],
            )
            notes.append("Provider call skipped because the clip was not usable.")
        else:
            context = timeline.model_dump(mode="json")
            first = self.provider.observe(
                prompt=overview_prompt(context),
                images=overview_images,
                context=context,
            )
            first = validate_observation(first, metadata.duration_seconds)
            images_sent += len(overview_images)
            passes += 1

            if mode == "single":
                observation = first
            else:
                local_intervals = local_candidate_intervals(
                    overview_candidates,
                    metadata.duration_seconds,
                    self.settings.detail_radius_seconds,
                )
                intervals = merge_intervals(
                    local_intervals,
                    first.candidate_intervals,
                    metadata.duration_seconds,
                )
                detail_candidates = select_detail_frames(
                    frames,
                    intervals,
                    budget=min(
                        self.settings.max_detail_frames,
                        self.provider.max_images_per_request,
                    ),
                )
                detail_images = self._candidate_images(frames, detail_candidates)
                if detail_images:
                    detail_context = {
                        "timeline": context,
                        "coarse_observation": first.model_dump(mode="json"),
                        "selected_intervals": [
                            interval.model_dump(mode="json")
                            for interval in intervals
                        ],
                    }
                    observation = self.provider.observe(
                        prompt=detail_prompt(detail_context),
                        images=detail_images,
                        context=detail_context,
                    )
                    observation = validate_observation(
                        observation, metadata.duration_seconds
                    )
                    images_sent += len(detail_images)
                    passes += 1
                else:
                    observation = first
                    notes.append(
                        "No interval passed the detail-escalation threshold."
                    )

        if keep_artifacts is not None:
            save_debug_artifacts(keep_artifacts, overview_images, detail_images)
            notes.append(
                "Selected debug frames were retained because keep_artifacts "
                "was explicitly enabled."
            )

        elapsed_ms = round((time.perf_counter() - started) * 1000)
        total_frames = max(1, metadata.total_frames)
        context_reduction = max(0.0, 1.0 - (images_sent / total_frames))
        findings = sorted(
            observation.findings,
            key=lambda item: (
                {"high": 0, "medium": 1, "low": 2}[item.severity.value],
                {"high": 0, "medium": 1, "low": 2}[item.confidence.value],
            ),
        )[:2]
        status = (
            "retry"
            if not quality.usable or not observation.exercise_matches
            else "completed"
        )
        summary = (
            observation.overview
            if observation.exercise_matches
            else (
                "The visible movement did not reliably match the selected "
                f"exercise ({exercise.value}). Please verify the selection or "
                "record another clip."
            )
        )
        return AnalysisResult(
            status=status,
            exercise=exercise,
            summary=summary,
            media_quality=quality,
            repetitions=repetitions,
            positive_observations=observation.positive_observations[:3],
            prioritized_findings=findings,
            uncertainty=observation.uncertainty,
            aggregate_metrics=metrics,
            diagnostics=AnalysisDiagnostics(
                provider=self.provider.name,
                model=self.provider.model,
                passes=passes,
                processed_local_frames=len(frames),
                images_sent=images_sent,
                estimated_full_video_frames=metadata.total_frames,
                context_reduction_ratio=context_reduction,
                elapsed_ms=elapsed_ms,
                notes=notes,
            ),
        )

    @staticmethod
    def _candidate_images(
        frames: list, candidates: list
    ) -> list[ImageInput]:
        return [
            ImageInput(
                jpeg=frames[candidate.source_index].jpeg,
                timestamp_seconds=candidate.timestamp_seconds,
                reasons=tuple(candidate.reasons),
            )
            for candidate in candidates
        ]

    @staticmethod
    def _media_quality(frames: list, metrics: dict) -> MediaQuality:
        if not frames:
            return MediaQuality(
                usable=False,
                confidence=Confidence.HIGH,
                visibility_fraction=0.0,
                problems=["No readable frames were extracted."],
                retry_guidance=["Upload a supported, readable video clip."],
            )
        visible_fraction = float(metrics.get("pose_visible_fraction") or 0.0)
        problems: list[str] = []
        guidance: list[str] = []
        if visible_fraction < 0.35:
            problems.append("The body was not reliably visible in enough frames.")
            guidance.append(
                "Record the full body from a stable angle with good lighting "
                "and no major occlusion."
            )
        return MediaQuality(
            usable=visible_fraction >= 0.35,
            confidence=(
                Confidence.HIGH
                if visible_fraction >= 0.75
                else Confidence.MEDIUM
                if visible_fraction >= 0.50
                else Confidence.LOW
            ),
            visibility_fraction=visible_fraction,
            problems=problems,
            retry_guidance=guidance,
        )

