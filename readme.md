# restruct

> **Safely restructure messy codebases while preserving git history.**

`restruct` is a command-line tool built in Python 3.12+ using [Typer](https://typer.tiangolo.com/) and [GitPython](https://gitpython.readthedocs.io/). It analyzes chaotic directory structures, detects structural code smells, auto-identifies project frameworks, and generates safe, batch-isolated migration plans executed entirely through history-preserving `git mv` operations.

---

## 🏗 Workflow & Architecture Diagrams

### 1. High-Level CLI Workflow

```
 ┌────────────────┐
 │ Messy Codebase │
 └───────┬────────┘
         │
         ▼
 ┌────────────────┐     Scans structure & rules
 │ restruct       │ ───────────────────────────────┐
 │ analyze        │                                │
 └───────┬────────┘                                ▼
         │                             ┌───────────────────────┐
         ▼                             │ Structural Health     │
 ┌────────────────┐                    │ Report & Health Score │
 │ restruct       │                    └───────────────────────┘
 │ plan           │ ───────────────────────────────┐
 └───────┬────────┘                                │
         │                                         ▼
         ▼                             ┌───────────────────────┐
 ┌────────────────┐                    │ migration-plan.md     │
 │ restruct       │                    │ plan.json             │
 │ execute        │                    └───────────────────────┘
 └───────┬────────┘
         │
         ├─── (All Tests Pass) ──────► [ Successfully Migrated Codebase ]
         │
         └─── (Tests Fail) ──────────► ┌───────────────────────┐
                                       │ restruct              │
                                       │ rollback              │
                                       └───────────────────────┘
```

---

### 2. Safety Pipeline & Batch Execution Flow

```
                  ┌───────────────────────────────┐
                  │ restruct execute --plan plan  │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │  Create & switch branch to    │
                  │     `restruct/migration`     │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Iterate Batches (1..N)│
                     └───────────┬───────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌───────────────────┐                           ┌───────────────────┐
│   Executes Batch  │                           │   Runs Auto-      │
│   Steps (git mv)  │ ────────────────────────► │   Detected Tests  │
└───────────────────┘                           └────────┬──────────┘
                                                         │
                                        ┌────────────────┴────────────────┐
                                        │                                 │
                                        ▼                                 ▼
                                  [ Tests Pass ]                   [ Tests Fail ]
                                        │                                 │
                                        ▼                                 ▼
                               ┌──────────────────┐             ┌───────────────────┐
                               │ Log SUCCESS in   │             │ Stop Execution &  │
                               │ MIGRATION_LOG.md │             │ Prompt Rollback   │
                               └──────────────────┘             └───────────────────┘
```

---

### 3. Batching Tier & Dependency Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BATCH DEPENDENCY TIER SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Batch 1: Prerequisites & Setup                                              │
│ └── mkdir -p missing directories, create required baseline files (__init__)  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Batch 2: Isolated Relocations (Medium Risk)                                 │
│ └── git mv misplaced assets, relocate standalone test files to /tests       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Batch 3: Folder Consolidation & Naming Refactors (Medium/High Risk)         │
│ └── git mv package subtrees, rename casing issues (camelCase -> snake_case)  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Batch 4: Dead Code & Folder Cleanup (Low Risk)                              │
│ └── Remove dead directories containing only .gitkeep or .DS_Store files     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation & Getting Started

### Prerequisites
- **Python 3.12+**
- **Git** installed and available in PATH

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/restruct.git
   cd restruct
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   *(On Windows PowerShell: `.venv\Scripts\Activate.ps1`)*

3. **Install the package in editable mode:**
   ```bash
   pip install -e .
   ```

4. **Verify installation:**
   ```bash
   restruct --help
   ```

---

## 📖 Command Reference

### 1. `restruct analyze`
Scans a target directory, auto-detects the framework, identifies structural anti-patterns, and produces a health report.

```bash
# Basic inspection
restruct analyze /path/to/project

# Override framework detection
restruct analyze /path/to/project --framework FastAPI

# Output raw JSON (for CI/CD pipelines)
restruct analyze /path/to/project --json
```

---

### 2. `restruct plan`
Generates an isolated, batch-organized migration plan with step-by-step risk profiles and explicit rollback operations.

```bash
# Output plan directly to console
restruct plan /path/to/project

# Generate human-readable Markdown documentation
restruct plan /path/to/project --output MIGRATION_PLAN.md

# Save structured plan to JSON (required for execution)
restruct plan /path/to/project --json > plan.json
```

---

### 3. `restruct execute`
Executes migration steps batch by batch. Defaults to `--dry-run` to prevent accidental modifications.

```bash
# Perform a dry-run (simulates changes without executing)
restruct execute /path/to/project --plan plan.json

# Actually execute migration on project repository
restruct execute /path/to/project --plan plan.json --execute

# Run non-interactively up to batch 2 (ideal for CI)
restruct execute /path/to/project --plan plan.json --execute --batch 2 --yes
```

---

### 4. `restruct rollback`
Reverts all file moves and operations executed in a target batch.

```bash
# Revert operations in Batch 2
restruct rollback /path/to/project --plan plan.json --batch 2
```

---

## 🛡️ Safety Features & Invariants

| Safety Feature | Mechanism | Purpose |
| :--- | :--- | :--- |
| **Git Branch Isolation** | Automatic checkout to `restruct/migration` | Keeps `main`/`master` clean and isolated. |
| **History Preservation** | Pure `git mv` operations | Retains full file commit history across relocations. |
| **Safe Removals** | `rm -f` or `rmdir` on empty dirs only | Guarantees non-tracked code is never forcibly deleted. |
| **Dry-Run Default** | Operations require explicit `--execute` flag | Prevents accidental execution. |
| **Automated Testing** | Runs detected test suite after each batch | Verifies code stability between steps. |
| **Migration Audit** | Appends entries to `MIGRATION_LOG.md` | Provides a clear record of performed actions. |

---

## 📂 Project Structure

```
restruct/
├── pyproject.toml         # Build system configuration & dependencies
├── README.md              # Project documentation
└── restruct/
    ├── __init__.py        # Package initialization
    ├── cli.py             # Typer CLI application entry point
    ├── analyzer.py        # Codebase scanner & health report engine
    ├── planner.py         # Batching algorithm & plan generator
    ├── executor.py        # Safe execution & testing harness
    └── utils.py           # Git & test command helper utilities
```

---

## 🤝 Contributing & License

Contributions are welcome! Please feel free to open issues or submit pull requests.

This project is licensed under the **MIT License**.