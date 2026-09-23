import copy
import unittest
import test_router

router = test_router.router


class PresetTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_router.RouterTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.q = self.fixture.q
        self.task = self.q['task']
        self.presets = router.read_json(router.PRESETS)

    def result(self, profile):
        return router.decide(self.q, self.presets[profile], test_router.NOW)

    def trial(self):
        self.task.update(consequence='low', uncertainty='low')
        self.task['assessment'].update(kind='implement', specification='exact')

    def test_presets_valid_and_balanced_is_default(self):
        for profile, policy in self.presets.items():
            router.validate_policy(policy)
            self.assertEqual(policy['routing_strategy'], profile)
            self.assertEqual(policy['max_children'], 1)
            self.assertEqual(policy['max_children_per_request'], 2)
        self.assertEqual(self.presets['balanced'], router.read_json(router.RECOMMENDED_POLICY))
        self.assertEqual(self.presets['balanced'], router.read_json(router.DEFAULT_POLICY))

    def test_trial_preserves_lane_and_recovery_floor(self):
        self.trial()
        self.assertEqual(self.result('economy')['recommended'], {'model': 'gpt-6-luna', 'effort': 'high'})
        self.assertEqual(self.result('economy')['lane'], 'routine')
        self.assertEqual(self.result('balanced')['recommended']['model'], 'gpt-6-sol')
        self.q['failure']['kind'] = 'verification'
        self.assertEqual(self.result('economy')['recommended'], {'model': 'gpt-6-sol', 'effort': 'high'})

    def test_each_economic_trial_gate_is_necessary(self):
        self.trial()
        original = copy.deepcopy(self.task)
        for key, value in [('consequence', 'normal'), ('uncertainty', 'normal'), ('kind', 'review'),
                           ('specification', 'bounded'), ('verification', 'judgment'), ('scope', 'cross_component'),
                           ('input_form', 'visual'), ('boundary', 'adjacent')]:
            with self.subTest(key=key):
                self.q['task'] = copy.deepcopy(original)
                target = self.q['task'] if key in {'consequence', 'uncertainty'} else self.q['task']['assessment']
                target[key] = value
                self.q['task']['assessment']['boundary_evidence'] = 'Specific unresolved adjacent interaction'
                self.assertNotEqual(self.result('economy')['recommended']['model'], 'gpt-6-luna')

    def test_premium_promotes_only_evidenced_ambiguity(self):
        self.assertEqual(self.result('premium')['recommended'], {'model': 'gpt-6-sol', 'effort': 'high'})
        a = self.task['assessment']
        a['boundary'] = 'adjacent'
        for evidence in (None, '', ' '):
            a['boundary_evidence'] = evidence
            self.assertEqual(self.result('premium')['action'], 'direct')
        a['boundary_evidence'] = 'Adjacent state owner unresolved despite known local API'
        self.assertEqual(self.result('premium')['recommended'], {'model': 'gpt-6-astra', 'effort': 'high'})
        self.assertEqual(self.result('balanced')['recommended']['model'], 'gpt-6-sol')
        self.task['consequence'] = 'high'
        self.assertEqual(self.result('premium')['recommended'], {'model': 'gpt-6-astra', 'effort': 'xhigh'})

    def test_all_profiles_preserve_no_delegation_and_critical_floor(self):
        self.task['consequence'] = 'high'
        for profile in self.presets:
            self.assertEqual(self.result(profile)['recommended']['model'], 'gpt-6-astra')
        self.q.pop('delegation')
        for profile in self.presets:
            self.assertEqual(self.result(profile)['action'], 'direct')

    def test_visual_input_never_qualifies_for_mechanical_lane(self):
        self.task.update(complexity='mechanical', consequence='low', uncertainty='low')
        self.task['assessment'].update(kind='extract', specification='exact', verification='deterministic', input_form='visual')
        for profile in self.presets:
            self.assertNotEqual(self.result(profile)['recommended']['model'], 'gpt-6-luna')

    def test_explicit_model_remains_authoritative(self):
        self.trial()
        self.q['explicit'] = {'model': 'gpt-6-astra', 'effort': 'medium'}
        for profile in self.presets:
            self.assertEqual(self.result(profile)['recommended'], {'model': 'gpt-6-astra', 'effort': 'medium'})


if __name__ == '__main__':
    unittest.main()
