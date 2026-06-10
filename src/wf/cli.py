from __future__ import annotations
import typer
import questionary
from rich.console import Console

from .config import (
    CONFIG_FILE,
    delete_workspace_meta,
    list_workspaces,
    load_config,
    load_workspace,
)
from .workspace import create_workspace, open_workspace, remove_workspace

app = typer.Typer(
    name="wf",
    help="Workspace manager for feature-based multi-repo development.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.command()
def create() -> None:
    """Interactively create a new workspace."""
    config = load_config()

    if not config.repos:
        console.print(f"[red]No repositories configured.[/red]")
        console.print(f"Create [bold]{CONFIG_FILE}[/bold] to get started. See [dim]config.example.yaml[/dim] for the format.")
        raise typer.Exit(1)

    choices = [questionary.Choice(title=r.name, value=r) for r in config.repos]
    selected = questionary.checkbox("Select repositories:", choices=choices).ask()

    if not selected:
        console.print("[dim]No repositories selected.[/dim]")
        raise typer.Exit(0)

    name = questionary.text(
        "Feature name:",
        validate=lambda v: True if v.strip() else "Name cannot be empty",
    ).ask()

    if not name:
        raise typer.Exit(0)

    name = name.strip()

    if load_workspace(name):
        console.print(f"[red]Workspace '{name}' already exists.[/red] Run [bold]wf open {name}[/bold] to open it.")
        raise typer.Exit(1)

    console.print(f"\n[bold]Creating workspace [cyan]{name}[/cyan][/bold]")
    console.print(f"Branch: [dim]feature/{name}[/dim]")

    try:
        create_workspace(name, selected, config)
    except Exception as e:
        console.print(f"\n[red]Failed:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"\n[bold green]✓ Workspace '{name}' created.[/bold green]")
    console.print(f"Open with: [bold]wf open {name}[/bold]")


@app.command()
def open(name: str = typer.Argument(..., help="Workspace name")) -> None:
    """Open an existing workspace in the configured editor."""
    config = load_config()
    meta = load_workspace(name)

    if not meta:
        console.print(f"[red]Workspace '{name}' not found.[/red]")
        _suggest(list_workspaces())
        raise typer.Exit(1)

    open_workspace(meta, config.settings.editor)


@app.command(name="list")
def list_cmd() -> None:
    """List all workspaces."""
    names = list_workspaces()

    if not names:
        console.print("[dim]No workspaces. Run [bold]wf create[/bold] to get started.[/dim]")
        return

    for name in names:
        meta = load_workspace(name)
        if meta:
            repos = ", ".join(r.repo_name for r in meta.repos)
            console.print(f"[bold]{name}[/bold]  [dim]{meta.branch}[/dim]  ({repos})")
        else:
            console.print(name)


@app.command()
def remove(
    name: str = typer.Argument(..., help="Workspace name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    delete_branches: bool = typer.Option(False, "--delete-branches", help="Also delete the feature branches"),
) -> None:
    """Remove a workspace, its worktrees, and optionally its branches."""
    meta = load_workspace(name)

    if not meta:
        console.print(f"[red]Workspace '{name}' not found.[/red]")
        _suggest(list_workspaces())
        raise typer.Exit(1)

    console.print(f"\nWorkspace: [bold]{name}[/bold]  [dim]{meta.branch}[/dim]")
    for repo in meta.repos:
        console.print(f"  • {repo.repo_name}  [dim]{repo.worktree_path}[/dim]")
    if delete_branches:
        console.print(f"  • Branch [dim]{meta.branch}[/dim] will be deleted from each repo")
    console.print()

    if not yes:
        confirmed = questionary.confirm(f"Remove workspace '{name}'?", default=False).ask()
        if not confirmed:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    remove_workspace(meta, delete_branches=delete_branches)
    delete_workspace_meta(name)
    console.print(f"\n[bold green]✓ Workspace '{name}' removed.[/bold green]")


def _suggest(names: list[str]) -> None:
    if names:
        console.print(f"Available: {', '.join(names)}")
