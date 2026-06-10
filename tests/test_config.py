from __future__ import annotations
import yaml
import pytest
import wf.config as config_module
from wf.models import AppConfig, WorkspaceMetadata, WorkspaceRepo


@pytest.fixture(autouse=True)
def patch_config_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.yaml")
    monkeypatch.setattr(config_module, "WORKSPACES_DIR", tmp_path / "workspaces")


def _meta(name: str = "my-feature") -> WorkspaceMetadata:
    return WorkspaceMetadata(
        name=name,
        branch=f"feature/{name}",
        created_at="2024-01-01T00:00:00+00:00",
        repos=[
            WorkspaceRepo(
                repo_id="mr",
                repo_name="myrepo",
                worktree_path=f"/tmp/projs/{name}/wt_mr_{name}",
                branch=f"feature/{name}",
            )
        ],
    )


def test_load_config_missing_file():
    config = config_module.load_config()
    assert isinstance(config, AppConfig)
    assert config.repos == []
    assert config.settings.editor == "cursor"


def test_load_config_parses_yaml(tmp_path):
    config_file = config_module.CONFIG_FILE
    data = {
        "settings": {"editor": "code", "worktrees_base": "~/work"},
        "repos": [{"name": "myrepo", "short_id": "mr", "path": "~/git/myrepo"}],
    }
    config_file.write_text(yaml.dump(data))
    config = config_module.load_config()
    assert config.settings.editor == "code"
    assert config.settings.worktrees_base == "~/work"
    assert len(config.repos) == 1
    assert config.repos[0].name == "myrepo"


def test_save_and_load_workspace():
    meta = _meta()
    config_module.save_workspace(meta)
    loaded = config_module.load_workspace("my-feature")
    assert loaded is not None
    assert loaded.name == "my-feature"
    assert loaded.branch == "feature/my-feature"
    assert loaded.repos[0].repo_id == "mr"


def test_load_workspace_returns_none_for_unknown():
    assert config_module.load_workspace("nonexistent") is None


def test_delete_workspace_meta_removes_file():
    meta = _meta()
    config_module.save_workspace(meta)
    assert config_module.load_workspace("my-feature") is not None
    config_module.delete_workspace_meta("my-feature")
    assert config_module.load_workspace("my-feature") is None


def test_delete_workspace_meta_noop_when_missing():
    config_module.delete_workspace_meta("does-not-exist")  # should not raise


def test_list_workspaces_empty_when_dir_missing():
    assert config_module.list_workspaces() == []


def test_list_workspaces_sorted():
    for name in ["zebra", "alpha", "mango"]:
        config_module.save_workspace(_meta(name))
    assert config_module.list_workspaces() == ["alpha", "mango", "zebra"]
