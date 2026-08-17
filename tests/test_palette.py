import pytest

from conftest import FakeScreen
from plugins import palette as palette_module
from plugins.palette import (
    ColorPalette,
    build_palette,
    load_palette,
    sample_colors_at,
    save_palette,
    select_color,
)


def test_nearest_swatch_picks_the_closest_color():
    palette = ColorPalette()
    palette.add_swatch((10, 10), (255, 0, 0))
    palette.add_swatch((20, 10), (0, 255, 0))
    palette.add_swatch((30, 10), (0, 0, 255))

    position, color = palette.nearest_swatch((250, 10, 10))

    assert (position, color) == ((10, 10), (255, 0, 0))


def test_nearest_swatch_on_an_empty_palette_returns_none():
    assert ColorPalette().nearest_swatch((0, 0, 0)) is None


def test_length_reflects_the_number_of_swatches():
    palette = ColorPalette()
    assert len(palette) == 0

    palette.add_swatch((0, 0), (1, 2, 3))
    assert len(palette) == 1


def test_colors_keep_the_calibration_order():
    palette = ColorPalette()
    palette.add_swatch((0, 0), (1, 1, 1))
    palette.add_swatch((1, 1), (2, 2, 2))

    assert palette.colors_rgb() == [(1, 1, 1), (2, 2, 2)]


def test_sampling_uses_a_single_screenshot(monkeypatch):
    screenshots = []
    screen = FakeScreen({(10, 10): (255, 0, 0), (20, 20): (0, 255, 0)})

    def fake_screenshot():
        screenshots.append(1)
        return screen

    monkeypatch.setattr(palette_module.pyautogui, "screenshot", fake_screenshot)

    assert sample_colors_at([(10, 10), (20, 20)]) == [(255, 0, 0), (0, 255, 0)]
    assert len(screenshots) == 1


def test_sampling_nothing_takes_no_screenshot(monkeypatch):
    def explode():
        raise AssertionError("aucune capture ne devrait etre prise")

    monkeypatch.setattr(palette_module.pyautogui, "screenshot", explode)

    assert sample_colors_at([]) == []


def test_a_click_outside_the_screen_does_not_crash(monkeypatch):
    screen = FakeScreen({(99, 99): (7, 7, 7)}, size=(100, 100))
    monkeypatch.setattr(palette_module.pyautogui, "screenshot", lambda: screen)

    assert sample_colors_at([(9999, 9999)]) == [(7, 7, 7)]


def test_build_palette_pairs_positions_with_sampled_colors(monkeypatch):
    screen = FakeScreen({(5, 5): (1, 2, 3), (6, 6): (4, 5, 6)})
    monkeypatch.setattr(palette_module.pyautogui, "screenshot", lambda: screen)

    palette = build_palette([(5, 5), (6, 6)])

    assert palette.swatches == [((5, 5), (1, 2, 3)), ((6, 6), (4, 5, 6))]


def test_saving_then_loading_gives_back_the_same_palette(tmp_path):
    palette = ColorPalette()
    palette.add_swatch((10, 20), (255, 0, 0))
    palette.add_swatch((30, 40), (0, 255, 0))
    path = tmp_path / "palette.json"

    save_palette(palette, str(path))
    reloaded = load_palette(str(path))

    assert reloaded.swatches == palette.swatches


def test_saving_creates_missing_directories(tmp_path):
    path = tmp_path / "nested" / "dir" / "palette.json"

    save_palette(ColorPalette(), str(path))

    assert path.exists()


def test_select_color_moves_and_clicks_on_the_swatch(fake_mouse):
    palette = ColorPalette()
    palette.add_swatch((123, 456), (255, 0, 0))

    result = select_color(fake_mouse, palette, (240, 10, 10))

    assert result == ((123, 456), (255, 0, 0))
    assert fake_mouse.moves() == [(123, 456)]
    assert fake_mouse.count("click") == 1


def test_select_color_does_nothing_without_swatches(fake_mouse):
    assert select_color(fake_mouse, ColorPalette(), (0, 0, 0)) is None
    assert fake_mouse.events == []
