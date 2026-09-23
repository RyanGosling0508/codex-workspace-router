import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "router.py"
spec = importlib.util.spec_from_file_location("router", SCRIPT)
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)
NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = router.read_json(router.DEFAULT_POLICY)
        self.q = {
            "schema_version": 1, "depth": 0,
            "host": {"id": "test-host", "os": "windows" if os.name == "nt" else "posix",
                     "cwd": str(self.root), "verified": True},
            "runtime": {"host_id": "test-host", "delegation_available": True, "slots_available": 2,
                        "active_children": 0, "children_started": 0},
            "delegation": {"reason": "explicit_user", "user_requested": True,
                           "evidence": "User explicitly asked for an independent subagent task"},
            "scope": {"confirmed": True, "read_roots": [str(self.root)],
                      "write_roots": [str(self.root / "out")], "protected_paths": [str(self.root / "source")]},
            "task": {"trivial": False, "tool_bound": False, "independent": True, "context_complete": True,
                     "work_type": "read", "complexity": "routine", "consequence": "normal", "uncertainty": "normal",
                     "benefit": "parallel", "reasoning_minutes": 6,
                     "read_paths": [str(self.root / "source")], "write_paths": [], "resources": [],
                     "acceptance": ["Locate coordinate errors with reproducible evidence"], "constraints": ["Do not edit sources"]},
            "active": [], "failure": {"kind": "none", "recovery_attempts": 0},
            "catalog": {"host_id": "test-host", "source": "runtime-tool", "captured_at": NOW.isoformat(),
                        "models": [{"model": model, "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"]}
                                   for model in ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra", "gpt-5.6-terra"]]}}

    def run_route(self):
        return router.decide(self.q, self.policy, NOW)

    def test_routine_delegation(self):
        r = self.run_route()
        self.assertEqual(r["action"], "delegate")
        self.assertEqual(r["recommended"], {"model": "gpt-6-sol", "effort": "medium"})
        self.assertIsNone(r["actual"])
        self.assertFalse(r["authorizes_execution"])
        self.assertFalse(r["spawn"]["allow_nested_delegation"])

    def test_mechanical_route(self):
        self.q["task"].update(complexity="mechanical", uncertainty="low", consequence="low")
        self.assertEqual(self.run_route()["recommended"]["model"], "gpt-6-luna")

    def test_high_consequence_and_uncertainty(self):
        self.q["task"].update(complexity="mechanical", consequence="high")
        self.assertEqual(self.run_route()["recommended"], {"model": "gpt-6-astra", "effort": "high"})
        self.q["task"].update(consequence="normal", uncertainty="high")
        self.assertEqual(self.run_route()["lane"], "complex")

    def test_early_direct_controls(self):
        for change in [{"enabled": False}, {"disable_delegation": True}, {"depth": 1}]:
            with self.subTest(change=change):
                r = router.decide({"schema_version": 1, **change}, self.policy, NOW)
                self.assertEqual(r["action"], "direct")
                self.assertIsNone(r["spawn"])

    def test_small_or_waiting_work(self):
        for key in ("trivial", "tool_bound"):
            with self.subTest(key=key):
                q = copy.deepcopy(self.q)
                q["task"][key] = True
                self.assertEqual(router.decide(q, self.policy, NOW)["action"], "direct")

    def test_dependent_or_incomplete_context(self):
        for key in ("independent", "context_complete"):
            q = copy.deepcopy(self.q)
            q["task"][key] = False
            self.assertEqual(router.decide(q, self.policy, NOW)["action"], "direct")

    def test_acceptance_required(self):
        self.q["task"]["acceptance"] = []
        self.assertEqual(self.run_route()["action"], "direct")

    def test_scope_and_host_verified(self):
        self.q["scope"]["confirmed"] = False
        self.assertEqual(self.run_route()["action"], "direct")
        self.q["scope"]["confirmed"] = True
        self.q["host"]["verified"] = False
        self.assertEqual(self.run_route()["action"], "direct")

    def test_other_host_or_os(self):
        self.q["runtime"]["host_id"] = "remote"
        self.assertEqual(self.run_route()["action"], "direct")
        self.q["runtime"]["host_id"] = "test-host"
        self.q["host"]["os"] = "posix" if os.name == "nt" else "windows"
        self.assertEqual(self.run_route()["reason"], "run-preflight-on-the-execution-host")

    def test_missing_cwd(self):
        self.q["host"]["cwd"] = str(self.root / "missing")
        self.assertEqual(self.run_route()["action"], "direct")

    def test_outside_read(self):
        self.q["task"]["read_paths"] = [str(self.root.parent / "unrelated")]
        self.assertEqual(self.run_route()["reason"], "read-outside-task-scope")

    def test_outside_write(self):
        self.q["task"].update(work_type="edit", write_paths=[str(self.root / "unrelated")])
        self.assertEqual(self.run_route()["reason"], "write-outside-task-scope")

    def test_protected_source_and_parent(self):
        self.q["scope"]["write_roots"] = [str(self.root)]
        self.q["task"]["work_type"] = "edit"
        for path in (self.root, self.root / "source" / "file.txt"):
            self.q["task"]["write_paths"] = [str(path)]
            self.assertEqual(self.run_route()["reason"], "write-overlaps-protected-source")

    def test_read_cannot_declare_writes(self):
        self.q["task"]["write_paths"] = [str(self.root / "out")]
        self.assertEqual(self.run_route()["reason"], "read-task-declares-writes")

    def test_parent_traversal(self):
        self.q["task"]["read_paths"] = [str(self.root / ".." / "other")]
        self.assertEqual(self.run_route()["reason"], "routing-input-or-capability-unverified")

    def test_windows_path_boundaries(self):
        self.assertFalse(router.within("c:\\project-extra", "c:\\project", "windows"))
        self.assertTrue(router.within("c:\\project\\src", "c:\\project", "windows"))
        for path in ("C:\\project\\a:stream", "C:relative", "\\\\?\\C:\\project"):
            with self.assertRaises(ValueError):
                router.canonical(path, "windows")

    def test_existing_symlink_escape(self):
        link = self.root / "out" / "link"
        link.parent.mkdir()
        try:
            link.symlink_to(self.root.parent, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation not permitted on this host")
        self.q["task"].update(work_type="edit", write_paths=[str(link / "outside")])
        self.assertEqual(self.run_route()["reason"], "write-outside-task-scope")

    def test_write_read_conflicts(self):
        self.q["active"] = [{"host_id": "test-host", "read_paths": [],
                            "write_paths": [str(self.root / "source")], "resources": []}]
        self.assertEqual(self.run_route()["action"], "serialize")

    def test_disjoint_readers(self):
        self.q["active"] = [{"host_id": "test-host", "read_paths": [str(self.root / "source")],
                            "write_paths": [], "resources": []}]
        self.assertEqual(self.run_route()["action"], "delegate")

    def test_shared_resource_across_hosts(self):
        self.q["task"]["resources"] = ["navip-live"]
        self.q["active"] = [{"host_id": "remote", "read_paths": [], "write_paths": [], "resources": ["navip-live"]}]
        self.assertEqual(self.run_route()["action"], "serialize")

    def test_slots_and_unavailable_tool(self):
        self.q["runtime"]["slots_available"] = 0
        self.assertEqual(self.run_route()["action"], "serialize")
        self.q["runtime"]["delegation_available"] = False
        self.assertEqual(self.run_route()["action"], "direct")

    def test_conflict_operations_do_not_consume_child_quota(self):
        self.q["active"] = [{"host_id": "test-host", "read_paths": [],
                             "write_paths": [str(self.root / "out" / name)], "resources": []}
                            for name in ("coordinator", "test-runner")]
        self.assertEqual(self.run_route()["action"], "delegate")
        self.q["runtime"].update(active_children=1, children_started=1)
        self.assertEqual(self.run_route()["reason"], "concurrency-cap")

    def test_substantial_work_stays_direct_without_need(self):
        del self.q["delegation"]
        self.q["task"].update(complexity="critical", reasoning_minutes=60)
        self.assertEqual(self.run_route()["reason"], "direct-by-default-no-delegation-need")

    def test_direct_default_needs_no_catalog(self):
        del self.q["delegation"]
        del self.q["catalog"]
        self.assertEqual(self.run_route()["reason"], "direct-by-default-no-delegation-need")

    def test_explicit_delegation_needs_observed_user_request(self):
        self.q["delegation"]["user_requested"] = False
        self.assertEqual(self.run_route()["reason"], "explicit-delegation-not-requested")

    def test_delegation_needs_concrete_evidence(self):
        self.q["delegation"]["evidence"] = "  "
        self.assertEqual(self.run_route()["reason"], "delegation-evidence-missing")

    def test_targeted_review_can_use_same_model(self):
        self.q["delegation"] = {"reason": "verification_gap", "evidence": "Check whether the axis swap preserves handedness"}
        self.q["task"]["benefit"] = "quality"
        self.q["current"] = {"source": "runtime", "model": "gpt-6-sol", "effort": "medium"}
        self.assertEqual(self.run_route()["action"], "delegate")

    def test_auto_review_cannot_write(self):
        self.q["delegation"] = {"reason": "verification_gap", "evidence": "Check axis handedness"}
        self.q["task"].update(work_type="edit", write_paths=[str(self.root / "out")])
        self.assertEqual(self.run_route()["reason"], "independent-verification-is-read-only")

    def test_parallel_speed_requires_user_priority(self):
        self.q["delegation"] = {"reason": "deadline_parallel", "evidence": "Implementation can run alongside analysis"}
        self.assertEqual(self.run_route()["reason"], "parallel-speed-not-requested")
        self.q["delegation"]["user_prioritized_speed"] = True
        self.assertEqual(self.run_route()["action"], "delegate")

    def test_speculative_savings_cannot_open_gate(self):
        self.q["delegation"] = {"reason": "verification_gap", "evidence": "The candidate model may be cheaper"}
        self.q["task"]["benefit"] = "cost"
        self.assertEqual(self.run_route()["reason"], "speculative-savings-do-not-justify-delegation")

    def test_total_budget_includes_finished_children(self):
        self.q["runtime"].update(active_children=0, children_started=2)
        self.assertEqual(self.run_route()["reason"], "total-child-budget-exhausted")

    def test_started_count_cannot_be_less_than_active(self):
        self.q["runtime"].update(active_children=1, children_started=0)
        self.assertEqual(self.run_route()["reason"], "routing-input-or-capability-unverified")

    def test_legacy_request_cannot_bypass_total_budget(self):
        del self.q["runtime"]["children_started"]
        self.assertEqual(self.run_route()["action"], "direct")

    def test_disabled_overrides_evidence(self):
        self.q["disable_delegation"] = True
        self.assertEqual(self.run_route()["reason"], "delegation-disabled")

    def test_fractional_counts_rejected(self):
        self.q["runtime"]["active_children"] = 0.5
        self.assertEqual(self.run_route()["action"], "direct")

    def test_external_actions_stay_coordinator(self):
        for kind in ("external_action", "shared_resource"):
            self.q["task"]["work_type"] = kind
            self.assertEqual(self.run_route()["action"], "direct")

    def test_infrastructure_not_escalated(self):
        for kind in router.NON_REASONING_FAILURES:
            self.q["failure"]["kind"] = kind
            r = self.run_route()
            self.assertEqual(r["action"], "direct")
            self.assertIsNone(r["recommended"])

    def test_recovery_bounded(self):
        self.q["failure"]["kind"] = "reasoning"
        self.assertEqual(self.run_route()["lane"], "complex")
        self.q["failure"]["recovery_attempts"] = 1
        self.assertEqual(self.run_route()["reason"], "recovery-budget-exhausted")

    def test_catalog_stale_wrong_host_and_untrusted_source(self):
        for key, value in [("captured_at", (NOW - timedelta(hours=7)).isoformat()),
                           ("captured_at", (NOW + timedelta(minutes=5)).isoformat()),
                           ("host_id", "remote"), ("source", "config-file")]:
            q = copy.deepcopy(self.q)
            q["catalog"][key] = value
            self.assertEqual(router.decide(q, self.policy, NOW)["action"], "direct")

    def test_no_quality_downgrade_when_astra_missing(self):
        self.q["task"]["consequence"] = "high"
        self.q["catalog"]["models"] = self.q["catalog"]["models"][:2]
        self.assertEqual(self.run_route()["reason"], "no-supported-quality-lane")

    def test_explicit_model_not_substituted(self):
        self.q["explicit"] = {"model": "unavailable", "effort": "high"}
        self.assertEqual(self.run_route()["action"], "report_unsupported")

    def test_explicit_terra(self):
        self.q["explicit"] = {"model": "gpt-5.6-terra", "effort": "medium"}
        self.assertEqual(self.run_route()["recommended"]["model"], "gpt-5.6-terra")

    def test_max_only_explicit_ultra_separate(self):
        self.assertNotIn(self.run_route()["recommended"]["effort"], ["max", "ultra"])
        self.q["explicit"] = {"model": "gpt-6-astra", "effort": "max"}
        self.assertEqual(self.run_route()["recommended"]["effort"], "max")
        self.q["explicit"]["effort"] = "ultra"
        self.assertEqual(self.run_route()["action"], "report_unsupported")

    def test_current_config_not_runtime(self):
        self.q["task"]["benefit"] = "quality"
        self.q["current"] = {"source": "config", "model": "gpt-6-sol", "effort": "medium"}
        self.assertNotIn("current_observed", self.run_route())
        self.q["current"]["source"] = "runtime"
        self.assertEqual(self.run_route()["current_observed"], {"model": "gpt-6-sol", "effort": "medium"})
        self.assertEqual(self.run_route()["action"], "delegate")

    def test_no_unknown_benefit_or_speculative_critical_savings(self):
        self.q["task"]["reasoning_minutes"] = None
        self.assertEqual(self.run_route()["action"], "direct")
        self.q["task"].update(reasoning_minutes=6, consequence="high", benefit="cost")
        self.assertEqual(self.run_route()["action"], "direct")

    def test_malformed_input_closes_delegation(self):
        for request in (None, [], {}, {"schema_version": 2}, {"schema_version": 1, "depth": True}):
            self.assertEqual(router.decide(request, self.policy, NOW)["action"], "direct")
        self.assertEqual(router.decide(self.q, {}, NOW)["action"], "direct")
        self.q["task"]["trivial"] = "false"
        self.assertEqual(self.run_route()["action"], "direct")

    def test_completion_needs_acceptance(self):
        self.assertEqual(router.reconcile({"state": "completed", "acceptance": "pending"})["action"], "validate")
        self.assertEqual(router.reconcile({"state": "completed", "acceptance": "passed"})["action"], "accept")
        for state in ("failed", "interrupted"):
            self.assertEqual(router.reconcile({"state": state, "acceptance": "passed"})["action"], "inspect-failure")

    def test_timeout_does_not_interrupt(self):
        r = router.reconcile({"state": "running", "acceptance": "pending", "progress_overdue": True})
        self.assertFalse(r["interrupt"])
        self.assertFalse(r["terminal"])

    def test_audit_drops_content_and_unverified_model(self):
        r = router.audit_record({"state": "completed", "acceptance": "passed", "prompt": "SECRET",
                                 "path": "private/path", "observed": {"source": "child-prose", "model": "gpt-6-astra"}})
        self.assertNotIn("SECRET", json.dumps(r))
        self.assertNotIn("private/path", json.dumps(r))
        self.assertIsNone(r["observed_model"])

    def test_cli_stdio_decision(self):
        self.q["catalog"]["captured_at"] = datetime.now(timezone.utc).isoformat()
        result = subprocess.run([sys.executable, str(SCRIPT), "decide", "--input", "-"],
                                input=json.dumps(self.q), text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["action"], "delegate")


if __name__ == "__main__":
    unittest.main()
