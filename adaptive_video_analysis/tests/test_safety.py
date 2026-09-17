from __future__ import annotations

from calis_video.safety import validate_observation
from calis_video.schemas import Confidence, Severity, VLMFinding, VLMObservation


def test_removes_medical_claims_and_out_of_range_timestamps() -> None:
    observation = VLMObservation(
        exercise_matches=True,
        overview="Test",
        findings=[
            VLMFinding(
                label="Diagnosis",
                timestamp_seconds=1,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                visible_evidence="You have an injury.",
                correction_cue="Seek treatment.",
            ),
            VLMFinding(
                label="Late timestamp",
                timestamp_seconds=99,
                severity=Severity.LOW,
                confidence=Confidence.LOW,
                visible_evidence="Visible",
                correction_cue="Try again",
            ),
        ],
    )
    validated = validate_observation(observation, duration_seconds=3)
    assert validated.findings == []
    assert len(validated.uncertainty) == 2

