import unittest
from types import SimpleNamespace
from controls import InputController, TrackingHealth
from game import Game


def frame(now, face=True, hand=True, sequence=1):
    return SimpleNamespace(captured_at=now, sequence=sequence,
                           face=[(0.5, 0.5)] if face else None,
                           hand=[(0.5, 0.5)] * 21 if hand else None)


class ControlTests(unittest.TestCase):
    def test_both_tracking_losses_pause_after_grace_and_require_resume(self):
        for lost in ("face", "hand"):
            health, game = TrackingHealth(), Game()
            health.update(frame(10), None, 10)
            game.toggle(health.ready)
            health.update(frame(10.2, **{lost: False}), None, 10.2)
            game.update(0.01, 0.5, False, health.can_continue, health.reason)
            self.assertEqual(game.state, "running")
            health.update(frame(10.7, **{lost: False}), None, 10.7)
            game.update(0.01, 0.5, False, health.can_continue, health.reason)
            self.assertEqual(game.state, "paused")
            self.assertIn(lost.capitalize(), game.reason)
            health.update(frame(11), None, 11)
            game.update(0.01, 0.5, False, health.can_continue)
            self.assertEqual(game.state, "paused")
            game.toggle(health.ready)
            self.assertEqual(game.state, "running")

    def test_stale_and_error_results_do_not_allow_resume(self):
        health = TrackingHealth()
        health.update(frame(0), None, 2)
        self.assertFalse(health.ready)
        self.assertFalse(health.can_continue)
        health.update(frame(3), "camera failed", 3)
        self.assertFalse(health.ready)

    def test_keyboard_bounds_fire_and_no_camera_dependency(self):
        controls = InputController(keyboard=True)
        for _ in range(100):
            output = controls.update(None, None, 0, 0.1, direction=1, fire=True)
        self.assertEqual(output.x, 1)
        self.assertTrue(output.shoot)
        for _ in range(100):
            output = controls.update(None, None, 0, 0.1, direction=-1)
        self.assertEqual(output.x, 0)

    def test_held_pinch_drives_fire_while_game_applies_cooldown(self):
        controls = InputController()
        points = [(0.5, 0.5)] * 21
        packet = frame(1)
        packet.hand = points
        controls.update(packet, None, 1, 0.01)
        packet = frame(1.1, sequence=2)
        packet.hand = points
        self.assertTrue(controls.update(packet, None, 1.1, 0.01).shoot)
        self.assertTrue(controls.update(packet, None, 1.11, 0.01).shoot)

    def test_camera_gap_does_not_complete_a_pending_pinch(self):
        controls = InputController()
        controls.update(frame(1), None, 1, 0.01)
        self.assertFalse(controls.update(frame(2, sequence=2), None, 2, 0.01).shoot)
        self.assertFalse(controls.update(frame(2.1, sequence=3), None, 2.1, 0.01).shoot)
