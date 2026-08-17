import json
import os

import pyautogui

from core.calibration import capture_points


class ColorPalette:
    def __init__(self):
        self.swatches = []

    def add_swatch(self, position, color_rgb):
        self.swatches.append((position, color_rgb))

    def nearest_swatch(self, color_rgb):
        if not self.swatches:
            return None

        def dist(swatch_color):
            return sum((a - b) ** 2 for a, b in zip(swatch_color, color_rgb))

        return min(self.swatches, key=lambda s: dist(s[1]))

    def colors_rgb(self):
        return [color for _, color in self.swatches]


def save_palette(palette, path):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    data = [{"position": list(position), "color": list(color)} for position, color in palette.swatches]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_palette(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    palette = ColorPalette()
    for entry in data:
        palette.add_swatch(tuple(entry["position"]), tuple(entry["color"]))
    return palette


def sample_color_at(position):
    x, y = position
    pixel = pyautogui.screenshot().getpixel((x, y))
    return tuple(pixel[:3])


def calibrate_palette(n_swatches, on_step=None):
    palette = ColorPalette()
    for i in range(n_swatches):
        if on_step is not None:
            on_step(i, n_swatches)
        position = capture_points(1)[0]
        color = sample_color_at(position)
        palette.add_swatch(position, color)
    return palette


def select_color(mouse_controller, palette, target_color_rgb):
    swatch = palette.nearest_swatch(target_color_rgb)
    if swatch is None:
        return None

    position, matched_color = swatch
    mouse_controller.move_to(*position, duration=0.2)
    mouse_controller.click()
    return position, matched_color
