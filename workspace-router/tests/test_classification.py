import copy
import unittest
import test_router
router = test_router.router


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        # Reuse the host-scoped request fixture without duplicating the old suite.
        self.fixture = test_router.RouterTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.q = self.fixture.q
        self.policy = self.fixture.policy
        self.task = self.q['task']

    def decide(self):
        return self.fixture.run_route()

    def mechanical(self):
        self.task.update(complexity='mechanical', consequence='low', uncertainty='low')
        self.task['assessment'].update(kind='extract', specification='exact', verification='deterministic', scope='local')

    def test_mechanical_requires_every_condition(self):
        self.mechanical()
        valid = copy.deepcopy(self.task)
        for field, value in [('kind', 'implement'), ('specification', 'bounded'),
                             ('verification', 'tests'), ('scope', 'cross_component'),
                             ('consequence', 'normal'), ('uncertainty', 'normal')]:
            with self.subTest(field=field):
                task = copy.deepcopy(valid)
                (task if field in {'consequence', 'uncertainty'} else task['assessment'])[field] = value
                self.assertNotEqual(router.classify_task(task)['lane'], 'mechanical')

    def test_missing_or_unsubstantiated_assessment_does_not_delegate(self):
        del self.task['assessment']
        self.assertEqual(self.decide()['reason'], 'task-assessment-missing')
        for a in (None, {}, {'evidence': ''}, {'evidence': ' ', 'kind': 'extract'}):
            self.task['assessment'] = a
            self.assertEqual(self.decide()['action'], 'direct')

    def test_false_mechanical_label_cannot_downgrade_implementation(self):
        self.task.update(complexity='mechanical', consequence='low', uncertainty='low')
        self.assertEqual(self.decide()['lane'], 'routine')

    def test_ambiguous_cross_component_and_judgment_work(self):
        for change in ({'scope': 'cross_component'}, {'specification': 'open'},
                       {'kind': 'debug', 'verification': 'judgment'},
                       {'kind': 'review', 'verification': 'judgment'}):
            with self.subTest(change=change):
                self.task['assessment'] = {**{'kind': 'implement', 'specification': 'bounded',
                    'verification': 'tests', 'scope': 'local', 'input_form': 'text', 'boundary': 'clear', 'evidence': 'Observed problem with acceptance'}, **change}
                self.assertEqual(self.decide()['recommended'], {'model': 'gpt-6-sol', 'effort': 'high'})

    def test_open_system_design_uses_astra_even_normal_consequence(self):
        self.task['assessment'].update(kind='design', scope='system', specification='open', verification='judgment')
        self.assertEqual(self.decide()['lane'], 'critical')
        self.assertIn('open-or-uncertain-system-work', self.decide()['classification']['reasons'])
        self.assertEqual(self.decide()['recommended']['model'], 'gpt-6-astra')

    def test_exact_system_work_is_complex_and_high_risk_always_critical(self):
        self.mechanical()
        self.task['assessment']['scope'] = 'system'
        self.assertEqual(self.decide()['lane'], 'complex')
        self.task['consequence'] = 'high'
        self.assertEqual(self.decide()['lane'], 'critical')

    def test_explicit_complexity_is_a_floor(self):
        self.mechanical()
        for lane in router.LANES:
            self.task['complexity'] = lane
            self.assertEqual(self.decide()['lane'], lane)

    def test_no_basis_needs_no_assessment(self):
        del self.task['assessment']
        del self.q['delegation']
        self.assertEqual(self.decide()['reason'], 'direct-by-default-no-delegation-need')

    def test_legacy_policy_keeps_its_previous_behavior(self):
        self.policy.pop('classification_mode')
        del self.task['assessment']
        self.assertEqual(self.decide()['action'], 'delegate')

    def test_fallback_only_with_supported_effort(self):
        self.task['complexity'] = 'complex'
        self.q['catalog']['models'] = [{'model': 'gpt-6-sol', 'efforts': ['medium', 'xhigh']}]
        self.assertEqual(self.decide()['recommended']['effort'], 'xhigh')
        self.task['consequence'] = 'high'
        self.assertEqual(self.decide()['reason'], 'no-supported-quality-lane')

    def test_low_workload_is_not_a_license_to_delegate(self):
        self.task['reasoning_minutes'] = 4.99
        self.assertEqual(self.decide()['action'], 'direct')
        self.task['reasoning_minutes'] = 5
        self.assertEqual(self.decide()['action'], 'delegate')

    def test_review_kind_alone_does_not_force_high_effort(self):
        self.task['assessment'].update(kind='review', verification='deterministic')
        self.assertEqual(self.decide()['lane'], 'routine')


if __name__ == '__main__':
    unittest.main()
