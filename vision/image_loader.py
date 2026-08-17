import cv2
import numpy as np
import requests


def load_image(path):
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Impossible de charger l'image : {path}")
    return image


def load_image_from_url(url, timeout=15):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    data = np.frombuffer(response.content, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Le contenu de cette URL n'est pas une image valide.")
    return image


def get_image_info(image):
    height, width = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1
    return {"width": width, "height": height, "channels": channels}
