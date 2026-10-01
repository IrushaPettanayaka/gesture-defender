"""Integration checks for fallback, camera ownership and UI coordinate mapping."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import unittest
from unittest.mock import Mock, patch
import numpy as np
import pygame
import app
import tracking
from game import Game
from gestures import Controls
from session import Session
from settings import WIDTH, HEIGHT
from ui import Renderer
from preferences import DEFAULTS


class RuntimeTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_error_can_switch_to_demo_and_closes_worker(self):
        worker = Mock()
        worker.snapshot.return_value = (None, 'Tracking blocked')
        events = [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_k)],
                  [pygame.event.Event(pygame.QUIT)]]
        with patch.object(app, 'create_worker', return_value=worker), \
                patch.object(pygame.event, 'get', side_effect=events), \
                patch.object(app, 'Renderer') as renderer:
            self.assertEqual(app.run(demo=False, smoke_frames=10), 0)
            args = renderer.return_value.draw.call_args.args
            self.assertTrue(args[-2])
            self.assertIsNone(args[-3])
        worker.close.assert_called_once()
        self.assertFalse(pygame.display.get_init())

    def test_worker_closes_partial_initialization_on_error(self):
        face = Mock()
        with patch.object(tracking, 'FaceTracker', return_value=face), \
                patch.object(tracking, 'HandTracker', side_effect=RuntimeError('model failed')):
            worker = tracking.TrackingWorker()
            worker.start()
            worker.thread.join(timeout=2)
            worker.close()
        face.close.assert_called_once()
        self.assertEqual(worker.snapshot()[1], 'model failed')

    def test_preview_and_all_overlay_states_render(self):
        pygame.display.init()
        pygame.font.init()
        renderer = Renderer(pygame.display.set_mode((WIDTH, HEIGHT)))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        packet = tracking.TrackingFrame(1, 0, frame, [(0.3, 0.2), (0.7, 0.7)], [(0.5, 0.5)] * 21)
        game = Game()
        for state in ('ready', 'setup', 'calibrating', 'running', 'paused', 'gameover'):
            game.state = state
            renderer.draw(game, packet, Controls(palm_progress=0.5), True, True, 'Hand detected', None, False, 60)
        self.assertIsNotNone(renderer.preview)

    def test_camera_switch_waits_for_release_before_opening_next_device(self):
        first, second = Mock(), Mock()
        first.snapshot.return_value = second.snapshot.return_value = (None, None)
        first.thread.is_alive.return_value = True
        factory = Mock(side_effect=[first, second])
        session = Session(DEFAULTS.copy(), factory, keyboard=False)
        session.perform('camera_next')
        self.assertEqual(factory.call_count, 1)
        first.stop.set.assert_called_once()
        first.thread.is_alive.return_value = False
        session.poll_camera()
        self.assertEqual(factory.call_args.args[0], 1)
        session.close()
        second.close.assert_called_once()

    def test_restart_clears_interpreter_hold_and_steering_offsets(self):
        session = Session(DEFAULTS.copy(), Mock())
        session.perform('choose_keyboard')
        session.controller.gestures.fist_since = 1
        session.controller.gestures.palm_offset = 0.7
        session.controller.gestures.exit_offset = 0.4
        session.perform('restart')
        self.assertIsNone(session.controller.gestures.fist_since)
        self.assertEqual(session.controller.gestures.palm_offset, 0)
        self.assertEqual(session.controller.gestures.exit_offset, 0)
        self.assertTrue(session.controller.gestures.fist_latched)
        self.assertEqual(session.game.state, 'running')

    def test_resized_menu_buttons_map_to_logical_coordinates(self):
        pygame.display.init()
        pygame.font.init()
        renderer = Renderer(pygame.display.set_mode((WIDTH//2, HEIGHT//2)))
        renderer.draw(Game(), None, Controls(), False, False, '', None, True, 60)
        self.assertEqual(renderer.click((268/2, 524/2)), 'play')


if __name__ == '__main__':
    unittest.main()
