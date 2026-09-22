import os
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple

MEMBER_PALETTES = {
    "Mehrnaz": {"fill": "#2E1065", "stroke": "#A78BFA", "text": "#EDE9FE"},
    "Mamad":   {"fill": "#451A03", "stroke": "#F59E0B", "text": "#FEF3C7"},
    "Danny":   {"fill": "#172554", "stroke": "#3B82F6", "text": "#DBEAFE"},
    "Kamran":  {"fill": "#022C22", "stroke": "#10B981", "text": "#D1FAE5"},
    "Hessam":  {"fill": "#500724", "stroke": "#EC4899", "text": "#FCE7F3"},
    "Arash":   {"fill": "#083344", "stroke": "#06B6D4", "text": "#CFFAFE"},
    "Ramin":   {"fill": "#450A0A", "stroke": "#EF4444", "text": "#FEE2E2"},
}

STATUS_ICONS = {
    "TODO": "⏳",
    "IN_PROGRESS": "🔄",
    "BLOCKED": "🚫",
    "CHANGES_REQUESTED": "⚠️",
    "VERIFIED_ON_DISK": "🔍",
    "HARNESS_READY": "⚙️",
    "DONE": "✅"
}

# Contract rules: keywords each deliverable target must satisfy
TARGET_KEYWORD_RULES = {
    "TSK-01": ["sagittal", "tripod", "40cm"],
    "TSK-02": [".mp4"],
    "TSK-03": ["mediapipe", "pose"],
    "TSK-04": ["hip_sag", "no_rep_depth"],
    "TSK-05": ["cues", "status"],
    "TSK-06": ["camera", "flutter"],
    "TSK-07": ["pytest", "test_"]
}

# Inherent pipeline sequence extracted from sprint architecture contracts
TASK_FLOW_SEQUENCE = [
    ("TSK-01", "TSK-04", "Angles Spec"),
    ("TSK-01", "TSK-06", "Camera Constraints"),
    ("TSK-02", "TSK-03", "Video Clips Feed"),
    ("TSK-03", "TSK-04", "Landmark Stream"),
    ("TSK-05", "TSK-04", "Schema Contract"),
    ("TSK-04", "TSK-07", "Rule Verification"),
    ("TSK-02", "TSK-07", "Test Inputs")
]

def load_sprint_spec(spec_path: str) -> Dict[str, Any]:
    with open(spec_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def inspect_task_on_disk(target_path: Path, keywords: list) -> Tuple[bool, list]:
    """Inspects file/directory existence and scans for mandatory contract keywords."""
    if not target_path.exists():
        return False, []

    matched = []
    if target_path.is_dir():
        dir_files = [f.name.lower() for f in target_path.glob("*")]
        for kw in keywords:
            if any(kw.lower() in fname for fname in dir_files):
                matched.append(kw)
        return True, matched
    else:
        try:
            content = target_path.read_text(encoding="utf-8", errors="ignore").lower()
            for kw in keywords:
                if kw.lower() in content:
                    matched.append(kw)
        except Exception:
            pass
        return True, matched

def determine_dynamic_status(task_id: str, matrix_item: dict, base_dir: Path) -> Tuple[str, str]:
    target_rel = matrix_item.get("target", "")
    target_full = base_dir / target_rel
    req_keywords = TARGET_KEYWORD_RULES.get(task_id, [])

    exists, matched_kw = inspect_task_on_disk(target_full, req_keywords)
    default_status = matrix_item.get("status", "TODO")

    if exists:
        if set(req_keywords).issubset(set(matched_kw)) and len(req_keywords) > 0:
            return "VERIFIED_ON_DISK", f"Matched: {', '.join(matched_kw)}"
        return "IN_PROGRESS", f"Present; missing keywords"

    return default_status, f"Awaiting: {target_rel}"

def build_automated_mermaid(sprint_data: Dict[str, Any], project_root: Path) -> str:
    matrix = sprint_data.get("github_issue_matrix", {})
    blockers = sprint_data.get("current_sprint_state", {}).get("current_blockers", [])

    lines = [
        "```mermaid",
        "graph TD",
        "    %% Global Node Styles"
    ]

    for member, colors in MEMBER_PALETTES.items():
        lines.append(
            f"    classDef style_{member} fill:{colors['fill']},stroke:{colors['stroke']},stroke-width:2px,color:{colors['text']};"
        )
    lines.append("    classDef blockedNode fill:#7F1D1D,stroke:#DC2626,stroke-width:3px,color:#FEE2E2,stroke-dasharray: 5 5;")
    lines.append("    classDef verifiedNode fill:#064E3B,stroke:#059669,stroke-width:3px,color:#ECFDF5;")

    lines.append("\n    %% Automated Task States")
    task_statuses = {}

    for task_id, info in matrix.items():
        owner = info.get("owner", "Unassigned")
        branch = info.get("branch", "N/A")
        safe_id = task_id.replace("-", "_")

        computed_status, note = determine_dynamic_status(task_id, info, project_root)

        if any(task_id in b or info.get("issue") in b for b in blockers):
            computed_status = "BLOCKED"

        task_statuses[task_id] = computed_status
        icon = STATUS_ICONS.get(computed_status, "⏳")

        label = f"\"{icon} <b>{task_id}: {owner}</b><br/><code>{branch}</code><br/>Status: <i>{computed_status}</i><br/><small>{note}</small>\""
        lines.append(f"    {safe_id}[{label}]")

    lines.append("\n    %% Pipeline Sequence & Dependencies")
    for src, dst, label in TASK_FLOW_SEQUENCE:
        src_safe = src.replace("-", "_")
        dst_safe = dst.replace("-", "_")
        src_status = task_statuses.get(src, "TODO")

        if src_status in ["BLOCKED", "CHANGES_REQUESTED"]:
            lines.append(f"    {src_safe} ==x|Blocked by {src}| {dst_safe}")
        else:
            lines.append(f"    {src_safe} -->|{label}| {dst_safe}")

    lines.append("\n    %% Styling Assignments")
    for task_id, info in matrix.items():
        safe_id = task_id.replace("-", "_")
        owner = info.get("owner", "")
        status = task_statuses.get(task_id, "")

        if status == "BLOCKED":
            lines.append(f"    class {safe_id} blockedNode;")
        elif status == "VERIFIED_ON_DISK":
            lines.append(f"    class {safe_id} verifiedNode;")
        elif owner in MEMBER_PALETTES:
            lines.append(f"    class {safe_id} style_{owner};")

    lines.append("```")
    return "\n".join(lines)

def main():
    project_root = Path(__file__).resolve().parents[2]
    sprint_spec_file = project_root / "docs" / "07_architecture" / "sprint_01.yaml"
    output_doc = project_root / "docs" / "07_architecture" / "workflow_map.md"

    if not sprint_spec_file.exists():
        sprint_spec_file = project_root / "sprint_01.yaml"

    if not sprint_spec_file.exists():
        print(f"[ERROR] Sprint spec not found at {sprint_spec_file}")
        return

    sprint_data = load_sprint_spec(str(sprint_spec_file))
    diagram = build_automated_mermaid(sprint_data, project_root)

    with open(output_doc, "w", encoding="utf-8") as f:
        f.write("# Sprint 01: Automated Live Workflow & Dependency Engine\n\n")
        f.write("> **Zero-Manual-Tracking Notice:** Generated dynamically via disk inspections against `sprint_01.yaml`.\n\n")
        f.write(diagram + "\n")

    print(f"[SUCCESS] Workflow dynamically generated at: {output_doc}")

if __name__ == "__main__":
    main()