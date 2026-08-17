import cv2


def image_to_grid(image, cols, rows=None):
    cols = max(int(cols), 1)
    if rows is None:
        aspect = image.shape[0] / image.shape[1]
        rows = max(1, round(cols * aspect))
    else:
        rows = max(int(rows), 1)

    return cv2.resize(image, (cols, rows), interpolation=cv2.INTER_AREA)
