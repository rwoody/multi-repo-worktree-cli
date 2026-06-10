from __future__ import annotations
from pathlib import Path
import yaml
from .models import AppConfig, WorkspaceMetadata

CONFIG_DIR = Path.home() / ".config" / "wf-tool"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
WORKSPACES_DIR = CONFIG_DIR / "workspaces"


def load_config() -> AppConfig:
    if not CONFIG_FILE.exists():
        return AppConfig()
    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f) or {}
    return AppConfig.model_validate(data)


def load_workspace(name: str) -> WorkspaceMetadata | None:
    path = WORKSPACES_DIR / f"{name}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return WorkspaceMetadata.model_validate(data)


def save_workspace(meta: WorkspaceMetadata) -> None:
    WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
    path = WORKSPACES_DIR / f"{meta.name}.yaml"
    with open(path, "w") as f:
        yaml.dump(meta.model_dump(), f, default_flow_style=False)


def delete_workspace_meta(name: str) -> None:
    path = WORKSPACES_DIR / f"{name}.yaml"
    if path.exists():
        path.unlink()


def list_workspaces() -> list[str]:
    if not WORKSPACES_DIR.exists():
        return []
    return sorted(p.stem for p in WORKSPACES_DIR.glob("*.yaml"))
