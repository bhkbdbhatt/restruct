import json
from pathlib import Path
from typing import Any
from restruct.analyzer import CodebaseAnalyzer

class MigrationPlanner:
    def __init__(self, root: Path, framework_override: str | None = None):
        self.root = root.resolve()
        self.analyzer = CodebaseAnalyzer(self.root, framework_override)

    def generate_plan(self) -> dict[str, Any]:
        analysis = self.analyzer.run()
        problems = analysis["problems"]

        batches = [
            {"batch": 1, "name": "Prerequisites & Standard Structure", "steps": []},
            {"batch": 2, "name": "Isolated File Relocations", "steps": []},
            {"batch": 3, "name": "Folder Consolidation & Naming Fixes", "steps": []},
            {"batch": 4, "name": "Dead Code & Empty Directory Cleanup", "steps": []}
        ]

        step_id = 1

        # Batch 1: Create missing directories
        if "Missing 'tests/' directory" in problems["missing_standard_files"]:
            batches[0]["steps"].append({
                "id": step_id,
                "command": "mkdir -p tests/",
                "risk": "low",
                "affected_files": 1,
                "rollback": "rmdir -p tests 2>/dev/null || true"
            })
            step_id += 1

        # Batch 2: Move test files & misplaced source files
        for loc_issue in problems["wrong_locations"]:
            if "Test file outside tests directory: " in loc_issue:
                src_path = loc_issue.replace("Test file outside tests directory: ", "")
                filename = Path(src_path).name
                dst_path = f"tests/{filename}"
                batches[1]["steps"].append({
                    "id": step_id,
                    "command": f"git mv {src_path} {dst_path}",
                    "risk": "medium",
                    "affected_files": 1,
                    "rollback": f"git mv {dst_path} {src_path}"
                })
                step_id += 1

        # Batch 3: Rename inconsistent files
        for name_issue in problems["naming_inconsistencies"]:
            src_path = name_issue.replace("Non-snake_case Python module: ", "")
            p = Path(src_path)
            snake_name = "".join(["_" + c.lower() if c.isupper() else c.lower() for c in p.stem]).lstrip("_").replace("-", "_")
            dst_path = str(p.parent / f"{snake_name}{p.suffix}")
            if src_path != dst_path:
                batches[2]["steps"].append({
                    "id": step_id,
                    "command": f"git mv {src_path} {dst_path}",
                    "risk": "medium",
                    "affected_files": 1,
                    "rollback": f"git mv {dst_path} {src_path}"
                })
                step_id += 1

        # Batch 4: Clean dead folders
        for dead_dir in problems["dead_folders"]:
            batches[3]["steps"].append({
                "id": step_id,
                "command": f"rm -f {dead_dir}/.gitkeep 2>/dev/null || true && rmdir {dead_dir}",
                "risk": "low",
                "affected_files": 1,
                "rollback": f"mkdir -p {dead_dir}"
            })
            step_id += 1

        # Filter out empty batches
        active_batches = [b for b in batches if b["steps"]]
        return {"framework": analysis["framework"], "batches": active_batches}

    def write_markdown_doc(self, plan: dict[str, Any], output_path: Path) -> None:
        lines = [f"# Migration Plan ({plan['framework']})\n"]
        for b in plan["batches"]:
            lines.append(f"## Batch {b['batch']}: {b['name']}\n")
            for s in b["steps"]:
                lines.append(f"### Step {s['id']}: `{s['command']}`")
                lines.append(f"- **Risk Level:** {s['risk'].capitalize()}")
                lines.append(f"- **Files Affected:** {s['affected_files']}")
                lines.append(f"- **Rollback:** `{s['rollback']}`\n")
        output_path.write_text("\n".join(lines))