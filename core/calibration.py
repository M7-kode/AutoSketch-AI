import time

from pynput import keyboard, mouse

# Laisse le temps au clic qui a declenche l'action courante (bouton, boite de
# dialogue) de se dissiper avant d'ecouter, sinon ce meme clic est capture
# comme point de calibration et la zone/palette obtenue est incoherente.
CLICK_SETTLE_DELAY = 0.4


def capture_points(n):
    time.sleep(CLICK_SETTLE_DELAY)
    points = []

    def on_click(x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            points.append((x, y))
            if len(points) >= n:
                return False

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

    return points


def capture_points_until_enter():
    time.sleep(CLICK_SETTLE_DELAY)
    points = []

    def on_click(x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            points.append((x, y))

    def on_key_press(key):
        if key == keyboard.Key.enter:
            return False

    with mouse.Listener(on_click=on_click) as mouse_listener:
        with keyboard.Listener(on_press=on_key_press) as keyboard_listener:
            keyboard_listener.join()
        mouse_listener.stop()

    return points


def map_points(points, image_shape, zone_top_left, zone_bottom_right):
    img_h, img_w = image_shape[:2]
    zx1, zy1 = zone_top_left
    zx2, zy2 = zone_bottom_right
    zone_w = zx2 - zx1
    zone_h = zy2 - zy1

    mapped = []
    for x, y in points:
        nx = zx1 + (x / img_w) * zone_w
        ny = zy1 + (y / img_h) * zone_h
        mapped.append((round(nx), round(ny)))
    return mapped
