# Install, upgrade and roll back

**English** | [简体中文](installation.zh-CN.md) · [Documentation](README.md)

Requirements: a Codex client that loads skills, Python **3.10+** for the helper (tested with 3.12), and a runtime with selectable subagents if you want delegation. Unsupported delegation falls back to the current coordinator. Python must be available on the execution host.

Clone this repository or download and extract its ZIP. From the repository root:

### Windows / PowerShell

```powershell
git clone https://github.com/RyanGosling0508/codex-workspace-router.git
cd codex-workspace-router
python --version
python -X utf8 -B install_router.py
python -X utf8 -B install_router.py --install
```

### Linux / macOS

```bash
git clone https://github.com/RyanGosling0508/codex-workspace-router.git
cd codex-workspace-router
python3 --version
python3 -B install_router.py
python3 -B install_router.py --install
```

The first installer call is a **preview**. Only `--install` writes files. Default target: `$CODEX_HOME/skills/workspace-router`, or `~/.codex/skills/workspace-router` if `CODEX_HOME` is unset. Use `--codex-home /absolute/path` for a different Codex home. If Python is not on PATH, use the absolute path to an interpreter you have verified.

Skill discovery locations can differ by client/version. If your client follows the current `~/.agents/skills` or repository `.agents/skills` convention, place the **`workspace-router` directory** in that supported skill directory instead. Avoid duplicate installations with the same skill name. Check your client's [skill discovery documentation](https://learn.chatgpt.com/docs/build-skills).

You can also ask Codex's available skill installer to install `workspace-router` from this repository:

```text
Use $skill-installer to install the workspace-router skill from
https://github.com/RyanGosling0508/codex-workspace-router/tree/main/workspace-router
```

Verify that `workspace-router` appears in the skill list. Start a new task to load the updated instructions; restart the client if discovery has not refreshed. Installation changes neither your selected main model nor global `config.toml` nor project `AGENTS.md` files.

### SSH deployment

Run the same clone/install process **inside the connected remote execution host**, using that host's Python and Codex home. Then check discovery and model/delegation capabilities there. Local installation is not remote deployment. Do not share credentials or assume local Windows paths work remotely. The installer never opens SSH connections.

## Configure, disable, upgrade and roll back

Edit the **installed** `references/policy.json` to change supported model candidates or limits. Set `enabled` to `false` to keep direct work while disabling this router's delegation. For one request, say “no subagents.” Editing a downloaded source copy does not change an existing installation.

To upgrade with the companion installer, merge any local customizations into your reviewed source package first:

```bash
python3 -B install_router.py
python3 -B install_router.py --install --replace
```

Use `python -X utf8 -B` on Windows. A differing installation requires `--replace`; identical content is a no-op. Replacements back up the old skill under `<Codex home>/router-backups/`, outside skill discovery. The installer prints the backup path. To roll back, preview with `--source /absolute/backup/path`, then repeat with `--install --replace`. Do not run concurrent installers. Manual `.agents/skills` deployments require a manual backup/update in that same chosen directory.

## Open the installed policy in Router Studio

From the repository root after installation:

```sh
python run_console.py --installed --port 0 --open
```

Use `python3` on Linux/macOS. Check that Policy source points to your installation. Balanced is the default; Restore recommended defaults restores the complete Balanced policy. For a manual `.agents/skills` installation, use `--policy /absolute/path/workspace-router/references/policy.json`. See the [console guide](console.md).
