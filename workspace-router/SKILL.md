---
name: workspace-router
description: Control unnecessary delegation in substantial project work. Keep the main agent by default; select a bounded model-specific child for an explicit delegation request, a concrete independent verification gap, or user-prioritized parallel speed. Check host, scope, conflicts, and acceptance before dispatch.
---

# Workspace Router

Optimize for **quality first, fewer unnecessary agents**. Keep the current coordinator and the user's current project/host. Default to direct execution, including substantial work. This skill requests bounded delegation only under the evidence gate below. It does not switch the main model, grant permissions, create top-level tasks, or move work across SSH hosts. Model routing is not evidence of lower cost.

## Choose the smallest useful workflow

- Answer ordinary questions and do tiny edits directly. Do not call the router to restate an obvious decision.
- Run independent reads or commands concurrently when sufficient; this is tool concurrency, not multi-model work. Rendering, downloads, compilation, or waiting alone do not justify another reasoning agent.
- Consider a child only when the user explicitly requests delegation, a specific correctness question needs an independent read-only check, or the user explicitly prioritizes parallel speed. Record the concrete request or verification gap. Complexity, available slots, a cheaper model, or a generic desire for quality is insufficient. Do not ask about parallelism on every task; when no basis exists, simply work directly without invoking the helper or collecting a catalog.
- Do not start a model just to classify difficulty, rewrite a handoff, summarize another agent, or repeat the main implementation. Use the current context to make the gate decision. A targeted reviewer can inspect correctness, but the coordinator should not blindly reimplement or rerun all successful checks.
- Preserve the current task's intent and prior decisions, including a short follow-up such as “继续”. Reassess after a meaningful scope change or an observed failure, not after every tool call.

## Task classification and defaults

Read [the task boundaries](references/task-boundaries.md) when preparing an eligible child. Use the installed `references/policy.json` as the current configuration; `references/default-policy.json` is the recommended reset template. Never infer current settings from the example defaults below or a previously cached policy.

The recommended `evidence-v1` classifier requires `task.assessment` with kind, specification, verification, scope, input_form, boundary and concrete evidence. It applies the highest matching rule and preserves the declared complexity as a floor. Only text-only, exact, mechanically checkable, local extraction/transformation with low consequence and low uncertainty qualifies for Luna/high. Bounded routine work uses Sol/medium; cross-component, open, uncertain or judgment-heavy investigation uses Sol/high; high-consequence work and open/uncertain system design use Astra/high. Missing assessment means no automatic dispatch. These are operational boundaries, not guarantees of model quality.

Read [presets and evidence](references/presets.md) for economic trial and premium ambiguity rules. The paragraph above describes Balanced defaults. Economy may try the deterministic candidate pool for strictly testable low-risk local implementation; retain the routine recovery floor. Premium promotes evidenced adjacent-lane ambiguity. Record `boundary_evidence` when boundary is adjacent; significant unresolved uncertainty remains high. Every preset preserves acceptance and the direct-by-default gate.

## Before delegation

Read [the host and workspace checklist](references/workspaces.md) for multi-root projects, shared resources, or SSH. Read [the protocol](references/protocol.md) when making a router request or managing a child. Do not read all references on simple direct work.

1. Observe the current execution host, working directory, applicable project instructions, allowed task paths, and tools. A sidebar project can contain several roots; it is not an isolation boundary. A remote connection registration is not proof of a live remote runtime.
2. Identify explicit read/write paths, protected sources, shared resources, acceptance, and relevant existing changes. Carry these into the child capsule. File writes must already be within the user's task and current permissions. Test/build commands may write caches: list those paths and resources too.
3. Observe supported models and efforts **on this host** from the current spawn tool schema or App Server `model/list`. Do not read unrelated session logs, infer the current model from config defaults, or treat a cached model list as live availability. Unknown capabilities mean keep the work local.
4. Run `scripts/router.py decide` using an observed Python 3.10+ executable and a structured request. Python is a local helper only; no API key or network call is needed. Request files belong in the task's scratch directory and contain no credentials. Discover a working interpreter on the actual execution host; never assume a local executable path exists over SSH.
5. Delegate only on `action=delegate`, after rechecking slots and overlap. `serialize` means do not run the conflicting local work either while the owner is active. `direct` is not authorization to bypass a rejected scope, protected asset, or permission. `report_unsupported` preserves an explicit model choice: explain the limitation and continue only work independent of it.

## Dispatch and finish

Use the current runtime's real collaboration tool. Prefer a model override with `fork_turns="none"` and a self-contained capsule; map the plan to the actual tool schema instead of forwarding the whole JSON. Do not synthesize a nonexistent tool or require legacy custom-agent names. If the runtime cannot select the proposed model, keep the coordinator and disclose the limitation when material.

The capsule includes only necessary goal/context; host/cwd; read/write/protected paths; existing changes to preserve; applicable instructions; tools/environment; acceptance and validation budget; shared resources; no nested delegation; stop condition. Ask for findings, changed paths, verification evidence and blockers; no conversation recap or ceremonial report. Children cannot expand scope or change hosts. Defaults: one active child, at most two child starts across the current user request including replacements/retries, and at most one evidence-based recovery per bounded subtask. Preserve counters across re-planning; finishing a child does not restore the total budget. Runtime/user limits may be lower.

Tell the user briefly why a child is needed, e.g. “坐标轴转换还缺独立验证，交给 Sol 做一次只读检查。” Parallel speed and independent review may increase total usage; never call them savings without measured total usage and a valid comparison. Do not print banners for direct work. Requested routes are not proof of actual execution; use runtime metadata where available, otherwise label unverified.

Wait for required results. A wait timeout is not failure; inspect actual progress before considering interruption. A child reporting completed is not proof of correctness: review its diff/evidence and the task's acceptance criteria. Repeat a check only after changes, failures, or unresolved concerns. Do not mark a failed or interrupted child accepted because its partial output looks plausible.

Before finalizing, ensure required child work is complete or honestly report its blocker. Stop only this request's unneeded active children through available runtime controls; never affect unrelated projects or background tasks. Do not reuse a child across user requests in this version.

## Recovery and controls

- Respect “不要子代理/关闭路由/这次直接做” immediately. A skill instruction does not override a user's explicit no-delegation request.
- Separate reasoning/verification failures from network, auth, permissions, unavailable models, or missing dependencies. Fix the latter within scope; more reasoning is not their remedy.
- On helper failure, unsupported catalog, or unavailable collaboration tools, continue authorized work with the coordinator. Do not silently adopt another model after the user pinned one.
- Never auto-select Max or Ultra. User-requested Max must be supported; Ultra belongs to a separately requested native workflow and cannot be nested inside this router.
- Use [maintenance and evaluation](references/maintenance.md) for persistent enable/disable, upgrades, telemetry, or tuning. No automatic self-editing of policy, model-download, remote install, or update loop.
