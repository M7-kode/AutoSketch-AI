"""Ordre de passage des traces : minimiser la distance parcourue a vide.

Deux etapes complementaires. Le glouton donne un ordre correct tres vite,
le 2-opt le raffine en defaisant les croisements que le glouton laisse.
"""

import math


def _distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def total_travel_distance(paths):
    """Distance parcourue bouton relache, entre la fin d'un trace et le debut du suivant."""
    if len(paths) < 2:
        return 0.0
    return sum(_distance(paths[i][-1], paths[i + 1][0]) for i in range(len(paths) - 1))


def optimize_path_order(paths, start_point=None):
    """Plus proche voisin : a chaque etape on prend le trace le plus proche, en le
    retournant si on l'attaque plus court par la fin."""
    if not paths:
        return []

    remaining = [list(p) for p in paths]
    ordered = []
    current_point = start_point if start_point is not None else remaining[0][0]

    while remaining:
        best_index = None
        best_distance = None
        best_path = None

        for i, path in enumerate(remaining):
            d_start = _distance(current_point, path[0])
            d_end = _distance(current_point, path[-1])
            if d_end < d_start:
                candidate, d = list(reversed(path)), d_end
            else:
                candidate, d = path, d_start

            if best_distance is None or d < best_distance:
                best_distance = d
                best_index = i
                best_path = candidate

        remaining.pop(best_index)
        ordered.append(best_path)
        current_point = best_path[-1]

    return ordered


def refine_with_two_opt(paths, max_passes=5):
    """Inverse les segments d'itineraire qui se croisent, tant que ca raccourcit le trajet."""
    order = [list(p) for p in paths]
    n = len(order)
    if n < 2:
        return order

    def entry(k):
        return order[k][0]

    def exit_(k):
        return order[k][-1]

    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(n - 1):
            for j in range(i + 1, n):
                old_cost = _distance(exit_(i), entry(i + 1))
                if j + 1 < n:
                    old_cost += _distance(exit_(j), entry(j + 1))

                new_cost = _distance(exit_(i), exit_(j))
                if j + 1 < n:
                    new_cost += _distance(entry(i + 1), entry(j + 1))

                if new_cost < old_cost - 1e-6:
                    segment = order[i + 1:j + 1]
                    segment.reverse()
                    segment = [list(reversed(p)) for p in segment]
                    order[i + 1:j + 1] = segment
                    improved = True

    return order
