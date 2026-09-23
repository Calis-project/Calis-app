import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List

# Initialize Google GenAI client
api_key = os.getenv("GEMINI_API_KEY")
client = None

if api_key:
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
    except ImportError:
        print("[WARN] google-genai package not installed. Falling back to local inspection.")

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
    "VERIFIED": "✅",
    "HARNESS_READY": "⚙️",
    "DONE": "🏆"
}

TASK_FLOW_SEQUENCE = [
    ("TSK-01", "TSK-04", "Angles Spec"),
    ("TSK-01", "TSK-06", "Camera Constraints"),
    ("TSK-02", "TSK-03", "Video Clips Feed"),
    ("TSK-03", "TSK-04", "Landmark Stream"),
    ("TSK-05", "TSK-04", "Schema Contract"),
    ("TSK-04", "TSK-07", "Rule Verification"),
    ("TSK-02", "TSK-07", "Test Inputs")
]

def load_sprint_spec(spec_path: Path) -> Dict[str, Any]:
    with open(spec_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def evaluate_task_with_ai(task_id: str, owner: str, role: str, target_rel: str, declared_status: str, project_root: Path) -> Dict[str, Any]:
    target_path = project_root / target_rel

    if not client:
        return {
            "completion_percentage": 50 if target_path.exists() else 0,
            "dynamic_status": declared_status,
            "technical_critique": "GEMINI_API_KEY not configured. Performed disk presence check.",
            "key_achievements": ["File verified on disk" if target_path.exists() else "Awaiting deliverable"],
            "gaps_and_risks": ["AI semantic analysis skipped."],
            "standup_question": "What is the delivery estimate for this module?"
        }

    if not target_path.exists():
        content = "TARGET FILE/DIRECTORY DOES NOT EXIST ON DISK"
    elif target_path.is_dir():
        items = [f"{f.name} ({f.stat().st_size / 1024:.1f} KB)" for f in target_path.glob("*")]
        content = f"Directory contents of {target_rel}:\n" + ("\n".join(items) if items else "Directory is empty.")
    else:
        content = target_path.read_text(encoding="utf-8", errors="ignore")[:7000]

    system_instruction = (
        "You are the Lead Computer Vision & Biomechanics Architect for Calis-app (Sprint 01: Golden Spike).\n"
        "Evaluate deliverables against sprint architecture contracts:\n"
        "1. Pure edge computing (zero cloud streaming, in-memory frames only).\n"
        "2. Biomechanics: HIP_SAG < 160 deg; NO_REP_DEPTH > 90 deg.\n"
        "Output strictly valid JSON with keys: 'completion_percentage' (int 0-100), 'dynamic_status', "
        "'technical_critique', 'key_achievements', 'gaps_and_risks', 'standup_question'."
    )

    user_prompt = f"""
    TASK: {task_id}
    ASSIGNEE: {owner} ({role})
    TARGET: {target_rel}
    DECLARED STATUS: {declared_status}

    EVALUATE ARTIFACT EVIDENCE:
    ```
    {content}
    ```
    """

    try:
        from google.genai import types
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {
            "completion_percentage": 0,
            "dynamic_status": declared_status,
            "technical_critique": f"Gemini evaluation error: {str(e)}",
            "key_achievements": [],
            "gaps_and_risks": ["Audit call failed."],
            "standup_question": "Please verify task status manually."
        }

def make_progress_bar(pct: int, length: int = 8) -> str:
    filled = int(length * (pct / 100))
    return "█" * filled + "░" * (length - filled)

def generate_report(sprint_data: dict, assessments: List[dict]) -> str:
    sprint_state = sprint_data.get("current_sprint_state", {})
    completed_assets = sprint_state.get("completed_assets", [])
    blockers = sprint_state.get("current_blockers", [])
    sprint_id = sprint_state.get("sprint_id", "Sprint 01")
    dod = sprint_state.get("dod_threshold", ">= 80% accuracy")

    total_tasks = len(assessments)
    avg_completion = sum(a["evaluation"]["completion_percentage"] for a in assessments) / total_tasks if total_tasks else 0

    lines = [
        f"# {sprint_id}: Comprehensive Execution Report",
        "",
        f"> **Generated:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` | **Auditor:** `workflow_agent.py (Gemini Engine)`",
        "",
        "---",
        "",
        "## 1. Executive Summary & Progress Metric",
        "",
        f"- **Definition of Done (DoD):** {dod}",
        f"- **Sprint Average Progress:** **{avg_completion:.1f}%**",
        "",
        "### Key Phase Achievements",
        ""
    ]

    for asset in completed_assets:
        lines.append(f"- 🏆 **{asset}**")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Active Blockers & Risks",
        ""
    ])

    if blockers:
        for b in blockers:
            lines.append(f"- 🚫 **{b}**")
    else:
        lines.append("- ✅ No active blockers identified in sprint spec.")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Task Assessments & Contract Compliance",
        "",
        "| Task | Owner | Target | Status | Progress | Technical Critique |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ])

    for a in assessments:
        ev = a["evaluation"]
        status = ev.get("dynamic_status", a["status"])
        pct = ev.get("completion_percentage", 0)
        icon = STATUS_ICONS.get(status, "⏳")
        lines.append(
            f"| **{a['task_id']}** | **{a['owner']}** | `{a['target']}` | {icon} `{status}` | **{pct}%** | {ev.get('technical_critique', '')} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Standup & Review Questions",
        ""
    ])

    for a in assessments:
        ev = a["evaluation"]
        lines.append(f"### 👤 {a['owner']} — {a['task_id']}")
        lines.append(f"- **Progress:** {ev.get('completion_percentage', 0)}% (`{ev.get('dynamic_status', a['status'])}`)")
        lines.append(f"- **Question to Ask:** > *\"{ev.get('standup_question', 'Status check?')}\"*")
        lines.append("")

    return "\n".join(lines)

def generate_mermaid(sprint_data: dict, assessments: List[dict]) -> str:
    lines = [
        "```mermaid",
        "graph TD",
        "    %% Styles"
    ]
    for member, colors in MEMBER_PALETTES.items():
        lines.append(
            f"    classDef style_{member} fill:{colors['fill']},stroke:{colors['stroke']},stroke-width:2px,color:{colors['text']};"
        )
    lines.append("    classDef blockedNode fill:#7F1D1D,stroke:#DC2626,stroke-width:3px,color:#FEE2E2,stroke-dasharray: 5 5;")
    lines.append("    classDef verifiedNode fill:#064E3B,stroke:#059669,stroke-width:3px,color:#ECFDF5;")

    lines.append("\n    %% Tasks")
    task_map = {}
    for a in assessments:
        safe_id = a["task_id"].replace("-", "_")
        ev = a["evaluation"]
        status = ev.get("dynamic_status", a["status"])
        pct = ev.get("completion_percentage", 0)
        bar = make_progress_bar(pct)
        icon = STATUS_ICONS.get(status, "⏳")
        task_map[a["task_id"]] = status

        label = (
            f"\"{icon} <b>{a['task_id']}: {a['owner']}</b><br/>"
            f"<code>{a['branch']}</code><br/>"
            f"Progress: <b>{pct}%</b> [{bar}]<br/>"
            f"Status: <i>{status}</i>\""
        )
        lines.append(f"    {safe_id}[{label}]")

    lines.append("\n    %% Pipeline Sequence")
    for src, dst, label in TASK_FLOW_SEQUENCE:
        src_safe = src.replace("-", "_")
        dst_safe = dst.replace("-", "_")
        src_status = task_map.get(src, "TODO")

        if src_status in ["BLOCKED", "CHANGES_REQUESTED"]:
            lines.append(f"    {src_safe} ==x|Blocked by {src}| {dst_safe}")
        else:
            lines.append(f"    {src_safe} -->|{label}| {dst_safe}")

    lines.append("\n    %% Classes")
    for a in assessments:
        safe_id = a["task_id"].replace("-", "_")
        status = a["evaluation"].get("dynamic_status", a["status"])
        if status == "BLOCKED":
            lines.append(f"    class {safe_id} blockedNode;")
        elif status in ["VERIFIED", "DONE"]:
            lines.append(f"    class {safe_id} verifiedNode;")
        elif a["owner"] in MEMBER_PALETTES:
            lines.append(f"    class {safe_id} style_{a['owner']};")

    lines.append("```")
    return "\n".join(lines)

def main():
    project_root = Path(__file__).resolve().parents[2]
    sprint_spec_file = project_root / "docs" / "07_architecture" / "sprint_01.yaml"
    out_dir = project_root / "docs" / "07_architecture"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not sprint_spec_file.exists():
        sprint_spec_file = project_root / "sprint_01.yaml"

    if not sprint_spec_file.exists():
        print(f"[ERROR] Sprint spec not found at {sprint_spec_file}")
        return

    sprint_data = load_sprint_spec(sprint_spec_file)
    matrix = sprint_data.get("github_issue_matrix", {})

    assessments = []
    for task_id, info in matrix.items():
        eval_result = evaluate_task_with_ai(
            task_id=task_id,
            owner=info.get("owner", "Unassigned"),
            role="Engineering",
            target_rel=info.get("target", ""),
            declared_status=info.get("status", "TODO"),
            project_root=project_root
        )
        assessments.append({
            "task_id": task_id,
            "owner": info.get("owner", "Unassigned"),
            "branch": info.get("branch", "N/A"),
            "target": info.get("target", ""),
            "status": info.get("status", "TODO"),
            "evaluation": eval_result
        })

    report_content = generate_report(sprint_data, assessments)
    report_file = out_dir / "sprint_progress_report.md"
    report_file.write_text(report_content, encoding="utf-8")

    mermaid_content = generate_mermaid(sprint_data, assessments)
    map_file = out_dir / "workflow_map.md"
    map_file.write_text(
        "# Sprint 01: Automated Live Workflow & Dependency Engine\n\n"
        "> **Notice:** Generated dynamically via AI code audits against `sprint_01.yaml`.\n\n"
        + mermaid_content + "\n",
        encoding="utf-8"
    )

    print(f"[SUCCESS] Wrote report to: {report_file}")
    print(f"[SUCCESS] Wrote workflow map to: {map_file}")

if __name__ == "__main__":
    main()