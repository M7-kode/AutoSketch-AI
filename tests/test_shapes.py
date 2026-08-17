import pytest

from conftest import FakeMouse
from drawing_engine.shapes import draw_path_with_speed, zigzag_fill_points


def test_zigzag_stays_inside_the_rectangle():
    points = zigzag_fill_points((10, 20), (110, 120), lines=4)

    for x, y in points:
        assert 10 <= x <= 110
        assert 20 <= y <= 120


def test_zigzag_spans_the_full_height():
    points = zigzag_fill_points((0, 0), (10, 100), lines=5)
    ys = [y for _, y in points]

    assert min(ys) == 0
    assert max(ys) == 100


def test_more_lines_means_a_denser_fill():
    sparse = zigzag_fill_points((0, 0), (10, 10), lines=2)
    dense = zigzag_fill_points((0, 0), (10, 10), lines=8)

    assert len(dense) > len(sparse)


def test_zigzag_alternates_direction():
    # Un aller-retour continu : chaque passe repart du bord ou la precedente s'est arretee,
    # sinon la souris traverse le rectangle a vide entre deux lignes.
    points = zigzag_fill_points((0, 0), (10, 40), lines=4)

    for index in range(0, len(points) - 2, 2):
        end_of_line = points[index + 1]
        start_of_next = points[index + 2]
        assert end_of_line[0] == start_of_next[0]


def test_zigzag_never_collapses_to_zero_lines():
    assert len(zigzag_fill_points((0, 0), (10, 10), lines=0)) >= 2


def test_drawing_a_path_presses_once_and_releases_once(fake_mouse):
    draw_path_with_speed(fake_mouse, [(0, 0), (10, 0), (10, 10)], speed=10000)

    assert fake_mouse.count("press") == 1
    assert fake_mouse.count("release") == 1


def test_the_button_is_pressed_before_moving_and_released_last(fake_mouse):
    draw_path_with_speed(fake_mouse, [(0, 0), (10, 0)], speed=10000)
    kinds = fake_mouse.kinds()

    assert kinds[0] == "move"      # on se place d'abord
    assert kinds[1] == "press"     # puis on appuie
    assert kinds[-1] == "release"  # et on relache a la fin


def test_every_point_of_the_path_is_visited(fake_mouse):
    path = [(0, 0), (10, 0), (10, 10), (0, 10)]

    draw_path_with_speed(fake_mouse, path, speed=10000)

    assert fake_mouse.moves() == path


def test_a_path_with_less_than_two_points_draws_nothing(fake_mouse):
    draw_path_with_speed(fake_mouse, [(5, 5)], speed=10000)

    assert fake_mouse.events == []


def test_interrupting_still_releases_the_button(fake_mouse):
    class AlreadySet:
        def is_set(self):
            return True

    draw_path_with_speed(fake_mouse, [(0, 0), (10, 0), (20, 0)], speed=10000,
                         exit_event=AlreadySet())

    assert fake_mouse.count("release") == 1


def test_the_button_is_released_even_if_the_mouse_fails():
    # Le pire scenario de cette application : laisser le clic bloque dans le
    # logiciel de dessin de l'utilisateur.
    mouse = FakeMouse(fail_on_move=2)

    with pytest.raises(RuntimeError):
        draw_path_with_speed(mouse, [(0, 0), (10, 0), (20, 0)], speed=10000)

    assert mouse.count("release") == 1
