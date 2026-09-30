import os
import shutil
import subprocess
from pathlib import Path
import git

EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "build", "dist", ".pytest_cache", ".mypy_cache"}

def is_git_repo(path: Path) -> bool:
    try:
        git.Repo(path, search_parent_directories=True)
        return True
    except git.InvalidGitRepositoryError:
        return False

def get_git_repo(path: Path) -> git.Repo:
    return git.Repo(path, search_parent_directories=True)

def detect_test_command(root: Path) -> str | None:
    """Auto-detect test command based on configuration files."""
    if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists() or (root / "tests").exists():
        if shutil.which("pytest"):
            return "pytest"
        return "python -m unittest"
    if (root / "package.json").exists():
        return "npm test"
    if (root / "go.mod").exists():
        return "go test ./..."
    if (root / "Cargo.toml").exists():
        return "cargo test"
    return None

def run_command(cmd: str, cwd: Path) -> tuple[int, str, str]:
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr