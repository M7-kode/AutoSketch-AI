import cv2
import numpy as np


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
