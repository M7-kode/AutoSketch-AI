from autosketch.settings import clamp_detail, detail_to_epsilon_ratio, detail_to_grid_cols


def test_clamp_detail_stays_within_bounds():
    assert clamp_detail(0) == 1
    assert clamp_detail(-5) == 1
    assert clamp_detail(99) == 10
    assert clamp_detail(5) == 5


def test_clamp_detail_accepts_the_float_from_the_slider():
    assert clamp_detail(4.6) == 5


def test_more_detail_means_less_simplification():
    assert detail_to_epsilon_ratio(10) < detail_to_epsilon_ratio(5) < detail_to_epsilon_ratio(1)


def test_epsilon_ratio_stays_a_small_positive_fraction():
    # cv2.approxPolyDP prend un ratio du perimetre : au-dela de quelques
    # pourcents la forme est detruite, en dessous de 0 il leve une erreur.
    for detail in range(1, 11):
        assert 0 < detail_to_epsilon_ratio(detail) < 0.05


def test_more_detail_means_more_grid_columns():
    assert detail_to_grid_cols(1) < detail_to_grid_cols(10)


def test_grid_columns_stay_usable():
    for detail in range(1, 11):
        assert 4 <= detail_to_grid_cols(detail) <= 64
