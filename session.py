"""Screen transitions and camera ownership, independent of drawing and collisions."""
import logging
import time
from calibration import Calibration
from controls import InputController
from game import Game


class Session:
    def __init__(self, preferences, create_worker, best=0, keyboard=True, save_best=None):
        self.prefs = preferences
        self.create_worker = create_worker
        self.save_best = save_best or (lambda: None)
        self.game = Game()
        self.game.best = best
        self.game.reset()
        self.controller = InputController(keyboard=keyboard)
        self.page, self.return_page = 'menu', 'menu'
        self.worker, self.packet, self.error = None, None, None
        self.retired = []
        self.pending_camera = False
        self.calibration = None
        self.input_guard = True
        self.transition_pending = True
        self.started = time.monotonic()
        self.preview_generation = 0
        if not keyboard:
            self.open_camera()

    @property
    def ready(self):
        return self.controller.keyboard or self.controller.health.ready

    def stop_camera(self):
        if self.worker:
            self.worker.stop.set()
            self.retired.append(self.worker)
            self.worker = None
        self.pending_camera = False
        self.packet = self.error = None
        self.preview_generation += 1

    def open_camera(self):
        self.game.pause('Camera setup')
        self.game.state = 'setup'
        self.page, self.calibration = 'setup', None
        self.stop_camera()
        self.controller = InputController(keyboard=False, x=self.controller.x)
        self.pending_camera = True
        self.started = time.monotonic()
        self.input_guard = True
        self.poll_camera()

    def poll_camera(self):
        if self.pending_camera and not any(w.thread.is_alive() for w in self.retired):
            self.retired.clear()
            self.pending_camera = False
            try:
                self.worker = self.create_worker(self.prefs['camera_index'], self.prefs['low_resolution'])
            except Exception as error:
                self.error = str(error)
                logging.exception('Camera startup failed')
        if self.worker:
            self.packet, self.error = self.worker.snapshot()

    def reset_run(self):
        self.save_best()
        self.game.reset()
        self.controller = InputController(keyboard=self.controller.keyboard)
        self.controller.gestures.pinching = self.controller.gestures.palm_latched = True
        self.controller.gestures.fist_latched = self.controller.gestures.blocked_until_release = True
        self.calibration = None
        self.input_guard = True

    def perform(self, action):
        if not action:
            return
        game, prefs = self.game, self.prefs
        # UI actions never carry a held fire/gesture into resumed play.
        self.input_guard = True
        self.transition_pending = True
        if action == 'play':
            self.page = 'mode'
        elif action in ('settings', 'controls'):
            game.pause('Paused by you')
            if self.page == action:
                self.page = self.return_page
            else:
                self.return_page = self.page
                self.page = action
        elif action == 'back':
            self.page = self.return_page if self.page in ('settings', 'controls') else 'menu'
        elif action == 'main_menu':
            self.stop_camera()
            self.reset_run()
            self.controller = InputController(keyboard=True)
            self.page = 'menu'
        elif action == 'choose_camera':
            if self.page in ('menu', 'mode'):
                self.reset_run()
            self.open_camera()
        elif action == 'choose_keyboard':
            if self.page in ('menu', 'mode'):
                self.reset_run()
            self.stop_camera()
            self.controller = InputController(keyboard=True, x=self.controller.x)
            self.calibration = None
            game.state = 'running'
            self.page = 'play'
        elif action == 'switch_input':
            if self.controller.keyboard:
                self.open_camera()
            else:
                self.stop_camera()
                self.controller = InputController(keyboard=True, x=self.controller.x)
                self.calibration = None
                game.state, game.reason = 'paused', 'Keyboard mode selected - resume when ready'
                self.page = 'play'
        elif action in ('start', 'resume'):
            if self.ready and not self.calibration and game.state in ('ready', 'setup', 'paused'):
                game.state, game.reason = 'running', ''
                self.page = 'play'
        elif action == 'pause':
            game.pause('Paused by you')
        elif action == 'restart':
            self.reset_run()
            if self.controller.keyboard:
                game.state, self.page = 'running', 'play'
            else:
                game.state, self.page = 'setup', 'setup'
        elif action == 'recalibrate' and not self.controller.keyboard:
            game.pause('Recalibration')
            game.state, self.page = 'setup', 'setup'
            self.calibration = Calibration()
        elif action == 'default_range':
            prefs['range_left'], prefs['range_right'] = 0.08, 0.92
            self.calibration = None
            game.reason = 'Default range selected'
        elif action in ('camera_prev', 'camera_next'):
            prefs['camera_index'] = max(0, min(9, prefs['camera_index'] + (1 if action == 'camera_next' else -1)))
            if not self.controller.keyboard:
                self.open_camera()
        elif action == 'retry_camera' and not self.controller.keyboard:
            self.open_camera()
        elif action == 'resolution':
            prefs['low_resolution'] = not prefs['low_resolution']
            if not self.controller.keyboard:
                self.open_camera()
        elif action in ('mute', 'reduced_motion', 'toggle_preview'):
            key = {'mute': 'muted', 'toggle_preview': 'preview_visible', 'reduced_motion': 'reduced_motion'}[action]
            prefs[key] = not prefs[key]
        elif action in ('volume_up', 'volume_down'):
            prefs['volume'] = round(max(0, min(1, prefs['volume'] + (0.1 if action == 'volume_up' else -0.1))), 1)
        elif action in ('sensitivity_up', 'sensitivity_down'):
            prefs['sensitivity'] = round(max(0.5, min(2, prefs['sensitivity'] + (0.1 if action == 'sensitivity_up' else -0.1))), 1)

    def escape(self):
        if self.page in ('controls', 'settings', 'mode'):
            self.perform('back')
        elif self.page == 'setup':
            self.perform('main_menu')
        elif self.page == 'play':
            if self.game.state == 'running':
                self.perform('pause')
            elif self.game.state == 'paused':
                self.perform('resume')
            else:
                self.perform('main_menu')

    def update(self, now, dt, direction=0, fire=False, shield=False):
        ui_event, self.transition_pending = self.transition_pending, False
        self.poll_camera()
        g = self.controller.gestures
        g.range_left, g.range_right = self.prefs['range_left'], self.prefs['range_right']
        g.sensitivity = self.prefs['sensitivity']
        active = self.page == 'play' and self.game.state == 'running'
        controls = self.controller.update(self.packet, self.error, now, dt,
                                          direction if active else 0, fire=fire and active, shield=shield and active)
        if not ui_event and not fire and not controls.pinching and not controls.fist and not controls.palm_progress:
            self.input_guard = False
        if controls.toggle and not self.input_guard and not self.calibration:
            if self.page == 'play':
                self.perform('pause' if self.game.state == 'running' else 'resume')
            elif self.page == 'setup':
                self.perform('start')
        if self.page == 'setup' and self.calibration:
            x = self.packet.hand[8][0] if self.controller.health.ready else None
            result = self.calibration.update(x, dt)
            if result:
                self.prefs['range_left'], self.prefs['range_right'] = result
                self.game.reason, self.calibration = 'Calibrated', None
                self.input_guard = True
        previous = self.game.state
        self.game.update(dt, controls.x, controls.shoot and not self.input_guard,
                         self.controller.keyboard or self.controller.health.can_continue,
                         self.controller.health.reason, shield=controls.shield and not self.input_guard)
        if self.game.state == 'gameover' and previous != 'gameover':
            self.save_best()
        return controls

    def status(self):
        if self.controller.keyboard:
            return ''
        if self.error:
            return 'Camera unavailable. Retry, select another camera, or use the keyboard.'
        if self.pending_camera:
            return 'Releasing the previous camera before opening the selected device...'
        if self.packet is None:
            return 'Loading models and opening camera...' if time.monotonic()-self.started < 15 else 'Camera is taking longer than expected. Retry or play with the keyboard.'
        if not self.controller.health.ready:
            return self.controller.health.reason
        return self.controller.feedback

    def close(self):
        if self.worker:
            self.worker.close()
        for worker in self.retired:
            worker.close()
        return all(not w.thread.is_alive() for w in self.retired + ([self.worker] if self.worker else []))
