"""Integration checks for error fallback, frame display, and resource cleanup."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import unittest
from unittest.mock import Mock, patch
import numpy as np
import pygame
import app
import tracking
from game import Game
from gestures import Controls
from settings import WIDTH, HEIGHT
from ui import Renderer
from preferences import DEFAULTS


class RuntimeTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_error_can_switch_to_demo_and_closes_worker(self):
        worker = Mock()
        worker.snapshot.return_value = (None, "Tracking blocked")
        events = [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_k)],
                  [pygame.event.Event(pygame.QUIT)]]
        with patch.object(app, "create_worker", return_value=worker), \
                patch.object(pygame.event, "get", side_effect=events), \
                patch.object(app, "Renderer") as renderer:
            self.assertEqual(app.run(demo=False, smoke_frames=10), 0)
            args = renderer.return_value.draw.call_args.args
            self.assertTrue(args[-2])  # Demo enabled.
            self.assertIsNone(args[-3])  # Error cleared.
        worker.close.assert_called_once()
        self.assertFalse(pygame.display.get_init())

    def test_worker_closes_partial_initialization_on_error(self):
        face = Mock()
        with patch.object(tracking, "FaceTracker", return_value=face), \
                patch.object(tracking, "HandTracker", side_effect=RuntimeError("model failed")):
            worker = tracking.TrackingWorker()
            worker.start()
            worker.thread.join(timeout=2)
            worker.close()
        face.close.assert_called_once()
        self.assertEqual(worker.snapshot()[1], "model failed")

    def test_preview_and_all_overlay_states_render(self):
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        renderer = Renderer(screen)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        packet = tracking.TrackingFrame(1, 0, frame, [(0.3, 0.2), (0.7, 0.7)], [(0.5, 0.5)] * 21)
        game = Game()
        for state in ("ready", "setup", "calibrating", "running", "paused", "gameover"):
            game.state = state
            renderer.draw(game, packet, Controls(palm_progress=0.5), True, True,
                          "Hand detected", None, False, 60)
        self.assertIsNotNone(renderer.preview)

    def test_camera_switch_waits_for_release_before_opening_next_device(self):
        first, second = Mock(), Mock()
        first.snapshot.return_value = second.snapshot.return_value = (None, None)
        # Switching must wait a full loop while the original worker is alive.
        first.thread.is_alive.side_effect = [True, False]
        second.thread.is_alive.return_value = False
        events = [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHTBRACKET)], [], [],
                  [pygame.event.Event(pygame.QUIT)]]
        with patch.object(app, 'create_worker', side_effect=[first, second]) as create, \
                patch.object(app, 'Preferences') as prefs, \
                patch.object(pygame.event, 'get', side_effect=events), \
                patch.object(app, 'Renderer'):
            prefs.return_value.values = DEFAULTS.copy()
            self.assertEqual(app.run(demo=False, smoke_frames=10), 0)
            self.assertEqual(create.call_args_list[0].args[0], 0)
            self.assertEqual(create.call_args_list[1].args[0], 1)
        first.stop.set.assert_called_once()
        second.close.assert_called_once()

    def test_restart_clears_interpreter_hold_and_steering_offsets(self):
        controllers = []
        real_controller = app.InputController
        def create_controller(**kwargs):
            controller = real_controller(**kwargs)
            controllers.append(controller)
            if len(controllers) == 1:
                controller.gestures.fist_since = 1
                controller.gestures.palm_offset = 0.7
                controller.gestures.exit_offset = 0.4
            return controller
        events = [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)],
                  [pygame.event.Event(pygame.QUIT)]]
        with patch.object(app, 'InputController', side_effect=create_controller), \
                patch.object(pygame.event, 'get', side_effect=events), \
                patch.object(app, 'Renderer'):
            app.run(demo=True, smoke_frames=10)
        self.assertEqual(len(controllers), 2)
        self.assertIsNone(controllers[1].gestures.fist_since)
        self.assertEqual(controllers[1].gestures.palm_offset, 0)
        self.assertEqual(controllers[1].gestures.exit_offset, 0)
        self.assertTrue(controllers[1].gestures.fist_latched)

    def test_resized_menu_buttons_map_to_logical_coordinates(self):
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((550, 380))
        renderer = Renderer(screen)
        renderer.menu_open = True
        renderer.draw(Game(), None, Controls(), False, False, "Keyboard", None, True, 60)
        self.assertEqual(renderer.click((60, 275)), pygame.K_SPACE)


if __name__ == "__main__":
    unittest.main()
