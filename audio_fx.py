"""Small synthesized effects; no files, microphone access, or audio dependency."""
from array import array
import math
import pygame


class Audio:
    def __init__(self):
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            for name, frequency, duration in (("shot", 880, 0.065), ("hit", 160, 0.18),
                                               ("destroy", 330, 0.12), ("wave", 660, 0.22)):
                count = int(22050 * duration)
                data = array("h", (int(6500 * (1 - i / count) ** 2 *
                                    math.sin(math.tau * frequency * (i / 22050) * (1 - 0.4 * i / count)))
                                   for i in range(count)))
                self.sounds[name] = pygame.mixer.Sound(buffer=data)
        except pygame.error:
            pass

    def play(self, name, preferences):
        if not preferences["muted"] and name in self.sounds:
            self.sounds[name].set_volume(preferences["volume"])
            self.sounds[name].play()
