from __future__ import annotations

import json
from typing import Any

from calis_video.schemas import VLMObservation


SYSTEM_POLICY = """
You are the visual observation layer of a calisthenics form-analysis system.
The user selected the exercise. Analyze only visible evidence in the supplied,
chronological, timestamped frames. The frames are sparse samples and may omit
events. Do not infer an injury, diagnosis, pain, or medical risk. Do not claim
precise biomechanical measurements from pixels. Treat local pose measurements
as approximate candidate signals, not ground truth. If camera angle, occlusion,
sampling, or visibility makes a claim uncertain, say so. Use supportive,
non-judgmental language. Return JSON only.
""".strip()


def overview_prompt(context: dict[str, Any]) -> str:
    schema = json.dumps(VLMObservation.model_json_schema(), separators=(",", ":"))
    payload = json.dumps(context, separators=(",", ":"), default=str)
    return f"""
{SYSTEM_POLICY}

Task: Perform a coarse first pass. Establish whether the selected exercise
matches the visible sequence, describe the movement briefly, and identify at
most four short time intervals that genuinely warrant denser inspection.
Findings in this pass must be tentative. Prefer intervals supported by both
visual evidence and the local timeline. Timestamps must fall within the video.

Local timeline:
{payload}

Required JSON Schema:
{schema}
""".strip()


def detail_prompt(context: dict[str, Any]) -> str:
    schema = json.dumps(VLMObservation.model_json_schema(), separators=(",", ":"))
    payload = json.dumps(context, separators=(",", ":"), default=str)
    return f"""
{SYSTEM_POLICY}

Task: Inspect the denser evidence from selected intervals. Return only findings
that are directly visible in these frames. Each finding needs a timestamp,
confidence, visible evidence, and one concrete correction cue. Include at most
two prioritized corrections and up to three positive observations. A sparse
frame sequence cannot prove smoothness, tempo, joint tracking, or events between
frames; explicitly record such uncertainty when relevant.

Analysis context:
{payload}

Required JSON Schema:
{schema}
""".strip()

