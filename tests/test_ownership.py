from vectoreels.processing.ownership import find_single_account_captions

DEFAULT_THRESHOLD = 0.9


def test_finds_caption_dominated_by_one_account() -> None:
    pairs = [("shared caption", "alice")] * 9 + [("shared caption", "bob")]
    assert find_single_account_captions(pairs) == {"shared caption"}


def test_excludes_caption_spread_across_accounts() -> None:
    pairs = [(f"shared caption", f"account_{i}") for i in range(10)]
    assert find_single_account_captions(pairs) == set()


def test_ignores_empty_captions() -> None:
    pairs = [("", "alice")] * 10
    assert find_single_account_captions(pairs) == set()


def test_threshold_is_exclusive_boundary_respecting() -> None:
    # exactly 90% -> meets the >= 0.9 default threshold
    pairs = [("caption", "alice")] * 9 + [("caption", "bob")]
    assert find_single_account_captions(pairs, threshold=0.9) == {"caption"}


def test_custom_threshold() -> None:
    pairs = [("caption", "alice")] * 5 + [("caption", "bob")] * 5
    assert find_single_account_captions(pairs, threshold=0.5) == {"caption"}
    assert find_single_account_captions(pairs, threshold=0.6) == set()
