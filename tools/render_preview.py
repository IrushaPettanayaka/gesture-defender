"""Synthetic-only UI gallery at target window sizes. Never opens a camera."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
from pathlib import Path
import sys
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from game import Body, Game
from gestures import Controls
from settings import WIDTH, HEIGHT
from ui import Renderer
from calibration import Calibration


def synthetic_packet():
    image = pygame.Surface((640, 480))
    image.fill((29, 42, 62))
    pygame.draw.circle(image, (75, 97, 121), (285, 190), 77)
    pygame.draw.ellipse(image, (61, 80, 104), (120, 270, 340, 260))
    font = pygame.font.Font(None, 26)
    image.blit(font.render('SIMULATED PREVIEW / NO CAMERA IMAGE', True, (210, 225, 239)), (24, 22))
    points = [(0.8, 0.65)] * 21
    points[8] = (0.77, 0.37)
    rgb = pygame.surfarray.array3d(image).transpose(1, 0, 2).copy()
    return SimpleNamespace(sequence=1, rgb=rgb, face=[(0.32, 0.24), (0.57, 0.56)], hand=points)


def render_gallery(directory=None, sizes=None):
    pygame.display.init()
    pygame.font.init()
    destination = Path(directory) if directory else Path(__file__).resolve().parents[1] / 'artifacts/ui-1.3'
    destination.mkdir(parents=True, exist_ok=True)
    screens = ('menu', 'mode', 'setup', 'loading', 'error', 'calibration', 'play', 'keyboard', 'hidden', 'paused', 'gameover', 'settings', 'controls', 'boss')
    try:
        for size in sizes or ((1366, 768), (1920, 1080), (1066, 600)):
            renderer = Renderer(pygame.display.set_mode(size))
            renderer.preferences['reduced_motion'] = True
            packet = synthetic_packet()
            for scene in screens:
                game = Game(seed=5)
                game.state = 'running'
                game.best, game.score, game.record_at_start = 2800, 3650, 2800
                game.best = max(game.best, game.score)
                game.wave = 3
                game.obstacles = [Body(190, 320, 100, 38), Body(360, 400, 65, 46, 'armored', 2, 3), Body(580, 260, 150, 28, 'zigzag')]
                game.shield_remaining = 1.5
                game.combo_hits, game.combo_remaining = 7, 1.6
                renderer.page = scene if scene in ('menu','mode','settings','controls') else 'setup' if scene in ('setup','loading','error','calibration') else 'play'
                renderer.can_start = scene not in ('error', 'loading')
                renderer.calibration = Calibration() if scene == 'calibration' else None
                renderer.preferences['preview_visible'] = scene != 'hidden'
                if scene == 'paused':
                    game.state, game.reason = 'paused', 'Hand lost - return to view'
                    renderer.can_start = False
                if scene == 'gameover':
                    game.state = 'gameover'
                if scene == 'boss':
                    game.wave = 5
                    game.start_boss()
                    game.boss_timer = 0
                    game._update_boss(0.01)
                error = 'Could not open camera 0. Check Windows camera permission, the privacy shutter, and other camera apps.' if scene == 'error' else None
                use_packet = None if scene in ('loading','error','keyboard') else packet
                controls = Controls(x=0.68, fist=scene=='play', fist_progress=0.7)
                renderer.draw(game, use_packet, controls, bool(use_packet), bool(use_packet), 'Loading models and opening camera...' if scene=='loading' else 'Tracking ready', error, scene=='keyboard', 60)
                pygame.image.save(renderer.window, str(destination / f'{scene}-{size[0]}x{size[1]}.png'))
    finally:
        pygame.quit()


if __name__ == '__main__':
    render_gallery()
