"""Deterministic arcade simulation: shields, enemy types, combos and bosses."""
from dataclasses import dataclass
import math
import random
import pygame
from settings import ARENA


@dataclass
class Body:
    x: float
    y: float
    speed: float
    size: int
    kind: str = 'normal'
    hp: int = 1
    max_hp: int = 1
    age: float = 0.0
    origin_x: float | None = None
    vx: float = 0.0
    hit_flash: float = 0.0

    def rect(self):
        height = 68 if self.kind == 'boss' else self.size
        return pygame.Rect(round(self.x - self.size / 2), round(self.y - height / 2), self.size, height)


class Game:
    def __init__(self, seed=None):
        self.random = random.Random(seed)
        self.arena = pygame.Rect(ARENA)
        self.best = 0
        self.reset()

    def reset(self):
        self.record_at_start = self.best
        self.state, self.reason = 'ready', ''
        self.score, self.lives = 0, 3
        self.elapsed, self.wave_time = 0.0, 0.0
        self.spawn_timer, self.shot_timer, self.invulnerable = 0.65, 0.0, 0.0
        self.obstacles, self.bullets, self.hostile_bullets = [], [], []
        self.player_x = float(self.arena.centerx)
        self.events, self.wave = [], 1
        self.shield_remaining, self.shield_cooldown = 0.0, 0.0
        self.combo_hits, self.combo_remaining = 0, 0.0
        self.boss = None
        self.boss_phase, self.boss_timer, self.attack_index = 'rest', 1.2, 0
        self.warning_lanes, self.fan_paths = [], []
        self.defeated_boss_waves = set()

    @property
    def player(self):
        return pygame.Rect(round(self.player_x) - 20, self.arena.bottom - 58, 40, 32)

    @property
    def multiplier(self):
        return min(4, 1 + self.combo_hits // 5)

    def pause(self, reason):
        if self.state == 'running':
            self.state, self.reason = 'paused', reason

    def toggle(self, tracking_ready):
        if self.state == 'running':
            self.state, self.reason = 'paused', 'Paused by you'
        elif tracking_ready and self.state in ('ready', 'paused', 'setup'):
            self.state, self.reason = 'running', ''

    def activate_shield(self):
        if self.state == 'running' and self.shield_remaining <= 0 and self.shield_cooldown <= 0:
            self.shield_remaining = 2.0
            self.events.append(('shield', self.player_x, self.player.centery))
            return True
        return False

    def damage(self):
        if self.shield_remaining > 0 or self.invulnerable > 0:
            return
        self.lives -= 1
        self.invulnerable = 1.2
        self.combo_hits, self.combo_remaining = 0, 0.0
        self.events.append(('hit', self.player_x, self.player.centery))
        if self.lives <= 0:
            self.state = 'gameover'

    def advance_wave(self):
        self.wave += 1
        self.wave_time = 0.0
        self.spawn_timer = 1.2
        self.events.append(('wave', self.arena.centerx, self.arena.centery))

    def start_boss(self):
        health = min(60, 20 + (self.wave // 5 - 1) * 8)
        self.boss = Body(self.arena.centerx, self.arena.top + 95, 0, 120, 'boss', health, health)
        self.obstacles.clear()
        self.hostile_bullets.clear()
        self.boss_phase, self.boss_timer, self.attack_index = 'rest', 1.5, 0
        self.warning_lanes, self.fan_paths = [], []

    def spawn_enemy(self):
        kinds = ['normal'] * 5
        if self.wave >= 2:
            kinds += ['armored'] * 2
        if self.wave >= 3:
            kinds += ['zigzag'] * 3
        kind = self.random.choice(kinds)
        speed = min(250, 105 + self.elapsed * 2.5)
        size, health = (46, 3) if kind == 'armored' else (28, 1) if kind == 'zigzag' else (self.random.randint(26, 42), 1)
        speed = speed * 0.65 if kind == 'armored' else min(320, speed * 1.25) if kind == 'zigzag' else speed
        margin = 95 if kind == 'zigzag' else size / 2 + 8
        x = self.random.uniform(self.arena.left + margin, self.arena.right - margin)
        # Avoid dense entry clusters; defer instead of stacking unavoidable walls.
        if any(e.y < self.arena.top + 70 and abs(e.x - x) < 85 for e in self.obstacles):
            return
        self.obstacles.append(Body(x, self.arena.top - 30, speed, size, kind, health, health, origin_x=x))

    def hit_enemy(self, enemy):
        if enemy.hp <= 0:
            return
        enemy.hp -= 1
        enemy.hit_flash = 0.14
        self.combo_hits += 1
        self.combo_remaining = 2.0
        self.events.append(('enemy_hit', enemy.x, enemy.y))
        if enemy.hp > 0:
            return
        points = {'normal': 25, 'armored': 75, 'zigzag': 40, 'boss': 500}[enemy.kind]
        self.score += points * self.multiplier
        self.events.append(('destroy', enemy.x, enemy.y))
        if enemy is self.boss:
            self.defeated_boss_waves.add(self.wave)
            self.boss = None
            self.hostile_bullets.clear()
            self.warning_lanes, self.fan_paths = [], []
            self.advance_wave()
        elif enemy in self.obstacles:
            self.obstacles.remove(enemy)
        self.best = max(self.best, self.score)

    def update(self, dt, x, shoot, face_present, loss_reason='Face lost - return to the camera', shield=False):
        self.events.clear()
        if self.state == 'running' and not face_present:
            self.pause(loss_reason)
        if self.state != 'running':
            return
        if shield:
            self.activate_shield()
        remaining = max(0.0, min(dt, 0.25))
        while remaining > 0 and self.state == 'running':
            step = min(remaining, 1 / 120)
            self._step(step, x, shoot)
            remaining -= step
            shoot = False

    def _step(self, dt, x, shoot):
        self.elapsed += dt
        self.player_x = self.arena.left + 24 + max(0.0, min(1.0, x)) * (self.arena.width - 48)
        self.shot_timer = max(0, self.shot_timer - dt)
        self.invulnerable = max(0, self.invulnerable - dt)
        if self.shield_remaining > 0:
            remaining = self.shield_remaining - dt
            self.shield_remaining = max(0, remaining)
            if remaining <= 0:
                self.shield_cooldown = max(0, 8.0 + remaining)
        else:
            self.shield_cooldown = max(0, self.shield_cooldown - dt)
        self.combo_remaining = max(0, self.combo_remaining - dt)
        if self.combo_remaining <= 0:
            self.combo_hits = 0
        if shoot and self.shot_timer <= 0:
            self.bullets.append(Body(self.player_x, self.player.top, -620, 8))
            self.shot_timer = 0.23
            self.events.append(('shot', self.player_x, self.player.top))

        if self.wave % 5 == 0 and self.boss is None and self.wave not in self.defeated_boss_waves:
            self.start_boss()
        if self.boss:
            self._update_boss(dt)
        else:
            self.wave_time += dt
            if self.wave_time >= 20:
                self.advance_wave()
                if self.wave % 5 == 0:
                    self.start_boss()
            if not self.boss:
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    self.spawn_enemy()
                    self.spawn_timer = max(0.28, 0.95 - self.elapsed * 0.009)

        for bullet in self.bullets[:]:
            bullet.y += bullet.speed * dt
            if bullet.y < self.arena.top:
                self.bullets.remove(bullet)
        targets = list(self.obstacles) + ([self.boss] if self.boss else [])
        for enemy in targets:
            enemy.hit_flash = max(0, enemy.hit_flash - dt)
            if enemy is not self.boss:
                enemy.age += dt
                enemy.y += enemy.speed * dt
                if enemy.kind == 'zigzag':
                    if enemy.origin_x is None:
                        enemy.origin_x = enemy.x
                    enemy.x = max(self.arena.left + 18, min(self.arena.right - 18,
                                  enemy.origin_x + math.sin(enemy.age * 2.8) * 65))
            for bullet in self.bullets[:]:
                if enemy.hp > 0 and bullet.rect().colliderect(enemy.rect()):
                    self.bullets.remove(bullet)
                    self.hit_enemy(enemy)
            if enemy.hp <= 0 or enemy.kind == 'boss':
                continue
            if enemy.rect().colliderect(self.player):
                self.obstacles.remove(enemy)
                self.damage()
            elif enemy.y - enemy.size / 2 > self.arena.bottom:
                self.obstacles.remove(enemy)
                self.score += 10
        for bullet in self.hostile_bullets[:]:
            bullet.x += bullet.vx * dt
            bullet.y += bullet.speed * dt
            if bullet.rect().colliderect(self.player):
                self.hostile_bullets.remove(bullet)
                self.damage()
            elif bullet.y > self.arena.bottom + 20 or not self.arena.left - 30 < bullet.x < self.arena.right + 30:
                self.hostile_bullets.remove(bullet)
        self.best = max(self.best, self.score)

    def _update_boss(self, dt):
        boss = self.boss
        boss.age += dt
        boss.x = self.arena.centerx + math.sin(boss.age * 0.65) * 160
        self.boss_timer -= dt
        if self.boss_phase == 'active' and self.attack_index % 2 == 0:
            if any(pygame.Rect(x - 28, self.arena.top, 56, self.arena.height).colliderect(self.player) for x in self.warning_lanes):
                self.damage()
        if self.boss_timer > 0:
            return
        if self.boss_phase == 'rest':
            self.boss_phase, self.boss_timer = 'warning', 1.2
            if self.attack_index % 2 == 0:
                center = max(self.arena.left + 220, min(self.arena.right - 220, self.player_x))
                self.warning_lanes = [center - 190, center, center + 190]
                self.fan_paths = []
            else:
                self.warning_lanes = []
                self.fan_paths = [(boss.x, boss.y + 35, vx, 165) for vx in (-110, -55, 0, 55, 110)]
        elif self.boss_phase == 'warning':
            self.boss_phase, self.boss_timer = 'active', 0.45
            if self.attack_index % 2:
                for x, y, vx, speed in self.fan_paths:
                    self.hostile_bullets.append(Body(x, y, speed, 14, 'hostile', vx=vx))
                self.fan_paths = []
        else:
            self.attack_index += 1
            self.boss_phase, self.boss_timer = 'rest', 1.5
            self.warning_lanes, self.fan_paths = [], []
