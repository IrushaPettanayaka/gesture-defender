"""Procedural depth, ship shading and short impact effects."""
import math
import random
import pygame


class Effects:
    def __init__(self):
        self.particles = []
        self.random = random.Random(19)
        self.bank = 0.0
        self.previous_x = None

    def update(self, game, dt, reduced):
        if game.state in ('ready', 'setup') and game.elapsed == 0:
            self.particles.clear()
            self.previous_x = None
            self.bank = 0
        target = 0 if self.previous_x is None else max(-0.35, min(0.35, (game.player_x - self.previous_x) * 0.025))
        self.previous_x = game.player_x
        self.bank += (target - self.bank) * min(1, dt * 12)
        if reduced:
            self.particles.clear()
            self.bank = 0
            return
        for name, x, y in game.events:
            if name not in ("hit", "destroy", "enemy_hit"):
                continue
            for _ in range(6 if name == "enemy_hit" else 20):
                angle, speed = self.random.random() * math.tau, self.random.uniform(35, 170)
                self.particles.append([x, y, math.cos(angle) * speed, math.sin(angle) * speed, 0.5,
                                       (255, 140, 115) if name == "destroy" else (87, 235, 223)])
        self.particles = self.particles[-160:]
        if game.state == "running":
            for p in self.particles:
                p[0] += p[2] * dt
                p[1] += p[3] * dt
                p[4] -= dt
            self.particles = [p for p in self.particles if p[4] > 0]

    def draw_particles(self, screen):
        for x, y, _, _, life, color in self.particles:
            pygame.draw.circle(screen, color, (int(x), int(y)), max(1, int(life * 6)))

    def ship(self, screen, player, elapsed, reduced):
        cx, cy = player.centerx, player.centery
        def point(x, y):
            return (cx + x * math.cos(self.bank) - y * math.sin(self.bank),
                    cy + x * math.sin(self.bank) + y * math.cos(self.bank))
        glow = pygame.Surface((100, 100), pygame.SRCALPHA)
        for radius, alpha in ((42, 8), (32, 12), (23, 16)):
            pygame.draw.circle(glow, (50, 230, 220, alpha), (50, 50), radius)
        screen.blit(glow, (cx - 50, cy - 50))
        flame = 20 if reduced else 23 + 8 * math.sin(elapsed * 31)
        pygame.draw.polygon(screen, (35, 110, 148), [point(-7, 17), point(0, 17 + flame), point(7, 17)])
        pygame.draw.polygon(screen, (155, 255, 240), [point(-3, 17), point(0, 27), point(3, 17)])
        pygame.draw.polygon(screen, (26, 98, 116), [point(0, -23), point(-25, 21), point(-5, 14)])
        pygame.draw.polygon(screen, (70, 197, 202), [point(0, -23), point(25, 21), point(5, 14)])
        pygame.draw.polygon(screen, (145, 248, 235), [point(0, -23), point(-5, 14), point(0, 19), point(5, 14)])
        pygame.draw.polygon(screen, (16, 54, 78), [point(0, -10), point(-3, 5), point(3, 5)])
        pygame.draw.aalines(screen, (166, 255, 244), False, [point(-25, 21), point(0, -23), point(25, 21)])
