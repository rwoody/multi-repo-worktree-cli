from __future__ import annotations
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from .config import load_config, save_workspace
from .git import GitError, add_worktree, remove_worktree, delete_branch
from .models import AppConfig, RepoConfig, WorkspaceMetadata, WorkspaceRepo

console = Console()


def _worktree_path(base: Path, workspace: str, repo: RepoConfig) -> Path:
    return base / workspace / f"wt_{repo.short_id}_{workspace}"


def create_workspace(name: str, selected_repos: list[RepoConfig], config: AppConfig) -> WorkspaceMetadata:
    branch = f"feature/{name}"
    base = Path(config.settings.worktrees_base).expanduser()

    workspace_repos: list[WorkspaceRepo] = []

    for repo in selected_repos:
        repo_path = Path(repo.path).expanduser()
        wt_path = _worktree_path(base, name, repo)

        console.print(f"\n[bold cyan]→ {repo.name}[/bold cyan]")

        if not repo_path.exists():
            console.print(f"  [red]✗[/red] Repo path not found: [dim]{repo_path}[/dim]")
            raise RuntimeError(f"Repo path not found: {repo_path}")

        # Parent must exist before git worktree add
        wt_path.parent.mkdir(parents=True, exist_ok=True)

        with console.status(f"Creating worktree [dim]{wt_path.name}[/dim]..."):
            try:
                add_worktree(repo_path, wt_path, branch, repo.default_branch)
            except GitError as e:
                console.print(f"  [red]✗ Git error:[/red] {e}")
                raise

        console.print(f"  [green]✓[/green] Worktree [dim]{wt_path.name}[/dim] on branch [dim]{branch}[/dim]")

        for fname in repo.copy_files:
            src = repo_path / fname
            dst = wt_path / fname
            if src.exists():
                shutil.copy2(src, dst)
                console.print(f"  [green]✓[/green] Copied [dim]{fname}[/dim]")
            else:
                console.print(f"  [yellow]⚠[/yellow] [dim]{fname}[/dim] not found in source repo, skipping")

        for action in repo.bootstrap:
            if action.type == "run":
                cwd = wt_path / action.cwd if action.cwd else wt_path
                console.print(f"  [dim]$ {action.command}[/dim]")
                result = subprocess.run(action.command, shell=True, cwd=cwd)
                if result.returncode != 0:
                    console.print(f"  [yellow]⚠[/yellow] Exited with code {result.returncode}")

        workspace_repos.append(WorkspaceRepo(
            repo_id=repo.short_id,
            repo_name=repo.name,
            worktree_path=str(wt_path),
            branch=branch,
        ))

    meta = WorkspaceMetadata(
        name=name,
        branch=branch,
        created_at=datetime.now(timezone.utc).isoformat(),
        repos=workspace_repos,
    )
    save_workspace(meta)
    return meta


def open_workspace(meta: WorkspaceMetadata, editor: str) -> None:
    for repo in meta.repos:
        wt_path = Path(repo.worktree_path)
        if not wt_path.exists():
            console.print(f"[yellow]⚠[/yellow] Worktree not found: [dim]{wt_path}[/dim]")
            continue
        console.print(f"Opening [bold]{repo.repo_name}[/bold] → [dim]{wt_path}[/dim]")
        subprocess.Popen([editor, str(wt_path)])


def remove_workspace(meta: WorkspaceMetadata, delete_branches: bool = False) -> None:
    config = load_config()
    base = Path(config.settings.worktrees_base).expanduser()

    repo_configs = {r.short_id: r for r in config.repos}

    for repo_meta in meta.repos:
        wt_path = Path(repo_meta.worktree_path)
        repo_config = repo_configs.get(repo_meta.repo_id)

        if repo_config:
            repo_path = Path(repo_config.path).expanduser()

            if wt_path.exists():
                try:
                    remove_worktree(repo_path, wt_path)
                    console.print(f"[green]✓[/green] Removed worktree [dim]{wt_path.name}[/dim]")
                except GitError as e:
                    console.print(f"[yellow]⚠[/yellow] Could not remove worktree: {e}")

            if delete_branches:
                try:
                    delete_branch(repo_path, repo_meta.branch)
                    console.print(f"[green]✓[/green] Deleted branch [dim]{repo_meta.branch}[/dim] in {repo_meta.repo_name}")
                except GitError as e:
                    console.print(f"[yellow]⚠[/yellow] Could not delete branch in {repo_meta.repo_name}: {e}")
        else:
            # No config entry; just nuke the directory
            if wt_path.exists():
                shutil.rmtree(wt_path)
                console.print(f"[green]✓[/green] Removed [dim]{wt_path}[/dim]")

    workspace_dir = base / meta.name
    if workspace_dir.exists():
        try:
            workspace_dir.rmdir()  # only removes if empty
        except OSError:
            pass  # non-empty; leave it
