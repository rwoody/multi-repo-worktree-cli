from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class BootstrapAction(BaseModel):
    type: str  # only "run" supported for now
    command: str
    cwd: Optional[str] = None  # relative to worktree root; defaults to worktree root


class RepoConfig(BaseModel):
    name: str
    short_id: str
    path: str  # supports ~ expansion
    default_branch: str = "main"
    copy_files: list[str] = Field(default_factory=list)
    bootstrap: list[BootstrapAction] = Field(default_factory=list)


class AppSettings(BaseModel):
    worktrees_base: str = "~/projs"
    editor: str = "cursor"


class AppConfig(BaseModel):
    settings: AppSettings = Field(default_factory=AppSettings)
    repos: list[RepoConfig] = Field(default_factory=list)


class WorkspaceRepo(BaseModel):
    repo_id: str       # matches RepoConfig.short_id
    repo_name: str
    worktree_path: str
    branch: str


class WorkspaceMetadata(BaseModel):
    name: str
    branch: str
    created_at: str    # ISO datetime
    repos: list[WorkspaceRepo]
