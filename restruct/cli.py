import json
from pathlib import Path
from typing import Optional
import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from restruct.analyzer import CodebaseAnalyzer
from restruct.executor import PlanExecutor
from restruct.planner import MigrationPlanner
from restruct.utils import is_git_repo

app = typer.Typer(help="Safely restructure messy codebases while preserving git history.")
console = Console()

@app.command()
def analyze(
    path: Path = typer.Argument(..., help="Path to codebase directory"),
    json_output: bool = typer.Option(False, "--json", help="Output analysis in JSON format"),
    framework: Optional[str] = typer.Option(None, "--framework", help="Override framework auto-detection")
):
    """Scans codebase and outputs a structure health report."""
    if not path.exists():
        rprint("[red]Error:[/red] Invalid path.")
        raise typer.Exit(code=1)

    analyzer = CodebaseAnalyzer(path, framework_override=framework)
    report = analyzer.run()

    if json_output:
        print(json.dumps(report, indent=2))
        return

    rprint(f"\n[bold green]Detected Framework:[/bold green] {report['framework']}\n")
    rprint("[bold blue]Current Layout (ASCII Tree):[/bold blue]")
    rprint(report["tree"] or "  (empty or restricted)")

    rprint("\n[bold red]Problems Found:[/bold red]")
    probs = report["problems"]
    for category, items in probs.items():
        if items:
            rprint(f"  [yellow]{category.replace('_', ' ').title()}:[/yellow]")
            for item in items:
                rprint(f"    - {item}")
    if not any(probs.values()):
        rprint("  [green]No structural issues detected![/green]")

    rprint("\n[bold cyan]Suggested Structure:[/bold cyan]")
    rprint(report["suggested_structure"])

@app.command()
def plan(
    path: Path = typer.Argument(..., help="Path to codebase directory"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write human-readable Markdown doc"),
    json_output: bool = typer.Option(False, "--json", help="Output plan in JSON format"),
    framework: Optional[str] = typer.Option(None, "--framework", help="Override framework auto-detection")
):
    """Generates a numbered, batch-isolated migration plan."""
    planner = MigrationPlanner(path, framework_override=framework)
    plan_data = planner.generate_plan()

    if output:
        planner.write_markdown_doc(plan_data, output)
        rprint(f"[green]Migration plan document written to {output}[/green]")

    if json_output:
        print(json.dumps(plan_data, indent=2))
        return

    if not output and not json_output:
        rprint(f"\n[bold green]Migration Plan for {plan_data['framework']}:[/bold green]\n")
        for b in plan_data["batches"]:
            rprint(f"[bold yellow]Batch {b['batch']}: {b['name']}[/bold yellow]")
            for s in b["steps"]:
                rprint(f"  {s['id']}. `{s['command']}` [dim](Risk: {s['risk']})[/dim]")

@app.command()
def execute(
    path: Path = typer.Argument(..., help="Path to codebase directory"),
    plan_file: Path = typer.Option(..., "--plan", help="Path to JSON plan file"),
    execute: bool = typer.Option(False, "--execute", help="Actually execute the migration (default is dry-run)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    batch: Optional[int] = typer.Option(None, "--batch", help="Execute only up to batch N")
):
    """Executes the migration plan batch by batch with auto-testing safety checks."""
    dry_run = not execute
    if dry_run:
        rprint("[yellow]Running in DRY-RUN mode. Pass --execute to run commands.[/yellow]")

    if not dry_run and not is_git_repo(path):
        rprint("[red]Error: Targeted path is not a valid Git repository.[/red]")
        raise typer.Exit(code=1)

    plan_data = json.loads(plan_file.read_text())
    executor = PlanExecutor(path, plan_data, dry_run=dry_run, skip_confirm=yes)
    success = executor.execute(max_batch=batch)

    if not success:
        rprint("\n[red]Execution stopped due to failure.[/red]")
        raise typer.Exit(code=1)

@app.command()
def rollback(
    path: Path = typer.Argument(..., help="Path to codebase directory"),
    plan_file: Path = typer.Option(..., "--plan", help="Path to JSON plan file"),
    batch: int = typer.Option(..., "--batch", help="Batch number to revert")
):
    """Reverts changes for a specific batch using recorded rollback commands."""
    plan_data = json.loads(plan_file.read_text())
    executor = PlanExecutor(path, plan_data, dry_run=False)
    executor.rollback_batch(batch)

if __name__ == "__main__":
    app()