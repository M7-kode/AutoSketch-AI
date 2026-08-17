import os
import sys

import pytest

from autosketch.screen import presets as presets_module
from autosketch.screen.palette import ColorPalette
from autosketch.screen.presets import (
    SITE_NAMES,
    SITE_PRESETS,
    default_presets_dir,
    has_preset,
    load_site_preset,
    preset_path,
    save_site_preset,
)


@pytest.fixture(autouse=True)
def isolated_presets_dir(tmp_path, monkeypatch):
    """Ne jamais toucher aux vraies calibrations de l'utilisateur pendant les tests."""
    monkeypatch.setattr(presets_module, "PRESETS_DIR", str(tmp_path / "presets"))


@pytest.fixture
def palette():
    palette = ColorPalette()
    palette.add_swatch((10, 20), (255, 0, 0))
    palette.add_swatch((30, 40), (0, 255, 0))
    return palette


def test_from_the_sources_the_presets_sit_at_the_project_root(monkeypatch):
    # Le module vit dans autosketch/screen/ : il faut remonter jusqu'a la racine,
    # pas s'arreter dans le package.
    monkeypatch.delattr(sys, "frozen", raising=False)
    directory = default_presets_dir()

    assert os.path.basename(directory) == "presets"
    assert os.path.basename(os.path.dirname(directory)) != "autosketch"
    assert os.path.isdir(os.path.dirname(directory))


def test_in_the_executable_the_presets_leave_the_temporary_bundle(monkeypatch, tmp_path):
    # PyInstaller efface son dossier temporaire a la fermeture : y ecrire ferait
    # perdre la calibration a chaque redemarrage.
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))

    directory = default_presets_dir()

    assert str(tmp_path / "Roaming") in directory
    assert os.path.basename(directory) == "presets"


def test_the_executable_still_has_somewhere_to_write_without_appdata(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("APPDATA", raising=False)

    directory = default_presets_dir()

    assert directory.startswith(os.path.expanduser("~"))


def test_the_expected_sites_are_offered():
    assert "Skribbl.io" in SITE_NAMES
    assert "Gartic Phone" in SITE_NAMES
    assert "Paint" in SITE_NAMES


def test_each_site_gets_its_own_file():
    paths = [preset_path(name) for name in SITE_NAMES]

    assert len(set(paths)) == len(paths)


def test_an_unknown_site_is_rejected():
    with pytest.raises(ValueError):
        preset_path("Photoshop")


def test_saving_then_loading_gives_back_palette_and_zone(palette):
    save_site_preset("Skribbl.io", palette, ((100, 200), (500, 600)))

    reloaded_palette, zone = load_site_preset("Skribbl.io")

    assert reloaded_palette.swatches == palette.swatches
    assert zone == ((100, 200), (500, 600))


def test_sites_do_not_overwrite_each_other(palette):
    other = ColorPalette()
    other.add_swatch((1, 1), (9, 9, 9))

    save_site_preset("Skribbl.io", palette, ((0, 0), (10, 10)))
    save_site_preset("Paint", other, ((50, 50), (60, 60)))

    assert load_site_preset("Skribbl.io")[1] == ((0, 0), (10, 10))
    assert load_site_preset("Paint")[1] == ((50, 50), (60, 60))


def test_recalibrating_replaces_the_previous_calibration(palette):
    save_site_preset("Paint", palette, ((0, 0), (10, 10)))
    save_site_preset("Paint", palette, ((5, 5), (99, 99)))

    assert load_site_preset("Paint")[1] == ((5, 5), (99, 99))


def test_a_site_never_calibrated_returns_none():
    assert load_site_preset("Gartic Phone") is None
    assert has_preset("Gartic Phone") is False


def test_has_preset_after_saving(palette):
    save_site_preset("Paint", palette, ((0, 0), (10, 10)))

    assert has_preset("Paint") is True


def test_a_calibration_without_colors_is_still_usable():
    save_site_preset("Autre", ColorPalette(), ((0, 0), (10, 10)))

    reloaded_palette, zone = load_site_preset("Autre")

    assert len(reloaded_palette) == 0
    assert zone == ((0, 0), (10, 10))
