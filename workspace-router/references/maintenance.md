# Controls, evidence, and maintenance

Policy is `references/policy.json`. Default quality lanes are Luna/medium for narrow mechanical work, Sol/medium for bounded routine work, Sol/high for complex work, Astra/high for consequential work; ordered fallbacks must exist in the live catalog. These are initial operating choices, not benchmark claims. Terra is available only through an explicit supported request or an intentional policy revision; do not auto-select an older model merely because it exists. Max/Ultra are never automatic.

User control: “这次直接做/不要子代理” disables delegation for the current task. Persistently set policy `enabled:false` to disable the installed router, or disable the skill through the app if supported. Keep automatic discovery enabled by default; it is a model-selected skill, not a guaranteed every-message interception hook. A new task or app refresh may be needed after installation before discovery. `$workspace-router` is the explicit invocation.

Version 1.1 defaults: direct execution even for large work; delegation only for an explicit child request, a concrete independent read-only verification gap, or explicitly prioritized parallel speed. Model price, task complexity and spare slots alone do not open this gate. One active child, two total child starts per user request including retries/replacements, no grandchildren, one recovery per bounded subtask, minimum three estimated reasoning minutes, capability observations at most six hours old. Obtain fresh capabilities after reconnecting or switching hosts; age alone cannot prove availability. Slot counts and resource checks are advisory, not atomic global locks. Serialize shared writes whose other owners cannot be observed.

Do not add a classifier model, automatic review of every change, or a second summarizer. For an authorized child, send necessary context once and request a compact artifact/evidence report. The main agent verifies acceptance and reports the result without recreating the child's full analysis. Direct work does not require a JSON request or capability probe. These changes reduce opportunities for overhead; they do not establish actual quota savings. Keep the user's selected main model unchanged.

## Evidence without hidden collection

No telemetry is sent and no persistent usage log is enabled by default. If the user requests evaluation, `router.py audit --input event.json --audit-dir <approved-task-directory>` writes one unique JSON event. Omit `--audit-dir` to print only. Inputs: terminal `state`, `acceptance`, optional `observed:{source:"runtime",model,effort}`, `elapsed_seconds`, `input_tokens`, `output_tokens`. Missing observations remain null. These supplied observations are not cryptographically attested. The helper drops prompts, file paths and free-text rationale.

Evaluate representative tasks on the same acceptance criteria: final correctness, missed requirements, rework, end-to-end time and total coordinator-plus-child tokens when available. Subscription quota usage is not dollar cost; absent pricing and complete usage, do not calculate savings. Start with a small set of actual low-risk independent tasks; scripted gate tests do not demonstrate improved model quality. Do not claim a percentage improvement from synthetic cases.

## Upgrades and rollback

Keep model IDs outside the skill body in policy. When the runtime model list changes, record the change, test candidate routes and acceptance quality, then intentionally update the policy version. Do not auto-map an unknown new model to a quality lane. No self-update, model downloads, hidden API credentials, or edits to global `config.toml`, project `AGENTS.md`, or unrelated skills.

The companion installer previews by default, refuses changed existing installations unless `--replace` is supplied, and backs up an old installation outside the discovery directory before replacement. Reinstalling identical content is a no-op. Keep local policy customizations by merging them into the reviewed package before replacement; do not blindly overwrite them. For rollback, preview the backup as `--source`, then install it with `--replace`. Disable delegation immediately if behavior degrades while retaining ordinary coordinator work.

Run the packaged unit tests and skill validator after changes. Repeat independent behavioral evaluation when dispatch/lifecycle/scope logic changes. Validate on each execution OS before declaring support verified there.

## Provenance

This is an independent implementation, informed by the workflow idea in [codex-auto-model-router](https://github.com/orange-the-weak/codex-auto-model-router). It does not copy that project's router code or install its legacy agent presets. Official interfaces inform the boundaries: [skills](https://learn.chatgpt.com/docs/build-skills), [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [App Server](https://learn.chatgpt.com/docs/app-server), [remote connections](https://learn.chatgpt.com/docs/remote-connections). Recheck current documentation and actual runtime schema when upgrading.
