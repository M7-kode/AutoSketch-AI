import numpy as np

import cv2

from autosketch.drawing.plan import (
    DrawPlan,
    build_color_plan,
    build_contour_plan,
    build_pixel_plan,
    distinct_color_count,
)


def logo_image():
    """Fond uni et une forme simple : le cas type d'un dessin de Skribbl."""
    image = np.full((200, 200, 3), 255, dtype=np.uint8)
    cv2.circle(image, (100, 100), 45, (0, 0, 200), -1)
    return image


def all_points(plan):
    return [point for _, paths in plan.groups for path in paths for point in path]


def assert_within_source(plan):
    height, width = plan.source_shape
    for x, y in all_points(plan):
        assert 0 <= x <= width
        assert 0 <= y <= height


def test_plan_counts_its_paths():
    plan = DrawPlan(groups=[(None, [[(0, 0)], [(1, 1)]]), ((1, 2, 3), [[(2, 2)]])],
                    source_shape=(10, 10))

    assert plan.path_count() == 3


# -- contours --

def test_contour_plan_finds_the_shape(shape_image):
    plan = build_contour_plan(shape_image)

    assert plan.path_count() > 0
    assert plan.source_shape == (100, 100)


def test_contour_plan_traces_in_a_single_color(shape_image):
    plan = build_contour_plan(shape_image)

    assert plan.colors() == [None]


def test_contour_plan_stays_inside_the_image(shape_image):
    assert_within_source(build_contour_plan(shape_image))


def test_a_blank_image_has_nothing_to_draw():
    blank = np.full((50, 50, 3), 255, dtype=np.uint8)

    plan = build_contour_plan(blank)

    assert plan.path_count() == 0
    assert plan.groups == []


def test_less_detail_simplifies_the_trace(shape_image):
    detailed = build_contour_plan(shape_image, epsilon_ratio=0.001, smooth=False)
    coarse = build_contour_plan(shape_image, epsilon_ratio=0.04, smooth=False)

    assert len(all_points(coarse)) <= len(all_points(detailed))


# -- couleur --

def test_color_plan_makes_one_group_per_color(two_tone_image):
    plan = build_color_plan(two_tone_image, palette_colors_rgb=[(255, 0, 0), (0, 0, 255)],
                            skip_background=False)

    assert len(plan.groups) == 2


def test_color_plan_only_uses_palette_colors(two_tone_image):
    palette = [(255, 0, 0), (0, 0, 255)]

    plan = build_color_plan(two_tone_image, palette_colors_rgb=palette, skip_background=False)

    for color in plan.colors():
        assert color in palette


def test_color_plan_stays_inside_the_image(two_tone_image):
    assert_within_source(build_color_plan(two_tone_image,
                                          palette_colors_rgb=[(255, 0, 0), (0, 0, 255)],
                                          skip_background=False))


def test_color_plan_falls_back_to_kmeans_without_a_palette(two_tone_image):
    plan = build_color_plan(two_tone_image, color_count=2, skip_background=False)

    assert plan.path_count() > 0
    assert all(color is not None for color in plan.colors())


def test_a_palette_missing_the_background_color_still_draws_something():
    # Le bug remonte par l'utilisateur : avec une palette qui ne contient pas la
    # couleur du fond, toute l'image se ramene a une seule couleur. Elle n'a plus
    # qu'un contour, le cadre, et l'ecarter comme "fond" ne laissait plus rien.
    plan = build_color_plan(logo_image(), palette_colors_rgb=[(255, 0, 0), (0, 0, 255)])

    assert plan.path_count() > 0


def test_a_flat_image_is_drawn_rather_than_dropped():
    flat = np.full((60, 60, 3), (0, 0, 255), dtype=np.uint8)

    plan = build_color_plan(flat, palette_colors_rgb=[(255, 0, 0)])

    assert plan.path_count() > 0


def test_the_background_is_still_skipped_when_there_is_more_to_draw():
    # La retombee ne doit pas annuler l'optimisation dans le cas normal.
    plan = build_color_plan(logo_image(), palette_colors_rgb=[(255, 255, 255), (255, 0, 0)])

    assert plan.path_count() == 1  # le cercle seul, pas le cadre du fond


def test_counting_colors_explains_an_empty_plan():
    logo = logo_image()

    assert distinct_color_count(logo, palette_colors_rgb=[(255, 0, 0), (0, 0, 255)]) == 1
    assert distinct_color_count(logo, palette_colors_rgb=[(255, 255, 255), (255, 0, 0)]) == 2


def test_the_detail_slider_is_not_what_makes_a_plan_empty(two_tone_image):
    # Le message d'erreur conseillait de baisser le detail : c'etait faux, le
    # nombre de traces ne depend pas de ce reglage.
    palette = [(255, 0, 0), (0, 0, 255)]
    counts = {build_color_plan(two_tone_image, palette_colors_rgb=palette,
                               epsilon_ratio=ratio).path_count()
              for ratio in (0.001, 0.01, 0.028)}

    assert 0 not in counts


def test_skipping_the_background_drops_the_full_frame_contour():
    # Un fond uni couvre toute l'image : le tracer reviendrait a faire le tour de
    # la zone de dessin pour rien.
    image = np.full((40, 40, 3), (0, 0, 255), dtype=np.uint8)
    image[10:20, 10:20] = (255, 0, 0)

    with_background = build_color_plan(image, palette_colors_rgb=[(255, 0, 0), (0, 0, 255)],
                                       skip_background=False)
    without_background = build_color_plan(image, palette_colors_rgb=[(255, 0, 0), (0, 0, 255)],
                                          skip_background=True)

    assert without_background.path_count() < with_background.path_count()


# -- pixels --

def test_pixel_plan_reports_the_grid_as_its_reference(two_tone_image):
    plan = build_pixel_plan(two_tone_image, cols=8, palette_colors_rgb=[(255, 0, 0), (0, 0, 255)])

    rows, cols = plan.source_shape
    assert cols == 8
    assert rows == 8  # l'image est carree


def test_pixel_plan_stays_inside_the_grid(two_tone_image):
    assert_within_source(build_pixel_plan(two_tone_image, cols=8,
                                          palette_colors_rgb=[(255, 0, 0), (0, 0, 255)]))


def test_pixel_plan_only_uses_palette_colors(two_tone_image):
    palette = [(255, 0, 0), (0, 0, 255)]

    plan = build_pixel_plan(two_tone_image, cols=6, palette_colors_rgb=palette)

    for color in plan.colors():
        assert color in palette


def test_pixel_plan_draws_far_fewer_strokes_than_there_are_cells(two_tone_image):
    # C'est tout l'interet de la fusion : deux aplats ne doivent pas couter 64 traits.
    plan = build_pixel_plan(two_tone_image, cols=8, palette_colors_rgb=[(255, 0, 0), (0, 0, 255)])

    assert plan.path_count() < 8 * 8


def test_a_long_stroke_gets_more_fill_passes_than_a_short_one():
    # Sinon les zones etirees ressortent clairsemees par rapport aux petites.
    tall = np.zeros((40, 10, 3), dtype=np.uint8)
    tall[:, :] = (0, 0, 255)

    plan = build_pixel_plan(tall, cols=4, palette_colors_rgb=[(255, 0, 0)])
    rows, _ = plan.source_shape
    longest = max(len(path) for _, paths in plan.groups for path in paths)

    assert longest > 4
