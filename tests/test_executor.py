import threading

from core.executor import execute_plan
from core.plan import DrawPlan
from plugins.palette import ColorPalette

ZONE = ((100, 100), (200, 200))


def square_plan(colors=(None,)):
    """Un trait carre par couleur, dans un repere 10x10."""
    path = [(0, 0), (10, 0), (10, 10), (0, 10)]
    return DrawPlan(groups=[(color, [list(path)]) for color in colors], source_shape=(10, 10))


def palette_with(colors):
    palette = ColorPalette()
    for index, color in enumerate(colors):
        palette.add_swatch((10 + index, 20), color)
    return palette


def test_every_path_is_drawn(fake_mouse):
    plan = DrawPlan(groups=[(None, [[(0, 0), (5, 5)], [(1, 1), (6, 6)]])], source_shape=(10, 10))

    drawn = execute_plan(plan, fake_mouse, ZONE, speed=10000, color_pause=0)

    assert drawn == 2
    assert fake_mouse.count("press") == 2


def test_the_drawing_lands_inside_the_calibrated_zone(fake_mouse):
    execute_plan(square_plan(), fake_mouse, ZONE, speed=10000, color_pause=0)

    for x, y in fake_mouse.moves():
        assert 100 <= x <= 200
        assert 100 <= y <= 200


def test_the_image_is_stretched_to_fill_the_zone(fake_mouse):
    execute_plan(square_plan(), fake_mouse, ZONE, speed=10000, color_pause=0)
    xs = [x for x, _ in fake_mouse.moves()]
    ys = [y for _, y in fake_mouse.moves()]

    assert (min(xs), max(xs)) == (100, 200)
    assert (min(ys), max(ys)) == (100, 200)


def test_the_button_is_never_left_pressed(fake_mouse):
    plan = square_plan(colors=[(255, 0, 0), (0, 0, 255)])

    execute_plan(plan, fake_mouse, ZONE, speed=10000, palette=palette_with([(255, 0, 0)]),
                 color_pause=0)

    assert fake_mouse.count("press") == fake_mouse.count("release")


def test_a_color_is_selected_once_per_group(fake_mouse):
    plan = square_plan(colors=[(255, 0, 0), (0, 0, 255)])

    execute_plan(plan, fake_mouse, ZONE, speed=10000,
                 palette=palette_with([(255, 0, 0), (0, 0, 255)]), color_pause=0)

    assert fake_mouse.count("click") == 2


def test_without_a_palette_no_color_is_clicked(fake_mouse):
    plan = square_plan(colors=[(255, 0, 0), (0, 0, 255)])

    execute_plan(plan, fake_mouse, ZONE, speed=10000, palette=None, color_pause=0)

    assert fake_mouse.count("click") == 0


def test_a_contour_plan_needs_no_color_selection(fake_mouse):
    execute_plan(square_plan(colors=[None]), fake_mouse, ZONE, speed=10000,
                 palette=palette_with([(255, 0, 0)]), color_pause=0)

    assert fake_mouse.count("click") == 0


def test_escape_before_the_start_draws_nothing(fake_mouse):
    exit_event = threading.Event()
    exit_event.set()

    drawn = execute_plan(square_plan(), fake_mouse, ZONE, speed=10000,
                         exit_event=exit_event, color_pause=0)

    assert drawn == 0
    assert fake_mouse.events == []


def test_escape_stops_the_remaining_paths(fake_mouse):
    exit_event = threading.Event()
    many_paths = DrawPlan(groups=[(None, [[(0, 0), (5, 5)] for _ in range(20)])],
                          source_shape=(10, 10))

    class StopAfterFirst:
        def is_set(self):
            stop = bool(fake_mouse.count("release"))
            return stop

    drawn = execute_plan(many_paths, fake_mouse, ZONE, speed=10000,
                         exit_event=StopAfterFirst(), color_pause=0)

    assert drawn == 1


def test_progress_is_reported_for_each_color(fake_mouse):
    messages = []
    plan = square_plan(colors=[(255, 0, 0), (0, 0, 255)])

    execute_plan(plan, fake_mouse, ZONE, speed=10000,
                 palette=palette_with([(255, 0, 0), (0, 0, 255)]),
                 color_pause=0, on_event=messages.append)

    assert len(messages) == 2


def test_an_empty_plan_is_harmless(fake_mouse):
    drawn = execute_plan(DrawPlan(groups=[], source_shape=(10, 10)), fake_mouse, ZONE,
                         speed=10000, color_pause=0)

    assert drawn == 0
    assert fake_mouse.events == []
