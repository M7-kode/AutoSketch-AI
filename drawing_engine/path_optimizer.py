import math


def _distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def optimize_path_order(paths, start_point=None):
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


def total_travel_distance(paths):
    if len(paths) < 2:
        return 0.0
    return sum(_distance(paths[i][-1], paths[i + 1][0]) for i in range(len(paths) - 1))
