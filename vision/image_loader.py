import cv2


def load_image(path):
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Impossible de charger l'image : {path}")
    return image


def get_image_info(image):
    height, width = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1
    return {"width": width, "height": height, "channels": channels}
