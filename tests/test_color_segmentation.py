import numpy as np
import pytest

from vision.color_segmentation import color_masks, quantize_colors, quantize_to_palette

RED_BGR = (0, 0, 255)
BLUE_BGR = (255, 0, 0)


def unique_colors(image):
    return {tuple(int(v) for v in pixel) for row in image for pixel in row}


def test_quantizing_only_produces_colors_from_the_palette(two_tone_image):
    palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    quantized, _ = quantize_to_palette(two_tone_image, palette)

    palette_bgr = {(b, g, r) for r, g, b in palette}
    assert unique_colors(quantized).issubset(palette_bgr)


def test_quantizing_keeps_the_image_geometry(two_tone_image):
    quantized, _ = quantize_to_palette(two_tone_image, [(255, 0, 0), (0, 0, 255)])

    assert quantized.shape == two_tone_image.shape
    assert quantized.dtype == two_tone_image.dtype


def test_a_color_absent_from_the_palette_snaps_to_the_closest_one():
    # Une image entierement orange avec une palette rouge/bleu doit virer au rouge.
    image = np.full((10, 10, 3), (0, 80, 255), dtype=np.uint8)

    quantized, _ = quantize_to_palette(image, [(255, 0, 0), (0, 0, 255)])

    assert unique_colors(quantized) == {RED_BGR}


def test_centers_are_returned_in_bgr_to_match_the_image(two_tone_image):
    _, centers = quantize_to_palette(two_tone_image, [(255, 0, 0)])

    assert centers == [RED_BGR]


def test_an_empty_palette_is_rejected(two_tone_image):
    with pytest.raises(ValueError):
        quantize_to_palette(two_tone_image, [])


def test_dithering_does_not_introduce_colors_outside_the_palette():
    gradient = np.zeros((20, 20, 3), dtype=np.uint8)
    for column in range(20):
        gradient[:, column] = (0, 0, column * 12)
    palette = [(255, 0, 0), (0, 0, 0)]

    quantized, _ = quantize_to_palette(gradient, palette, dither=True)

    assert unique_colors(quantized).issubset({RED_BGR, (0, 0, 0)})


def test_kmeans_reduces_the_image_to_k_colors():
    image = np.random.randint(0, 255, (30, 30, 3), dtype=np.uint8)

    quantized, centers = quantize_colors(image, k=4)

    assert len(centers) == 4
    assert len(unique_colors(quantized)) <= 4


def test_kmeans_never_asks_for_more_colors_than_there_are_pixels():
    image = np.full((2, 2, 3), 128, dtype=np.uint8)

    _, centers = quantize_colors(image, k=99)

    assert len(centers) <= 4


def test_masks_split_the_image_without_overlapping(two_tone_image):
    quantized, centers = quantize_to_palette(two_tone_image, [(255, 0, 0), (0, 0, 255)])

    masks = color_masks(quantized, centers)
    total = sum((mask > 0).sum() for _, mask in masks)

    assert total == two_tone_image.shape[0] * two_tone_image.shape[1]


def test_a_mask_selects_exactly_its_own_color(two_tone_image):
    quantized, centers = quantize_to_palette(two_tone_image, [(255, 0, 0), (0, 0, 255)])

    for color_bgr, mask in color_masks(quantized, centers):
        selected = quantized[mask > 0]
        assert all(tuple(int(v) for v in pixel) == color_bgr for pixel in selected)
