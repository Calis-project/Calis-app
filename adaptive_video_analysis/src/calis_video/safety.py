from __future__ import annotations

from .schemas import VLMFinding, VLMObservation


FORBIDDEN_MEDICAL_PHRASES = (
    "you have an injury",
    "diagnosis",
    "torn",
    "will prevent injury",
    "safe from injury",
    "guaranteed",
)


def _is_safe_text(text: str) -> bool:
    normalized = text.casefold()
    return not any(phrase in normalized for phrase in FORBIDDEN_MEDICAL_PHRASES)


def validate_observation(
    observation: VLMObservation, duration_seconds: float
) -> VLMObservation:
    findings: list[VLMFinding] = []
    uncertainty = list(observation.uncertainty)
    for finding in observation.findings:
        texts = (
            finding.label,
            finding.visible_evidence,
            finding.correction_cue,
        )
        if not all(_is_safe_text(text) for text in texts):
            uncertainty.append(
                f"A provider finding was removed by the safety policy: "
                f"{finding.label}"
            )
            continue
        if (
            finding.timestamp_seconds is not None
            and finding.timestamp_seconds > duration_seconds + 0.25
        ):
            uncertainty.append(
                f"A provider finding used an out-of-range timestamp: "
                f"{finding.label}"
            )
            continue
        findings.append(finding)
    return observation.model_copy(
        update={
            "findings": findings,
            "positive_observations": [
                text
                for text in observation.positive_observations
                if _is_safe_text(text)
            ],
            "uncertainty": uncertainty,
        }
    )

