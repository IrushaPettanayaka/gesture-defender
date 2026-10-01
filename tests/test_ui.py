"""Behavioral UI checks: navigation must preserve combat and camera ownership."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import time
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
import pygame
from session import Session
from preferences import DEFAULTS
from gestures import Controls
from ui import Renderer
from ui_components import StableMessage
from game import Game
from arena_view import ArenaView
from preferences import Preferences
from settings import WIDTH, HEIGHT


def packet():
    points = [(0.5, 0.6)] * 21
    points[0], points[9], points[8], points[4] = (0.5,0.8), (0.5,0.6), (0.7,0.4), (0.1,0.5)
    return SimpleNamespace(sequence=1, captured_at=time.monotonic(), hand=points, face=[(0.3,0.3)])


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.worker = Mock()
        self.worker.snapshot.side_effect = lambda: (packet(), None)
        self.worker.thread.is_alive.return_value = False
        self.factory = Mock(return_value=self.worker)
        self.session = Session(DEFAULTS.copy(), self.factory, best=100)

    def step(self, **kwargs):
        return self.session.update(time.monotonic(), 0.02, **kwargs)

    def test_menu_and_settings_do_not_start_camera(self):
        self.session.perform('settings')
        self.step()
        self.session.escape()
        self.session.perform('play')
        self.step()
        self.factory.assert_not_called()
        self.assertEqual(self.session.page, 'mode')

    def test_setup_calibration_cancel_start_pause_and_menu(self):
        s = self.session
        s.perform('choose_camera')
        self.step()
        self.assertTrue(s.ready)
        s.perform('recalibrate')
        s.perform('start')
        self.assertEqual(s.page, 'setup')
        s.perform('default_range')
        s.perform('start')
        self.assertEqual((s.page, s.game.state), ('play', 'running'))
        s.perform('pause')
        elapsed = s.game.elapsed
        self.step()
        self.assertEqual(s.game.elapsed, elapsed)
        s.perform('main_menu')
        self.assertEqual(s.page, 'menu')
        self.worker.stop.set.assert_called_once()
        self.factory.assert_called_once()

    def test_hidden_preview_does_not_stop_or_restart_camera(self):
        s = self.session
        s.perform('choose_camera')
        self.step()
        s.perform('toggle_preview')
        for _ in range(3):
            self.step()
        self.assertFalse(s.prefs['preview_visible'])
        self.assertIs(s.worker, self.worker)
        self.factory.assert_called_once()
        self.worker.stop.set.assert_not_called()
        self.worker.close.assert_not_called()

    def test_keyboard_restart_does_not_create_camera(self):
        s = self.session
        s.perform('choose_keyboard')
        s.game.score, s.game.best, s.game.lives = 200, 200, 0
        s.game.state = 'gameover'
        s.perform('restart')
        self.assertEqual((s.game.score, s.game.lives, s.game.state), (0, 3, 'running'))
        self.assertEqual(s.game.record_at_start, 200)
        self.factory.assert_not_called()

    def test_camera_restart_reuses_existing_worker(self):
        s = self.session
        s.perform('choose_camera')
        self.step()
        s.perform('start')
        s.game.state = 'gameover'
        s.perform('restart')
        self.step()
        self.factory.assert_called_once()
        self.assertIs(s.worker, self.worker)

    def test_settings_escape_does_not_resume_and_timers_freeze(self):
        s = self.session
        s.perform('choose_keyboard')
        self.step()
        s.game.activate_shield()
        s.game.combo_remaining = 1.4
        s.perform('settings')
        before = (s.game.elapsed, s.game.shield_remaining, s.game.combo_remaining)
        self.step()
        s.escape()
        self.assertEqual(s.page, 'play')
        self.assertEqual(s.game.state, 'paused')
        self.assertEqual(before, (s.game.elapsed, s.game.shield_remaining, s.game.combo_remaining))

    def test_resume_click_and_held_fire_cannot_leak_to_shooting(self):
        s = self.session
        s.perform('choose_keyboard')
        for _ in range(4):
            self.step(fire=True, shield=True)
        self.assertFalse(s.game.bullets)
        self.assertEqual(s.game.shield_remaining, 0)
        self.step(fire=False)
        self.step(fire=True)
        self.assertEqual(len(s.game.bullets), 1)
        s.perform('pause')
        s.perform('resume')
        self.step(fire=True)
        self.assertEqual(len(s.game.bullets), 1)

    def test_no_auto_resume_after_tracking_recovers(self):
        s = self.session
        s.perform('choose_camera')
        self.step()
        s.perform('start')
        self.worker.snapshot.side_effect = lambda: (None, 'Device disconnected')
        self.step()
        self.assertEqual(s.game.state, 'paused')
        self.worker.snapshot.side_effect = lambda: (packet(), None)
        self.step()
        self.assertEqual(s.game.state, 'paused')
        s.perform('resume')
        self.assertEqual(s.game.state, 'running')

    def test_camera_error_allows_keyboard_fallback(self):
        s = self.session
        self.factory.side_effect = RuntimeError('Camera denied')
        s.perform('choose_camera')
        self.assertIn('denied', s.error)
        s.perform('choose_keyboard')
        self.step()
        self.assertEqual(s.game.state, 'running')
        self.assertTrue(s.controller.keyboard)
        self.assertIsNone(s.error)

    def test_settings_repeated_shortcut_returns_to_origin(self):
        s = self.session
        s.perform('settings')
        s.perform('settings')
        self.assertEqual(s.page, 'menu')

    def test_pause_shortcut_cannot_resume_game_over(self):
        s = self.session
        s.perform('choose_keyboard')
        s.game.state, s.game.lives = 'gameover', 0
        s.perform('resume')
        self.assertEqual(s.game.state, 'gameover')


class UIComponentTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def render(self, page='menu', size=(1366, 768), ready=True):
        pygame.display.init()
        pygame.font.init()
        renderer = Renderer(pygame.display.set_mode(size))
        renderer.page, renderer.can_start = page, ready
        game = Game()
        if page == 'play':
            game.state = 'running'
        renderer.draw(game, None, Controls(), False, False, '', None, True, 60)
        return renderer

    def test_keyboard_focus_and_enter_select_visible_button(self):
        renderer = self.render()
        self.assertEqual(renderer.navigate(pygame.K_RETURN), 'play')
        renderer.navigate(pygame.K_TAB)
        self.assertEqual(renderer.navigate(pygame.K_RETURN), 'controls')
        renderer.navigate(pygame.K_TAB, reverse=True)
        self.assertEqual(renderer.navigate(pygame.K_RETURN), 'play')

    def test_release_requires_same_enabled_button_and_cancels_drag(self):
        r=self.render()
        play=next(b for b in r.buttons if b.action=='play')
        controls=next(b for b in r.buttons if b.action=='controls')
        r.pointer_down(play.rect.center)
        self.assertEqual(r.ui.pressed,'play')
        self.assertIsNone(r.pointer_up(controls.rect.center))
        self.assertIsNone(r.pointer_up(play.rect.center))
        r.pointer_down(play.rect.center)
        self.assertEqual(r.pointer_up(play.rect.center),'play')
        r=self.render('setup',ready=False)
        start=next(b for b in r.buttons if b.action=='start')
        r.pointer_down(start.rect.center)
        self.assertIsNone(r.pointer_up(start.rect.center))

    def test_scene_change_cancels_pending_pointer(self):
        r=self.render()
        play=next(b for b in r.buttons if b.action=='play')
        r.pointer_down(play.rect.center)
        r.page='mode'
        r.draw(Game(),None,Controls(),False,False,'',None,True,60)
        self.assertIsNone(r.ui.pressed)
        self.assertIsNone(r.pointer_up(play.rect.center))

    def test_world_projection_preserves_collision_bounds_and_center(self):
        game=Game()
        viewport=pygame.Rect(24,100,1318,478)
        for source,destination in ((game.arena.topleft,viewport.topleft),
                                   (game.arena.bottomright,viewport.bottomright),
                                   (game.arena.center,viewport.center)):
            self.assertEqual(ArenaView.project(source,game.arena,viewport),destination)

    def test_visual_preferences_and_calibration_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'settings.json'
            p=Preferences(path)
            p.values.update(reduced_motion=True,preview_visible=False,fullscreen=True,
                            range_left=.2,range_right=.75,volume=.7)
            p.save()
            self.assertFalse(p.error)
            self.assertEqual(Preferences(path).values,p.values)
    def test_disabled_start_cannot_be_clicked_or_keyboard_activated(self):
        renderer = self.render('setup', ready=False)
        button = next(b for b in renderer.buttons if b.action == 'start')
        self.assertFalse(button.enabled)
        self.assertIsNone(renderer.click(button.rect.center))
        for _ in range(len(renderer.buttons)*2):
            renderer.navigate(pygame.K_TAB)
            self.assertNotEqual(renderer.navigate(pygame.K_RETURN), 'start')

    def test_bounds_and_scaled_hit_testing_at_target_sizes(self):
        for size in ((1366,768), (1920,1080), (1066,600), (1280,1024)):
            for page in ('menu','mode','setup','settings','controls','play'):
                r = self.render(page, size)
                for b in r.buttons:
                    self.assertTrue(pygame.Rect(0,0,WIDTH,HEIGHT).contains(b.rect), (page,b.action))
                    if b.enabled:
                        scale = min(size[0]/WIDTH, size[1]/HEIGHT)
                        pos = (b.rect.centerx*scale+(size[0]-WIDTH*scale)/2,
                               b.rect.centery*scale+(size[1]-HEIGHT*scale)/2)
                        self.assertEqual(r.click(pos), b.action)

    def test_preview_region_is_outside_playfield(self):
        r = self.render('play')
        self.assertFalse(r.viewport.colliderect(pygame.Rect(24,598,192,144)))
        self.assertFalse(r.debug)

    def test_tracking_message_stabilizes_flicker_but_errors_are_immediate(self):
        status = StableMessage()
        self.assertEqual(status.update('Ready', 0.1), 'Ready')
        self.assertEqual(status.update('Searching', 0.2), 'Ready')
        self.assertEqual(status.update('Ready', 0.1), 'Ready')
        self.assertEqual(status.update('Searching', 0.2), 'Ready')
        self.assertEqual(status.update('Searching', 0.3), 'Searching')
        self.assertEqual(status.update('Camera denied', 0.01, urgent=True), 'Camera denied')

    def test_new_best_requires_beating_record_at_start(self):
        game = Game()
        game.best = 100
        game.reset()
        game.score = 100
        self.assertFalse(game.score > game.record_at_start)
        game.score = 101
        self.assertTrue(game.score > game.record_at_start)
