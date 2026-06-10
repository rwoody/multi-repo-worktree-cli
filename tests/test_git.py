from __future__ import annotations
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from wf.git import GitError, _run, add_worktree, delete_branch, remove_worktree


REPO = Path("/fake/repo")
WT = Path("/fake/wt")


def _result(returncode=0, stdout="", stderr=""):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


@patch("wf.git.subprocess.run")
def test_run_returns_stdout(mock_run):
    mock_run.return_value = _result(stdout="on branch main")
    assert _run(REPO, ["status"]) == "on branch main"


@patch("wf.git.subprocess.run")
def test_run_prefers_stderr_on_failure(mock_run):
    mock_run.return_value = _result(returncode=1, stderr="fatal: not a repo", stdout="ignored")
    with pytest.raises(GitError, match="fatal: not a repo"):
        _run(REPO, ["status"])


@patch("wf.git.subprocess.run")
def test_run_falls_back_to_stdout_on_failure(mock_run):
    mock_run.return_value = _result(returncode=1, stderr="", stdout="some error output")
    with pytest.raises(GitError, match="some error output"):
        _run(REPO, ["status"])


@patch("wf.git.subprocess.run")
def test_add_worktree_happy_path(mock_run):
    mock_run.return_value = _result()
    add_worktree(REPO, WT, "feature/foo", "main")
    called_args = mock_run.call_args[0][0]
    assert called_args == ["git", "worktree", "add", "-b", "feature/foo", str(WT), "main"]


@patch("wf.git.subprocess.run")
def test_add_worktree_retries_without_b_when_branch_exists(mock_run):
    mock_run.side_effect = [
        _result(returncode=1, stderr="a branch named 'feature/foo' already exists"),
        _result(),
    ]
    add_worktree(REPO, WT, "feature/foo", "main")
    assert mock_run.call_count == 2
    retry_args = mock_run.call_args_list[1][0][0]
    assert "-b" not in retry_args
    assert "feature/foo" in retry_args
    assert str(WT) in retry_args


@patch("wf.git.subprocess.run")
def test_add_worktree_reraises_unrelated_error(mock_run):
    mock_run.return_value = _result(returncode=1, stderr="permission denied")
    with pytest.raises(GitError, match="permission denied"):
        add_worktree(REPO, WT, "feature/foo", "main")
    assert mock_run.call_count == 1


@patch("wf.git.subprocess.run")
def test_remove_worktree(mock_run):
    mock_run.return_value = _result()
    remove_worktree(REPO, WT)
    called_args = mock_run.call_args[0][0]
    assert called_args == ["git", "worktree", "remove", "--force", str(WT)]


@patch("wf.git.subprocess.run")
def test_delete_branch(mock_run):
    mock_run.return_value = _result()
    delete_branch(REPO, "feature/foo")
    called_args = mock_run.call_args[0][0]
    assert called_args == ["git", "branch", "-D", "feature/foo"]
