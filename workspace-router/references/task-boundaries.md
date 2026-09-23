# Task boundaries · recommended defaults 1.3

[Three presets and empirical evidence](presets.md)

**English** | [简体中文](task-boundaries.zh-CN.md)

This is a child-agent policy, not a main-model switch or per-message interception hook. Main-agent execution remains the default. Read this rubric only when a real delegation need exists. The task type alone never justifies a child.

## Recommended policy

| Lane | Default | Admission criteria after the delegation gate | Examples |
|---|---|---|---|
| Deterministic | GPT-6 Luna / high | ALL: text-only input; extraction or transformation; exact specification; deterministic verification; local scope; low consequence; low uncertainty | Extract records against a fixed schema, apply a prescribed document mapping |
| Routine | GPT-6 Sol / medium | No higher condition applies; bounded work with known interfaces and acceptance | Local feature implementation, reproducible localized fix, ordinary source-based research |
| Complex | GPT-6 Sol / high | ANY: cross-component/system scope; open specification; high uncertainty; debugging/review/design requiring judgment; declared complex floor | Cross-module state bug, concurrency diagnosis, mathematical or coordinate review |
| Critical / system design | GPT-6 Astra / high | ANY: high consequence; system scope AND (open specification OR high uncertainty); declared critical floor | High-impact production migration review, system architecture with unresolved constraints |

Apply the **highest** matching lane. The existing `complexity` value is a floor: an exact-looking substep cannot reduce a task already known to be critical. One diagnosed reasoning/verification recovery may raise one lane; infrastructure failures do not. New defaults allow one active child, two total starts per user request, one recovery, and at least five estimated minutes of reasoning work. Five minutes is an overhead heuristic, not a measurement of savings; do not count waiting or inflate estimates.

## Evidence to supply

Under `classification_mode: "evidence-v1"`, `task.assessment` is required after the delegation gate:

```json
{
  "kind": "implement",
  "specification": "bounded",
  "verification": "tests",
  "scope": "local",
  "input_form": "text",
  "boundary": "clear",
  "evidence": "Existing parser interface is fixed; a supplied fixture reproduces the defect and verifies the repair."
}
```

- `kind`: `extract`, `transform`, `implement`, `debug`, `review`, `research`, `design`. Select the work actually delegated, not the overall project title.
- `specification`: `exact` means rules and edge cases are prescribed; `bounded` means requirements are clear with implementation choices remaining; `open` means consequential requirements or design choices remain unresolved.
- `verification`: `deterministic` means exact comparison/schema/rules can establish acceptance; `tests` means meaningful tests or explicit behavioral checks; `judgment` means acceptance needs reasoning, interpretation or visual judgment. Having some tests does not make a correctness review deterministic.
- `scope`: `local` means one bounded component or artifact set with stable interfaces; `cross_component` means reasoning across interacting components; `system` means system-wide constraints, architecture or contracts. File count is not the criterion: many files under one exact mapping may still be local.
- `input_form`: `text` requires no visual perception (source code counts as text); `visual` requires image/OCR/visual interpretation.
- `boundary`: `clear` or `adjacent`. Adjacent-lane ambiguity requires concrete, nonempty `boundary_evidence`. Significant unresolved uncertainty must still be rated high. The defaults table describes Balanced; see presets for exceptions.
- `evidence`: explain the actual specification, verification method, scope and consequential uncertainties. The existing `task.consequence` and `task.uncertainty` fields still supply those ratings.

High consequence means a mistake could materially affect safety, money, irreversible data loss or access controls. Mentioning a production system, security, medicine or money does not by itself establish high impact: classify the actual delegated decision and its possible consequences. Unknown risk needs investigation, not an invented low rating. High uncertainty includes competing untested hypotheses or unclear constraints. A known reproduction with a narrow proven cause may be routine debugging; debugging based on incomplete evidence is not.

Missing assessment returns `direct` with `task-assessment-missing`; malformed evidence returns the normal invalid-input direct result. Neither grants permission to perform unsafe or out-of-scope work. The helper verifies structure and deterministic rules, not the truth of supplied evidence, and does not classify raw natural language.

## Fallbacks and exclusions

- Deterministic: Luna/high → Sol/medium → Astra/low.
- Routine: Sol/medium → Astra/medium.
- Complex: Sol/high → Sol/xhigh → Astra/high.
- Critical: Astra/high → Astra/xhigh. No other-model downgrade.

These are predefined alternatives inside each lane, not benchmark equivalence claims. A candidate is usable only if the **current host** reports that exact model and effort. An unavailable critical route stays with the coordinator, with the limitation disclosed; staying with the coordinator is not certification that its model meets the desired quality bar. Resolve that limitation before claiming critical acceptance.

Terra and older Sol remain available for an explicit supported user selection or intentional custom policy. They have no automatic role in this GPT-6-focused default. Explicit user choices are preserved and marked by the request's `explicit` field; Max requires an explicit supported request, Ultra a separate native workflow. Model choice does not add browser, computer-use, image-generation or remote-host tools. Shared browser/desktop actions and external side effects remain with the coordinator under the existing gate.

## Evidence and limitations

Reviewed official documentation on **2026-09-23**:

- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna): positioned for focused, high-volume work.
- [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol): positioned for complex coding and agentic workflows.
- [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra): positioned for the hardest end-to-end reasoning and deliverables.
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): suggests Sol as the usual starting model and Luna for narrow lighter tasks; explicit effort starting points include Sol/medium and Luna/high. We choose higher Astra effort for this policy's consequential lane.
- [Model selection](https://learn.chatgpt.com/docs/model-selection): recommends trying the same inputs and retaining the lightest configuration that satisfies quality requirements.
- [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra): a previous-family intelligence/cost balance option; that positioning alone does not establish a better default than Sol for our tasks.

The four boundaries, five-minute threshold and fallback order are **our engineering choices**, informed by these sources. They are not official performance guarantees or measured subscription savings. No paid cross-model benchmark was run to create this release. Automated tests verify routing behavior, not the quality of model outputs. Versioned defaults are stored in `default-policy.json`; current editable policy is `policy.json`. Restore recommended defaults in the console to load the full recommended policy as a draft, then review and apply.
