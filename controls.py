"""Normalize keyboard/gesture input and apply tracking-loss grace periods."""
from gestures import Controls, GestureInterpreter
from settings import TRACKING_GRACE, TRACKING_TIMEOUT, KEYBOARD_SPEED, INPUT_MAX_AGE


class TrackingHealth:
    def __init__(self):
        self.last_face = self.last_hand = None
        self.face_ok = self.hand_ok = self.ready = self.can_continue = False
        self.reason = "Waiting for face and hand"

    def update(self, packet, error, now):
        fresh = packet is not None and now - packet.captured_at <= TRACKING_TIMEOUT
        self.face_ok = bool(fresh and packet.face is not None and not error)
        self.hand_ok = bool(fresh and packet.hand is not None and not error)
        if self.face_ok:
            self.last_face = packet.captured_at
        if self.hand_ok:
            self.last_hand = packet.captured_at
        self.ready = bool(self.face_ok and self.hand_ok and now - packet.captured_at <= INPUT_MAX_AGE)
        self.can_continue = bool(not error and fresh and self.last_face is not None
                                 and self.last_hand is not None
                                 and now - self.last_face <= TRACKING_GRACE
                                 and now - self.last_hand <= TRACKING_GRACE)
        if error:
            self.reason = "Camera / tracking unavailable"
        elif not fresh:
            self.reason = "Waiting for camera frames"
        elif now - packet.captured_at > INPUT_MAX_AGE:
            self.reason = "Tracking result delayed - controls held"
        elif not self.face_ok and not self.hand_ok:
            self.reason = "Face and hand lost - return to view"
        elif not self.face_ok:
            self.reason = "Face lost - return to view"
        elif not self.hand_ok:
            self.reason = "Hand lost - return to view"
        else:
            self.reason = "Tracking ready"


class InputController:
    def __init__(self, keyboard=False, x=0.5):
        self.keyboard = keyboard
        self.x = x
        self.gestures = GestureInterpreter()
        self.gestures.x = x
        self.health = TrackingHealth()
        self.last_sequence = -1
        self.last_capture = None
        self.display = Controls(x=x)
        self.feedback = "Hand detected"
        self.previous_wrist = None

    def update(self, packet, error, now, dt, direction=0, fire=False, shield=False):
        self.health.update(packet, error, now)
        output = Controls(x=self.x, palm_progress=self.display.palm_progress,
                          pinching=self.display.pinching, fist=self.display.fist,
                          fist_progress=self.display.fist_progress)
        input_fresh = bool(packet and now - packet.captured_at <= INPUT_MAX_AGE and self.health.ready)
        if not self.keyboard:
            if packet and packet.sequence != self.last_sequence:
                if self.last_capture is not None and packet.captured_at - self.last_capture > TRACKING_GRACE:
                    self.gestures.update(None, now)
                output = self.gestures.update(packet.hand if input_fresh else None, now)
                if input_fresh:
                    xs, ys = zip(*packet.hand)
                    wrist = packet.hand[0]
                    jump = 0 if self.previous_wrist is None else abs(wrist[0] - self.previous_wrist[0]) + abs(wrist[1] - self.previous_wrist[1])
                    self.previous_wrist = wrist
                    if min(xs) < 0.025 or max(xs) > 0.975 or min(ys) < 0.025 or max(ys) > 0.975:
                        self.feedback = "Hint: move your hand fully into view"
                    elif max(ys) - min(ys) > 0.7 or max(xs) - min(xs) > 0.65:
                        self.feedback = "Hint: try moving your hand farther away"
                    elif jump > 0.16:
                        self.feedback = "Hint: landmarks unstable; hold steady"
                    else:
                        self.feedback = "Hand detected / tracking ready"
                self.last_sequence = packet.sequence
                self.last_capture = packet.captured_at
            elif not input_fresh:
                output = self.gestures.update(None, now)
            if not input_fresh:
                output.x = self.x
                output.shoot = output.toggle = output.shield = False
                output.pinching = False
            else:
                # A held pinch repeats through the shared game firing cooldown.
                output.shoot = output.shoot or output.pinching
        if self.keyboard or direction:
            output.x = max(0.0, min(1.0, self.x + direction * KEYBOARD_SPEED * min(dt, 0.1)))
            self.gestures.x = output.x
        output.shoot = output.shoot or fire
        output.shield = output.shield or shield
        self.x = output.x
        self.display = output
        return output
