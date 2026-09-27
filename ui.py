"""Pygame rendering; images remain in memory."""
import math
import pygame
from hand_tracking import CONNECTIONS
from settings import WIDTH, HEIGHT
from effects import Effects
from preferences import DEFAULTS

BG, INK, MUTED = (9, 15, 28), (229, 240, 249), (139, 158, 182)
CYAN, GOLD, RED = (84, 231, 215), (255, 202, 112), (255, 106, 130)


class Renderer:
    def __init__(self, screen):
        self.window = screen
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        self.fonts = {s: pygame.font.Font(None, s) for s in (20, 23, 28, 36, 58)}
        self.preview = None
        self.sequence = -1
        self.effects = Effects()
        self.preferences = DEFAULTS.copy()
        self.settings_open = False
        self.menu_open = False
        self.calibration = None
        self.buttons = []
        self.last_tick = pygame.time.get_ticks()

    def click(self, position):
        w, h = self.window.get_size()
        scale = min(w / WIDTH, h / HEIGHT)
        x = (position[0] - (w - WIDTH * scale) / 2) / scale
        y = (position[1] - (h - HEIGHT * scale) / 2) / scale
        return next((key for rect, key in self.buttons if rect.collidepoint(x, y)), None)

    def button(self, label, rect, key):
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.screen, (22, 55, 70), rect, border_radius=8)
        pygame.draw.rect(self.screen, (51, 121, 131), rect, 1, border_radius=8)
        self.text(label, (rect.x + 15, rect.y + 13), 23, CYAN)
        self.buttons.append((rect, key))

    def text(self, value, pos, size=23, color=INK):
        self.screen.blit(self.fonts[size].render(str(value), True, color), pos)

    def wrapped(self, value, x, y, width, color=MUTED):
        line = ""
        for word in value.split():
            candidate = f"{line} {word}".strip()
            if self.fonts[20].size(candidate)[0] > width and line:
                self.text(line, (x, y), 20, color)
                y += 21
                line = word
            else:
                line = candidate
        self.text(line, (x, y), 20, color)
        return y + 25

    def draw(self, game, packet, controls, face_ok, hand_ok, status, error, demo, fps):
        self.buttons.clear()
        ticks = pygame.time.get_ticks()
        dt = min(0.1, max(0.001, (ticks - self.last_tick) / 1000))
        self.last_tick = ticks
        reduced = self.preferences["reduced_motion"]
        self.effects.update(game, dt, reduced)
        screen = self.screen
        screen.fill(BG)
        self.text("GESTURE DEFENDER", (24, 22), 36)
        self.text("Dodge the fall. Pinch to fire.", (25, 64), 23, MUTED)
        self.text(f"SCORE  {game.score:05d}", (425, 28), 28, CYAN)
        self.text(f"BEST  {game.best:05d}", (425, 62), 20, MUTED)
        self.text(f"LIVES  {'| ' * game.lives}", (620, 28), 28, RED)
        arena = game.arena
        pygame.draw.rect(screen, (14, 24, 41), arena, border_radius=18)
        screen.set_clip(arena)
        for offset in range(0, arena.height, 30):
            color = (14, 24 + int(offset / arena.height * 7), 41 + int(offset / arena.height * 13))
            pygame.draw.rect(screen, color, (arena.x, arena.y + offset, arena.width, 30))
        for x in range(arena.left - 200, arena.right + 201, 100):
            pygame.draw.line(screen, (22, 43, 61), (arena.centerx, arena.top + 60), (x, arena.bottom))
        for i in range(60):
            x = arena.x + (i * 137 + 31) % arena.width
            y = arena.y + (i * 73 + (0 if reduced else game.elapsed) * (10 + i % 4 * 5)) % arena.height
            pygame.draw.circle(screen, (37, 62, 83), (int(x), int(y)), 1 + i % 2)
        for bullet in game.bullets:
            pygame.draw.line(screen, (31, 117, 128), (bullet.x, bullet.y + 28), (bullet.x, bullet.y), 4)
            pygame.draw.rect(screen, CYAN, bullet.rect().inflate(-2, 13), border_radius=3)
        for rock in game.obstacles:
            r = rock.size / 2
            color = (231, 197, 112) if rock.kind == 'armored' else (217, 133, 255) if rock.kind == 'zigzag' else RED
            if rock.hit_flash > 0:
                color = INK
            if rock.kind == 'armored':
                rect = rock.rect()
                pygame.draw.rect(screen, (74, 65, 50), rect, border_radius=7)
                pygame.draw.rect(screen, color, rect, 3, border_radius=7)
                pygame.draw.rect(screen, color, rect.inflate(-14, -14), 2)
                self.text(str(rock.hp), (rock.x - 5, rock.y - 6), 20, color)
                continue
            if rock.kind == 'zigzag':
                vertices = [(rock.x, rock.y - r), (rock.x + r, rock.y), (rock.x, rock.y + r), (rock.x - r, rock.y)]
                pygame.draw.polygon(screen, (57, 36, 82), vertices)
                pygame.draw.polygon(screen, color, vertices, 2)
                pygame.draw.line(screen, color, (rock.x - 7, rock.y), (rock.x + 7, rock.y), 2)
                continue
            vertices = [(rock.x + math.cos(i * math.tau / 7 + game.elapsed) * r,
                         rock.y + math.sin(i * math.tau / 7 + game.elapsed) * r) for i in range(7)]
            pygame.draw.polygon(screen, (93, 49, 71), vertices)
            pygame.draw.polygon(screen, (166, 73, 89), [vertices[0], vertices[1], vertices[2], (rock.x, rock.y)])
            pygame.draw.polygon(screen, (64, 36, 59), [vertices[3], vertices[4], vertices[5], (rock.x, rock.y)])
            pygame.draw.polygon(screen, color, vertices, 2)
        if game.boss:
            boss = game.boss
            rect = boss.rect()
            color = INK if boss.hit_flash > 0 else RED
            pygame.draw.polygon(screen, (100, 45, 65), [(rect.left, rect.top + 15), (rect.centerx, rect.top),
                                (rect.right, rect.top + 15), (rect.right - 18, rect.bottom),
                                (rect.centerx, rect.bottom - 15), (rect.left + 18, rect.bottom)])
            pygame.draw.rect(screen, color, rect.inflate(-25, -26), 3, border_radius=5)
            bar = pygame.Rect(arena.x + 170, arena.y + 42, 400, 9)
            pygame.draw.rect(screen, (68, 38, 52), bar)
            pygame.draw.rect(screen, RED, (bar.x, bar.y, int(bar.width * boss.hp / boss.max_hp), bar.height))
            label = 'DODGE: LANCE' if game.attack_index % 2 == 0 else 'DODGE: FAN'
            self.text(f"BOSS {boss.hp}/{boss.max_hp}  /  {label if game.boss_phase == 'warning' else game.boss_phase.upper()}", (bar.x, bar.y - 23), 20, GOLD)
        for x in game.warning_lanes:
            if game.boss_phase == 'warning':
                pygame.draw.rect(screen, GOLD, (x - 28, arena.top + 170, 56, arena.height - 170), 2)
                for y in range(arena.top + 180, arena.bottom, 22):
                    pygame.draw.line(screen, GOLD, (x - 10, y), (x + 10, y + 8), 1)
            elif game.boss_phase == 'active':
                pygame.draw.rect(screen, RED, (x - 28, arena.top + 160, 56, arena.height - 160))
                pygame.draw.rect(screen, INK, (x - 8, arena.top + 160, 16, arena.height - 160))
        for x, y, vx, speed in game.fan_paths:
            travel = (arena.bottom - y) / speed
            pygame.draw.line(screen, GOLD, (x, y), (x + vx * travel, arena.bottom), 1)
        for bullet in game.hostile_bullets:
            pygame.draw.circle(screen, RED, (int(bullet.x), int(bullet.y)), 7)
            pygame.draw.circle(screen, GOLD, (int(bullet.x), int(bullet.y)), 3)
        player = game.player
        if not game.invulnerable or int(game.invulnerable * 12) % 2:
            self.effects.ship(screen, player, game.elapsed, reduced)
        if game.shield_remaining > 0:
            pygame.draw.ellipse(screen, CYAN, player.inflate(32, 34), 3)
        self.effects.draw_particles(screen)
        self.text(f"WAVE {game.wave:02d}", (arena.x + 20, arena.y + 18), 23, MUTED)
        if game.invulnerable > 0.95:
            pygame.draw.rect(screen, RED, arena.inflate(-6, -6), width=3, border_radius=15)
        if game.state != "running":
            shade = pygame.Surface(arena.size, pygame.SRCALPHA)
            shade.fill((4, 10, 22, 205))
            screen.blit(shade, arena)
            title, subtitle = {
                "ready": ("READY, PILOT?", "Hold an open palm to start"),
                "paused": ("PAUSED", game.reason),
                "gameover": ("GAME OVER", f"Final score: {game.score}   /   Press R to restart"),
                "calibrating": ("FIND YOUR RANGE", "Keep face + hand visible. Enter: use default range"),
                "setup": ("CAMERA SETUP", game.reason or "Choose a camera, calibrate, then Start"),
            }[game.state]
            if demo and game.state == "ready":
                subtitle = "Press Space to start"
            setup = game.state in ('setup', 'calibrating')
            self.text(title, (arena.x + 65, arena.y + (50 if setup else 220)), 58)
            self.text(subtitle, (arena.x + 66, arena.y + (105 if setup else 284)), 28, CYAN)
            if game.state == "paused":
                hint = "Space / P to resume" if demo else "Face + hand in view, then palm / Space / P to resume"
                self.text(hint, (arena.x + 66, arena.y + 324), 23, MUTED)
            elif game.state == "ready":
                hint = "Arrows / A-D to steer. Hold Space to fire." if demo else "Move index finger to steer / pinch to shoot"
                self.text(hint, (arena.x + 66, arena.y + 324), 23, MUTED)
            if game.state in ("setup", "calibrating"):
                self.text(f"Camera {self.preferences['camera_index']}    [ / ] change    T retry", (90, 250), 23, MUTED)
                self.button("Previous", (90, 285, 140, 42), pygame.K_LEFTBRACKET)
                self.button("Next camera", (242, 285, 160, 42), pygame.K_RIGHTBRACKET)
                self.button("Retry", (414, 285, 130, 42), pygame.K_t)
                # Setup remains one screen; the live preview/status stay at right.
                self.button("Calibrate", (90, 535, 175, 44), pygame.K_c)
                self.button("Start", (278, 535, 175, 44), pygame.K_SPACE)
                self.button("Keyboard mode", (466, 535, 195, 44), pygame.K_k)
                self.text("Enter: use default range   +/-: sensitivity", (90, 600), 23, MUTED)
            if game.state in ("setup", "calibrating") and self.calibration:
                self.wrapped(self.calibration.message, arena.x + 66, arena.y + 330, 620, GOLD)
                pygame.draw.rect(screen, (32, 63, 78), (arena.x + 66, arena.y + 380, 600, 8))
                pygame.draw.rect(screen, CYAN, (arena.x + 66, arena.y + 380, int(600 * self.calibration.progress), 8))
            elif game.state not in ("setup", "calibrating"):
                label = "Restart" if game.state == "gameover" else "Resume" if game.state == "paused" else "Start game"
                self.button(label, (90, 505, 175, 46), pygame.K_r if game.state == "gameover" else pygame.K_SPACE)
                self.button("Switch input", (278, 505, 175, 46), pygame.K_k)
                self.button("Settings", (466, 505, 175, 46), pygame.K_F1)
                self.button("Quit", (90, 568, 175, 42), pygame.K_q)
        screen.set_clip(None)
        pygame.draw.rect(screen, (39, 58, 78), arena, width=1, border_radius=18)
        self.text("INPUT: WEBCAM" if not demo else "INPUT: KEYBOARD", (790, 112), 23, CYAN)
        preview_rect = pygame.Rect(790, 148, 286, 215)
        pygame.draw.rect(screen, (20, 32, 50), preview_rect, border_radius=10)
        if packet:
            if packet.sequence != self.sequence:
                h, w = packet.rgb.shape[:2]
                self.preview = pygame.transform.smoothscale(
                    pygame.image.frombuffer(packet.rgb.tobytes(), (w, h), "RGB"), preview_rect.size)
                self.sequence = packet.sequence
            screen.blit(self.preview, preview_rect)
            def point(x, y):
                return (preview_rect.x + round(x * preview_rect.width),
                        preview_rect.y + round(y * preview_rect.height))
            screen.set_clip(preview_rect)
            if face_ok and packet.face:
                x1, y1 = min(p[0] for p in packet.face), min(p[1] for p in packet.face)
                x2, y2 = max(p[0] for p in packet.face), max(p[1] for p in packet.face)
                box = pygame.Rect(point(x1, y1), (round((x2 - x1) * preview_rect.width),
                                                 round((y2 - y1) * preview_rect.height)))
                pygame.draw.rect(screen, CYAN, box.inflate(8, 8), 2, border_radius=8)
                for x, y in packet.face:
                    pygame.draw.circle(screen, (109, 188, 187), point(x, y), 1)
            if hand_ok and packet.hand:
                points = [point(x, y) for x, y in packet.hand]
                for a, b in CONNECTIONS:
                    pygame.draw.line(screen, GOLD, points[a], points[b], 1)
                for index, p in enumerate(points):
                    pygame.draw.circle(screen, CYAN if index == 8 else GOLD, p, 4 if index == 8 else 2)
            screen.set_clip(None)
        else:
            label = "Camera off" if demo else ("Camera unavailable" if error else "Starting camera...")
            self.text(label, (810, 240), 23, MUTED)
        self.text("FACE  " + ("OFF" if demo else "OK" if face_ok else "NOT FOUND"), (790, 382), 20, CYAN if face_ok else MUTED)
        self.text("HAND  " + ("OFF" if demo else "OK" if hand_ok else "NOT FOUND"), (930, 382), 20, CYAN if hand_ok else MUTED)
        self.wrapped(status, 790, 414, 280, GOLD)
        pygame.draw.rect(screen, (32, 48, 66), (790, 461, 286, 5), border_radius=2)
        progress = controls.fist_progress if controls.fist else controls.palm_progress
        pygame.draw.rect(screen, CYAN, (790, 461, int(286 * progress), 5), border_radius=2)
        self.text("CONTROLS", (790, 491), 23)
        lines = ("Arrows / A-D   Move", "Space   Start / fire") if demo else ("Index finger   Move / hold pinch   Fire", "Open palm   Start / pause")
        for i, line in enumerate((*lines, "P / Esc   Pause menu", "R   Restart    Q   Quit",
                                  "K / Tab   Switch input mode", "F1   Settings / calibration",
                                  "S / hold fist   Shield")):
            self.text(line, (790, 520 + i * 22), 20, MUTED)
        self.text("LOCAL ONLY  /  NO RECORDING", (790, 708), 20, CYAN)
        shield_text = f"SHIELD {game.shield_remaining:.1f}s" if game.shield_remaining > 0 else f"SHIELD WAIT {game.shield_cooldown:.1f}s" if game.shield_cooldown > 0 else "SHIELD READY / S or fist"
        self.text(shield_text, (790, 680), 20, CYAN if game.shield_cooldown <= 0 else MUTED)
        self.text(f"{fps:.0f} FPS", (24, HEIGHT - 26), 20, MUTED)
        self.text(f"COMBO {game.multiplier}x  /  {game.combo_hits} hits  /  {game.combo_remaining:.1f}s", (255, HEIGHT - 26), 20, GOLD)
        pygame.draw.rect(screen, (57, 54, 44), (580, HEIGHT - 24, 150, 5))
        pygame.draw.rect(screen, GOLD, (580, HEIGHT - 24, int(150 * game.combo_remaining / 2), 5))
        if error:
            # Keep setup controls and preview available even when startup fails.
            panel = pygame.Rect(60, 335, 685, 180)
            pygame.draw.rect(screen, (37, 20, 34), panel, border_radius=16)
            pygame.draw.rect(screen, RED, panel, 2, border_radius=16)
            self.text("CAMERA / TRACKING UNAVAILABLE", (80, 355), 28, RED)
            self.wrapped(error[:360], 80, 392, panel.width - 40, INK)
            self.text("T: retry   [ / ]: camera   K: keyboard mode", (80, 484), 23, GOLD)
        if self.settings_open or self.menu_open:
            self.buttons.clear()
            panel = pygame.Rect(75, 170, 950, 465)
            pygame.draw.rect(screen, (12, 26, 43), panel, border_radius=16)
            pygame.draw.rect(screen, (51, 121, 131), panel, 2, border_radius=16)
            self.text("SETTINGS / PAUSE", (110, 200), 36)
            prefs = self.preferences
            lines = [f"M   Sound: {'muted' if prefs['muted'] else 'on'}     V   Volume: {int(prefs['volume'] * 100)}%",
                     f"E   Reduced motion / effects: {'on' if prefs['reduced_motion'] else 'off'}",
                     f"L   Tracking resolution: {'424 x 318' if prefs['low_resolution'] else '640 x 480'} (applies immediately)",
                     f"[ / ]   Camera index: {prefs['camera_index']}    T   Retry camera",
                     f"- / +   Sensitivity: {prefs['sensitivity']:.1f}x     C   Recalibrate",
                     "Space / P: resume    K: switch input    Esc / F1: close menu"]
            for i, line in enumerate(lines):
                self.text(line, (110, 258 + i * 36), 23, MUTED)
            self.button("Resume / Start", (110, 535, 195, 48), pygame.K_SPACE)
            self.button("Switch input", (325, 535, 190, 48), pygame.K_k)
            self.button("Quit game", (535, 535, 190, 48), pygame.K_q)
        w, h = self.window.get_size()
        scale = min(w / WIDTH, h / HEIGHT)
        size = (max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale)))
        self.window.fill(BG)
        self.window.blit(pygame.transform.smoothscale(screen, size), ((w - size[0]) // 2, (h - size[1]) // 2))
        pygame.display.flip()
