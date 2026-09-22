import os
import yaml
from pathlib import Path

# Distinct palette per team member
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
    "READY_FOR_REVIEW": "👀",
    "DONE": "✅"
}

def load_reports(folder_path: str):
    reports = []
    path = Path(folder_path)
    for file_path in path.glob("*.yaml"):
        with open(file_path, "r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
            if data and "task_id" in data:
                reports.append(data)
    return reports

def build_mermaid_graph(reports):
    chart = [
        "```mermaid",
        "graph TD",
        "    %% Global Node Styles"
    ]
    
    # 1. Define color styles for each team member
    for member, colors in MEMBER_PALETTES.items():
        chart.append(
            f"    classDef style_{member} fill:{colors['fill']},stroke:{colors['stroke']},stroke-width:2px,color:{colors['text']};"
        )
    chart.append("    classDef blockedNode fill:#7F1D1D,stroke:#DC2626,stroke-width:3px,color:#FEE2E2,stroke-dasharray: 5 5;")

    chart.append("\n    %% Tasks & Active Branches")
    # 2. Add task nodes
    for item in reports:
        raw_id = item["task_id"]
        safe_id = raw_id.replace("-", "_")
        owner = item.get("owner", "Unassigned")
        status = item.get("status", "TODO")
        branch = item.get("branch", "N/A")
        icon = STATUS_ICONS.get(status, "⏳")

        label = f"\"{icon} <b>{raw_id}: {owner}</b><br/><code>{branch}</code><br/>Status: <i>{status}</i>\""
        chart.append(f"    {safe_id}[{label}]")

    chart.append("\n    %% Task Dependencies")
    # 3. Add directional edges
    for item in reports:
        target_id = item["task_id"].replace("-", "_")
        deps = item.get("blockers_and_dependencies", {}).get("dependencies", [])
        if deps:
            for dep in deps:
                clean_dep = dep.replace("-", "_")
                chart.append(f"    {clean_dep} ==>|Blocks| {target_id}")

    chart.append("\n    %% Apply Member Colors")
    # 4. Color-code nodes by owner or blocked status
    for item in reports:
        safe_id = item["task_id"].replace("-", "_")
        owner = item.get("owner", "")
        status = item.get("status", "")
        
        if status == "BLOCKED":
            chart.append(f"    class {safe_id} blockedNode;")
        elif owner in MEMBER_PALETTES:
            chart.append(f"    class {safe_id} style_{owner};")

    chart.append("```")
    return "\n".join(chart)

def main():
    reports_dir = "docs/06_feedback/reports"
    output_doc = "docs/07_architecture/workflow_map.md"

    reports = load_reports(reports_dir)
    if not reports:
        print(f"[WARN] No YAML reports found in {reports_dir}. Exiting.")
        return

    mermaid_code = build_mermaid_graph(reports)

    with open(output_doc, "w", encoding="utf-8") as f:
        f.write("# Sprint 01: Team Workflow & Dependency Map\n\n")
        f.write("> **Internal Tool Notice:** Generated automatically by `src/internal_tools/workflow_agent.py`.\n\n")
        f.write(mermaid_code + "\n")

    print(f"[SUCCESS] Updated visual workflow written to {output_doc}")

if __name__ == "__main__":
    main()