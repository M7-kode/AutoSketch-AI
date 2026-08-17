import json
import os

import pyautogui


class ColorPalette:
    def __init__(self):
        self.swatches = []

    def add_swatch(self, position, color_rgb):
        self.swatches.append((tuple(position), tuple(color_rgb)))

    def nearest_swatch(self, color_rgb):
        if not self.swatches:
            return None

        def dist(swatch):
            return sum((a - b) ** 2 for a, b in zip(swatch[1], color_rgb))

        return min(self.swatches, key=dist)

    def colors_rgb(self):
        return [color for _, color in self.swatches]

    def __len__(self):
        return len(self.swatches)


def sample_colors_at(positions):
    """Echantillonne toutes les positions sur une seule capture d'ecran : la palette
    du site doit rester telle quelle pendant l'operation, et N captures seraient lentes."""
    if not positions:
        return []

    screen = pyautogui.screenshot()
    width, height = screen.size

    colors = []
    for x, y in positions:
        x = min(max(int(x), 0), width - 1)
        y = min(max(int(y), 0), height - 1)
        colors.append(tuple(screen.getpixel((x, y))[:3]))
    return colors


def build_palette(positions):
    palette = ColorPalette()
    for position, color in zip(positions, sample_colors_at(positions)):
        palette.add_swatch(position, color)
    return palette


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


def select_color(mouse_controller, palette, target_color_rgb):
    swatch = palette.nearest_swatch(target_color_rgb)
    if swatch is None:
        return None

    position, matched_color = swatch
    mouse_controller.move_to(*position, duration=0.2)
    mouse_controller.click()
    return position, matched_color
