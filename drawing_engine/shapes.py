import math
import time

DEFAULT_SPEED = 400.0


def draw_path_with_speed(mouse_controller, points, speed=DEFAULT_SPEED, min_segment_duration=0.02, exit_event=None):
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


def draw_line(mouse_controller, start, end, speed=DEFAULT_SPEED, exit_event=None):
    draw_path_with_speed(mouse_controller, [start, end], speed=speed, exit_event=exit_event)


def draw_rectangle(mouse_controller, top_left, bottom_right, speed=DEFAULT_SPEED, exit_event=None):
    x1, y1 = top_left
    x2, y2 = bottom_right
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
    draw_path_with_speed(mouse_controller, corners, speed=speed, exit_event=exit_event)


def draw_circle(mouse_controller, center, radius, segments=36, speed=DEFAULT_SPEED, exit_event=None):
    cx, cy = center
    points = []
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((round(x), round(y)))
    draw_path_with_speed(mouse_controller, points, speed=speed, exit_event=exit_event)


def draw_ellipse(mouse_controller, top_left, bottom_right, segments=48, speed=DEFAULT_SPEED, exit_event=None):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    rx, ry = abs(x2 - x1) / 2, abs(y2 - y1) / 2

    points = []
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        x = cx + rx * math.cos(angle)
        y = cy + ry * math.sin(angle)
        points.append((round(x), round(y)))
    draw_path_with_speed(mouse_controller, points, speed=speed, exit_event=exit_event)


def draw_polyline(mouse_controller, points, closed=False, speed=DEFAULT_SPEED, exit_event=None):
    path_points = list(points)
    if closed and path_points and path_points[0] != path_points[-1]:
        path_points.append(path_points[0])
    draw_path_with_speed(mouse_controller, path_points, speed=speed, exit_event=exit_event)


def zigzag_fill_points(top_left, bottom_right, lines=4):
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


def draw_filled_rect(mouse_controller, top_left, bottom_right, lines=4, speed=DEFAULT_SPEED, exit_event=None):
    draw_path_with_speed(mouse_controller, zigzag_fill_points(top_left, bottom_right, lines),
                          speed=speed, exit_event=exit_event)
