from datetime import datetime
from pathlib import Path
from typing import Any
import git
from restruct.utils import detect_test_command, get_git_repo, run_command

class PlanExecutor:
    def __init__(self, root: Path, plan: dict[str, Any], dry_run: bool = True, skip_confirm: bool = False):
        self.root = root.resolve()
        self.plan = plan
        self.dry_run = dry_run
        self.skip_confirm = skip_confirm
        self.repo = get_git_repo(self.root) if not self.dry_run else None

    def prepare_branch(self) -> None:
        if self.dry_run or not self.repo:
            return
        current_branches = [b.name for b in self.repo.branches]
        target_branch = "restruct/migration"
        if target_branch in current_branches:
            self.repo.git.checkout(target_branch)
        else:
            self.repo.git.checkout("-b", target_branch)

    def log_migration(self, batch_num: int, status: str, details: str) -> None:
        if self.dry_run:
            return
        log_file = self.root / "MIGRATION_LOG.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"## [{timestamp}] Batch {batch_num} - {status}\n{details}\n\n"
        with open(log_file, "a") as f:
            f.write(entry)

    def execute(self, max_batch: int | None = None) -> bool:
        if not self.dry_run:
            self.prepare_branch()

        test_cmd = detect_test_command(self.root)

        for batch in self.plan["batches"]:
            b_num = batch["batch"]
            if max_batch and b_num > max_batch:
                break

            print(f"\n--- Executing Batch {b_num}: {batch['name']} ---")

            # Execute steps
            for step in batch["steps"]:
                cmd = step["command"]
                print(f"  [Step {step['id']}] {cmd}")
                if not self.dry_run:
                    ret, stdout, stderr = run_command(cmd, cwd=self.root)
                    if ret != 0:
                        print(f"  [Error] Step failed: {stderr}")
                        self.log_migration(b_num, "FAILED", f"Command failed: {cmd}\nError: {stderr}")
                        return False

            # Run test suite
            if test_cmd and not self.dry_run:
                print(f"  Running test suite: {test_cmd}")
                t_ret, t_out, t_err = run_command(test_cmd, cwd=self.root)
                if t_ret != 0:
                    print(f"\n[!] Tests failed after Batch {b_num}. Stopping execution.")
                    print(t_out or t_err)
                    self.log_migration(b_num, "TESTS_FAILED", f"Tests failed after batch {b_num}.")
                    return False

            self.log_migration(b_num, "SUCCESS", f"Executed {len(batch['steps'])} steps successfully.")

        return True

    def rollback_batch(self, batch_num: int) -> None:
        target_batch = None
        for b in self.plan["batches"]:
            if b["batch"] == batch_num:
                target_batch = b
                break

        if not target_batch:
            print(f"Batch {batch_num} not found in plan.")
            return

        print(f"Rolling back Batch {batch_num}...")
        for step in reversed(target_batch["steps"]):
            rollback_cmd = step["rollback"]
            print(f"  Executing rollback: {rollback_cmd}")
            if not self.dry_run:
                run_command(rollback_cmd, cwd=self.root)

        self.log_migration(batch_num, "ROLLED_BACK", f"Rolled back batch {batch_num}.")