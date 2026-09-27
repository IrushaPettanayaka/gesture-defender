"""Render deterministic UI review images using only synthetic data; no camera."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from game import Body, Game
from gestures import Controls
from settings import WIDTH, HEIGHT
from ui import Renderer
from calibration import Calibration


def main():
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    renderer = Renderer(screen)
    destination = Path(__file__).resolve().parents[1] / 'artifacts'
    destination.mkdir(exist_ok=True)
    try:
        for scene in ('setup', 'error', 'enemies', 'boss', 'fan'):
            game = Game(seed=5)
            game.state = 'setup' if scene in ('setup', 'error') else 'running'
            renderer.calibration = Calibration() if scene == 'setup' else None
            if scene == 'enemies':
                game.obstacles = [Body(190, 320, 100, 38), Body(360, 400, 65, 46, 'armored', 2, 3),
                                  Body(580, 260, 150, 28, 'zigzag')]
                game.shield_remaining = 1.5
                game.combo_hits, game.combo_remaining = 7, 1.6
            if scene in ('boss', 'fan'):
                game.wave = 5
                game.start_boss()
                game.attack_index = 1 if scene == 'fan' else 0
                game.boss_timer = 0
                game._update_boss(0.01)
            error = 'Camera access denied or device disconnected. Check permissions and choose another camera.' if scene == 'error' else None
            renderer.draw(game, None, Controls(), False, False,
                          'Synthetic preview / no camera used', error, False, 60)
            pygame.image.save(screen, str(destination / f'ui-{scene}.png'))
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
