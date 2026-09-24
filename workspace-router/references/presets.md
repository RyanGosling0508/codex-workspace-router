# Presets and evidence · 1.4

**English** | [简体中文](presets.zh-CN.md)

**Balanced is the default.** These presets choose eligible child routes, not the Codex main model. Direct work remains direct. Host, scope, conflict, permissions and acceptance checks apply to all presets.

| Task | Economy | Balanced (default) | Premium |
|---|---|---|---|
| Deterministic text extraction/transformation | Luna / High | Luna / High | Luna / High |
| Exact, low-risk read-only fact check against bounded sources | Try Luna / High | Try Luna / High | Sol / High |
| Exact, low-risk, testable local implementation/fix | Try Luna / High | Sol / Medium | Sol / High |
| Other routine work | Sol / Medium | Sol / Medium | Sol / High |
| Cross-component, open, difficult debugging/judgment | Sol / High | Sol / High | Astra / High |
| High-consequence decisions or open/uncertain system design | Astra / High | Astra / High | Astra / XHigh |
| Evidenced adjacent-lane ambiguity | No lightweight trial; highest established lane | Highest established lane | Promote one lane, capped at critical |

## GPT-6 guidance refresh · 1.4

The existing Sol/Medium and Luna/High settings already match the [official subagent starting points](https://learn.chatgpt.com/docs/agent-configuration/subagents). Its read-only explorer and documentation examples support a narrow expansion beyond extraction. Sol remains the implementation and investigation workhorse; this update changes eligible task boundaries, not model IDs or an assumed release date.

Economy and Balanced now allow a **focused source-check trial** only when the assessed lane is routine, work type read, write paths empty, kind research, specification exact, verification sources, scope local, input text, boundary clear, consequence low, uncertainty low, and no recovery is in progress. `source_evidence` must describe bounded sources (including relevant versions) and how each factual claim will be checked against cited locations. A source list alone is insufficient. This is for locating documented facts or a prescribed code symbol, not proving correctness, diagnosing an unknown cause, interpreting conflicting evidence or open-ended research. These stricter cutoffs are our engineering judgment.

The trial reuses the configured mechanical candidate pool while preserving the routine classification. A diagnosed reasoning/verification failure recovers to complex; network/auth failures do not trigger a stronger model. Premium retains Sol/High. Existing requests without `verification: sources` keep their routes, and legacy classification never enables this trial. Explicit user choices still win. The helper checks field structure, not factual truth: the coordinator must inspect the returned references before acceptance.

Reviewed official [Sol](https://developers.openai.com/api/docs/models/gpt-6-sol) and [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) pages on 2026-09-23 (America/New_York). API feature lists are not runtime availability; use this host's observed spawn catalog. API prices do not establish subscription savings. No new model-output A/B evaluation was run for 1.4; tests cover admission, recovery and compatibility. The earlier third-party reports below were not revalidated in this refresh.

## Admission and recovery

Economy permits a bounded trial only when the base lane is routine, no reasoning recovery is in progress, kind is implement/debug, specification exact, verification tests, scope local, input text, boundary clear, consequence low and uncertainty low. All conditions are necessary. It reuses `lanes.mechanical` candidates (factory: Luna/High → Sol/Medium → Astra/Low) while retaining the routine lane and recording `candidate_pool: mechanical`. It does not relabel implementation as deterministic work. A diagnosed reasoning/verification failure disables the trial and raises routine to complex (Sol/High), within the one-recovery limit. Reassess changed scope; a plausible answer without acceptance is not success.

Premium ambiguity requires `assessment.boundary: adjacent` and a nonempty `boundary_evidence` describing the concrete unresolved boundary. All presets first apply hard consequence/scope/uncertainty rules; no preset lowers an established floor. Material unresolved uncertainty must be rated high, not hidden as mere ambiguity. Premium then promotes one lane, capped at critical. More effort is a quality preference, not a universal performance guarantee.

All presets allow one active child, two total starts per user request, one diagnosed recovery, and a five-minute reasoning-work threshold. The threshold is an overhead heuristic, not an official capability cutoff. Premium does not increase agent count. Economy cannot certify lowest total usage in advance.

`routing_strategy` stores behavior; `presets.json` contains complete templates, `default-policy.json` the Balanced reset template, and `policy.json` current settings. The console matches whole policies to names; edits display Custom. Candidate fallback handles availability, not execution retries. Terra is available for explicit/custom selection; evidence does not establish it as the best automatic GPT-6-era route. No automatic Max/Ultra.

## Evidence reviewed (2026-09-23 UTC)

1. **Official guidance:** [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) supplies starting points including Sol/Medium and Luna/High. [Model selection](https://learn.chatgpt.com/docs/model-selection) recommends comparing the same inputs and retaining a lighter configuration that satisfies quality.
2. **First-hand user test, small sample:** [merefield's original report](https://community.openai.com/t/announcing-gpt-6-sol-and-gpt-6-luna-in-the-api-codex-and-chatgpt/1399925/6) reports both Luna/High and Sol/High passing three coding tasks. It motivates narrow testable trials, not wholesale substitution in complex repositories. We did not reproduce it; the report is not statistically conclusive. Its API-equivalent estimates are not subscription quota measurements.
3. **Independent evaluation, different domain:** [Roboflow Vision Evals](https://playground.roboflow.com/models/openai/gpt-6-luna) compares low/high effort with three runs per task; additional reasoning does not improve every visual task. This motivates per-task verification and excludes visual/OCR extraction from the text-only deterministic lane; it does not establish coding performance.
4. **Benchmark limitations:** [ARC Prize Luna results](https://arcprize.org/results/openai-gpt-6-luna) separate effort and harness configurations. These results are not repository acceptance tests or universal capability cutoffs.
5. **Model positioning:** official pages for [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sol](https://developers.openai.com/api/docs/models/gpt-6-sol) and [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) inform narrow-task, coding-workhorse and hardest-work routes. The Premium promotion rule and exact High/XHigh choices are engineering judgments, not official guarantees.

The complete presets have not all been empirically validated by users. Public evidence informs their design; automated tests verify routing/configuration behavior. This release ran no paid cross-model A/B tests and measured no subscription savings. Establishing lowest successful total cost requires equivalent tasks, tools and acceptance, including coordinator, children, retries and review—not merely child-call prices. Future revisions should retain model/effort, task set, prompt, tools, success, latency, observed usage and failure categories. A single successful trial must not automatically rewrite policy.
