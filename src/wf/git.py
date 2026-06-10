from __future__ import annotations
import subprocess
from pathlib import Path


class GitError(Exception):
    pass


def _run(cwd: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def add_worktree(repo_path: Path, worktree_path: Path, branch: str, from_ref: str) -> None:
    """Create a new branch and worktree. Falls back to using an existing branch."""
    try:
        _run(repo_path, ["worktree", "add", "-b", branch, str(worktree_path), from_ref])
    except GitError as e:
        err = str(e).lower()
        if "already exists" in err or "a branch named" in err:
            # Branch exists; add worktree against it without -b
            _run(repo_path, ["worktree", "add", str(worktree_path), branch])
        else:
            raise


def remove_worktree(repo_path: Path, worktree_path: Path) -> None:
    _run(repo_path, ["worktree", "remove", "--force", str(worktree_path)])


def delete_branch(repo_path: Path, branch: str) -> None:
    _run(repo_path, ["branch", "-D", branch])
