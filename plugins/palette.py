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


def sample_color_at(position):
    x, y = position
    pixel = pyautogui.screenshot().getpixel((x, y))
    return tuple(pixel[:3])


def calibrate_palette(n_swatches):
    palette = ColorPalette()
    for i in range(n_swatches):
        input(f"Clique sur la couleur {i + 1}/{n_swatches} de la palette, puis appuie sur Entree...")
        position = capture_points(1)[0]
        color = sample_color_at(position)
        palette.add_swatch(position, color)
        print(f"  -> position {position}, couleur echantillonnee RGB{color}")
    return palette


def select_color(mouse_controller, palette, target_color_rgb):
    swatch = palette.nearest_swatch(target_color_rgb)
    if swatch is None:
        return None

    position, matched_color = swatch
    mouse_controller.move_to(*position, duration=0.2)
    mouse_controller.click()
    return position, matched_color
