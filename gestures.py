"""Time-based smoothing, pinch hysteresis, and hold/release gesture debouncing."""

from dataclasses import dataclass
import math
from settings import PALM_HOLD, GESTURE_COOLDOWN, PINCH_CLOSE, PINCH_OPEN


def finger_geometry(world):
    """PIP bend angle and fingertip reach relative to finger bone length."""
    values = []
    for base in (5, 9, 13, 17):
        a, b, c, tip = (world[base + i] for i in range(4))
        u = tuple(a[i] - b[i] for i in range(3))
        v = tuple(c[i] - b[i] for i in range(3))
        denominator = max(1e-9, math.dist(a, b) * math.dist(c, b))
        cosine = max(-1, min(1, sum(x * y for x, y in zip(u, v)) / denominator))
        angle = math.degrees(math.acos(cosine))
        length = max(1e-9, math.dist(a, b) + math.dist(b, c) + math.dist(c, tip))
        values.append((angle, math.dist(a, tip) / length))
    return values


@dataclass
class Controls:
    x: float = 0.5
    shoot: bool = False
    toggle: bool = False
    palm_progress: float = 0.0
    pinching: bool = False
    shield: bool = False
    fist: bool = False
    fist_progress: float = 0.0


class GestureInterpreter:
    def __init__(self):
        self.x = 0.5
        self.last_time = None
        self.pinching = False
        self.pinch_since = None
        self.last_shot = -100.0
        self.palm_since = None
        self.palm_latched = False
        self.last_toggle = -100.0
        self.seen_hand = False
        self.blocked_until_release = False
        self.range_left, self.range_right, self.sensitivity = 0.08, 0.92, 1.0
        self.fist_since = None
        self.fist_latched = False
        self.was_fist = False
        self.palm_offset = 0.0
        self.exit_offset = 0.0

    def update(self, points, now, aspect=4 / 3):
        dt = 0.033 if self.last_time is None else max(0.0, now - self.last_time)
        self.last_time = now
        output = Controls(x=self.x)
        if not points:
            self.was_fist = False
            self.palm_since = self.pinch_since = None
            self.fist_since = None
            # Keep latches until a visible released hand prevents repeat events
            # when tracking flickers during a held gesture.
            if self.seen_hand:
                self.pinching = self.palm_latched = True
                self.blocked_until_release = True
                self.fist_latched = True
            return output

        self.seen_hand = True

        def distance(a, b):
            return math.hypot((points[a][0] - points[b][0]) * aspect,
                              points[a][1] - points[b][1])

        # MCP/PIP/tip geometry separates curled fingers from a two-finger pinch.
        curled = [distance(tip, 0) < distance(pip, 0) * 1.12
                  and distance(tip, base) < distance(pip, base) * 1.3
                  for base, pip, tip in ((5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20))]
        # Once a strict fist is found, tolerate one uncertain fingertip. Occluded
        # tips jitter in real webcam landmarks; an extended palm still exits it.
        held_curled = [distance(tip, 0) < distance(pip, 0) * 1.2
                       and distance(tip, base) < distance(pip, base) * 1.65
                       for base, pip, tip in ((5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20))]
        world = getattr(points, 'world', None)
        if world and len(world) == 21:
            # Depth resolves fists pointed toward/away from the camera, where
            # projected tips can appear beyond their joints despite being curled.
            geometry = finger_geometry(world)
            curled = [angle < 135 and reach < 0.8 for angle, reach in geometry]
            held_curled = [angle < 155 and reach < 0.9 for angle, reach in geometry]
        fist = (all(curled) or (self.was_fist and sum(held_curled) >= 3)) and distance(0, 9) > 0.03
        palm_x = sum(points[i][0] for i in (0, 5, 9, 13, 17)) / 5
        def normalized(x):
            return 0.5 + ((x - self.range_left) / max(0.2, self.range_right - self.range_left) - 0.5) * self.sensitivity
        if fist:
            if not self.was_fist:
                self.palm_offset = self.x - normalized(palm_x)
            target = normalized(palm_x) + self.palm_offset
        else:
            if self.was_fist:
                self.exit_offset = self.x - normalized(points[8][0])
            target = normalized(points[8][0]) + self.exit_offset
            self.exit_offset *= math.exp(-dt / 0.2)
        self.was_fist = fist
        output.fist = fist
        if fist:
            if self.fist_since is None:
                self.fist_since = now
            output.fist_progress = min(1, (now - self.fist_since) / 0.35)
            if output.fist_progress >= 1 and not self.fist_latched:
                output.shield = True
                self.fist_latched = True
        else:
            self.fist_since = None
            # Require an actually extended finger, not a single noisy non-fist frame.
            if any(distance(tip, 0) > distance(pip, 0) * 1.18 for pip, tip in ((6, 8), (10, 12), (14, 16), (18, 20))):
                self.fist_latched = False
        target = max(0.0, min(1.0, target))
        self.x += (target - self.x) * (1 - math.exp(-dt / 0.09))
        output.x = self.x
        scale = max(distance(0, 9), 0.025)
        ratio = distance(4, 8) / scale
        if fist:
            self.pinch_since = self.palm_since = None
            self.pinching = False
            self.blocked_until_release = True
            self.palm_latched = False
            return output
        if ratio > PINCH_OPEN:
            self.pinching = False
            self.blocked_until_release = False
            self.pinch_since = None
        elif ratio < PINCH_CLOSE and not self.pinching and not self.blocked_until_release:
            if self.pinch_since is None:
                self.pinch_since = now
            if now - self.pinch_since >= 0.06 and now - self.last_shot >= 0.25:
                self.pinching = True
                self.last_shot = now
                output.shoot = True
        else:
            self.pinch_since = None
        output.pinching = self.pinching and not self.blocked_until_release

        # Wrist-relative distances support both hands and a rotated palm.
        extended = all(distance(tip, 0) > distance(joint, 0) * 1.18
                       for tip, joint in ((8, 6), (12, 10), (16, 14), (20, 18)))
        palm = extended and distance(4, 9) / scale > 0.65 and ratio > PINCH_OPEN
        if palm:
            if self.palm_since is None:
                self.palm_since = now
            output.palm_progress = min(1.0, (now - self.palm_since) / PALM_HOLD)
            if (output.palm_progress >= 1 and not self.palm_latched
                    and now - self.last_toggle >= GESTURE_COOLDOWN):
                output.toggle = True
                self.palm_latched = True
                self.last_toggle = now
        else:
            self.palm_since = None
            self.palm_latched = False
        return output
