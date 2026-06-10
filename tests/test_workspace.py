from __future__ import annotations
import pytest
from pathlib import Path
from unittest.mock import MagicMock, call, patch
from wf.models import AppConfig, AppSettings, RepoConfig, WorkspaceMetadata, WorkspaceRepo
from wf.workspace import create_workspace, open_workspace, remove_workspace


@pytest.fixture
def repo_dir(tmp_path):
    d = tmp_path / "myrepo"
    d.mkdir()
    return d


@pytest.fixture
def repo_cfg(repo_dir):
    return RepoConfig(name="myrepo", short_id="mr", path=str(repo_dir))


@pytest.fixture
def app_cfg(tmp_path, repo_cfg):
    return AppConfig(
        settings=AppSettings(worktrees_base=str(tmp_path / "projs")),
        repos=[repo_cfg],
    )


@patch("wf.workspace.save_workspace")
@patch("wf.workspace.add_worktree")
def test_create_workspace_happy_path(mock_add, mock_save, repo_cfg, app_cfg):
    meta = create_workspace("foo", [repo_cfg], app_cfg)
    assert meta.name == "foo"
    assert meta.branch == "feature/foo"
    assert len(meta.repos) == 1
    assert meta.repos[0].repo_id == "mr"
    assert meta.repos[0].branch == "feature/foo"
    mock_add.assert_called_once()
    mock_save.assert_called_once_with(meta)


@patch("wf.workspace.save_workspace")
@patch("wf.workspace.add_worktree")
def test_create_workspace_worktree_path_convention(mock_add, mock_save, tmp_path, repo_cfg, app_cfg):
    meta = create_workspace("myfeature", [repo_cfg], app_cfg)
    expected_path = str(tmp_path / "projs" / "myfeature" / "wt_mr_myfeature")
    assert meta.repos[0].worktree_path == expected_path


def test_create_workspace_missing_repo_raises(tmp_path):
    repo = RepoConfig(name="x", short_id="x", path=str(tmp_path / "nonexistent"))
    config = AppConfig(settings=AppSettings(worktrees_base=str(tmp_path / "projs")))
    with pytest.raises(RuntimeError, match="Repo path not found"):
        create_workspace("foo", [repo], config)


@patch("wf.workspace.save_workspace")
@patch("wf.workspace.shutil.copy2")
@patch("wf.workspace.add_worktree")
def test_create_workspace_copies_files(mock_add, mock_copy, mock_save, repo_dir, tmp_path):
    (repo_dir / ".env").write_text("KEY=val")
    repo_cfg = RepoConfig(
        name="myrepo", short_id="mr", path=str(repo_dir), copy_files=[".env"]
    )
    app_cfg = AppConfig(
        settings=AppSettings(worktrees_base=str(tmp_path / "projs")),
        repos=[repo_cfg],
    )
    create_workspace("foo", [repo_cfg], app_cfg)
    mock_copy.assert_called_once()
    src, _ = mock_copy.call_args[0]
    assert src == repo_dir / ".env"


@patch("wf.workspace.save_workspace")
@patch("wf.workspace.subprocess.run")
@patch("wf.workspace.add_worktree")
def test_create_workspace_runs_bootstrap(mock_add, mock_subproc, mock_save, repo_dir, tmp_path):
    mock_subproc.return_value = MagicMock(returncode=0)
    repo_cfg = RepoConfig(
        name="myrepo",
        short_id="mr",
        path=str(repo_dir),
        bootstrap=[{"type": "run", "command": "uv sync"}],
    )
    app_cfg = AppConfig(
        settings=AppSettings(worktrees_base=str(tmp_path / "projs")),
        repos=[repo_cfg],
    )
    create_workspace("foo", [repo_cfg], app_cfg)
    mock_subproc.assert_called_once()
    _, kwargs = mock_subproc.call_args
    assert kwargs.get("shell") is True


@patch("wf.workspace.subprocess.Popen")
def test_open_workspace_launches_editor(mock_popen, tmp_path):
    wt_path = tmp_path / "wt"
    wt_path.mkdir()
    meta = WorkspaceMetadata(
        name="foo",
        branch="feature/foo",
        created_at="2024-01-01T00:00:00+00:00",
        repos=[WorkspaceRepo(repo_id="mr", repo_name="myrepo", worktree_path=str(wt_path), branch="feature/foo")],
    )
    open_workspace(meta, "cursor")
    mock_popen.assert_called_once_with(["cursor", str(wt_path)])


@patch("wf.workspace.subprocess.Popen")
def test_open_workspace_skips_missing_paths(mock_popen, tmp_path):
    meta = WorkspaceMetadata(
        name="foo",
        branch="feature/foo",
        created_at="2024-01-01T00:00:00+00:00",
        repos=[WorkspaceRepo(repo_id="mr", repo_name="myrepo", worktree_path=str(tmp_path / "gone"), branch="feature/foo")],
    )
    open_workspace(meta, "cursor")
    mock_popen.assert_not_called()


@patch("wf.workspace.remove_worktree")
@patch("wf.workspace.load_config")
def test_remove_workspace_removes_worktrees(mock_load_config, mock_remove_wt, tmp_path):
    wt_path = tmp_path / "wt"
    wt_path.mkdir()
    repo_cfg = RepoConfig(name="myrepo", short_id="mr", path=str(tmp_path / "myrepo"))
    mock_load_config.return_value = AppConfig(
        settings=AppSettings(worktrees_base=str(tmp_path)),
        repos=[repo_cfg],
    )
    meta = WorkspaceMetadata(
        name="foo",
        branch="feature/foo",
        created_at="2024-01-01T00:00:00+00:00",
        repos=[WorkspaceRepo(repo_id="mr", repo_name="myrepo", worktree_path=str(wt_path), branch="feature/foo")],
    )
    remove_workspace(meta, delete_branches=False)
    mock_remove_wt.assert_called_once()


@patch("wf.workspace.delete_branch")
@patch("wf.workspace.remove_worktree")
@patch("wf.workspace.load_config")
def test_remove_workspace_deletes_branches_when_flagged(mock_load_config, mock_remove_wt, mock_del_branch, tmp_path):
    wt_path = tmp_path / "wt"
    wt_path.mkdir()
    repo_cfg = RepoConfig(name="myrepo", short_id="mr", path=str(tmp_path / "myrepo"))
    mock_load_config.return_value = AppConfig(
        settings=AppSettings(worktrees_base=str(tmp_path)),
        repos=[repo_cfg],
    )
    meta = WorkspaceMetadata(
        name="foo",
        branch="feature/foo",
        created_at="2024-01-01T00:00:00+00:00",
        repos=[WorkspaceRepo(repo_id="mr", repo_name="myrepo", worktree_path=str(wt_path), branch="feature/foo")],
    )
    remove_workspace(meta, delete_branches=True)
    mock_del_branch.assert_called_once()
