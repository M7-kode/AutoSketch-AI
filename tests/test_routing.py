from autosketch.drawing.routing import (
    optimize_path_order,
    refine_with_two_opt,
    total_travel_distance,
)


def test_travel_distance_of_a_single_path_is_zero():
    assert total_travel_distance([[(0, 0), (10, 10)]]) == 0.0


def test_travel_distance_counts_the_jumps_between_paths():
    paths = [[(0, 0), (10, 0)], [(20, 0), (30, 0)]]

    # un seul saut : de (10, 0) a (20, 0)
    assert total_travel_distance(paths) == 10.0


def test_ordering_reduces_the_distance_travelled_between_paths():
    scattered = [
        [(0, 0), (1, 0)],
        [(100, 100), (101, 100)],
        [(2, 0), (3, 0)],
        [(102, 100), (103, 100)],
    ]

    ordered = optimize_path_order(scattered)

    assert total_travel_distance(ordered) < total_travel_distance(scattered)


def test_ordering_keeps_every_path():
    paths = [[(0, 0), (1, 1)], [(5, 5), (6, 6)], [(9, 9), (8, 8)]]

    ordered = optimize_path_order(paths)

    assert len(ordered) == len(paths)
    for path in ordered:
        assert sorted(path) in [sorted(p) for p in paths]


def test_a_path_is_reversed_when_its_end_is_the_closest():
    # Depuis (0, 0), le trait [(50, 0), (10, 0)] est plus proche par sa fin.
    ordered = optimize_path_order([[(0, 0), (1, 0)], [(50, 0), (10, 0)]])

    assert ordered[1][0] == (10, 0)


def test_ordering_nothing_gives_nothing():
    assert optimize_path_order([]) == []


def test_two_opt_never_makes_the_route_worse():
    paths = [
        [(0, 0), (1, 0)],
        [(50, 50), (51, 50)],
        [(2, 0), (3, 0)],
        [(52, 50), (53, 50)],
        [(4, 0), (5, 0)],
    ]

    refined = refine_with_two_opt(paths)

    assert total_travel_distance(refined) <= total_travel_distance(paths)


def test_two_opt_keeps_every_path():
    paths = [[(0, 0), (1, 0)], [(9, 9), (8, 8)], [(4, 4), (5, 5)]]

    refined = refine_with_two_opt(paths)

    assert len(refined) == len(paths)


def test_two_opt_handles_trivial_input():
    assert refine_with_two_opt([]) == []
    assert refine_with_two_opt([[(0, 0), (1, 1)]]) == [[(0, 0), (1, 1)]]


def test_the_two_stages_combine_into_a_shorter_route():
    scattered = [
        [(0, 0), (1, 0)],
        [(80, 80), (81, 80)],
        [(2, 0), (3, 0)],
        [(82, 80), (83, 80)],
        [(4, 0), (5, 0)],
        [(84, 80), (85, 80)],
    ]

    optimized = refine_with_two_opt(optimize_path_order(scattered))

    assert total_travel_distance(optimized) < total_travel_distance(scattered)
