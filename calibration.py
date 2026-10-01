"""Two short, tracked holds establish a comfortable horizontal range."""
import statistics


class Calibration:
    def __init__(self):
        self.stage = 0
        self.elapsed = 0.0
        self.samples = []
        self.left = None
        self.result = None
        self.message = "Hold your index finger at your comfortable LEFT edge"

    @property
    def progress(self):
        return min(1.0, self.elapsed / 2.0)

    def update(self, x, dt):
        if self.result is not None:
            return self.result
        if x is None:
            self.elapsed = 0
            self.samples.clear()
            return None
        self.elapsed += min(dt, 0.1)
        if self.elapsed >= 1.0:
            self.samples.append(max(0.0, min(1.0, x)))
        if self.elapsed < 2.0:
            return None
        edge = statistics.median(self.samples)
        self.elapsed = 0
        self.samples.clear()
        if self.stage == 0:
            self.left = edge
            self.stage = 1
            self.message = "Now hold at your comfortable RIGHT edge"
        elif edge - self.left < 0.2:
            self.stage = 0
            self.message = "Range too narrow. Try LEFT again, or choose default range."
        else:
            self.result = (self.left, edge)
        return self.result
