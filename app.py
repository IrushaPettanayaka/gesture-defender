"""Application loop: input mode, tracking health, game state, and rendering."""
import time
import logging
import pygame
from controls import InputController
from game import Game
from scores import ScoreStore
from settings import WIDTH, HEIGHT
from ui import Renderer
from calibration import Calibration
from preferences import Preferences
from audio_fx import Audio
from assets import ROOT


def create_worker(camera_index, low_resolution=False):
    # Keyboard mode does not import OpenCV or MediaPipe.
    from tracking import TrackingWorker
    worker = TrackingWorker(camera_index, low_resolution)
    worker.start()
    return worker


def run(camera_index=None, demo=True, smoke_frames=0, score_path=None):
    pygame.display.init()
    pygame.font.init()
    worker, game, store = None, None, None
    retired = []
    preferences = None
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Gesture Defender")
        icon_path = ROOT / "art" / "game.png"
        if icon_path.is_file():
            pygame.display.set_icon(pygame.image.load(str(icon_path)))
        renderer, game = Renderer(screen), Game()
        store = ScoreStore(score_path)
        preferences = Preferences()
        prefs = preferences.values
        if camera_index is not None:
            prefs["camera_index"] = camera_index
        renderer.preferences = prefs
        audio = Audio() if not smoke_frames else None
        game.best = store.best
        controller = InputController(keyboard=demo)
        calibration = None
        pending_camera = False
        if not demo:
            game.state = 'setup'
        startup_error = None
        if not demo:
            try:
                worker = create_worker(prefs["camera_index"], prefs["low_resolution"])
            except Exception as error:
                startup_error = str(error)
        clock = pygame.time.Clock()
        logging.info('UI initialized; input=%s camera=%s', 'keyboard' if demo else 'webcam', prefs['camera_index'])
        frames = 0
        started = time.monotonic()

        def save_best():
            if not smoke_frames:
                store.save(game.best)

        while True:
            dt = clock.tick(60) / 1000
            now = time.monotonic()
            packet, error = worker.snapshot() if worker else (None, startup_error)
            if pending_camera and not any(w.thread.is_alive() for w in retired):
                retired.clear()
                pending_camera = False
                startup_error = None
                try:
                    worker = create_worker(prefs['camera_index'], prefs['low_resolution'])
                except Exception as failure:
                    startup_error = str(failure)
                    logging.exception('Camera restart failed')
                packet, error = None, startup_error
            quit_requested, toggle, start, restart, change_mode = False, False, False, False, False
            retry_camera, shield_key = False, False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_requested = True
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    key = event.key if event.type == pygame.KEYDOWN else renderer.click(event.pos)
                    if key == pygame.K_q:
                        quit_requested = True
                    elif key == pygame.K_ESCAPE:
                        game.pause("Paused - choose resume or quit")
                        renderer.menu_open = not renderer.menu_open
                        renderer.settings_open = False
                    elif key == pygame.K_F1:
                        game.pause("Settings")
                        renderer.settings_open = not renderer.settings_open
                        renderer.menu_open = False
                    elif key == pygame.K_m:
                        prefs["muted"] = not prefs["muted"]
                    elif key == pygame.K_v:
                        prefs["volume"] = round((prefs["volume"] + 0.2) % 1.01, 1)
                    elif key == pygame.K_e:
                        prefs["reduced_motion"] = not prefs["reduced_motion"]
                    elif key == pygame.K_l:
                        prefs["low_resolution"] = not prefs["low_resolution"]
                        retry_camera = not controller.keyboard
                    elif key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
                        prefs["camera_index"] = max(0, min(9, prefs["camera_index"] + (1 if key == pygame.K_RIGHTBRACKET else -1)))
                        retry_camera = not controller.keyboard
                    elif key in (pygame.K_MINUS, pygame.K_EQUALS, pygame.K_PLUS):
                        prefs["sensitivity"] = round(max(0.5, min(2, prefs["sensitivity"] + (-0.1 if key == pygame.K_MINUS else 0.1))), 1)
                    elif key == pygame.K_c and not controller.keyboard:
                        calibration = Calibration()
                        game.state = "setup"
                        renderer.settings_open = renderer.menu_open = False
                    elif key == pygame.K_RETURN and game.state in ("calibrating", "setup"):
                        prefs["range_left"], prefs["range_right"] = 0.08, 0.92
                        game.state, game.reason = "setup", "Default range selected - Start when tracking is ready"
                        calibration = None
                    elif key in (pygame.K_s, pygame.K_LSHIFT, pygame.K_RSHIFT):
                        shield_key = True
                    elif key == pygame.K_t and not controller.keyboard:
                        retry_camera = True
                    elif key == pygame.K_p:
                        toggle = True
                    elif key == pygame.K_SPACE:
                        start = game.state in ("ready", "paused", "setup")
                    elif key == pygame.K_r:
                        restart = True
                    elif key in (pygame.K_k, pygame.K_TAB):
                        change_mode = True
                elif event.type == pygame.WINDOWFOCUSLOST:
                    game.pause("Window lost focus")
            if quit_requested:
                break
            if change_mode:
                game.pause("Input mode changed - press Space to resume")
                if game.state in ("calibrating", "setup"):
                    game.state, game.reason = "paused", "Input mode changed"
                calibration = None
                renderer.menu_open = renderer.settings_open = False
                keyboard = not controller.keyboard
                if worker:
                    worker.stop.set()
                    retired.append(worker)
                    worker = None
                controller = InputController(keyboard=keyboard, x=controller.x)
                pending_camera = False
                startup_error = None
                renderer.sequence = -1
                if not keyboard:
                    game.state, game.reason = 'setup', ''
                    if any(w.thread.is_alive() for w in retired):
                        pending_camera = True
                    else:
                        try:
                            worker = create_worker(prefs["camera_index"], prefs["low_resolution"])
                        except Exception as failure:
                            startup_error = str(failure)
                packet, error = None, startup_error
                started = now
                start = toggle = False
            if retry_camera:
                game.state, game.reason = 'setup', 'Switching camera...'
                calibration = None
                if worker:
                    worker.stop.set()
                    retired.append(worker)
                    worker = None
                pending_camera = True
                controller = InputController(keyboard=False, x=controller.x)
                renderer.sequence = -1
                packet, error, startup_error = None, None, None
                renderer.menu_open = renderer.settings_open = False
                started = now
            if restart:
                save_best()
                game.reset()
                if not controller.keyboard:
                    game.state = 'setup'
                controller = InputController(keyboard=controller.keyboard)
                controller.gestures.pinching = controller.gestures.palm_latched = True
                controller.gestures.blocked_until_release = True
                controller.gestures.fist_latched = True
                calibration = None
                renderer.menu_open = renderer.settings_open = False
                start = toggle = False

            keys = pygame.key.get_pressed()
            controller.gestures.range_left = prefs["range_left"]
            controller.gestures.range_right = prefs["range_right"]
            controller.gestures.sensitivity = prefs["sensitivity"]
            direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
            controls = controller.update(packet, error, now, dt, direction,
                                         fire=bool(keys[pygame.K_SPACE] and game.state == "running"),
                                         shield=shield_key)
            health = controller.health
            can_start = controller.keyboard or health.ready
            if smoke_frames and controller.keyboard and frames == 0:
                start = True
            if (toggle or start or controls.toggle) and not restart and calibration is None:
                if game.state == "ready" and not controller.keyboard and can_start:
                    game.state = "setup"
                else:
                    game.toggle(can_start)
                renderer.menu_open = renderer.settings_open = False
                controls.shoot = False
            if game.state in ("calibrating", "setup") and calibration and not renderer.menu_open and not renderer.settings_open:
                x = packet.hand[8][0] if health.ready else None
                result = calibration.update(x, dt)
                if result:
                    prefs["range_left"], prefs["range_right"] = result
                    game.state, game.reason = "setup", "Calibrated - press Start to launch"
                    calibration = None
                    controller.gestures.pinching = controller.gestures.palm_latched = True
                    controller.gestures.blocked_until_release = True
            previous_state = game.state
            game.update(dt, controls.x, controls.shoot,
                        controller.keyboard or health.can_continue, health.reason, shield=controls.shield)
            if game.state == "gameover" and previous_state != "gameover":
                save_best()
            if audio:
                for name, _, _ in game.events:
                    audio.play(name, prefs)

            if controller.keyboard:
                status = "Camera off. Keyboard controls active."
            elif error:
                status = "Tracking unavailable. K: keyboard mode."
            elif not packet:
                status = "Loading local models and opening camera..."
                if now - started > 15:
                    status = "Camera startup delayed. K: keyboard mode."
            elif not health.ready:
                status = health.reason
            elif controls.fist:
                status = "Fist: shield hold / palm-center steering"
            elif controls.pinching:
                status = "Pinch held: firing. Release to stop."
            else:
                status = controller.feedback
            if store.error:
                status = store.error
            renderer.calibration = calibration
            renderer.draw(game, packet, controls, health.face_ok, health.hand_ok, status,
                          error, controller.keyboard, clock.get_fps())
            frames += 1
            if smoke_frames and frames >= smoke_frames:
                break
        return 0
    finally:
        if game is not None and store is not None and not smoke_frames:
            store.save(game.best)
        if preferences is not None and not smoke_frames:
            preferences.save()
        if worker:
            worker.close()
        for old_worker in retired:
            old_worker.close()
        pygame.quit()
        logging.info('Application closed; workers stopped=%s', all(not w.thread.is_alive() for w in retired + ([worker] if worker else [])))
