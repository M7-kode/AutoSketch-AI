import math
import time

DEFAULT_SPEED = 400.0


def draw_path_with_speed(mouse_controller, points, speed=DEFAULT_SPEED, min_segment_duration=0.02,
                         exit_event=None):
    """Trace une polyligne bouton enfonce, a vitesse constante en pixels/seconde.

    Le bouton est relache dans un finally : meme interrompu ou en cas d'erreur,
    on ne laisse jamais le clic bloque dans le logiciel de dessin."""
    if len(points) < 2:
        return

    mouse_controller.move_to(*points[0], duration=0.3)
    mouse_controller.press()
    try:
        time.sleep(0.05)
        for prev, curr in zip(points, points[1:]):
            if exit_event is not None and exit_event.is_set():
                break
            distance = math.hypot(curr[0] - prev[0], curr[1] - prev[1])
            duration = max(distance / speed, min_segment_duration) if speed > 0 else min_segment_duration
            mouse_controller.move_to(*curr, duration=duration)
    finally:
        mouse_controller.release()


def zigzag_fill_points(top_left, bottom_right, lines=4):
    """Balayage aller-retour remplissant un rectangle en un seul trait continu."""
    x1, y1 = top_left
    x2, y2 = bottom_right
    lines = max(int(lines), 1)
    step = (y2 - y1) / lines

    points = []
    going_right = True
    for i in range(lines + 1):
        y = y1 + step * i
        if going_right:
            points.append((x1, y))
            points.append((x2, y))
        else:
            points.append((x2, y))
            points.append((x1, y))
        going_right = not going_right
    return points
