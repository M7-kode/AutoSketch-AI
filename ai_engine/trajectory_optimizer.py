import math


def _distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def refine_with_two_opt(paths, max_passes=5):
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
