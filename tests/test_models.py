from __future__ import annotations
import pytest
from pydantic import ValidationError
from wf.models import (
    AppConfig,
    AppSettings,
    BootstrapAction,
    RepoConfig,
    WorkspaceMetadata,
    WorkspaceRepo,
)


def test_repo_config_defaults():
    repo = RepoConfig(name="myrepo", short_id="mr", path="~/git/myrepo")
    assert repo.default_branch == "main"
    assert repo.copy_files == []
    assert repo.bootstrap == []


def test_repo_config_full():
    repo = RepoConfig(
        name="myrepo",
        short_id="mr",
        path="~/git/myrepo",
        default_branch="develop",
        copy_files=[".env"],
        bootstrap=[{"type": "run", "command": "npm install"}],
    )
    assert repo.default_branch == "develop"
    assert repo.copy_files == [".env"]
    assert len(repo.bootstrap) == 1
    assert repo.bootstrap[0].type == "run"
    assert repo.bootstrap[0].command == "npm install"


def test_app_config_defaults():
    config = AppConfig()
    assert config.settings.worktrees_base == "~/projs"
    assert config.settings.editor == "cursor"
    assert config.repos == []


def test_app_settings_custom():
    settings = AppSettings(worktrees_base="~/workspaces", editor="code")
    assert settings.worktrees_base == "~/workspaces"
    assert settings.editor == "code"


def test_workspace_metadata_round_trip():
    meta = WorkspaceMetadata(
        name="my-feature",
        branch="feature/my-feature",
        created_at="2024-01-01T00:00:00+00:00",
        repos=[
            WorkspaceRepo(
                repo_id="mr",
                repo_name="myrepo",
                worktree_path="/tmp/projs/my-feature/wt_mr_my-feature",
                branch="feature/my-feature",
            )
        ],
    )
    restored = WorkspaceMetadata.model_validate(meta.model_dump())
    assert restored.name == meta.name
    assert restored.branch == meta.branch
    assert restored.repos[0].repo_id == "mr"
    assert restored.repos[0].worktree_path == meta.repos[0].worktree_path


def test_repo_config_missing_required_fields():
    with pytest.raises(ValidationError):
        RepoConfig(name="x")  # missing short_id and path


def test_bootstrap_action_cwd_optional():
    action = BootstrapAction(type="run", command="echo hi")
    assert action.cwd is None


def test_bootstrap_action_with_cwd():
    action = BootstrapAction(type="run", command="npm install", cwd="web/")
    assert action.cwd == "web/"
