import unittest
from detector.trigger_stabilizer import TriggerStabilizer


class StabilityTests(unittest.TestCase):
    def setUp(self):
        self.state = TriggerStabilizer()

    def confirm(self, trigger, start):
        self.assertIsNone(self.state.update(trigger, start))
        return self.state.update(trigger, start + 650)

    def test_requires_continuous_confirmation(self):
        self.assertIsNone(self.state.update('happy', 0))
        self.assertIsNone(self.state.update('happy', 649))
        self.assertEqual(self.state.update('happy', 650), 'happy')

    def test_alternating_noise_never_switches(self):
        for now in range(0, 10000, 100):
            self.assertIsNone(self.state.update('happy' if now % 200 else 'sad', now))
        self.assertEqual(self.state.current, 'neutral')

    def test_current_image_has_minimum_hold(self):
        self.assertEqual(self.confirm('happy', 0), 'happy')
        self.assertIsNone(self.state.update('sad', 700))
        self.assertIsNone(self.state.update('sad', 1350))
        self.assertIsNone(self.state.update('sad', 2449))
        self.assertEqual(self.state.update('sad', 2450), 'sad')

    def test_brief_tracking_loss_preserves_image(self):
        self.confirm('happy', 0)
        self.assertIsNone(self.state.update(None, 700))
        self.assertEqual(self.state.current, 'happy')
        self.assertIsNone(self.state.update('happy', 1000))

    def test_tracking_loss_restarts_pending_confirmation(self):
        self.state.update('happy', 0)
        self.state.update(None, 500)
        self.assertIsNone(self.state.update('happy', 650))
        self.assertIsNone(self.state.update('happy', 1299))
        self.assertEqual(self.state.update('happy', 1300), 'happy')

    def test_neutral_waits_for_release_and_confirmation(self):
        self.confirm('happy', 0)
        self.assertIsNone(self.state.update(None, 3249))
        self.assertIsNone(self.state.update(None, 3250))
        self.assertEqual(self.state.update(None, 3900), 'neutral')

    def test_same_state_does_not_emit_again(self):
        self.confirm('happy', 0)
        for now in [1000, 3000, 20000]:
            self.assertIsNone(self.state.update('happy', now))

    def test_elapsed_time_works_with_sparse_frames(self):
        self.assertEqual(self.confirm('happy', 0), 'happy')
        self.assertIsNone(self.state.update('sad', 3000))
        self.assertEqual(self.state.update('sad', 7000), 'sad')

    def test_configuration_discards_old_pending_candidate(self):
        self.state.update('happy', 0)
        self.state.configure({'confirm_ms': 1000})
        self.assertIsNone(self.state.update('happy', 1500))
        self.assertEqual(self.state.update('happy', 2500), 'happy')
