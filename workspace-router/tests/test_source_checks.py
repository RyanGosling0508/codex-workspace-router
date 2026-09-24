"""Admission, compatibility and recovery for focused factual research."""
import copy
import unittest
import test_router

router = test_router.router


class SourceCheckTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_router.RouterTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.q = self.fixture.q
        self.presets = router.read_json(router.PRESETS)
        self.q['task'].update(consequence='low', uncertainty='low')
        self.q['task']['assessment'].update(
            kind='research', specification='exact', verification='sources',
            evidence='Locate the documented timeout default for the pinned SDK version',
            source_evidence='Read the pinned SDK reference and declaration; cite both locations and compare the default')

    def result(self, profile='balanced'):
        return router.decide(self.q, self.presets[profile], test_router.NOW)

    def test_trial_is_routine_and_premium_keeps_its_quality_preference(self):
        for profile in ('economy', 'balanced'):
            r = self.result(profile)
            self.assertEqual(r['action'], 'delegate')
            self.assertEqual(r['lane'], 'routine')
            self.assertEqual(r['candidate_pool'], 'mechanical')
            self.assertEqual(r['recommended'], {'model': 'gpt-6-luna', 'effort': 'high'})
        self.assertEqual(self.result('premium')['recommended'], {'model': 'gpt-6-sol', 'effort': 'high'})

    def test_each_trial_condition_is_necessary(self):
        original = copy.deepcopy(self.q)
        cases = [('work_type', 'edit'), ('consequence', 'normal'), ('uncertainty', 'normal'),
                 ('complexity', 'complex'), ('complexity', 'critical'), ('kind', 'review'),
                 ('specification', 'bounded'), ('verification', 'judgment'),
                 ('scope', 'cross_component'), ('input_form', 'visual'), ('boundary', 'adjacent')]
        for profile in ('economy', 'balanced'):
            for key, value in cases:
                with self.subTest(profile=profile, key=key, value=value):
                    self.q = copy.deepcopy(original)
                    task = self.q['task']
                    (task if key in task else task['assessment'])[key] = value
                    task['assessment']['boundary_evidence'] = 'A second source may use a different version'
                    if key == 'work_type':
                        task['write_paths'] = [str(self.fixture.root / 'out' / 'report')]
                    self.assertNotEqual(self.result(profile)['recommended']['model'], 'gpt-6-luna')
        self.q = copy.deepcopy(original)
        self.q['task']['write_paths'] = [str(self.fixture.root / 'out' / 'cache')]
        self.assertEqual(self.result()['action'], 'direct')

    def test_source_evidence_is_required(self):
        for value in (None, '', ' ', [], 7):
            with self.subTest(value=value):
                self.q['task']['assessment']['source_evidence'] = value
                self.assertEqual(self.result()['action'], 'direct')
        del self.q['task']['assessment']['source_evidence']
        self.assertEqual(self.result()['action'], 'direct')

    def test_ordinary_research_and_legacy_policies_keep_their_routes(self):
        self.q['task']['assessment']['verification'] = 'judgment'
        self.assertEqual(self.result()['recommended']['model'], 'gpt-6-sol')
        self.q['task']['assessment']['verification'] = 'sources'
        del self.presets['balanced']['classification_mode']
        self.assertEqual(self.result()['recommended']['model'], 'gpt-6-sol')

    def test_recovery_and_environment_failures(self):
        for kind in ('reasoning', 'verification'):
            self.q['failure']['kind'] = kind
            r = self.result()
            self.assertEqual(r['lane'], 'complex')
            self.assertEqual(r['recommended'], {'model': 'gpt-6-sol', 'effort': 'high'})
            self.assertNotIn('candidate_pool', r)
        self.q['failure']['recovery_attempts'] = 1
        self.assertEqual(self.result()['reason'], 'recovery-budget-exhausted')
        self.q['failure'].update(kind='network', recovery_attempts=0)
        self.assertEqual(self.result()['action'], 'direct')

    def test_missing_luna_uses_configured_pool_and_explicit_choice_wins(self):
        self.q['catalog']['models'] = [row for row in self.q['catalog']['models'] if row['model'] != 'gpt-6-luna']
        self.assertEqual(self.result()['recommended'], {'model': 'gpt-6-sol', 'effort': 'medium'})
        self.q['explicit'] = {'model': 'gpt-6-astra', 'effort': 'medium'}
        self.assertEqual(self.result()['recommended'], self.q['explicit'])

    def test_trial_does_not_create_delegation_need(self):
        self.q.pop('delegation')
        self.assertEqual(self.result()['reason'], 'direct-by-default-no-delegation-need')


if __name__ == '__main__':
    unittest.main()
