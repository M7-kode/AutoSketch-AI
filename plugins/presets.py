import json
import os

from plugins.palette import ColorPalette

PRESETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "presets")

# (libelle affiche, nom de fichier) -- la calibration (couleurs + zone de dessin) est
# propre a l'ecran de chaque utilisateur, donc enregistree localement plutot que
# codee en dur : on ne peut pas deviner la resolution/le zoom de ton navigateur.
SITE_PRESETS = [
    ("Skribbl.io", "skribbl"),
    ("Gartic Phone", "gartic_phone"),
    ("Paint", "paint"),
    ("Personnalise", "custom"),
]


def preset_path(site_name):
    for label, slug in SITE_PRESETS:
        if label == site_name:
            return os.path.join(PRESETS_DIR, f"{slug}.json")
    raise ValueError(f"Site inconnu : {site_name}")


def has_preset(site_name):
    return os.path.exists(preset_path(site_name))


def save_site_preset(site_name, palette, zone_top_left, zone_bottom_right):
    os.makedirs(PRESETS_DIR, exist_ok=True)
    data = {
        "palette": [{"position": list(position), "color": list(color)} for position, color in palette.swatches],
        "zone": [list(zone_top_left), list(zone_bottom_right)],
    }
    with open(preset_path(site_name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_site_preset(site_name):
    path = preset_path(site_name)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    palette = ColorPalette()
    for entry in data.get("palette", []):
        palette.add_swatch(tuple(entry["position"]), tuple(entry["color"]))

    zone = data.get("zone")
    zone_top_left = tuple(zone[0]) if zone else None
    zone_bottom_right = tuple(zone[1]) if zone else None
    return palette, zone_top_left, zone_bottom_right
