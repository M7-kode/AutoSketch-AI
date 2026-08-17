import math
import time

from pynput import keyboard, mouse

from drawing_engine.shapes import draw_path_with_speed


def _polyline_length(points):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


class DrawingRecorder:
    def __init__(self):
        self.strokes = []
        self._points = []
        self._stroke_start_time = None
        self._pressed = False
        self._last_release_time = None
        self._pending_pause = 0.0

    def on_move(self, x, y):
        if self._pressed:
            self._points.append((x, y))

    def on_click(self, x, y, button, pressed):
        if button != mouse.Button.left:
            return

        now = time.perf_counter()
        if pressed:
            self._pressed = True
            self._pending_pause = (now - self._last_release_time) if self._last_release_time else 0.0
            self._points = [(x, y)]
            self._stroke_start_time = now
        else:
            self._pressed = False
            self._points.append((x, y))
            duration = (now - self._stroke_start_time) if self._stroke_start_time else 0.0
            if len(self._points) >= 2:
                self.strokes.append({
                    "points": list(self._points),
                    "duration": duration,
                    "length": _polyline_length(self._points),
                    "pause_before": self._pending_pause,
                })
            self._last_release_time = now

    def on_key_press(self, key):
        if key == keyboard.Key.esc:
            return False


def record_drawing():
    recorder = DrawingRecorder()
    with mouse.Listener(on_move=recorder.on_move, on_click=recorder.on_click) as mouse_listener:
        with keyboard.Listener(on_press=recorder.on_key_press) as keyboard_listener:
            keyboard_listener.join()
        mouse_listener.stop()
    return recorder.strokes


def extract_style(strokes, default_speed=300.0, default_pause=0.3, max_pause=3.0):
    if not strokes:
        return {"speed": default_speed, "avg_pause": default_pause}

    total_length = sum(s["length"] for s in strokes)
    total_duration = sum(s["duration"] for s in strokes)
    speed = (total_length / total_duration) if total_duration > 0 else default_speed

    pauses = [s["pause_before"] for s in strokes[1:] if s["pause_before"] > 0]
    avg_pause = (sum(pauses) / len(pauses)) if pauses else default_pause

    return {
        "speed": max(speed, 10.0),
        "avg_pause": min(avg_pause, max_pause),
    }


def apply_style(mouse_controller, paths, style):
    speed = style.get("speed", 300.0)
    pause = style.get("avg_pause", 0.3)
    for i, path_points in enumerate(paths):
        if i > 0 and pause > 0:
            time.sleep(pause)
        draw_path_with_speed(mouse_controller, path_points, speed)
