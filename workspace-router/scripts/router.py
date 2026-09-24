#!/usr/bin/env python3
"""Deterministic delegation advice. No network, model calls, or task execution.

Inputs are observations supplied by the coordinator, not a security attestation.
Codex permissions remain authoritative. Python 3.10+, standard library only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
import uuid

VERSION = "1.4.0"
EFFORTS = ["low", "medium", "high", "xhigh", "max", "ultra"]
LANES = ["mechanical", "routine", "complex", "critical"]
NON_REASONING_FAILURES = {"environment", "permission", "network", "auth", "model_unavailable"}
DEFAULT_POLICY = Path(__file__).resolve().parents[1] / "references" / "policy.json"
RECOMMENDED_POLICY = DEFAULT_POLICY.with_name("default-policy.json")
PRESETS = DEFAULT_POLICY.with_name("presets.json")


def read_json(path):
    with open(path, encoding="utf-8-sig") as stream:
        return json.load(stream)


def strings(value):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError("expected a list of nonempty strings")
    return value


def number(value, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError("invalid nonnegative finite number")
    return value


def flag(value):
    if not isinstance(value, bool):
        raise ValueError("boolean required")
    return value


def count(value):
    n = number(value)
    if int(n) != n:
        raise ValueError("integer count required")
    return int(n)


def enum(value, choices):
    if value not in choices:
        raise ValueError("unsupported enum value")
    return value


def canonical(value, system):
    """Resolve existing links on the execution host; compare other OS paths lexically."""
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("invalid path")
    cls = PureWindowsPath if system == "windows" else PurePosixPath
    p = cls(value)
    if not p.is_absolute() or ".." in p.parts:
        raise ValueError("paths must be absolute without parent traversal")
    if system == "windows":
        # Reject device namespaces and alternate data streams.
        if value.startswith(("\\\\?\\", "\\\\.\\")) or any(":" in part for part in p.parts[1:]):
            raise ValueError("unsupported Windows namespace")
    if (system == "windows") == (os.name == "nt"):
        p = cls(str(Path(value).resolve()))
    return str(p).casefold() if system == "windows" else str(p)


def within(path, root, system):
    cls = PureWindowsPath if system == "windows" else PurePosixPath
    try:
        cls(path).relative_to(cls(root))
        return True
    except ValueError:
        return False


def overlaps(a, b, system):
    return within(a, b, system) or within(b, a, system)


def clean_paths(values, system):
    return [canonical(x, system) for x in strings(values)]


def validate_policy(policy):
    if policy["schema_version"] != 1 or not isinstance(policy["version"], str):
        raise ValueError("unsupported policy")
    flag(policy["enabled"])
    enum(policy["preference"], {"quality-first"})
    enum(policy["delegation_mode"], {"evidence-only"})
    enum(policy.get("classification_mode", "legacy"), {"legacy", "evidence-v1"})
    enum(policy.get("routing_strategy", "balanced"), {"economy", "balanced", "premium"})
    if not 1 <= count(policy["max_children_per_request"]) <= 3:
        raise ValueError("total child budget must be between one and three")
    for key in ("max_children", "max_recovery_attempts"):
        n = number(policy[key])
        if int(n) != n or n > (3 if key == "max_children" else 1):
            raise ValueError("policy exceeds bounded delegation limits")
    number(policy["minimum_reasoning_minutes"])
    number(policy["catalog_max_age_hours"], 0.01)
    triggers = policy.get("triggers", {})
    if not isinstance(triggers, dict) or set(triggers) - {"explicit_user", "verification_gap", "deadline_parallel"}:
        raise ValueError("invalid trigger switches")
    for enabled in triggers.values():
        flag(enabled)
    for lane in LANES:
        candidates = policy["lanes"][lane]
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("lane needs candidates")
        for pair in candidates:
            if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str) or not pair[0]:
                raise ValueError("invalid route")
            enum(pair[1], EFFORTS[:4])
    return policy


def classify_task(task, mode="evidence-v1"):
    """Deterministic rubric over supplied evidence, not an NLP classifier.

    Existing complexity is a lower bound. Stronger signals can only raise it.
    Risk and uncertainty are observations that the coordinator must substantiate.
    """
    declared = enum(task["complexity"], LANES)
    consequence = enum(task["consequence"], {"low", "normal", "high"})
    uncertainty = enum(task["uncertainty"], {"low", "normal", "high"})
    enum(mode, {"legacy", "evidence-v1"})
    reasons = []
    rank = LANES.index(declared)
    if mode == "evidence-v1":
        a = task["assessment"]
        if not isinstance(a, dict) or not isinstance(a.get("evidence"), str) or not a["evidence"].strip():
            raise ValueError("task assessment needs concrete evidence")
        kind = enum(a["kind"], {"extract", "transform", "implement", "debug", "review", "research", "design"})
        specification = enum(a["specification"], {"exact", "bounded", "open"})
        verification = enum(a["verification"], {"deterministic", "tests", "sources", "judgment"})
        if verification == "sources" and (not isinstance(a.get("source_evidence"), str) or not a["source_evidence"].strip()):
            raise ValueError("source verification needs bounded sources and a check method")
        scope = enum(a["scope"], {"local", "cross_component", "system"})
        input_form = enum(a["input_form"], {"text", "visual"})
        boundary = enum(a["boundary"], {"clear", "adjacent"})
        if boundary == "adjacent" and (not isinstance(a.get("boundary_evidence"), str) or not a["boundary_evidence"].strip()):
            raise ValueError("ambiguous boundary needs concrete evidence")
        # All six conditions are required; a label like 'simple' cannot admit Luna.
        mechanical = (kind in {"extract", "transform"} and specification == "exact"
                      and verification == "deterministic" and scope == "local"
                      and consequence == "low" and uncertainty == "low" and input_form == "text")
        if mechanical:
            reasons.append("deterministic-local-low-risk")
        else:
            rank = max(rank, 1)
            reasons.append("requires-general-judgment")
        if scope in {"cross_component", "system"}:
            rank = max(rank, 2)
            reasons.append("cross-component-reasoning")
        if specification == "open":
            rank = max(rank, 2)
            reasons.append("open-specification")
        if kind in {"debug", "review", "design"} and verification == "judgment":
            rank = max(rank, 2)
            reasons.append("judgment-heavy-investigation")
        if scope == "system" and (specification == "open" or uncertainty == "high"):
            rank = 3
            reasons.append("open-or-uncertain-system-work")
    if consequence == "high":
        rank = 3
        reasons.append("high-consequence")
    if uncertainty == "high":
        rank = max(rank, 2)
        reasons.append("high-uncertainty")
    if rank == 0 and (consequence != "low" or uncertainty != "low"):
        rank = 1
        reasons.append("mechanical-risk-condition-not-met")
    if LANES.index(declared) >= rank:
        reasons.append("declared-complexity-floor")
    return {"mode": mode, "lane": LANES[rank], "reasons": reasons}


def catalog_models(catalog, host_id, now, policy):
    if catalog["host_id"] != host_id:
        raise ValueError("catalog belongs to another host")
    enum(catalog["source"], {"runtime-tool", "app-server-model-list"})
    captured = datetime.fromisoformat(catalog["captured_at"].replace("Z", "+00:00"))
    if captured.tzinfo is None:
        raise ValueError("catalog timestamp needs timezone")
    age = (now - captured).total_seconds()
    if age < -60 or age > policy["catalog_max_age_hours"] * 3600:
        raise ValueError("catalog expired or clock invalid")
    result = {}
    for row in catalog["models"]:
        model = row["model"]
        if not isinstance(model, str) or not model or model in result:
            raise ValueError("invalid or duplicate model")
        efforts = strings(row["efforts"])
        if not efforts or any(e not in EFFORTS for e in efforts):
            raise ValueError("invalid efforts")
        result[model] = efforts
    return result


def _decide(request, policy, now):
    validate_policy(policy)
    if request["schema_version"] != 1:
        raise ValueError("unsupported request")
    policy_hash = hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()[:16]
    out = {"schema_version": 1, "router_version": VERSION, "policy_version": policy["version"],
           "policy_hash": policy_hash, "action": "direct", "recommended": None,
           "actual": None, "spawn": None, "authorizes_execution": False}

    def finish(reason, action="direct"):
        out.update(reason=reason, action=action)
        return out

    # Stop switches never need a model catalog, scope, or successful classifier.
    if not policy["enabled"] or request.get("enabled") is False:
        return finish("router-disabled")
    if request.get("disable_delegation") is True:
        return finish("delegation-disabled")
    if "disable_delegation" in request:
        flag(request["disable_delegation"])
    if "enabled" in request:
        flag(request["enabled"])
    depth = count(request["depth"])
    if depth != 0:
        return finish("leaf-does-not-delegate")
    task = request["task"]
    if flag(task["trivial"]) or flag(task["tool_bound"]):
        return finish("direct-work-has-lower-overhead")
    work_type = enum(task["work_type"], {"read", "edit", "shared_resource", "external_action"})
    if work_type in {"shared_resource", "external_action"}:
        return finish("coordinator-controls-shared-or-external-action")
    # No classifier call or live catalog is needed to decline speculative delegation.
    delegation = request.get("delegation", {})
    basis = enum(delegation.get("reason", "none"),
                 {"none", "explicit_user", "verification_gap", "deadline_parallel"})
    if basis == "none":
        return finish("direct-by-default-no-delegation-need")
    if not policy.get("triggers", {}).get(basis, True):
        return finish("delegation-trigger-disabled")
    evidence = delegation.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        return finish("delegation-evidence-missing")
    if basis == "explicit_user" and not flag(delegation.get("user_requested", False)):
        return finish("explicit-delegation-not-requested")
    if basis == "verification_gap" and work_type != "read":
        return finish("independent-verification-is-read-only")
    if basis == "deadline_parallel":
        if not flag(delegation.get("user_prioritized_speed", False)) or task.get("benefit") != "parallel":
            return finish("parallel-speed-not-requested")
    if task.get("benefit") == "cost" and basis != "explicit_user":
        return finish("speculative-savings-do-not-justify-delegation")
    out["delegation_basis"] = basis
    out["cost_savings_verified"] = False
    if not flag(task["independent"]) or not flag(task["context_complete"]):
        return finish("task-not-ready-for-independent-delegation")
    if not strings(task["acceptance"]):
        return finish("acceptance-not-defined")
    strings(task["constraints"])
    scope = request["scope"]
    if not flag(scope["confirmed"]):
        return finish("scope-unconfirmed")
    host = request["host"]
    system = enum(host["os"], {"windows", "posix"})
    if not flag(host["verified"]) or host["id"] != request["runtime"]["host_id"]:
        return finish("host-not-verified")
    if (system == "windows") != (os.name == "nt"):
        return finish("run-preflight-on-the-execution-host")
    cwd = canonical(host["cwd"], system)
    if not Path(host["cwd"]).is_dir():
        return finish("working-directory-not-found")
    read_roots = clean_paths(scope["read_roots"], system)
    write_roots = clean_paths(scope["write_roots"], system)
    protected = clean_paths(scope["protected_paths"], system)
    reads = clean_paths(task["read_paths"], system)
    writes = clean_paths(task["write_paths"], system)
    if not any(within(cwd, p, system) for p in read_roots + write_roots):
        return finish("working-directory-outside-task-scope")
    if not reads and not writes:
        return finish("file-task-has-no-explicit-paths")
    if work_type == "read" and writes:
        return finish("read-task-declares-writes")
    if work_type == "edit" and not writes:
        return finish("edit-task-has-no-write-paths")
    if any(not any(within(p, r, system) for r in read_roots + write_roots) for p in reads):
        return finish("read-outside-task-scope")
    if any(not any(within(p, r, system) for r in write_roots) for p in writes):
        return finish("write-outside-task-scope")
    if any(overlaps(p, r, system) for p in writes for r in protected):
        return finish("write-overlaps-protected-source")
    resources = strings(task["resources"])
    active = request["active"]
    if not isinstance(active, list):
        raise ValueError("active must be a list")
    # Shared external resource names conflict even across hosts.
    for other in active:
        if set(resources) & set(strings(other["resources"])):
            return finish("shared-resource-busy", "serialize")
        if other["host_id"] == host["id"]:
            other_reads = clean_paths(other["read_paths"], system)
            other_writes = clean_paths(other["write_paths"], system)
            if (any(overlaps(w, p, system) for w in writes for p in other_reads + other_writes)
                    or any(overlaps(r, w, system) for r in reads for w in other_writes)):
                return finish("file-access-conflict", "serialize")
    runtime = request["runtime"]
    if not flag(runtime["delegation_available"]):
        return finish("delegation-tool-unavailable")
    active_children = count(runtime["active_children"])
    children_started = count(runtime["children_started"])
    if children_started < active_children:
        raise ValueError("started child count is less than active child count")
    if children_started >= policy["max_children_per_request"]:
        return finish("total-child-budget-exhausted")
    if count(runtime["slots_available"]) < 1 or active_children >= policy["max_children"]:
        return finish("concurrency-cap", "serialize")
    failure = request["failure"]
    failure_kind = enum(failure["kind"], {"none", "reasoning", "verification"} | NON_REASONING_FAILURES)
    attempts = count(failure["recovery_attempts"])
    if attempts > policy["max_recovery_attempts"]:
        return finish("recovery-budget-exhausted")
    if failure_kind in NON_REASONING_FAILURES:
        return finish("fix-environment-or-capability-without-reasoning-escalation")
    if failure_kind != "none" and attempts >= policy["max_recovery_attempts"]:
        return finish("recovery-budget-exhausted")
    classification_mode = policy.get("classification_mode", "legacy")
    if classification_mode == "evidence-v1" and "assessment" not in task:
        return finish("task-assessment-missing")
    classification = classify_task(task, classification_mode)
    lane = classification["lane"]
    strategy = policy.get("routing_strategy", "balanced")
    assessment = task.get("assessment", {})
    if classification_mode == "evidence-v1" and strategy == "premium" and assessment["boundary"] == "adjacent":
        lane = LANES[min(3, LANES.index(lane) + 1)]
        classification["reasons"].append("premium-ambiguous-boundary-upgrade")
    # Only classified reasoning/verification failures may raise one lane.
    if failure_kind in {"reasoning", "verification"}:
        lane = LANES[min(3, LANES.index(lane) + 1)]
        classification["reasons"].append("diagnosed-reasoning-recovery")
    classification["lane"] = lane
    out["classification"] = classification
    out["lane"] = lane
    explicit = request.get("explicit", {})
    models = catalog_models(request["catalog"], host["id"], now, policy)
    current = request.get("current", {})
    if current.get("source") == "runtime" and isinstance(current.get("model"), str) and current.get("effort") in EFFORTS:
        out["current_observed"] = {"model": current["model"], "effort": current["effort"]}
    choices = policy["lanes"][lane]
    # Economic pilot preserves the assessed lane and its recovery floor. Only
    # the candidate pool changes; output never claims the model is proven adequate.
    if (classification_mode == "evidence-v1" and strategy == "economy" and lane == "routine"
            and failure_kind == "none" and task["consequence"] == "low" and task["uncertainty"] == "low"
            and assessment["kind"] in {"implement", "debug"} and assessment["specification"] == "exact"
            and assessment["verification"] == "tests" and assessment["scope"] == "local"
            and assessment["input_form"] == "text" and assessment["boundary"] == "clear"):
        choices = policy["lanes"]["mechanical"]
        classification["reasons"].append("economy-testable-local-trial")
        out["candidate_pool"] = "mechanical"
    # Focused factual research is still routine work, not deterministic extraction.
    # Explicit source checks opt into this trial; existing request formats retain
    # their routes. Failed acceptance recovers from the routine floor above.
    if (classification_mode == "evidence-v1" and strategy in {"economy", "balanced"}
            and lane == "routine" and failure_kind == "none"
            and work_type == "read" and not writes
            and task["consequence"] == "low" and task["uncertainty"] == "low"
            and assessment["kind"] == "research" and assessment["specification"] == "exact"
            and assessment["verification"] == "sources" and assessment["scope"] == "local"
            and assessment["input_form"] == "text" and assessment["boundary"] == "clear"):
        choices = policy["lanes"]["mechanical"]
        classification["reasons"].append("focused-source-check-trial")
        out["candidate_pool"] = "mechanical"
    requested_model, requested_effort = explicit.get("model"), explicit.get("effort")
    if requested_model is not None or requested_effort is not None:
        if requested_effort is not None:
            enum(requested_effort, EFFORTS)
        if requested_effort == "ultra":
            return finish("ultra-requires-separate-native-workflow", "report_unsupported")
        if requested_model is not None:
            if not isinstance(requested_model, str) or requested_model not in models:
                return finish("explicit-model-unavailable", "report_unsupported")
            # An explicit model is not replaced. Choose a supported effort when unspecified.
            if requested_effort is None:
                defaults = [e for m, e in choices if m == requested_model]
                requested_effort = defaults[0] if defaults else ("high" if lane in {"complex", "critical"} else "medium")
            choices = [[requested_model, requested_effort]]
        else:
            choices = [[m, requested_effort] for m, _ in choices]
    chosen = next(({"model": m, "effort": e} for m, e in choices if e in models.get(m, [])), None)
    if chosen is None:
        return finish("explicit-effort-unavailable" if explicit else "no-supported-quality-lane",
                      "report_unsupported" if explicit else "direct")
    out["recommended"] = chosen
    # A passed evidence gate can justify a separate perspective even on the same
    # model; model equality must not cancel an explicit independent-child request.
    enum(task["benefit"], {"quality", "parallel", "cost", "none"})
    minutes = task.get("reasoning_minutes")
    if minutes is None or number(minutes) < policy["minimum_reasoning_minutes"]:
        return finish("delegation-benefit-not-established")
    if task["benefit"] == "none":
        return finish("delegation-benefit-not-established")
    if task["benefit"] == "cost" and lane in {"complex", "critical"}:
        return finish("quality-takes-priority-over-speculative-savings")
    out["spawn"] = {"model": chosen["model"], "reasoning_effort": chosen["effort"],
                    "fork_turns": "none", "host_id": host["id"], "cwd": cwd,
                    "read_paths": reads, "write_paths": writes, "protected_paths": protected,
                    "resources": resources, "acceptance": task["acceptance"],
                    "constraints": task["constraints"], "allow_nested_delegation": False,
                    "delegation_basis": basis,
                    "max_children_per_request": policy["max_children_per_request"],
                    "max_recovery_attempts": policy["max_recovery_attempts"]}
    return finish("bounded-independent-work-with-supported-route", "delegate")


def decide(request, policy=None, now=None):
    """Routing errors close delegation, not the user's authorized ordinary workflow."""
    try:
        return _decide(request, read_json(DEFAULT_POLICY) if policy is None else policy,
                       datetime.now(timezone.utc) if now is None else now)
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, IndexError) as exc:
        return {"schema_version": 1, "router_version": VERSION, "action": "direct",
                "reason": "routing-input-or-capability-unverified", "error_type": type(exc).__name__,
                "recommended": None, "actual": None, "spawn": None, "authorizes_execution": False}


def reconcile(event):
    """Suggest lifecycle action; never poll, interrupt, or mark acceptance itself."""
    state = enum(event["state"], {"running", "idle", "completed", "failed", "interrupted"})
    acceptance = enum(event["acceptance"], {"pending", "passed", "failed"})
    if state == "completed":
        return {"action": "accept" if acceptance == "passed" else "validate" if acceptance == "pending" else "inspect-failure",
                "terminal": True, "interrupt": False}
    if state in {"failed", "interrupted"}:
        return {"action": "inspect-failure", "terminal": True, "interrupt": False}
    return {"action": "inspect-progress" if event.get("progress_overdue") is True else "wait-for-event",
            "terminal": False, "interrupt": False}


def audit_record(event):
    """Explicit opt-in, metadata-only event. No prompt, paths, or model rationales."""
    state = enum(event["state"], {"completed", "failed", "interrupted"})
    acceptance = enum(event["acceptance"], {"pending", "passed", "failed"})
    observed = event.get("observed", {})
    model, effort = None, None
    if observed.get("source") == "runtime":
        if re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}", str(observed.get("model", ""))):
            model = observed["model"]
        if observed.get("effort") in EFFORTS:
            effort = observed["effort"]
    metrics = {}
    for key in ("elapsed_seconds", "input_tokens", "output_tokens"):
        value = event.get(key)
        metrics[key] = None if value is None else number(value)
    return {"schema_version": 1, "router_version": VERSION,
            "event_id": uuid.uuid4().hex, "recorded_at": datetime.now(timezone.utc).isoformat(),
            "state": state, "acceptance": acceptance, "observed_model": model,
            "observed_effort": effort, **metrics}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["decide", "reconcile", "audit"])
    parser.add_argument("--input", required=True, help="UTF-8 JSON, or - for stdin")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--audit-dir", type=Path, help="Explicit directory for individual metadata events")
    args = parser.parse_args()
    try:
        data = json.load(sys.stdin) if args.input == "-" else read_json(args.input)
        if args.command == "decide":
            result = decide(data, read_json(args.policy))
        elif args.command == "reconcile":
            result = reconcile(data)
        else:
            result = audit_record(data)
            if args.audit_dir:
                args.audit_dir.mkdir(parents=True, exist_ok=True)
                target = args.audit_dir / (result["event_id"] + ".json")
                with target.open("x", encoding="utf-8") as stream:
                    json.dump(result, stream, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({"action": "direct", "reason": "helper-unavailable", "error_type": type(exc).__name__,
                          "authorizes_execution": False}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
