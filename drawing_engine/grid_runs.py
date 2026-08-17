def extract_color_runs(quantized_grid):
    """Fusionne les cellules adjacentes de meme couleur en traits (comme DrawBot),
    en choisissant le sens de balayage (lignes ou colonnes) qui produit le moins de traits."""
    rows, cols = quantized_grid.shape[:2]

    def scan(vertical):
        outer_count = cols if vertical else rows
        inner_count = rows if vertical else cols
        runs = {}
        nb_runs = 0
        for outer in range(outer_count):
            run_color = None
            run_start = 0
            for inner in range(inner_count):
                row, col = (inner, outer) if vertical else (outer, inner)
                color = tuple(int(c) for c in quantized_grid[row, col])
                if run_color is None:
                    run_color = color
                    run_start = inner
                elif color != run_color:
                    runs.setdefault(run_color, []).append(_to_bbox(outer, run_start, inner - 1, vertical))
                    nb_runs += 1
                    run_color = color
                    run_start = inner
            runs.setdefault(run_color, []).append(_to_bbox(outer, run_start, inner_count - 1, vertical))
            nb_runs += 1
        return runs, nb_runs

    def _to_bbox(outer, start, end, vertical):
        if vertical:
            return (start, outer, end, outer)
        return (outer, start, outer, end)

    runs_by_row, nb_by_row = scan(False)
    runs_by_col, nb_by_col = scan(True)
    return runs_by_col if nb_by_col < nb_by_row else runs_by_row
