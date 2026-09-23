# Codex Workspace Router

**English** | [简体中文](README.zh-CN.md)

A Codex skill for **quality-first work with fewer unnecessary agents**. Keep the main agent by default. Delegate only when a concrete need justifies the handoff.

**Version 1.3.0 · Python standard library · No router API key · MIT**

**Default preset: Balanced.** Choose Economy, Balanced or Premium in the bilingual console; [compare the presets and their evidence](workspace-router/references/presets.md).

> This skill selects bounded **subagents**, not the main model for each message. It is not a pre-request model gateway and does not guarantee lower cost or quota usage.

## Recommended task boundaries

Defaults now require explicit task evidence and use Luna/high, Sol/medium, Sol/high or Astra/high according to the highest matching condition. Read the [exact boundaries, examples and research basis](workspace-router/references/task-boundaries.md). The console can restore the complete recommended policy without editing each lane.

## Visual console

Router Studio includes Chinese/English switching, editable model lanes, rule simulations, reviewed saves and version history. Start with `python run_console.py --open`. Read the [console guide](CONSOLE.md).

## What happens when you use it?

```text
Your request → current main agent
                 ├─ no concrete delegation need → complete the work directly
                 └─ a concrete need exists
                      → check host, paths, conflicts, acceptance and capabilities
                      → choose one supported child route
                      → inspect its result and answer
```

There is no additional classifier model, always-on router service, or automatic summarizer. The main agent uses the context it already has. The Python helper checks structured observations; it does not classify natural-language prompts or dispatch agents itself.

## Install

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

## How to trigger it

Automatic selection is enabled by `agents/openai.yaml` with `allow_implicit_invocation: true`. Codex may load the skill when a request matches its description; it is **not a guaranteed hook on every message**. Loading the skill does not imply launching an agent.

Explicit invocation:

```text
$workspace-router Continue implementing this feature using the existing acceptance criteria.
```

This still defaults to direct work. Examples of the decision:

| Request / observed situation | Expected behavior |
|---|---|
| “Fix this bug; keep agent overhead low.” | Main agent handles it directly, even if the task is substantial. |
| “Use one independent Sol/medium child to review the coordinate transform.” | Consider that exact route after scope and capability checks. |
| A concrete correctness gap requires an independent view, e.g. untested polygon winding after an axis swap | Consider a targeted **read-only** review; no automatic duplicate implementation. |
| “Prioritize turnaround time; parallelize independent work.” | Consider bounded parallelism; faster is not necessarily cheaper. |
| The candidate model might be cheaper, or slots are idle | Neither is enough to justify delegation. |
| “Do this directly; no subagents.” | Do not delegate. |
| A needed file is being modified or a shared build directory is busy | Wait or pick truly independent work. |

A specific verification gap can be detected by the main agent; the user need not choose a model or restate the policy each time. The main agent must not invent user consent or verification gaps to pass the gate.

## Policy

Only **after** delegation is justified, these initial lanes apply:

| Eligible work | First candidate | Ordered fallback |
|---|---|---|
| Mechanical, low uncertainty and low consequence | `gpt-6-luna` / high | Sol / medium → Astra / low |
| Bounded routine implementation or analysis | `gpt-6-sol` / medium | Astra / medium |
| Complex debugging or high uncertainty | `gpt-6-sol` / high | Astra / high |
| High-consequence correctness decisions | `gpt-6-astra` / high | No lower-lane fallback |

These are configurable starting choices, **not a benchmark ranking**. Model IDs and reasoning levels must be supported by the current execution host. The helper does not discover them itself. An unavailable user-pinned route is reported rather than silently substituted. Terra is not automatic; Max requires an explicit supported request; Ultra is outside this router's nested workflow.

Defaults in [`policy.json`](workspace-router/references/policy.json):

- Enabled, quality first, concrete-evidence delegation gate.
- **One active child**, **two total child starts per user request**, including replacements and retries.
- No grandchildren; at most one classified reasoning/verification recovery per bounded subtask.
- At least three estimated minutes of reasoning work before delegation is considered; this is an additional filter, not a reason to delegate.
- Same verified execution host; explicit read/write/protected paths; no overlapping file writes or shared-resource races.
- Capability observations expire after six hours; reconnecting or switching hosts requires fresh observations.
- Missing context, uncertain benefit, absent tools, malformed inputs or unavailable quality lanes keep work with the coordinator.
- Network/auth/permission/dependency problems are not reasons to upgrade the model.
- A child finishing is not acceptance. The coordinator checks the actual criteria and evidence.

The script checks supplied facts, not their truth. Prompt scopes are not a sandbox; resource checks are not atomic global locks. Existing permissions and project instructions remain authoritative. There is no guaranteed cost saving, trained difficulty classifier, or hidden usage collection.

## Configure, disable, upgrade and roll back

Edit the **installed** `references/policy.json` to change supported model candidates or limits. Set `enabled` to `false` to keep direct work while disabling this router's delegation. For one request, say “no subagents.” Editing a downloaded source copy does not change an existing installation.

To upgrade with the companion installer, merge any local customizations into your reviewed source package first:

```bash
python3 -B install_router.py
python3 -B install_router.py --install --replace
```

Use `python -X utf8 -B` on Windows. A differing installation requires `--replace`; identical content is a no-op. Replacements back up the old skill under `<Codex home>/router-backups/`, outside skill discovery. The installer prints the backup path. To roll back, preview with `--source /absolute/backup/path`, then repeat with `--install --replace`. Do not run concurrent installers. Manual `.agents/skills` deployments require a manual backup/update in that same chosen directory.

## Validate and inspect

```bash
python3 -B -m unittest discover -s workspace-router/tests -v
python3 -B -m unittest discover -s . -p test_installer.py -v
python3 -B scripts/check_package.py
```

Windows equivalent: replace `python3 -B` with `python -X utf8 -B`. CI runs these checks on Windows and Ubuntu with Python 3.12. A configured CI matrix is not a claim that an unrun job passed; see actual run results.

Before publication, Windows tests passed with the symlink test skipped where the host did not allow link creation. Rule tests establish covered behavior, not better model quality, long-term reliability, or cost savings.

- [`SKILL.md`](workspace-router/SKILL.md): agent-facing workflow.
- [`protocol.md`](workspace-router/references/protocol.md): input contract, gate results and child lifecycle.
- [`workspaces.md`](workspace-router/references/workspaces.md): generic multi-root / SSH checklist.
- [`maintenance.md`](workspace-router/references/maintenance.md): evaluation, optional metadata-only audit and policy updates.

The public package contains generic examples, not the original author's machine paths or private project inventory. Its core router and policy match the personalized 1.3.0 edition; keep private project rules in applicable local project instructions.

## Provenance and license

Independent implementation informed by the workflow idea in [codex-auto-model-router](https://github.com/orange-the-weak/codex-auto-model-router); no router code or legacy agent presets were copied. This is an independent community project, not an official OpenAI product.

Interface references: [Skills](https://learn.chatgpt.com/docs/build-skills), [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [App Server](https://learn.chatgpt.com/docs/app-server), [Remote connections](https://learn.chatgpt.com/docs/remote-connections).

[MIT License](LICENSE).

## Three complete presets

Economy / Balanced / Premium, with Balanced as default. Each preset replaces routes and boundary behavior; simulate the draft, then review and apply. See [admission rules and official/user evidence](workspace-router/references/presets.md). No main-model switch or subscription savings guarantee.
