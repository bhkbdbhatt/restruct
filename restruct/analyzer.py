import os
import re
from pathlib import Path
from typing import Any
from restruct.utils import EXCLUDE_DIRS

class CodebaseAnalyzer:
    def __init__(self, root: Path, framework_override: str | None = None):
        self.root = root.resolve()
        self.framework_override = framework_override

    def detect_framework(self) -> str:
        if self.framework_override:
            return self.framework_override
        
        if (self.root / "pyproject.toml").exists() or (self.root / "requirements.txt").exists():
            content = ""
            for name in ["pyproject.toml", "requirements.txt"]:
                p = self.root / name
                if p.exists():
                    content += p.read_text(errors="ignore")
            if "fastapi" in content.lower():
                return "FastAPI"
            if "flask" in content.lower():
                return "Flask"
            if "django" in content.lower():
                return "Django"
            return "Generic Python"

        if (self.root / "package.json").exists():
            content = (self.root / "package.json").read_text(errors="ignore")
            if "nest" in content.lower():
                return "NestJS"
            if "express" in content.lower():
                return "Express"
            return "Node.js / TypeScript"

        if (self.root / "go.mod").exists():
            return "Go"
        if (self.root / "Cargo.toml").exists():
            return "Rust"

        return "Unknown"

    def build_ascii_tree(self, dir_path: Path | None = None, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
        if dir_path is None:
            dir_path = self.root
        if current_depth >= max_depth:
            return ""

        tree_str = ""
        try:
            entries = sorted([e for e in dir_path.iterdir() if e.name not in EXCLUDE_DIRS], key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return ""

        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            tree_str += f"{prefix}{connector}{entry.name}\n"
            if entry.is_dir():
                extension = "    " if i == len(entries) - 1 else "│   "
                tree_str += self.build_ascii_tree(entry, prefix + extension, max_depth, current_depth + 1)
        return tree_str

    def find_problems(self) -> dict[str, list[str]]:
        problems = {
            "wrong_locations": [],
            "naming_inconsistencies": [],
            "dead_folders": [],
            "deep_nesting": [],
            "missing_standard_files": []
        }

        # 1. Traverse files & dirs
        for current_root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            rel_root = Path(current_root).relative_to(self.root)
            depth = len(rel_root.parts)

            # Deep nesting check (> 4 levels)
            if depth > 4:
                problems["deep_nesting"].append(str(rel_root))

            # Dead folder check
            if not dirs and not files:
                problems["dead_folders"].append(str(rel_root))
            elif not dirs and len(files) == 1 and files[0] in [".gitkeep", ".DS_Store"]:
                problems["dead_folders"].append(str(rel_root))

            for file in files:
                rel_file = rel_root / file
                file_str = str(rel_file)

                # Wrong location heuristics
                if any(p in rel_root.parts for p in ["public", "static", "assets"]) and file.endswith((".py", ".js", ".ts", ".go", ".rs")):
                    problems["wrong_locations"].append(f"Source code in public asset folder: {file_str}")
                
                if (file.startswith("test_") or file.endswith(("_test.py", ".spec.ts", ".test.js"))) and "tests" not in rel_root.parts:
                    problems["wrong_locations"].append(f"Test file outside tests directory: {file_str}")

                # Naming inconsistencies (Python focus: snake_case for modules)
                if file.endswith(".py") and file != "__init__.py":
                    name_without_ext = file[:-3]
                    if re.search(r'[A-Z]', name_without_ext) or "-" in name_without_ext:
                        problems["naming_inconsistencies"].append(f"Non-snake_case Python module: {file_str}")

        # Missing standard files check
        framework = self.detect_framework()
        if "Python" in framework or framework in ["FastAPI", "Flask", "Django"]:
            if not (self.root / "tests").exists():
                problems["missing_standard_files"].append("Missing 'tests/' directory")
            if not (self.root / ".gitignore").exists():
                problems["missing_standard_files"].append("Missing '.gitignore'")

        return problems

    def get_target_structure(self, framework: str) -> str:
        templates = {
            "FastAPI": "app/\n  ├── api/\n  ├── core/\n  ├── models/\n  └── main.py\ntests/\nscripts/\npyproject.toml",
            "Flask": "app/\n  ├── static/\n  ├── templates/\n  └── __init__.py\ntests/\npyproject.toml",
            "Django": "config/\napps/\nstatic/\ntemplates/\nmanage.py\nrequirements.txt",
            "Node.js / TypeScript": "src/\n  ├── controllers/\n  ├── services/\n  ├── models/\n  └── index.ts\ntests/\npackage.json"
        }
        return templates.get(framework, "src/\ntests/\nREADME.md\npyproject.toml")

    def run(self) -> dict[str, Any]:
        framework = self.detect_framework()
        return {
            "framework": framework,
            "tree": self.build_ascii_tree(),
            "problems": self.find_problems(),
            "suggested_structure": self.get_target_structure(framework)
        }