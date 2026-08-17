"""Genere assets/icon.ico : un coup de pinceau dans les couleurs de l'application.

Dessine en grand puis reduit, ce qui lisse les bords sans avoir a gerer
l'antialiasing a la main.

    python assets/make_icon.py
"""

import math
import os

from PIL import Image, ImageDraw

SIZE = 1024
BACKGROUND = (31, 36, 48, 255)      # #1f2430, le fond de l'application
STROKE = (79, 140, 255, 255)        # #4f8cff, sa couleur d'accent
HIGHLIGHT = (95, 208, 138, 255)     # #5fd08a, le vert "calibre"
ICON_SIZES = [(size, size) for size in (16, 24, 32, 48, 64, 128, 256)]


def cubic_bezier(t, p0, p1, p2, p3):
    u = 1 - t
    x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
    y = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
    return x, y


def draw_brush_stroke(draw, points, color, min_radius, max_radius):
    """Un trait dont l'epaisseur enfle au milieu, comme un vrai coup de pinceau."""
    steps = 400
    for step in range(steps + 1):
        t = step / steps
        x, y = cubic_bezier(t, *points)
        radius = min_radius + (max_radius - min_radius) * math.sin(math.pi * t)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


def build_icon():
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=int(SIZE * 0.22), fill=BACKGROUND)

    draw_brush_stroke(draw, [(210, 780), (420, 210), (610, 800), (820, 250)],
                      STROKE, min_radius=26, max_radius=62)

    # Le point de depart du trace, en vert : le curseur qui vient de se poser.
    draw.ellipse([160, 730, 260, 830], fill=HIGHLIGHT)

    return image


def main():
    output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    build_icon().save(output, format="ICO", sizes=ICON_SIZES)
    print(f"Icone ecrite : {output}")


if __name__ == "__main__":
    main()
