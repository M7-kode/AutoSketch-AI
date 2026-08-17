from autosketch.screen.calibration import map_points


def test_image_corners_land_on_zone_corners():
    points = map_points([(0, 0), (100, 50)], (50, 100), (10, 20), (110, 70))

    assert points == [(10, 20), (110, 70)]


def test_center_of_image_lands_on_center_of_zone():
    points = map_points([(50, 50)], (100, 100), (0, 0), (200, 200))

    assert points == [(100, 100)]


def test_image_is_scaled_down_to_a_smaller_zone():
    points = map_points([(100, 100)], (100, 100), (0, 0), (50, 50))

    assert points == [(50, 50)]


def test_zone_offset_is_applied():
    points = map_points([(0, 0)], (10, 10), (300, 400), (310, 410))

    assert points == [(300, 400)]


def test_result_is_rounded_to_whole_pixels():
    points = map_points([(1, 1)], (3, 3), (0, 0), (10, 10))

    for x, y in points:
        assert isinstance(x, int) and isinstance(y, int)


def test_no_points_gives_no_points():
    assert map_points([], (10, 10), (0, 0), (10, 10)) == []


def test_every_mapped_point_stays_inside_the_zone():
    source = [(x, y) for x in range(0, 101, 10) for y in range(0, 101, 10)]
    points = map_points(source, (100, 100), (50, 60), (250, 360))

    for x, y in points:
        assert 50 <= x <= 250
        assert 60 <= y <= 360
