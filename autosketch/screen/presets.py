"""Calibrations enregistrees par site.

La position de la zone de dessin et des couleurs depend de ton ecran, de ton
zoom et de la position de ta fenetre : rien n'est codable en dur, on enregistre
donc ce que tu as calibre chez toi.
"""

import json
import os
import sys

from autosketch.screen.palette import ColorPalette


def default_presets_dir():
    """Ou enregistrer les calibrations.

    Dans l'executable, __file__ pointe dans le dossier temporaire que
    PyInstaller efface a la fermeture : y ecrire ferait perdre la calibration
    a chaque redemarrage. On passe donc par le dossier utilisateur, toujours
    accessible en ecriture meme si l'exe est lance depuis un dossier protege.
    """
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "AutoSketch", "presets")

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(project_root, "presets")


PRESETS_DIR = default_presets_dir()

SITE_PRESETS = [
    ("Skribbl.io", "skribbl"),
    ("Gartic Phone", "gartic_phone"),
    ("Paint", "paint"),
    ("Autre", "autre"),
]

SITE_NAMES = [label for label, _ in SITE_PRESETS]


def preset_path(site_name):
    for label, slug in SITE_PRESETS:
        if label == site_name:
            return os.path.join(PRESETS_DIR, f"{slug}.json")
    raise ValueError(f"Site inconnu : {site_name}")


def has_preset(site_name):
    return os.path.exists(preset_path(site_name))


def save_site_preset(site_name, palette, zone):
    path = preset_path(site_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "palette": [{"position": list(position), "color": list(color)}
                    for position, color in palette.swatches],
        "zone": [list(zone[0]), list(zone[1])],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_site_preset(site_name):
    """Retourne (palette, zone) ou None si le site n'a jamais ete calibre."""
    path = preset_path(site_name)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    palette = ColorPalette()
    for entry in data.get("palette", []):
        palette.add_swatch(tuple(entry["position"]), tuple(entry["color"]))

    zone = data.get("zone")
    if not zone:
        return None
    return palette, (tuple(zone[0]), tuple(zone[1]))
