import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List
from openai import OpenAI

# Check for API key in environment
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def evaluate_task_with_ai(task_id: str, owner: str, role: str, target_rel: str, declared_status: str, project_root: Path) -> Dict[str, Any]:
    target_path = project_root / target_rel

    # Fallback if no API key is configured
    if not client:
        return {
            "completion_percentage": 50 if target_path.exists() else 0,
            "dynamic_status": declared_status,
            "technical_critique": "API key not found. Performed rule-based inspection.",
            "key_achievements": ["Rule check completed"],
            "gaps_and_risks": ["AI evaluation skipped"],
            "standup_question": "What is the expected delivery date for this deliverable?"
        }

    # Extract target artifact content or folder manifest
    if not target_path.exists():
        content = "TARGET FILE/DIRECTORY DOES NOT EXIST ON DISK"
    elif target_path.is_dir():
        items = [f"{f.name} ({f.stat().st_size / 1024:.1f} KB)" for f in target_path.glob("*")]
        content = f"Directory contents of {target_rel}:\n" + ("\n".join(items) if items else "Directory is empty.")
    else:
        content = target_path.read_text(encoding="utf-8", errors="ignore")[:7000]

    system_prompt = (
        "You are the Lead Computer Vision & Biomechanics Architect for Calis-app (Sprint 01).\n"
        "Evaluate deliverables against the sprint contract:\n"
        "1. Pure edge computing (zero cloud streaming).\n"
        "2. GDPR compliance: In-memory frame processing only.\n"
        "3. Biomechanics: HIP_SAG < 160 deg; NO_REP_DEPTH > 90 deg.\n"
        "Output strictly valid JSON with keys: 'completion_percentage' (int 0-100), 'dynamic_status', "
        "'technical_critique', 'key_achievements', 'gaps_and_risks', 'standup_question'."
    )

    user_prompt = f"""
    TASK: {task_id}
    ASSIGNEE: {owner} ({role})
    TARGET: {target_rel}
    DECLARED STATUS: {declared_status}

    EVALUATE ARTIFACT:
    ```
    {content}
    ```
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "completion_percentage": 0,
            "dynamic_status": declared_status,
            "technical_critique": f"Evaluation error: {str(e)}",
            "key_achievements": [],
            "gaps_and_risks": ["AI call failed"],
            "standup_question": "Please verify task status manually."
        }