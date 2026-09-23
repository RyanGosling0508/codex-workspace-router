# Triggers and everyday use

**English** | [简体中文](usage.zh-CN.md) · [Documentation](README.md)

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

## Use the presets

Start with Balanced and describe the project work normally. Model selection follows a justified delegation need. Economy may try Luna on testable, low-risk local implementation; Premium promotes evidenced ambiguity between adjacent lanes. All require acceptance. Defaults: one active child, two total starts, five minutes of reasoning work.

- [Complete presets and research](../workspace-router/references/presets.md)
- [Strict task boundaries](../workspace-router/references/task-boundaries.md)
- [FAQ and troubleshooting](faq.md)
