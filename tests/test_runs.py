import numpy as np

from autosketch.drawing.runs import extract_color_runs

COLORS = {"a": (0, 0, 0), "b": (255, 255, 255), "c": (255, 0, 0)}


def make_grid(rows):
    return np.array([[COLORS[char] for char in row] for row in rows], dtype=np.uint8)


def total_runs(runs):
    return sum(len(boxes) for boxes in runs.values())


def test_uniform_grid_collapses_to_one_run_per_line():
    runs = extract_color_runs(make_grid(["aaaa", "aaaa"]))

    assert list(runs) == [COLORS["a"]]
    # 2 lignes valent mieux que 4 colonnes : le balayage horizontal doit gagner.
    assert total_runs(runs) == 2


def test_horizontal_stripes_are_scanned_horizontally():
    runs = extract_color_runs(make_grid(["aaaa", "bbbb", "aaaa", "bbbb"]))

    # 4 traits en horizontal contre 16 en vertical.
    assert total_runs(runs) == 4
    for boxes in runs.values():
        for row_start, col_start, row_end, col_end in boxes:
            assert row_start == row_end          # chaque trait tient sur une ligne
            assert (col_start, col_end) == (0, 3)


def test_vertical_stripes_are_scanned_vertically():
    runs = extract_color_runs(make_grid(["abab", "abab", "abab", "abab"]))

    # 4 traits en vertical contre 16 en horizontal.
    assert total_runs(runs) == 4
    for boxes in runs.values():
        for row_start, col_start, row_end, col_end in boxes:
            assert col_start == col_end          # chaque trait tient sur une colonne
            assert (row_start, row_end) == (0, 3)


def test_fusion_beats_drawing_cell_by_cell():
    grid = make_grid(["aaaaaaaa"] * 8)
    runs = extract_color_runs(grid)

    assert total_runs(runs) < grid.shape[0] * grid.shape[1]


def test_runs_cover_every_cell_exactly_once():
    grid = make_grid(["abca", "bbca", "aacc"])
    runs = extract_color_runs(grid)

    covered = []
    for color, boxes in runs.items():
        for row_start, col_start, row_end, col_end in boxes:
            for row in range(row_start, row_end + 1):
                for col in range(col_start, col_end + 1):
                    covered.append((row, col))
                    assert tuple(int(v) for v in grid[row, col]) == color

    rows, cols = grid.shape[:2]
    assert sorted(covered) == sorted((r, c) for r in range(rows) for c in range(cols))


def test_single_cell_grid():
    runs = extract_color_runs(make_grid(["a"]))

    assert runs == {COLORS["a"]: [(0, 0, 0, 0)]}


def test_checkerboard_cannot_be_compressed():
    grid = make_grid(["abab", "baba", "abab", "baba"])
    runs = extract_color_runs(grid)

    assert total_runs(runs) == grid.shape[0] * grid.shape[1]
