"""Construction des traces a dessiner, sans jamais piloter la souris.

Un plan est une liste de groupes (couleur, traces) exprimes dans le repere de
l'image source. C'est ce qui rend le moteur testable : on peut verifier le
resultat sans bouger la souris ni ouvrir de fenetre.
"""

from dataclasses import dataclass

from autosketch.drawing.paths import contours_to_paths, smooth_path
from autosketch.drawing.routing import optimize_path_order, refine_with_two_opt
from autosketch.drawing.runs import extract_color_runs
from autosketch.drawing.strokes import zigzag_fill_points
from autosketch.vision.colors import color_masks, quantize_colors, quantize_to_palette
from autosketch.vision.contours import (
    detect_edges,
    find_contours,
    find_contours_from_mask,
    is_background_like,
)
from autosketch.vision.grid import image_to_grid


@dataclass
class DrawPlan:
    """groups: [(couleur_rgb ou None, [trace, ...]), ...]
    source_shape: (hauteur, largeur) du repere dans lequel les traces sont exprimees."""

    groups: list
    source_shape: tuple

    def path_count(self):
        return sum(len(paths) for _, paths in self.groups)

    def colors(self):
        return [color for color, _ in self.groups]


def _optimize(paths):
    if not paths:
        return []
    return refine_with_two_opt(optimize_path_order(paths))


def _build_paths(contours, epsilon_ratio, smooth):
    paths = contours_to_paths(contours, epsilon_ratio=epsilon_ratio)
    if smooth:
        paths = [smooth_path(p) for p in paths]
    return paths


def _quantize(image, palette_colors_rgb, color_count, dither):
    if palette_colors_rgb:
        return quantize_to_palette(image, palette_colors_rgb, dither=dither)
    return quantize_colors(image, k=color_count)


def build_contour_plan(image, epsilon_ratio=0.01, smooth=True):
    """Trace les contours de l'image en une seule couleur (celle deja selectionnee)."""
    contours = find_contours(detect_edges(image))
    paths = _optimize(_build_paths(contours, epsilon_ratio, smooth))
    groups = [(None, paths)] if paths else []
    return DrawPlan(groups=groups, source_shape=image.shape[:2])


def build_color_plan(image, palette_colors_rgb=None, color_count=6, dither=False,
                     epsilon_ratio=0.01, smooth=True, skip_background=True):
    """Un groupe de contours par couleur, en suivant la palette quand elle est connue."""
    quantized, centers = _quantize(image, palette_colors_rgb, color_count, dither)

    groups = []
    for color_bgr, mask in color_masks(quantized, centers):
        contours = find_contours_from_mask(mask)
        if skip_background:
            contours = [c for c in contours if not is_background_like(c, image.shape)]
        paths = _optimize(_build_paths(contours, epsilon_ratio, smooth))
        if paths:
            b, g, r = color_bgr
            groups.append(((r, g, b), paths))

    return DrawPlan(groups=groups, source_shape=image.shape[:2])


def build_pixel_plan(image, cols, palette_colors_rgb=None, color_count=6, dither=False,
                     fill_lines=4):
    """Remplissage par cellules : les cellules voisines de meme couleur sont fusionnees
    en un seul trait, ce qui reduit fortement le nombre de mouvements de souris."""
    grid = image_to_grid(image, cols)
    quantized_grid, _ = _quantize(grid, palette_colors_rgb, color_count, dither)
    rows, cols = quantized_grid.shape[:2]

    groups = []
    for color_bgr, runs in extract_color_runs(quantized_grid).items():
        paths = []
        for row_start, col_start, row_end, col_end in runs:
            # Densite de remplissage constante : un trait long recoit plus de passes
            # qu'une cellule isolee, sinon les zones etirees ressortent clairsemees.
            height_cells = (row_end - row_start) + 1
            lines = max(1, round(fill_lines * height_cells))
            paths.append(zigzag_fill_points((col_start, row_start),
                                            (col_end + 1, row_end + 1), lines))
        b, g, r = color_bgr
        groups.append(((r, g, b), _optimize(paths)))

    return DrawPlan(groups=groups, source_shape=(rows, cols))
