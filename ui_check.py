"""Repeatable native-window UI acceptance test, with synthetic camera data only.

This is intentionally separate from hardware diagnostics. It saves only rendered
synthetic screens and exercises the same event loop used by the packaged game.
"""
import json
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch
import pygame
import app
from preferences import DEFAULTS
from settings import WIDTH, HEIGHT, MIN_WINDOW


class SyntheticWorker:
    def __init__(self, *args):
        self.stop = threading.Event()
        self.thread = SimpleNamespace(is_alive=lambda: not self.stop.is_set())
        self.closed = False
        self.sequence = 0
        surface = pygame.Surface((640,480))
        surface.fill((29,42,62))
        pygame.draw.circle(surface, (75,97,121), (285,190), 77)
        pygame.draw.ellipse(surface, (61,80,104), (120,270,340,260))
        surface.blit(pygame.font.Font(None,26).render('SYNTHETIC UI TEST / NO REAL CAMERA', True, (210,225,239)), (20,20))
        self.rgb = pygame.surfarray.array3d(surface).transpose(1,0,2).copy()
        self.points = [(0.5,0.6)] * 21
        self.points[0], self.points[9], self.points[8], self.points[4] = (0.5,0.8), (0.5,0.6), (0.7,0.4), (0.1,0.5)

    def snapshot(self):
        self.sequence += 1
        return SimpleNamespace(sequence=self.sequence, captured_at=time.monotonic(), rgb=self.rgb,
                               face=[(0.32,0.24),(0.57,0.56)], hand=self.points), None

    def close(self):
        self.stop.set()
        self.closed = True
        return True


def verify(output_directory):
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    report = {'frozen': bool(getattr(sys,'frozen',False)), 'synthetic_camera_only': True,
              'success': False, 'checks': [], 'screenshots': []}
    workers = []
    paused_time = None
    def factory(*args):
        worker = SyntheticWorker()
        workers.append(worker)
        return worker
    def key(value):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=value, mod=0))
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=value, mod=0))
    def check(condition, message):
        if not condition:
            raise AssertionError(message)
        report['checks'].append(message)
    def click(renderer, action):
        button = next(b for b in renderer.buttons if b.action == action and b.enabled)
        w, h = renderer.window.get_size()
        scale = min(w/WIDTH,h/HEIGHT)
        pos = (round(button.rect.centerx*scale+(w-WIDTH*scale)/2), round(button.rect.centery*scale+(h-HEIGHT*scale)/2))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))
    def shot(renderer, name):
        path = directory / f'{name}.png'
        pygame.image.save(renderer.window, str(path))
        report['screenshots'].append(path.name)
    def exercise(frame, session, renderer):
        nonlocal paused_time
        if frame == 2:
            check(session.page == 'menu' and not workers, 'Main menu opens with camera off')
            shot(renderer,'menu')
            button=next(b for b in renderer.buttons if b.action=='play')
            w,h=renderer.window.get_size()
            scale=min(w/WIDTH,h/HEIGHT)
            pos=(round(button.rect.centerx*scale+(w-WIDTH*scale)/2),round(button.rect.centery*scale+(h-HEIGHT*scale)/2))
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))
        elif frame == 3:
            check(session.page=='menu' and renderer.ui.pressed=='play','Mouse down shows pressed state without activating')
            shot(renderer,'pressed-button')
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=(0,0)))
        elif frame == 4:
            check(session.page=='menu','Dragging outside cancels button activation')
            key(pygame.K_RETURN)
        elif frame == 5:
            check(session.page == 'mode', 'Enter activates focused Play button')
            shot(renderer,'input-mode')
            click(renderer,'choose_camera')
        elif frame == 8:
            check(session.page == 'setup' and session.ready, 'Camera setup shows current readiness')
            shot(renderer,'setup')
            click(renderer,'recalibrate')
        elif frame == 11:
            check(session.calibration is not None, 'Calibration starts on setup screen')
            shot(renderer,'calibration')
            click(renderer,'default_range')
        elif frame == 14:
            check(session.calibration is None, 'Default range cancels calibration')
            click(renderer,'start')
        elif frame == 18:
            check(session.game.state == 'running' and session.page == 'play', 'Setup Start enters gameplay')
            shot(renderer,'gameplay')
            key(pygame.K_h)
        elif frame == 22:
            check(not session.prefs['preview_visible'] and len(workers) == 1 and not workers[0].stop.is_set(), 'H hides preview while tracking stays running')
            shot(renderer,'hidden-preview')
            key(pygame.K_p)
        elif frame == 26:
            check(session.game.state == 'paused', 'P pauses gameplay')
            paused_time = session.game.elapsed
            shot(renderer,'pause')
        elif frame == 30:
            check(session.game.elapsed == paused_time, 'Simulation time freezes while paused')
            key(pygame.K_F1)
        elif frame == 34:
            check(session.page == 'settings', 'Settings opened from pause')
            shot(renderer,'settings')
            key(pygame.K_ESCAPE)
        elif frame == 38:
            check(session.page == 'play' and session.game.state == 'paused', 'Escape closes settings without resuming')
            key(pygame.K_RETURN)
        elif frame == 42:
            check(session.game.state == 'running' and not session.game.bullets, 'Enter resumes without firing')
            key(pygame.K_p)
        elif frame == 46:
            click(renderer,'main_menu')
        elif frame == 50:
            check(session.page == 'menu' and workers[0].stop.is_set(), 'Main Menu stops camera ownership')
            click(renderer,'play')
        elif frame == 54:
            click(renderer,'choose_keyboard')
        elif frame == 58:
            check(session.controller.keyboard and session.game.state == 'running', 'Keyboard-only start works')
            shot(renderer,'keyboard')
            key(pygame.K_F1)
        elif frame == 62:
            key(pygame.K_F11)
        elif frame == 66:
            check(renderer.fullscreen, 'Fullscreen toggle enters fullscreen')
            shot(renderer,'fullscreen')
            key(pygame.K_F11)
        elif frame == 70:
            check(not renderer.fullscreen, 'Fullscreen toggle restores window')
            key(pygame.K_ESCAPE)
        elif frame == 74:
            click(renderer,'resume')
        elif frame == 78:
            pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE, size=(800,450), w=800, h=450))
        elif frame == 82:
            check(renderer.window.get_width() >= MIN_WINDOW[0] and renderer.window.get_height() >= MIN_WINDOW[1], 'Minimum window size enforced')
            session.game.score = 3650
            session.game.best = 3650
            session.game.state = 'gameover'
        elif frame == 86:
            shot(renderer,'game-over')
            click(renderer,'restart')
        elif frame == 90:
            check(session.game.state == 'running' and session.game.lives == 3 and session.game.score == 0, 'Play Again resets combat')
            check(len(workers) == 1, 'No duplicate camera streams across navigation/restart')
            pygame.event.post(pygame.event.Event(pygame.QUIT))
    try:
        prefs = SimpleNamespace(values=DEFAULTS.copy(), error='', save=lambda: None)
        with patch.object(app,'create_worker',side_effect=factory), patch.object(app,'Preferences',return_value=prefs):
            result = app.run(demo=True, smoke_frames=120, score_path=directory/'unused-score.json', event_hook=exercise)
        check(result == 0 and not pygame.display.get_init(), 'Window exits cleanly')
        check(all(w.closed for w in workers), 'All camera workers closed')
        report['success'] = True
    except Exception as error:
        report['error'] = str(error)
    (directory/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return 0 if report['success'] else 1
