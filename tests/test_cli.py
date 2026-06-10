from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from wf.cli import app
from wf.models import AppConfig, AppSettings, RepoConfig, WorkspaceMetadata, WorkspaceRepo


runner = CliRunner()


def _meta(name: str = "my-feature") -> WorkspaceMetadata:
    return WorkspaceMetadata(
        name=name,
        branch=f"feature/{name}",
        created_at="2024-01-01T00:00:00+00:00",
        repos=[
            WorkspaceRepo(
                repo_id="mr",
                repo_name="myrepo",
                worktree_path=f"/tmp/{name}/wt_mr_{name}",
                branch=f"feature/{name}",
            )
        ],
    )


# --- wf list ---

@patch("wf.cli.list_workspaces")
def test_list_empty(mock_list):
    mock_list.return_value = []
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No workspaces" in result.output


@patch("wf.cli.load_workspace")
@patch("wf.cli.list_workspaces")
def test_list_shows_workspaces(mock_list, mock_load):
    mock_list.return_value = ["my-feature"]
    mock_load.return_value = _meta("my-feature")
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "my-feature" in result.output
    assert "feature/my-feature" in result.output
    assert "myrepo" in result.output


# --- wf open ---

@patch("wf.cli.list_workspaces")
@patch("wf.cli.load_workspace")
@patch("wf.cli.load_config")
def test_open_not_found(mock_cfg, mock_load, mock_list):
    mock_cfg.return_value = AppConfig()
    mock_load.return_value = None
    mock_list.return_value = []
    result = runner.invoke(app, ["open", "foo"])
    assert result.exit_code == 1
    assert "not found" in result.output


@patch("wf.cli.open_workspace")
@patch("wf.cli.load_workspace")
@patch("wf.cli.load_config")
def test_open_found(mock_cfg, mock_load, mock_open):
    mock_cfg.return_value = AppConfig()
    meta = _meta("my-feature")
    mock_load.return_value = meta
    result = runner.invoke(app, ["open", "my-feature"])
    assert result.exit_code == 0
    mock_open.assert_called_once_with(meta, "cursor")


# --- wf remove ---

@patch("wf.cli.list_workspaces")
@patch("wf.cli.load_workspace")
def test_remove_not_found(mock_load, mock_list):
    mock_load.return_value = None
    mock_list.return_value = []
    result = runner.invoke(app, ["remove", "foo"])
    assert result.exit_code == 1
    assert "not found" in result.output


@patch("wf.cli.delete_workspace_meta")
@patch("wf.cli.remove_workspace")
@patch("wf.cli.load_workspace")
def test_remove_with_yes_flag(mock_load, mock_remove, mock_delete):
    meta = _meta("my-feature")
    mock_load.return_value = meta
    result = runner.invoke(app, ["remove", "my-feature", "--yes"])
    assert result.exit_code == 0
    mock_remove.assert_called_once_with(meta, delete_branches=False)
    mock_delete.assert_called_once_with("my-feature")
    assert "removed" in result.output.lower()


@patch("wf.cli.delete_workspace_meta")
@patch("wf.cli.remove_workspace")
@patch("wf.cli.load_workspace")
def test_remove_with_delete_branches(mock_load, mock_remove, mock_delete):
    meta = _meta("my-feature")
    mock_load.return_value = meta
    result = runner.invoke(app, ["remove", "my-feature", "--yes", "--delete-branches"])
    assert result.exit_code == 0
    mock_remove.assert_called_once_with(meta, delete_branches=True)


@patch("wf.cli.questionary")
@patch("wf.cli.load_workspace")
def test_remove_cancelled(mock_load, mock_q):
    meta = _meta("my-feature")
    mock_load.return_value = meta
    mock_q.confirm.return_value.ask.return_value = False
    result = runner.invoke(app, ["remove", "my-feature"])
    assert result.exit_code == 0
    assert "Cancelled" in result.output


# --- wf create ---

@patch("wf.cli.load_config")
def test_create_no_repos_exits(mock_cfg):
    mock_cfg.return_value = AppConfig()
    result = runner.invoke(app, ["create"])
    assert result.exit_code == 1
    assert "No repositories configured" in result.output


@patch("wf.cli.load_workspace")
@patch("wf.cli.questionary")
@patch("wf.cli.load_config")
def test_create_duplicate_name_exits(mock_cfg, mock_q, mock_load):
    repo = RepoConfig(name="myrepo", short_id="mr", path="~/git/myrepo")
    mock_cfg.return_value = AppConfig(repos=[repo])
    mock_q.checkbox.return_value.ask.return_value = [repo]
    mock_q.text.return_value.ask.return_value = "existing"
    mock_load.return_value = _meta("existing")
    result = runner.invoke(app, ["create"])
    assert result.exit_code == 1
    assert "already exists" in result.output


@patch("wf.cli.create_workspace")
@patch("wf.cli.load_workspace")
@patch("wf.cli.questionary")
@patch("wf.cli.load_config")
def test_create_success(mock_cfg, mock_q, mock_load_ws, mock_create):
    repo = RepoConfig(name="myrepo", short_id="mr", path="~/git/myrepo")
    mock_cfg.return_value = AppConfig(repos=[repo])
    mock_q.checkbox.return_value.ask.return_value = [repo]
    mock_q.text.return_value.ask.return_value = "new-feature"
    mock_load_ws.return_value = None
    mock_create.return_value = _meta("new-feature")
    result = runner.invoke(app, ["create"])
    assert result.exit_code == 0
    mock_create.assert_called_once()
    assert "new-feature" in result.output
