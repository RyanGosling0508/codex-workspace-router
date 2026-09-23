# Request and lifecycle protocol

The coordinator classifies the task. This helper deterministically checks that classification against policy and supplied observations. It does not classify natural language, call models, dispatch tools, prove permissions, or establish OS isolation. Keep the current coordinator by default, including for large tasks. In version 1.1, missing delegation evidence returns direct before collecting scope/catalog facts; old request producers cannot silently retain broad automatic fan-out.

## Gather the inputs

Use JSON schema version 1. All paths are absolute paths on the execution host. Run the helper there. Resolve existing links; reject parent traversal. New links and concurrent external edits can invalidate a prior check, so recheck immediately before dispatch. The actual sandbox and project instructions remain authoritative.

- `host`: `id`, `os` (`windows`/`posix`), `cwd`, `verified` boolean. Use a stable runtime host identity, not a display label guessed from a project name.
- `runtime`: matching `host_id`, boolean `delegation_available`, nonnegative integer `slots_available`, `active_children`, `children_started`. `active_children` counts this coordinator's in-flight children; `children_started` counts all child starts in the current user request, including completed, failed, interrupted and replacement children. Do not reset on re-planning. `active` is a separate conflict list and can include coordinator operations. Account for runtime limits. Missing total count closes delegation.
- `delegation`: optional `{reason,evidence,user_requested?,user_prioritized_speed?}`. Missing or `reason:"none"` means direct. Other reasons: `explicit_user` requires `user_requested:true` grounded in a real request for a child; `verification_gap` requires a concrete correctness question, independent read-only work and adequate acceptance; `deadline_parallel` requires `user_prioritized_speed:true` from the user's stated preference and task `benefit:"parallel"`. Evidence is a nonempty description of that actual request/gap, not generic praise of parallelism. The script verifies the structure; the coordinator must verify its truth. Never invent consent or a gap to pass this gate. A pinned main model is not an explicit request for a child.
- `scope`: `confirmed`, `read_roots`, `write_roots`, `protected_paths`. Derive from the user's task and applicable instructions; a remembered sidebar root alone is insufficient. Empty write roots are normal for review.
- `task`: booleans `trivial`, `tool_bound`, `independent`, `context_complete`; `work_type` (`read`, `edit`, `shared_resource`, `external_action`); `complexity` (`mechanical`, `routine`, `complex`, `critical`); `consequence` and `uncertainty` (`low`, `normal`, `high`); `benefit` (`quality`, `parallel`, `cost`, `none`); estimated `reasoning_minutes`; string arrays `read_paths`, `write_paths`, `resources`, `acceptance`, `constraints`.
- `active`: every relevant in-flight child and coordinator operation, each with `host_id`, `read_paths`, `write_paths`, `resources`. Include known conflicts from other tasks; this file is not a global lock service. Unknown ownership of a shared resource means do not parallelize it.
- `catalog`: matching `host_id`, `source` (`runtime-tool` or `app-server-model-list`), timezone-aware `captured_at`, `models` array of `{model, efforts}`. Normalize the current tool's supported model overrides or the actual `model/list` response. Do not send the schema example below as a capability probe. No catalog is bundled because availability changes.
- `failure`: `kind` (`none`, `reasoning`, `verification`, `environment`, `permission`, `network`, `auth`, `model_unavailable`), `recovery_attempts` already consumed by this bounded task. A failed test is not automatically a reasoning failure: diagnose it first.
- `depth`: 0 for coordinator, greater than 0 for a child. Optional `enabled:false` or `disable_delegation:true` stops delegation immediately.
- Optional `current`: `{source:"runtime",model,effort}` only from runtime observation; omit if unknown. Optional `explicit`: `{model,effort}` for a user-pinned **child** route. A request to change the main model must be explained as outside this Skill's capability.

Complexity: mechanical means a deterministic, narrow transformation with low uncertainty and low consequences; routine means a bounded implementation with known interfaces; complex means cross-file reasoning, ambiguous design, or nontrivial debugging; critical means consequential correctness decisions or high cost of a mistake. High consequence forces critical, high uncertainty forces at least complex. The minute threshold is an initial heuristic, not measured savings. Do not inflate it to obtain a child.

## Minimal complete example

Illustration only: replace all host/path/catalog facts with observed values. This example describes a read-only review; commands that create caches require write declarations.

```json
{
  "schema_version": 1,
  "depth": 0,
  "host": {"id":"local-session", "os":"windows", "cwd":"C:/work/example-project", "verified":true},
  "runtime": {"host_id":"local-session", "delegation_available":true, "slots_available":2, "active_children":0, "children_started":0},
  "delegation": {"reason":"verification_gap", "evidence":"Verify whether the coordinate axis swap preserves polygon winding; existing tests do not cover mirrored coordinates"},
  "scope": {"confirmed":true, "read_roots":["C:/work/example-project"], "write_roots":[], "protected_paths":[]},
  "task": {
    "trivial":false, "tool_bound":false, "independent":true, "context_complete":true,
    "work_type":"read", "complexity":"complex", "consequence":"normal", "uncertainty":"normal",
    "benefit":"quality", "reasoning_minutes":8,
    "read_paths":["C:/work/example-project/src"], "write_paths":[], "resources":[],
    "acceptance":["Report reproducible coordinate-transform defects with source locations"],
    "constraints":["Read only; do not run commands that create caches"]
  },
  "active":[],
  "failure":{"kind":"none", "recovery_attempts":0},
  "catalog": {
    "host_id":"local-session", "source":"runtime-tool", "captured_at":"2000-01-01T00:00:00Z",
    "models":[{"model":"gpt-6-sol", "efforts":["medium","high"]}]
  }
}
```

Run with a verified interpreter; put the request under the current task's scratch folder:

```powershell
python -X utf8 -B '<installed-skill>/scripts/router.py' decide --input '<task-scratch>/route.json'
```

Use the absolute installed skill path. POSIX uses its observed `python3` executable and POSIX paths. No API key is involved.

## Interpret and dispatch

`delegate` is advice to dispatch within existing authorization. `direct` means keep the coordinator; fix any invalid scope before performing the work. `serialize` means wait for the conflicting owner or choose an independent task. `report_unsupported` means a pinned route could not be honored. `actual:null` is intentional: the helper never executes a model.

For the collaboration API, use only actual supported fields, e.g. `task_name`, a self-contained `message`, `model`, `reasoning_effort`, `fork_turns:"none"`. The helper's `host_id`, `cwd` and path lists belong in the message, not invented API parameters. A prompt scope is not a sandbox. Children must inherit runtime restrictions and obey their narrower task scope. Include the real goal and needed source facts, not just the JSON routing metadata. Review all required results before answering the user.

Track the child ID, route requested, actual route if exposed, own task scope, status, acceptance and cumulative child-start count in this request's working context. No cross-request child reuse. Runtime metadata can confirm a model; child prose cannot. This version has no background daemon, automatic event subscription, or persistent scheduler. Defaults are one active child and two total starts. A child returning idle/completed does not refill the total budget. `cost_savings_verified:false` is intentional: none of these routing observations establishes savings.

## Completion and recovery

`reconcile --input lifecycle.json` takes `{state,acceptance,progress_overdue?}`. States: `running`, `idle`, `completed`, `failed`, `interrupted`; acceptance: `pending`, `passed`, `failed`. Completed/pending produces `validate`, completed/passed produces `accept`; failed/interrupted cannot be accepted. Overdue progress calls for inspection, never automatic interruption. Runtime wait tools provide progress; the helper itself does not wait.

At most one classified reasoning/verification recovery per bounded task; carry the counter across attempts. It may move up one policy lane. Infrastructure failures stay infrastructure failures. Repeated or ambiguous failure returns to coordinator diagnosis with evidence. Never silently retry a user-pinned unavailable model as another model.
