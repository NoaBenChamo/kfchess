def calculate_new_ratings(white_rating, black_rating, result, k=32):
    """
    Pure ELO update.

    Args:
        white_rating: current white rating
        black_rating: current black rating
        result: "w" (white wins), "b" (black wins), or "d"/None (draw)
        k: K-factor (default 32)

    Returns:
        (new_white_rating, new_black_rating) as ints
    """
    if result in ("d", "draw", None):
        score_white, score_black = 0.5, 0.5
    elif result == "w":
        score_white, score_black = 1.0, 0.0
    elif result == "b":
        score_white, score_black = 0.0, 1.0
    else:
        raise ValueError(f"invalid result: {result!r}")

    expected_white = 1.0 / (
        1.0 + 10 ** ((black_rating - white_rating) / 400.0)
    )
    expected_black = 1.0 - expected_white

    new_white = round(white_rating + k * (score_white - expected_white))
    new_black = round(black_rating + k * (score_black - expected_black))
    return new_white, new_black
