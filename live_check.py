"""Opt-in real-camera control check; stores counts and ranges, never images."""
import json
from pathlib import Path
import sys
import time
import pygame
from controls import InputController
from game import Game
from preferences import Preferences
from settings import WIDTH, HEIGHT
from tracking import TrackingWorker
from ui import Renderer


def verify(output_path, seconds=30, camera_index=0):
    report = {'frozen': bool(getattr(sys, 'frozen', False)), 'frames': 0,
              'face_frames': 0, 'hand_frames': 0, 'shots': 0, 'palm_transitions': 0,
              'shields': 0, 'tracking_pauses': 0, 'controls_verified': False,
              'fist_frames': 0, 'max_fist_hold_progress': 0,
              'shield_requests': 0, 'shield_requests_while_paused': 0}
    positions = []
    pygame.display.init()
    pygame.font.init()
    worker = TrackingWorker(camera_index)
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Gesture Defender - real webcam verification')
        renderer, controller, game = Renderer(screen), InputController(), Game()
        renderer.setup_prompt = 'Press Space or Start Game to begin the 30-second check. Test fist first.'
        prefs = Preferences().values
        renderer.preferences = prefs
        controller.gestures.range_left = prefs['range_left']
        controller.gestures.range_right = prefs['range_right']
        controller.gestures.sensitivity = prefs['sensitivity']
        worker.start()
        deadline = None
        waiting_deadline = time.monotonic() + 120
        clock, sequence = pygame.time.Clock(), -1
        while time.monotonic() < (deadline if deadline is not None else waiting_deadline):
            dt = clock.tick(60) / 1000
            now = time.monotonic()
            events = pygame.event.get()
            if any(e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE)
                   for e in events):
                break
            packet, error = worker.snapshot()
            controls = controller.update(packet, error, now, dt)
            space_pressed = any(e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE for e in events)
            space_pressed = space_pressed or any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
                                                and renderer.click(e.pos) == 'start' for e in events)
            if deadline is None:
                if space_pressed and controller.health.ready:
                    deadline = now + max(5, min(60, seconds))
                    game.state = 'running'
                    # A visible released hand is required before the next action.
                    controller.gestures.fist_latched = False
                    controls.shoot = controls.toggle = controls.shield = False
                    space_pressed = False
                else:
                    game.state = 'setup'
                    game.reason = 'Press Space when face + hand are in view'
                    renderer.draw(game, packet, controls, controller.health.face_ok, controller.health.hand_ok,
                                  'Ready check: Space starts the timer. Test fist first, then move, pinch and palm.',
                                  error, False, clock.get_fps())
                    if error:
                        report['error'] = error
                        break
                    continue
            if packet and packet.sequence != sequence:
                sequence = packet.sequence
                report['frames'] += 1
                report['face_frames'] += int(packet.face is not None)
                report['hand_frames'] += int(packet.hand is not None)
                if controller.health.ready:
                    positions.append(controls.x)
                    report['fist_frames'] += int(controls.fist)
                    report['max_fist_hold_progress'] = round(max(report['max_fist_hold_progress'], controls.fist_progress), 3)
            if game.state == 'ready' and controller.health.ready:
                game.toggle(True)
            if controls.toggle:
                before = game.state
                game.toggle(controller.health.ready)
                report['palm_transitions'] += int(before != game.state)
            if space_pressed:
                game.toggle(controller.health.ready)
            if controls.shield:
                report['shield_requests'] += 1
                report['shield_requests_while_paused'] += int(game.state != 'running')
            game.spawn_timer = 10000
            before = game.state
            game.update(dt, controls.x, controls.shoot, controller.health.can_continue,
                        controller.health.reason, shield=controls.shield)
            report['tracking_pauses'] += int(before == 'running' and game.state == 'paused')
            report['shots'] += sum(e[0] == 'shot' for e in game.events)
            report['shields'] += sum(e[0] == 'shield' for e in game.events)
            status = f"{int(deadline - now)}s / Shots {report['shots']} / Palms {report['palm_transitions']} / Shields {report['shields']}"
            renderer.draw(game, packet, controls, controller.health.face_ok, controller.health.hand_ok,
                          status, error, False, clock.get_fps())
            if error:
                report['error'] = error
                break
        span = max(positions) - min(positions) if positions else 0
        report['normalized_movement_span'] = round(span, 3)
        report['movement_verified'] = span > 0.2
        report['pinch_verified'] = report['shots'] > 0
        report['palm_verified'] = report['palm_transitions'] >= 2
        report['fist_verified'] = report['shields'] > 0
        report['controls_verified'] = all(report[k] for k in
                                          ('movement_verified', 'pinch_verified', 'palm_verified', 'fist_verified'))
        report['note'] = 'Counts only count actual webcam-driven game actions. No synthetic landmarks supplied.'
    except Exception as error:
        report['error'] = str(error)
    finally:
        report['worker_stopped'] = worker.close()
        pygame.quit()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return 0 if report['controls_verified'] else 2
