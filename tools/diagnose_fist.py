"""Guided open/fist geometry check: aggregate ratios only; never saves images."""
import json
import math
from pathlib import Path
import statistics
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from tracking import TrackingWorker
from gestures import GestureInterpreter, finger_geometry
from game import Game
from ui import Renderer
from settings import WIDTH, HEIGHT


def main():
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Gesture Defender - focused fist check')
    worker, gesture, game = TrackingWorker(), GestureInterpreter(), Game()
    renderer, clock = Renderer(screen), pygame.time.Clock()
    samples = {'open': [], 'fist': []}
    world_samples = {'open': [], 'fist': []}
    counts = {'fist_detected': 0, 'shield_requests': 0}
    worker.start()
    start, sequence = None, -1
    deadline = time.monotonic() + 35
    try:
        while time.monotonic() < deadline:
            clock.tick(60)
            now = time.monotonic()
            if any(e.type == pygame.QUIT for e in pygame.event.get()):
                break
            packet, error = worker.snapshot()
            if start is None and packet and packet.hand:
                start = now
            elapsed = now - start if start else 0
            if elapsed >= 20 or error:
                break
            phase = 'open' if elapsed < 5 else 'fist'
            game.state = 'setup'
            game.reason = ('OPEN PALM for 5 seconds' if phase == 'open' else 'HOLD A FIST facing the camera')
            points = packet.hand if packet else None
            controls = gesture.update(points, now)
            if packet and packet.sequence != sequence and points:
                sequence = packet.sequence
                if phase == 'open' and elapsed > 1 or phase == 'fist' and elapsed > 7:
                    def distance(a, b):
                        return math.hypot((points[a][0] - points[b][0]) * 4 / 3, points[a][1] - points[b][1])
                    palm_scale = max(distance(0, 9), 0.001)
                    ratios = [[distance(tip, 0) / max(distance(pip, 0), 0.001),
                               distance(tip, base) / max(distance(pip, base), 0.001),
                               distance(tip, base) / palm_scale]
                              for base, pip, tip in ((5,6,8),(9,10,12),(13,14,16),(17,18,20))]
                    samples[phase].append(ratios)
                    if getattr(points, 'world', None):
                        world_samples[phase].append(finger_geometry(points.world))
                counts['fist_detected'] += int(controls.fist)
                counts['shield_requests'] += int(controls.shield)
            renderer.draw(game, packet, controls, bool(packet and packet.face), bool(points),
                          f'{max(0, int(20-elapsed))}s / Fist frames {counts["fist_detected"]}', error, False, clock.get_fps())
    finally:
        counts['worker_stopped'] = worker.close()
        pygame.quit()
    report = {'counts': counts, 'metrics': ['tip_wrist_over_pip_wrist', 'tip_mcp_over_pip_mcp', 'tip_mcp_over_palm']}
    for phase, values in samples.items():
        report[phase] = {'frames': len(values), 'median_by_finger': [[round(statistics.median(v[finger][metric] for v in values), 3)
                                     for metric in range(3)] for finger in range(4)] if values else []}
        world_values = world_samples[phase]
        report[phase]['world_angle_reach'] = [[round(statistics.median(v[finger][metric] for v in world_values), 3)
                                              for metric in range(2)] for finger in range(4)] if world_values else []
    path = Path(__file__).resolve().parents[1] / 'artifacts/fist-geometry.json'
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
