import cv2


def detect_edges(image, threshold1=50, threshold2=150):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return cv2.Canny(blurred, threshold1, threshold2)


def find_contours(edges):
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def find_contours_from_mask(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def is_background_like(contour, image_shape, area_ratio_threshold=0.9):
    image_area = image_shape[0] * image_shape[1]
    if image_area == 0:
        return False
    contour_area = cv2.contourArea(contour)
    return (contour_area / image_area) >= area_ratio_threshold
