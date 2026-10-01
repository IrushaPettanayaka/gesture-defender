"""Responsive arcade screens; drawing and navigation are separate from combat."""
import math
import pygame
from arena_view import ArenaView
from space_art import SpaceBackdrop, illustration, preview_mask
from hand_tracking import CONNECTIONS
from preferences import DEFAULTS
from settings import WIDTH, HEIGHT
from ui_components import Canvas, StableMessage, progress, gesture_icon, BG, PANEL, CYAN, RED, INK, MUTED, BORDER, GOLD


class Renderer:
    def __init__(self, screen):
        self.window = screen
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        self.ui = Canvas(self.screen)
        self.arena_view = ArenaView()
        self.backdrop = SpaceBackdrop((WIDTH,HEIGHT))
        self.menu_rocket = pygame.transform.rotozoom(illustration('rocket',310),-28,1)
        self.preferences = DEFAULTS.copy()
        self.page = 'auto'
        self.return_page = 'menu'
        self.calibration = None
        self.can_start = None
        self.setup_prompt = ''
        self.preview = None
        self.sequence = -1
        self.debug = False
        self.fullscreen = False
        self.message = StableMessage()
        self.last_tick = pygame.time.get_ticks()
        self.transition = 1.0
        self.last_scene = None
        self.elapsed = 0.0
        self.viewport = pygame.Rect(24, 100, WIDTH - 48, 478)

    @property
    def buttons(self):
        return self.ui.buttons

    def logical_position(self, position):
        w, h = self.window.get_size()
        scale = min(w / WIDTH, h / HEIGHT)
        return ((position[0] - (w - WIDTH * scale) / 2) / scale,
                (position[1] - (h - HEIGHT * scale) / 2) / scale)

    def click(self, position):
        return self.ui.click(self.logical_position(position))

    def pointer_down(self, position):
        self.ui.pointer_down(self.logical_position(position))

    def pointer_up(self, position):
        return self.ui.pointer_up(self.logical_position(position))

    def navigate(self, key, reverse=False):
        return self.ui.navigate(key, reverse)

    def header(self, title, subtitle=''):
        self.ui.text('GESTURE DEFENDER', (40, 25), 24, CYAN)
        self.ui.title(title, (36, 66), 60, lavender=True)
        if subtitle:
            self.ui.text(subtitle, (42, 140), 24, MUTED)

    def stars(self, reduced):
        self.backdrop.draw(self.screen,self.elapsed,reduced,quiet=self.page=='play',menu=self.page=='menu')

    def menu(self, game, reduced):
        u = self.ui
        u.text('A HANDS-ON SPACE ADVENTURE', (102, 110), 24, CYAN)
        u.title('GESTURE', (90,166),112)
        u.title('DEFENDER', (90,265),98,lavender=True)
        u.text('Move with your hand. Defend your space.', (102, 384), 32, MUTED)
        u.panel((96,428,344,50))
        u.text(f'PERSONAL BEST   {game.best:,}', (268,444),24,INK,center=True)
        u.button('PLAY', (96, 495, 344, 66), 'play', primary=True)
        u.button('Controls', (96, 580, 164, 54), 'controls')
        u.button('Settings', (276, 580, 164, 54), 'settings')
        u.button('Quit', (96, 652, 164, 48), 'quit')
        offset = 0 if reduced else math.sin(self.elapsed * 1.3) * 7
        self.screen.blit(self.menu_rocket,(841,278+offset))
        u.text('Camera stays off until you choose it.', (1000, 655), 24, MUTED, center=True)
        u.text('Tab / arrows to navigate    Enter to select', (96, 735), 20, MUTED)
        u.text('Art direction: Designed by vectorpouch / Freepik', (871,735),20,MUTED)

    def mode(self):
        u = self.ui
        self.header('How would you like to play?', 'Choose an input mode. You can switch later from Settings.')
        for x, title, subtitle, action, button in (
                (244, 'Use your camera', 'Steer with your index finger. Pinch to fire, make a fist to shield.', 'choose_camera', 'Set up camera'),
                (698, 'Use your keyboard', 'Move with arrows or A / D. Space fires. S or Shift activates the shield.', 'choose_keyboard', 'Play with keyboard')):
            u.panel((x, 236, 424, 338))
            gesture_icon(self.screen, 'fire' if action == 'choose_keyboard' else 'shield', (x+32, 274), CYAN)
            u.text(title, (x+32, 326), 40)
            u.wrap(subtitle, (x+32, 384, 360, 70), 28)
            u.button(button, (x+32, 484, 360, 54), action, primary=action == 'choose_camera')
        u.button('Back', (40, 686, 160, 48), 'back')
        u.text('All camera processing stays on this device.', (WIDTH//2, 626), 24, MUTED, center=True)

    def camera_preview(self, rect, packet, face_ok, hand_ok, label, detailed=False):
        rect = pygame.Rect(rect)
        self.ui.panel(rect)
        if packet is None:
            self.ui.text(label, (rect.centerx, rect.centery-12), 28, MUTED, center=True)
            return
        if self.sequence != packet.sequence or self.preview is None:
            h, w = packet.rgb.shape[:2]
            self.preview = pygame.image.frombuffer(packet.rgb.tobytes(), (w, h), 'RGB').copy()
            self.sequence = packet.sequence
        # Fit the image without distorting the player's face when preview sizes change.
        pw, ph = self.preview.get_size()
        inner=rect.inflate(-18,-20)
        scale = min(inner.width / pw, inner.height / ph)
        size = (round(pw * scale), round(ph * scale))
        target = pygame.Rect(0, 0, *size)
        target.center = rect.center
        rounded = pygame.Surface(size,pygame.SRCALPHA)
        rounded.blit(pygame.transform.smoothscale(self.preview,size),(0,0))
        rounded.blit(preview_mask(size),(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(rounded,target)
        self.screen.set_clip(target)
        def point(x, y):
            return target.x + round(x * target.width), target.y + round(y * target.height)
        if face_ok and packet.face:
            xs, ys = zip(*packet.face)
            box = pygame.Rect(point(min(xs), min(ys)), (max(1, round((max(xs)-min(xs))*target.width)), max(1, round((max(ys)-min(ys))*target.height))))
            pygame.draw.rect(self.screen, CYAN, box, 2, border_radius=8)
        if hand_ok and packet.hand:
            if detailed:
                points = [point(x, y) for x, y in packet.hand]
                for a, b in CONNECTIONS:
                    pygame.draw.line(self.screen, GOLD, points[a], points[b], 1)
                for p in points:
                    pygame.draw.circle(self.screen, GOLD, p, 3)
            else:
                pygame.draw.circle(self.screen, CYAN, point(*packet.hand[8]), 7, 2)
        self.screen.set_clip(None)

    def setup(self, game, packet, controls, face_ok, hand_ok, status, error, ready):
        u = self.ui
        self.header('Camera setup')
        u.text(f'Camera {self.preferences["camera_index"]}', (40, 149), 28)
        u.button('Previous', (346, 126, 120, 46), 'camera_prev', enabled=self.preferences['camera_index'] > 0)
        u.button('Next', (478, 126, 108, 46), 'camera_next', enabled=self.preferences['camera_index'] < 9)
        u.button('Retry', (598, 126, 130, 46), 'retry_camera')
        u.button('Play with keyboard', (1030, 124, 296, 48), 'choose_keyboard')
        self.camera_preview((40, 192, 688, 516), packet, face_ok, hand_ok,
                            'Camera unavailable' if error else 'Opening camera...', self.debug)
        u.panel((756, 192, 570, 516))
        u.text('FACE  ' + ('Detected' if face_ok else 'Searching'), (788, 222), 28, CYAN if face_ok else MUTED)
        u.text('HAND  ' + ('Detected' if hand_ok else 'Searching'), (1060, 222), 28, CYAN if hand_ok else MUTED)
        if error:
            u.text('Camera unavailable', (788, 270), 32, RED)
            u.wrap(str(error)[:180], (788, 310, 504, 80), 24, INK)
        else:
            instructions = self.setup_prompt or 'Keep your face and one full hand in view. Move your index finger left and right.'
            u.wrap(status if not ready else instructions, (788, 272, 504, 80), 28)
        u.text('MOVEMENT TEST', (788, 397), 22, MUTED)
        progress(self.screen, (788, 437, 504, 5), controls.x)
        px = 788 + max(0, min(1, controls.x)) * 504
        pygame.draw.polygon(self.screen, CYAN, [(px, 425), (px-9, 449), (px+9, 449)])
        u.button('Recalibrate', (788, 470, 246, 48), 'recalibrate', primary=True, enabled=ready and not self.calibration)
        u.button('Use default range', (1046, 470, 246, 48), 'default_range')
        if self.calibration:
            u.wrap(self.calibration.message, (788, 535, 504, 56), 24, GOLD)
            progress(self.screen, (788, 580, 504, 16), self.calibration.progress)
        else:
            u.wrap('Calibration saved. Start when comfortable.' if game.reason == 'Calibrated' else 'Calibrate your comfortable reach, or use the saved/default range.', (788, 536, 504, 60), 24)
        enabled = ready and not self.calibration and not error
        u.button('Start Game', (788, 610, 504, 52), 'start', primary=True, enabled=enabled)
        explanation = 'Finish calibration or choose default range.' if self.calibration else 'Start needs a current face and hand detection.' if not ready else 'Ready to play.'
        u.text(explanation, (788, 679), 22, MUTED)
        u.button('Back', (40, 716, 180, 44), 'main_menu')
        u.text('Mirrored preview  /  processed locally  /  no recording', (244, 733), 22, MUTED)

    def hud(self, game):
        u = self.ui
        u.panel((24,8,210,80))
        u.panel((242,8,216,80))
        u.panel((524,8,318,80))
        u.panel((960,8,382,80))
        u.text('SCORE', (45, 20), 20, MUTED)
        u.text(f'{game.score:,}', (45, 39), 40)
        u.text(f'COMBO {game.multiplier}x', (263, 23), 28, CYAN)
        if game.combo_remaining > 0:
            u.text(f'{game.combo_remaining:.1f}s', (263, 53), 22, MUTED)
            progress(self.screen, (320, 58, 110, 8), game.combo_remaining / 2)
        u.text(f'WAVE {game.wave:02d}', (WIDTH//2, 20 if game.boss else 32), 32, INK, center=True)
        if game.boss:
            u.text(f'BOSS   {game.boss.hp} / {game.boss.max_hp}', (WIDTH//2, 53), 22, RED, center=True)
            progress(self.screen, (WIDTH//2-133,73,266,8), game.boss.hp/game.boss.max_hp, RED)
        u.text(f'LIVES  {game.lives}', (980, 22), 28)
        state = f'ACTIVE  {game.shield_remaining:.1f}s' if game.shield_remaining > 0 else f'COOLDOWN  {game.shield_cooldown:.1f}s' if game.shield_cooldown > 0 else 'READY'
        gesture_icon(self.screen, 'shield', (980, 49), CYAN)
        u.text('SHIELD  ' + state, (1015, 53), 22)
        fill=game.shield_remaining/2 if game.shield_remaining>0 else 1-game.shield_cooldown/8
        progress(self.screen,(1122,27,195,10),fill)

    def gesture_cards(self, game, controls, keyboard):
        u = self.ui
        items = [('fire', 'Space / Fire' if keyboard else 'Pinch / Fire', controls.pinching or controls.shoot, 1 if controls.pinching else 0),
                 ('shield', 'S / Shield' if keyboard else 'Fist / Shield', controls.fist, controls.fist_progress),
                 ('pause', 'P / Pause' if keyboard else 'Hold palm / Pause', controls.palm_progress > 0, controls.palm_progress)]
        for i, (kind, label, active, hold) in enumerate(items):
            x = 240 + i * 250
            u.panel((x, 604, 230, 74), PANEL if active else (22,49,66))
            gesture_icon(self.screen, kind, (x+17, 625), CYAN if active else MUTED)
            u.text(label, (x+53, 628), 24, INK if active else MUTED)
            if hold:
                progress(self.screen, (x+16, 668, 198, 3), hold)

    def play(self, game, packet, controls, face_ok, hand_ok, guidance, keyboard, dt, reduced):
        self.arena_view.draw(game, self.screen, self.viewport, dt, reduced)
        pygame.draw.rect(self.screen, BORDER, self.viewport, 1, border_radius=10)
        self.hud(game)
        if game.boss and game.boss_phase == 'warning':
            self.ui.text('LANCE WARNING - move out of the lanes' if game.attack_index % 2 == 0 else 'FAN WARNING - move between the paths', (WIDTH//2, 110), 24, GOLD, center=True)
        if keyboard:
            self.ui.panel((24, 598, 192, 144))
            self.ui.text('KEYBOARD', (120, 630), 28, CYAN, center=True)
            self.ui.text('Arrows / A-D', (120, 668), 24, INK, center=True)
            self.ui.text('Camera off', (120, 708), 22, MUTED, center=True)
        elif self.preferences['preview_visible']:
            self.camera_preview((24, 598, 192, 144), packet, face_ok, hand_ok, 'No preview', self.debug)
        else:
            self.ui.panel((24, 598, 192, 144))
            self.ui.text('Preview hidden', (120, 645), 24, INK, center=True)
            self.ui.text('Tracking continues', (120, 680), 22, MUTED, center=True)
        self.gesture_cards(game, controls, keyboard)
        self.ui.button('Pause', (1004, 604, 144, 48), 'pause')
        self.ui.button('Hide preview' if self.preferences['preview_visible'] else 'Show preview', (1160, 604, 182, 48), 'toggle_preview', enabled=not keyboard)
        self.ui.button('Set up camera' if keyboard else 'Keyboard mode / camera off', (1004, 674, 338, 48), 'switch_input')
        self.ui.wrap(guidance, (240, 695, 730, 50), 24, GOLD)
        if game.state in ('paused', 'gameover'):
            self.overlay(game, keyboard)

    def overlay(self, game, keyboard):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((6, 2, 36, 205))
        self.screen.blit(shade, (0, 0))
        self.ui.buttons.clear()
        if self.ui.focus not in ('resume', 'recalibrate', 'settings', 'main_menu', 'restart'):
            self.ui.focus = None
        u = self.ui
        if game.state == 'gameover':
            u.panel((423, 158, 520, 452))
            u.title('GAME OVER', (683, 198), 48, lavender=True, center=True)
            if game.score > game.record_at_start:
                u.text('NEW BEST', (683, 254), 24, CYAN, center=True)
            u.text(f'{game.score:,}', (683, 296), 84, center=True)
            u.text(f'Best {game.best:,}   /   Wave {game.wave:02d}', (683, 392), 28, MUTED, center=True)
            u.button('Play Again', (459, 456, 448, 54), 'restart', primary=True)
            u.button('Main Menu', (459, 530, 448, 48), 'main_menu')
        else:
            u.panel((453, 155, 460, 482))
            u.title('PAUSED', (683, 192), 48, lavender=True, center=True)
            u.wrap(game.reason or 'Paused by you', (485, 254, 396, 60), 28)
            ready = keyboard or bool(self.can_start)
            u.button('Resume', (485, 330, 396, 48), 'resume', primary=True, enabled=ready)
            if not ready:
                u.text('Return face + hand to view to resume.', (485, 305), 22, GOLD)
            if not keyboard:
                u.button('Recalibrate', (485, 394, 396, 48), 'recalibrate')
            u.button('Settings', (485, 458 if not keyboard else 394, 396, 48), 'settings')
            u.button('Main Menu', (485, 522 if not keyboard else 458, 396, 48), 'main_menu')

    def settings(self, keyboard):
        u = self.ui
        self.header('Settings', 'Changes are saved on exit. Closing this screen never resumes play automatically.')
        p = self.preferences
        rows = [
            ('Input mode', 'Keyboard' if keyboard else 'Camera', 'switch_input'),
            ('Sound', 'Unmute' if p['muted'] else 'Mute', 'mute'),
            ('Camera preview', 'Visible' if p['preview_visible'] else 'Hidden', 'toggle_preview'),
            ('Reduced motion', 'On' if p['reduced_motion'] else 'Off', 'reduced_motion'),
            ('Display', 'Windowed' if self.fullscreen else 'Fullscreen', 'fullscreen'),
            ('Gesture sensitivity', f'{p["sensitivity"]:.1f}x', None),
            ('Camera resolution', 'Low / 424 x 318' if p['low_resolution'] else 'Standard / 640 x 480', 'resolution')]
        for i, (label, value, action) in enumerate(rows):
            y = 197 + i * 66
            u.panel((230, y, 906, 58))
            u.text(label, (254, y+16), 28)
            if i == 1:
                u.button('-', (510, y+6, 48, 46), 'volume_down')
                u.text(f'{round(p["volume"]*100)}%', (579, y+18), 24, MUTED)
                u.button('+', (650, y+6, 48, 46), 'volume_up')
            if action:
                u.button(value, (770, y+6, 342, 46), action)
            else:
                u.button('-', (770, y+6, 80, 46), 'sensitivity_down')
                u.text(value, (901, y+16), 28, CYAN)
                u.button('+', (1032, y+6, 80, 46), 'sensitivity_up')
        u.button('Back', (230, 689, 200, 48), 'back', primary=True)
        u.text('F11 display   /   H preview   /   F2 debug', (620, 707), 24, MUTED)

    def controls_page(self):
        u = self.ui
        self.header('Controls', 'Choose the way you play. Keyboard fallback is always available.')
        for x, title, lines in ((150, 'CAMERA', ['Index finger: steer left / right', 'Pinch: hold to fire, separate to stop', 'Fist: hold 0.35s for a 2s shield', 'Open palm: hold to pause / resume', 'Open your hand before another shield']),
                                (714, 'KEYBOARD', ['Arrows or A / D: steer', 'Space: fire / start / resume', 'S or Shift: activate shield', 'P or Escape: pause', 'R: play again after game over'])):
            u.panel((x, 216, 504, 350))
            u.text(title, (x+32, 249), 32, CYAN)
            for i, line in enumerate(lines):
                u.text(line, (x+32, 315+i*43), 28)
        u.text('Shield cooldown: 8s after expiry. Tracking recovery always waits for your resume.', (WIDTH//2, 620), 28, MUTED, center=True)
        u.button('Back', (150, 686, 200, 48), 'back', primary=True)

    def draw(self, game, packet, controls, face_ok, hand_ok, status, error, demo, fps):
        ticks = pygame.time.get_ticks()
        dt = min(0.1, max(0.001, (ticks-self.last_tick)/1000))
        self.last_tick = ticks
        reduced = self.preferences['reduced_motion']
        self.elapsed += dt
        page = self.page
        if page == 'auto':
            page = 'menu' if game.state == 'ready' else 'setup' if game.state in ('setup', 'calibrating') else 'play'
        scene = (page, game.state if page == 'play' else '')
        if scene != self.last_scene:
            self.transition = 0.0
            self.message = StableMessage()
            self.last_scene = scene
        self.transition = min(1, self.transition + dt / 0.12)
        self.ui.begin(scene, self.logical_position(pygame.mouse.get_pos()))
        self.screen.fill(BG)
        self.backdrop.draw(self.screen,self.elapsed,reduced,quiet=page=='play',menu=page=='menu')
        stable = self.message.update(status, dt, urgent=bool(error))
        ready = bool(face_ok and hand_ok) if self.can_start is None else self.can_start
        if page == 'menu':
            self.menu(game, reduced)
        elif page == 'mode':
            self.mode()
        elif page == 'setup':
            self.setup(game, packet, controls, face_ok, hand_ok, stable, error, ready)
        elif page == 'settings':
            self.settings(demo)
        elif page == 'controls':
            self.controls_page()
        else:
            guidance = '' if stable in ('Hand detected / tracking ready', 'Tracking ready') else stable
            self.play(game, packet, controls, face_ok, hand_ok, guidance, demo, dt, reduced)
        if self.debug:
            self.ui.panel((24, 2, 610, 30))
            self.ui.text(f'DEBUG   {fps:.0f} FPS   Face: {face_ok}   Hand: {hand_ok}   Frame: {getattr(packet, "sequence", "none")}', (32, 8), 22, GOLD)
        if not reduced and page != 'play' and self.transition < 1:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((*BG, int((1-self.transition)*100)))
            self.screen.blit(shade, (0, 0))
        w, h = self.window.get_size()
        scale = min(w/WIDTH, h/HEIGHT)
        size = (max(1, round(WIDTH*scale)), max(1, round(HEIGHT*scale)))
        self.window.fill(BG)
        self.window.blit(pygame.transform.smoothscale(self.screen, size), ((w-size[0])//2, (h-size[1])//2))
        pygame.display.flip()
