# Router Studio

**English** | [简体中文](CONSOLE.zh-CN.md)

A local bilingual policy editor. **中 / EN** changes the interface language, remembers your choice and keeps your current draft. Requires Python 3.10+, with no npm, API key or third-party Python packages.

## Start

From the repository directory:

```sh
python run_console.py --open
```

This edits the repository sample policy, **not your installed Skill**. Close the Python terminal to stop the server.

After installing or upgrading the Skill to 1.3 using the [installation guide](README.md), edit the installed policy:

```sh
python run_console.py --installed --open
```

Uses `CODEX_HOME` or `~/.codex` by default. Back up your custom model choices and workspace notes before upgrading; existing users should preserve their personal `references/workspaces.md` rather than overwrite it with the public template.

To select a particular file and an available port:

```sh
python run_console.py --policy /absolute/path/policy.json --port 0 --open
```

Each launch prints a URL with a temporary local access token. Open that full URL; do not share it. History defaults to `.local/console/history` inside the repository; use `--data-dir` to change it.

## Workflow

1. **Overview**: configure delegation triggers, concurrency, total starts, minimum work and recovery limits.
2. **Model lanes**: edit model IDs, efforts and fallback order for four lanes, including custom model IDs.
3. **Simulation lab**: choose synthetic tasks and resource conditions. The real rules engine returns recommendations and reasons. Configured candidates are assumed to support listed efforts; no account lookup, model call or agent dispatch occurs.
4. **Apply changes**: review the diff, then save. The previous policy is backed up. External file changes cause a conflict instead of silently overwriting a stale version.
5. **Version history**: load a previous policy as a draft, then apply to restore. Imports and presets also affect only the draft.

Changes affect future decisions that reload this file, not already dispatched tasks. Trigger switches permit consideration, never force delegation. Host, scope, conflict and budget checks remain active. Disabling independent review keeps that scenario with the main agent.

## Projects and SSH

Each server edits exactly the file selected at startup and displays its full path. It does not scan projects, connect to SSH or synchronize hosts. For a remote policy, run the repository on that host and access its loopback listener through SSH local port forwarding. Do not expose the service publicly. The remote host needs its own Python and Skill installation.

## Boundaries

- Edits child-agent routing, not the current conversation's main model.
- Animated paths, switches and transitions respect reduced-motion preferences.
- Binds only to `127.0.0.1`; checks a local token, Host and Origin; no arbitrary file access endpoint.
- History, exported drafts and target paths may contain personal configuration and are excluded from Git by default where applicable.
- No self-tuning, auto-update, startup registration or telemetry. Drafts live in page memory: language switching preserves them, but save or export before refreshing or closing.
- Atomic replacement and revision checks prevent typical stale overwrites; avoid multiple concurrent writers to the same policy file.

Validation:

```sh
python -B -m unittest console.test_console -v
python -B -m unittest discover -s workspace-router/tests -v
```

## Recommended defaults (1.3)

Use **Restore recommended defaults** to reset triggers, limits, classification mode and all model lanes together. It loads a draft, so review and apply as usual. The model page explains admission conditions and the simulation lab shows matching reasons. [Read the task boundaries](workspace-router/references/task-boundaries.md). Old imported policies remain labeled Legacy until explicitly reset.

## Three complete presets

Economy / Balanced / Premium, with Balanced as default. Each preset replaces routes and boundary behavior; simulate the draft, then review and apply. See [admission rules and official/user evidence](workspace-router/references/presets.md). No main-model switch or subscription savings guarantee.
