"""Execution d'un plan : c'est la seule couche qui touche reellement la souris."""

import time

from autosketch.screen.calibration import map_points
from autosketch.drawing.strokes import draw_path_with_speed
from autosketch.screen.palette import select_color


def execute_plan(plan, mouse, zone, speed, palette=None, exit_event=None,
                 color_pause=2.0, on_event=None):
    """Dessine un plan dans la zone d'ecran donnee.

    Retourne le nombre de traces effectivement dessinees (utile quand ECHAP
    interrompt le dessin en cours de route)."""
    zone_top_left, zone_bottom_right = zone

    def notify(message):
        if on_event is not None:
            on_event(message)

    def stopped():
        return exit_event is not None and exit_event.is_set()

    drawn = 0
    for color_rgb, paths in plan.groups:
        if stopped():
            break

        if color_rgb is not None and palette is not None:
            swatch = select_color(mouse, palette, color_rgb)
            if swatch is None:
                notify(f"Couleur RGB{color_rgb} : palette vide, selection ignoree.")
            else:
                position, matched = swatch
                notify(f"Couleur RGB{color_rgb} -> swatch RGB{matched} a {position} "
                       f"({len(paths)} trait(s))")
            if color_pause > 0:
                time.sleep(color_pause)

        for path in paths:
            if stopped():
                break
            screen_points = map_points(path, plan.source_shape, zone_top_left, zone_bottom_right)
            draw_path_with_speed(mouse, screen_points, speed=speed, exit_event=exit_event)
            drawn += 1

    return drawn
