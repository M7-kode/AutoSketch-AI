import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class FakeMouse:
    """Enregistre les appels au lieu de piloter la vraie souris."""

    def __init__(self, fail_on_move=None):
        self.events = []
        self._fail_on_move = fail_on_move
        self._move_count = 0

    def move_to(self, x, y, duration=None):
        self._move_count += 1
        if self._fail_on_move is not None and self._move_count == self._fail_on_move:
            raise RuntimeError("souris injoignable")
        self.events.append(("move", x, y))

    def press(self):
        self.events.append(("press",))

    def release(self):
        self.events.append(("release",))

    def click(self):
        self.events.append(("click",))

    def kinds(self):
        return [event[0] for event in self.events]

    def count(self, kind):
        return self.kinds().count(kind)

    def moves(self):
        return [(event[1], event[2]) for event in self.events if event[0] == "move"]


class FakeScreen:
    """Remplace une capture d'ecran pyautogui."""

    def __init__(self, pixels, size=(100, 100)):
        self.pixels = pixels
        self.size = size

    def getpixel(self, position):
        return self.pixels.get(position, (0, 0, 0)) + (255,)


@pytest.fixture
def fake_mouse():
    return FakeMouse()


@pytest.fixture
def two_tone_image():
    """40x40 BGR : moitie gauche rouge, moitie droite bleue."""
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    image[:, :20] = (0, 0, 255)   # BGR -> rouge
    image[:, 20:] = (255, 0, 0)   # BGR -> bleu
    return image


@pytest.fixture
def shape_image():
    """100x100 blanc avec un carre noir : de quoi produire des contours."""
    import cv2

    image = np.full((100, 100, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (20, 20), (80, 80), (0, 0, 0), -1)
    return image
