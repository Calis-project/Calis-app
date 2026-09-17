from __future__ import annotations

import pytest

from calis_video.evaluation import ClipEvaluation, score_records


def test_evaluation_scores_accuracy_efficiency_and_failures() -> None:
    report = score_records(
        [
            ClipEvaluation(
                id="a",
                video="a.mp4",
                status="completed",
                expected_reps=5,
                predicted_reps=5,
                expected_usable=True,
                predicted_usable=True,
                expected_labels=["hip_sag"],
                predicted_labels=["hip_sag"],
                images_sent=10,
                context_reduction_ratio=0.98,
                elapsed_ms=1000,
            ),
            ClipEvaluation(
                id="b",
                video="b.mp4",
                status="completed",
                expected_reps=4,
                predicted_reps=2,
                expected_usable=True,
                predicted_usable=False,
                expected_labels=["shallow_depth"],
                predicted_labels=["other"],
                images_sent=5,
                context_reduction_ratio=0.99,
                elapsed_ms=2000,
            ),
            ClipEvaluation(
                id="c",
                video="c.mp4",
                status="error",
                error="bad file",
                expected_usable=False,
            ),
        ]
    )
    assert report.total_clips == 3
    assert report.failed_clips == 1
    assert report.rep_count_mae == 1
    assert report.rep_exact_accuracy == 0.5
    assert report.usability_accuracy == 0.5
    assert report.finding_precision == 0.5
    assert report.finding_recall == 0.5
    assert report.mean_images_sent == pytest.approx(7.5)

