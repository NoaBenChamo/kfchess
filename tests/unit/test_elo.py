from server.elo import calculate_new_ratings


def test_win_against_stronger_opponent_gains_more_than_equal():
    equal_win = calculate_new_ratings(1200, 1200, "w")
    upset_win = calculate_new_ratings(1200, 1400, "w")

    equal_gain = equal_win[0] - 1200
    upset_gain = upset_win[0] - 1200

    assert upset_gain > equal_gain


def test_loss_against_stronger_opponent_loses_less_than_equal():
    equal_loss = calculate_new_ratings(1200, 1200, "b")
    expected_loss = calculate_new_ratings(1200, 1400, "b")

    equal_drop = 1200 - equal_loss[0]
    soft_drop = 1200 - expected_loss[0]

    assert soft_drop < equal_drop


def test_both_ratings_change_on_white_win():
    new_white, new_black = calculate_new_ratings(1200, 1200, "w")
    assert new_white > 1200
    assert new_black < 1200
    assert (new_white - 1200) == (1200 - new_black)


def test_draw_keeps_equal_ratings_equal():
    new_white, new_black = calculate_new_ratings(1200, 1200, "d")
    assert new_white == 1200
    assert new_black == 1200
