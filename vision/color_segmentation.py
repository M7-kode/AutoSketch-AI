import cv2
import numpy as np
from PIL import Image


def quantize_to_palette(image, palette_colors_rgb, dither=False):
    """Quantifie l'image (BGR) sur un jeu de couleurs fixe (RGB), comme DrawBot :
    chaque pixel produit correspond exactement a une couleur disponible dans la palette."""
    if not palette_colors_rgb:
        raise ValueError("La palette est vide.")

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)

    flat_colors = []
    for r, g, b in palette_colors_rgb:
        flat_colors.extend([r, g, b])
    flat_colors.extend([0] * (768 - len(flat_colors)))

    palette_image = Image.new("P", (16, 16))
    palette_image.putpalette(flat_colors)

    dither_mode = Image.FLOYDSTEINBERG if dither else Image.NONE
    quantized_pil = pil_image.quantize(palette=palette_image, dither=dither_mode).convert("RGB")

    quantized_rgb = np.array(quantized_pil)
    quantized_bgr = cv2.cvtColor(quantized_rgb, cv2.COLOR_RGB2BGR)
    centers = [(b, g, r) for r, g, b in palette_colors_rgb]
    return quantized_bgr, centers


def quantize_colors(image, k=6):
    data = image.reshape((-1, 3)).astype(np.float32)
    k = max(1, min(int(k), data.shape[0]))

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
    centers = centers.astype(np.uint8)
    quantized = centers[labels.flatten()].reshape(image.shape)
    return quantized, centers


def color_masks(quantized_image, centers):
    data = quantized_image.reshape((-1, 3))
    masks = []
    for center in centers:
        mask = np.all(data == center, axis=1).reshape(quantized_image.shape[:2])
        masks.append((tuple(int(c) for c in center), (mask.astype(np.uint8) * 255)))
    return masks
