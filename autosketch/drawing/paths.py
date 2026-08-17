import cv2


def smooth_path(points, iterations=2, cut_ratio=0.25):
    """Chaikin corner-cutting: smooths a polyline while staying within the
    convex hull of the original points (no overshoot past sharp corners,
    unlike a Catmull-Rom spline)."""
    if len(points) < 3 or iterations < 1:
        return list(points)

    current = list(points)
    for _ in range(iterations):
        if len(current) < 3:
            break
        next_points = [current[0]]
        for p0, p1 in zip(current, current[1:]):
            next_points.append((
                p0[0] + (p1[0] - p0[0]) * cut_ratio,
                p0[1] + (p1[1] - p0[1]) * cut_ratio,
            ))
            next_points.append((
                p0[0] + (p1[0] - p0[0]) * (1 - cut_ratio),
                p0[1] + (p1[1] - p0[1]) * (1 - cut_ratio),
            ))
        next_points.append(current[-1])
        current = next_points

    return current


def contours_to_paths(contours, min_points=3, epsilon_ratio=0.01):
    paths = []
    for contour in contours:
        if len(contour) < min_points:
            continue
        perimeter = cv2.arcLength(contour, closed=True)
        epsilon = epsilon_ratio * perimeter
        simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
        if len(simplified) < 2:
            continue
        path = [(int(p[0][0]), int(p[0][1])) for p in simplified]
        path.append(path[0])
        paths.append(path)
    return paths
