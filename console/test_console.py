import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from console.server import ConsoleServer, Conflict, PolicyStore, ROOT, simulate, validate


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'policy.json'
        self.policy = json.loads((ROOT / 'workspace-router/references/policy.json').read_text())
        self.path.write_text(json.dumps(self.policy), encoding='utf-8')
        self.store = PolicyStore(self.path, self.root / 'data')

    def test_save_backup_and_stale_revision(self):
        first = self.store.state()
        updated = copy.deepcopy(self.policy)
        updated['enabled'] = False
        saved = self.store.save(updated, first['revision'])
        self.assertFalse(saved['policy']['enabled'])
        self.assertEqual(saved['history'][0]['policy'], self.policy)
        with self.assertRaises(Conflict):
            self.store.save(self.policy, first['revision'])
        self.assertEqual(json.loads(self.path.read_text()), updated)
        restored = self.store.save(saved['history'][0]['policy'], saved['revision'])
        self.assertEqual(restored['policy'], self.policy)

    def test_invalid_save_leaves_file_unchanged(self):
        raw = self.path.read_bytes()
        self.policy['max_children'] = 3
        with self.assertRaises(ValueError):
            self.store.save(self.policy, self.store.state()['revision'])
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(self.store.history(), [])

    def test_noop_save_has_no_backup(self):
        self.assertTrue(self.store.save(self.policy, self.store.state()['revision'])['unchanged'])
        self.assertEqual(self.store.history(), [])

    def test_external_change_detected(self):
        old = self.store.state()
        self.path.write_text(json.dumps(self.policy) + '\n', encoding='utf-8')
        with self.assertRaises(Conflict):
            self.store.save(self.policy, old['revision'])

    def test_trigger_switch_and_legacy_default(self):
        self.assertEqual(simulate(self.policy, {'scenario': 'review'})['result']['action'], 'delegate')
        self.policy['triggers']['verification_gap'] = False
        result = simulate(self.policy, {'scenario': 'review'})['result']
        self.assertEqual(result['action'], 'direct')
        self.assertIn('delegation-trigger-disabled', str(result))
        self.policy.pop('triggers')
        self.assertEqual(simulate(self.policy, {'scenario': 'review'})['result']['action'], 'delegate')

    def test_simulator_boundaries(self):
        for scenario in ('routine', 'tiny'):
            result = simulate(self.policy, {'scenario': scenario})
            self.assertEqual(result['result']['action'], 'direct')
            self.assertFalse(result['capabilities_live'])
            self.assertNotIn('spawn', result['result'])
        for environment in ('offline', 'no-models', 'conflict'):
            self.assertNotEqual(simulate(self.policy, {'environment': environment})['result']['action'], 'delegate')
        self.assertNotEqual(simulate(self.policy, {'active_children': 1, 'children_started': 1})['result']['action'], 'delegate')

    def test_recommended_defaults_are_not_current_editable_policy(self):
        current = self.store.state()
        self.assertEqual(current['recommended_policy']['classification_mode'], 'evidence-v1')
        updated = copy.deepcopy(self.policy)
        updated['lanes']['mechanical'][0] = ['gpt-6-sol', 'high']
        saved = self.store.save(updated, current['revision'])
        self.assertEqual(saved['recommended_policy'], current['recommended_policy'])
        self.assertNotEqual(saved['recommended_policy'], saved['policy'])

    def test_presets_roundtrip_and_differ_in_simulation(self):
        presets = self.store.state()['presets']
        first = self.store.state()
        for key, policy in presets.items():
            saved = self.store.save(policy, first['revision'])
            self.assertEqual(saved['policy'], policy)
            first = saved
        for name, expected in [('economy', 'gpt-6-luna'), ('balanced', 'gpt-6-sol'), ('premium', 'gpt-6-sol')]:
            self.assertEqual(simulate(presets[name], {'scenario': 'local_trial'})['result']['recommended']['model'], expected)
        self.assertEqual(simulate(presets['premium'], {'scenario': 'borderline'})['result']['recommended']['model'], 'gpt-6-astra')

    def test_new_scenarios_explain_their_lane(self):
        extraction = simulate(self.policy, {'scenario': 'mechanical'})['result']
        self.assertEqual(extraction['recommended'], {'model': 'gpt-6-luna', 'effort': 'high'})
        architecture = simulate(self.policy, {'scenario': 'architecture'})['result']
        self.assertEqual(architecture['recommended'], {'model': 'gpt-6-astra', 'effort': 'high'})
        self.assertIn('open-or-uncertain-system-work', architecture['classification']['reasons'])

    def test_validation_rejects_unknowns_and_unsafe_efforts(self):
        for change in ({'triggers': {'verification_gap': 'false'}}, {'surprise': True},
                       {'lanes': {**self.policy['lanes'], 'critical': [['gpt-6-astra', 'ultra']]}}):
            with self.assertRaises(ValueError):
                validate({**self.policy, **change})

    def test_http_auth_origin_paths_and_save(self):
        server = ConsoleServer(0, self.store, 'test-token')
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def request(path, method='GET', data=None, headers=None):
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
            try:
                conn.request(method, path, json.dumps(data) if data is not None else None, headers or {})
                response = conn.getresponse()
                return response.status, response.read()
            finally:
                conn.close()
        self.assertEqual(request('/api/state')[0], 401)
        auth = {'X-Router-Token': 'test-token', 'Content-Type': 'application/json'}
        self.assertEqual(request('/api/state', headers={**auth, 'Origin': 'https://untrusted.example'})[0], 403)
        self.assertEqual(request('/api/state', headers={**auth, 'Host': 'untrusted.example'})[0], 403)
        self.assertEqual(request('/../../workspace-router/references/policy.json')[0], 404)
        status, raw = request('/api/state', headers=auth)
        self.assertEqual(status, 200)
        current = json.loads(raw)
        candidate = copy.deepcopy(self.policy)
        candidate['enabled'] = False
        self.assertEqual(request('/api/save', 'POST', {'policy': candidate, 'revision': current['revision']}, auth)[0], 200)
        self.assertEqual(request('/api/save', 'POST', {'policy': self.policy, 'revision': current['revision']}, auth)[0], 409)
        self.assertEqual(request('/api/save', 'POST', [], auth)[0], 400)


if __name__ == '__main__':
    unittest.main()
