from collections import Counter, defaultdict
from collections.abc import Iterable

DEFAULT_THRESHOLD = 0.9


def find_single_account_captions(
    caption_owner_pairs: Iterable[tuple[str, str]],
    threshold: float = DEFAULT_THRESHOLD,
) -> set[str]:
    """Captions where at least `threshold` fraction of occurrences come from
    the same account. Such a caption is that account's recurring theme, not
    a generic caption recycled across unrelated reels.
    """
    owner_counts_by_caption: dict[str, Counter[str]] = defaultdict(Counter)
    for caption, username in caption_owner_pairs:
        if not caption:
            continue
        owner_counts_by_caption[caption][username] += 1

    return {
        caption
        for caption, owner_counts in owner_counts_by_caption.items()
        if max(owner_counts.values()) / sum(owner_counts.values()) >= threshold
    }
