# wf — workspace manager for multi-repo feature development

`wf` is a CLI tool that automates the tedious parts of starting a feature that spans multiple git repositories: creating branches, setting up worktrees, copying `.env` files, and running bootstrap commands — all in one command.

```
$ wf create
? Select repositories:  [x] api-server  [x] web-portal
? Feature name: payments-v2

Creating workspace payments-v2
Branch: feature/payments-v2

→ api-server
  ✓ Worktree wt_as_payments-v2 on branch feature/payments-v2
  ✓ Copied .env
  $ uv sync --group canonical

→ web-portal
  ✓ Worktree wt_wp_payments-v2 on branch feature/payments-v2
  ✓ Copied .env
  $ npm install

✓ Workspace 'payments-v2' created.
Open with: wf open payments-v2
```

## Why

When working across multiple repos, starting a new feature means:
1. `cd` into each repo, `git checkout -b feature/...`
2. Set up a worktree or clone so you can work on multiple features at once
3. Copy `.env` from the main checkout into the worktree
4. Run `npm install`, `uv sync`, or whatever bootstrap the repo needs

Multiply that by 3–5 repos per feature and it's a lot of manual work. `wf` does it all at once.

## Prerequisites

- Python 3.11+
- git 2.5+ (for worktree support)
- [uv](https://docs.astral.sh/uv/) (recommended for install)

## Install

```bash
git clone https://github.com/rwoody/multi-repo-worktree-cli.git ~/git/wf-tool
cd ~/git/wf-tool
uv venv && uv pip install -e .
```

Add the binary to your PATH (pick one):

```bash
# Option A: add the venv to PATH in your shell profile
export PATH="$HOME/git/wf-tool/.venv/bin:$PATH"

# Option B: symlink to somewhere already on PATH
ln -s ~/git/wf-tool/.venv/bin/wf ~/.local/bin/wf
```

## Quick start

Copy the example config and edit it to match your setup:

```bash
mkdir -p ~/.config/wf-tool
cp ~/git/wf-tool/config.example.yaml ~/.config/wf-tool/config.yaml
$EDITOR ~/.config/wf-tool/config.yaml
```

Then create your first workspace:

```bash
wf create      # interactive: pick repos, enter a feature name
wf open myfeature
wf list
wf remove myfeature
```

## Commands

| Command | Description |
|---|---|
| `wf create` | Interactively create a new workspace (select repos, enter name) |
| `wf open <name>` | Open all repos for the workspace in the configured editor |
| `wf list` | List all workspaces with their branch and repos |
| `wf remove <name>` | Remove worktrees and workspace metadata |
| `wf remove <name> --yes` | Skip the confirmation prompt |
| `wf remove <name> --delete-branches` | Also delete the feature branches from each repo |

## Config reference

Config lives at `~/.config/wf-tool/config.yaml`.

```yaml
settings:
  worktrees_base: ~/projs   # root directory where workspace folders are created
  editor: cursor            # editor command: "cursor", "code", or any binary on PATH

repos:
  - name: api-server       # display name shown in prompts and wf list
    short_id: os            # short slug used in the worktree directory name
    path: ~/git/api-server # path to the main checkout of this repo (~ is expanded)
    default_branch: main    # branch to base new feature branches on

    copy_files:             # files to copy from main checkout into each worktree
      - .env

    bootstrap:              # commands to run inside the worktree after creation
      - type: run
        command: uv sync
        # cwd: optional subdirectory relative to worktree root (defaults to worktree root)

  - name: web-portal
    short_id: wp
    path: ~/git/web-portal
    default_branch: main
    copy_files:
      - .env
    bootstrap:
      - type: run
        command: uv sync
      - type: run
        command: npm install
        cwd: web/           # run from ~/projs/<workspace>/wt_wp_<workspace>/web/
```

## Worktree layout

Worktrees are created under `worktrees_base` using this convention:

```
~/projs/
  payments-v2/
    wt_as_payments-v2/    # api-server worktree  (wt_{short_id}_{workspace})
    wt_wp_payments-v2/    # web-portal worktree
```

Workspace metadata (branch, paths) is stored in `~/.config/wf-tool/workspaces/<name>.yaml`.

## Development

```bash
uv pip install -e ".[dev]"
pytest
```

## License

MIT
