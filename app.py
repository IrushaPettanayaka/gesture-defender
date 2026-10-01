"""Native window/event loop. Screen transitions live in session.py; UI in ui.py."""
import logging
import os
import time
import pygame
from assets import ROOT
from audio_fx import Audio
from preferences import Preferences
from scores import ScoreStore
from session import Session
from settings import WIDTH, HEIGHT, MIN_WINDOW
from ui import Renderer


def create_worker(camera_index, low_resolution=False):
    from tracking import TrackingWorker
    worker = TrackingWorker(camera_index, low_resolution)
    worker.start()
    return worker


def run(camera_index=None, demo=True, smoke_frames=0, score_path=None, event_hook=None):
    # SDL renders in native pixels; the UI maps both drawing and hit tests.
    # https://wiki.libsdl.org/SDL2/SDL_HINT_WINDOWS_DPI_AWARENESS
    os.environ.setdefault('SDL_WINDOWS_DPI_AWARENESS', 'permonitorv2')
    pygame.display.init()
    pygame.font.init()
    session = preferences = store = None
    try:
        preferences, store = Preferences(), ScoreStore(score_path)
        prefs = preferences.values
        if camera_index is not None:
            prefs['camera_index'] = camera_index
        desktop = pygame.display.get_desktop_sizes()[0]
        scale = min(1, (desktop[0]-64)/WIDTH, (desktop[1]-100)/HEIGHT)
        windowed_size = (max(MIN_WINDOW[0], int(WIDTH*scale)), max(MIN_WINDOW[1], int(HEIGHT*scale)))
        fullscreen = prefs['fullscreen'] and not smoke_frames
        screen = pygame.display.set_mode((0, 0) if fullscreen else windowed_size,
                                          pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE)
        pygame.display.set_caption('Gesture Defender')
        icon = ROOT / 'art/game.png'
        if icon.is_file():
            pygame.display.set_icon(pygame.image.load(str(icon)))
        renderer = Renderer(screen)
        renderer.preferences = prefs
        audio = Audio() if not smoke_frames else None
        def save_best():
            if session and not smoke_frames:
                store.save(session.game.best)
        session = Session(prefs, create_worker, store.best, demo, save_best)
        clock = pygame.time.Clock()
        frames, generation = 0, -1
        logging.info('UI initialized; input=%s', 'keyboard' if demo else 'camera setup')
        while True:
            dt = clock.tick(60) / 1000
            now = time.monotonic()
            shield, quit_requested = False, False
            if event_hook:
                event_hook(frames, session, renderer)
            for event in pygame.event.get():
                action = None
                if event.type == pygame.QUIT:
                    quit_requested = True
                elif event.type == pygame.WINDOWFOCUSLOST:
                    session.game.pause('Window lost focus - resume when ready')
                    session.input_guard = True
                    renderer.ui.pressed = None
                    renderer.ui.key_pressed = False
                elif event.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED) and not fullscreen:
                    size = getattr(event, 'size', screen.get_size())
                    size = (max(MIN_WINDOW[0], size[0]), max(MIN_WINDOW[1], size[1]))
                    if screen.get_size() != size:
                        screen = pygame.display.set_mode(size, pygame.RESIZABLE)
                        renderer.window = screen
                    windowed_size = size
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    renderer.pointer_down(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    action = renderer.pointer_up(event.pos)
                elif event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                    renderer.ui.key_pressed = False
                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    active = session.page == 'play' and session.game.state == 'running'
                    if key == pygame.K_q:
                        quit_requested = True
                    elif key == pygame.K_ESCAPE:
                        session.escape()
                    elif key == pygame.K_F2:
                        renderer.debug = not renderer.debug
                    elif key in (pygame.K_TAB, pygame.K_RETURN) or (not active and key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)):
                        renderer.ui.key_pressed = key == pygame.K_RETURN
                        action = renderer.navigate(key, bool(getattr(event, 'mod', 0) & pygame.KMOD_SHIFT))
                    elif key == pygame.K_SPACE and not active:
                        action = {'menu': 'play', 'setup': 'start'}.get(session.page)
                        if session.page == 'play' and session.game.state == 'paused':
                            action = 'resume'
                    elif key in (pygame.K_s, pygame.K_LSHIFT, pygame.K_RSHIFT) and active:
                        shield = True
                    elif key == pygame.K_p and session.page == 'play':
                        action = 'pause' if active else 'resume'
                    elif key == pygame.K_r and session.page == 'play':
                        action = 'restart'
                    else:
                        action = {pygame.K_F1: 'settings', pygame.K_F11: 'fullscreen', pygame.K_k: 'switch_input',
                                  pygame.K_h: 'toggle_preview', pygame.K_m: 'mute', pygame.K_v: 'volume_up',
                                  pygame.K_e: 'reduced_motion', pygame.K_l: 'resolution',
                                  pygame.K_c: 'recalibrate', pygame.K_t: 'retry_camera',
                                  pygame.K_LEFTBRACKET: 'camera_prev', pygame.K_RIGHTBRACKET: 'camera_next',
                                  pygame.K_MINUS: 'sensitivity_down', pygame.K_EQUALS: 'sensitivity_up',
                                  pygame.K_PLUS: 'sensitivity_up'}.get(key)
                if action == 'quit':
                    quit_requested = True
                elif action == 'fullscreen':
                    fullscreen = not fullscreen
                    prefs['fullscreen'] = fullscreen
                    screen = pygame.display.set_mode((0, 0) if fullscreen else windowed_size,
                                                      pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE)
                    renderer.window = screen
                    session.input_guard = True
                else:
                    session.perform(action)
            if quit_requested:
                break
            if smoke_frames and not event_hook and demo and frames == 0:
                session.perform('choose_keyboard')
            keys = pygame.key.get_pressed()
            direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
            controls = session.update(now, dt, direction, bool(keys[pygame.K_SPACE]), shield)
            if audio:
                for name, _, _ in session.game.events:
                    audio.play(name, prefs)
            if generation != session.preview_generation:
                renderer.sequence, renderer.preview = -1, None
                generation = session.preview_generation
            renderer.page, renderer.calibration = session.page, session.calibration
            renderer.can_start, renderer.fullscreen = session.ready, fullscreen
            health = session.controller.health
            renderer.draw(session.game, session.packet, controls, health.face_ok, health.hand_ok,
                          store.error or preferences.error or session.status(), session.error,
                          session.controller.keyboard, clock.get_fps())
            frames += 1
            if smoke_frames and frames >= smoke_frames:
                break
        return 0
    finally:
        if session and store and not smoke_frames:
            store.save(session.game.best)
        if preferences and not smoke_frames:
            preferences.save()
        stopped = session.close() if session else True
        pygame.quit()
        logging.info('Application closed; workers stopped=%s', stopped)
