"""Traduction du curseur unique "Detail" (1 a 10) vers les reglages du moteur.

Un seul curseur cote interface, deux echelles tres differentes cote moteur :
autant garder la conversion ici, ou elle se teste.
"""

DETAIL_MIN = 1
DETAIL_MAX = 10


def clamp_detail(detail):
    return max(DETAIL_MIN, min(int(round(float(detail))), DETAIL_MAX))


def detail_to_epsilon_ratio(detail):
    """Tolerance de simplification des contours : plus de detail = moins de simplification."""
    return (3.1 - 0.3 * clamp_detail(detail)) / 100.0


def detail_to_grid_cols(detail):
    """Nombre de colonnes de la grille en mode pixels."""
    return 4 + 6 * clamp_detail(detail)
