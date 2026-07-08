from collections import Counter, defaultdict
from collections.abc import Iterable

from vectoreels.processing.relevance import tokenize

BLOCK_PREFIX_LEN = 3


def cluster_captions(
    captions: Iterable[str | None],
    min_count: int = 10,
    block_prefix_len: int = BLOCK_PREFIX_LEN,
) -> list[tuple[str, int]]:
    """Group near-duplicate/truncated captions and return (representative_text,
    total_count) for every cluster whose combined occurrence count meets
    min_count. A cluster is formed when one caption's tokens are a prefix of
    another's, which catches the same caption cut short partway through.
    """
    counts: Counter[tuple[str, ...]] = Counter()
    original_text: dict[tuple[str, ...], str] = {}
    for caption in captions:
        if not caption:
            continue
        tokens = tuple(tokenize(caption))
        if not tokens:
            continue
        counts[tokens] += 1
        original_text.setdefault(tokens, caption)

    buckets: dict[tuple[str, ...], list[tuple[str, ...]]] = defaultdict(list)
    for tokens in counts:
        buckets[tokens[:block_prefix_len]].append(tokens)

    clusters: list[tuple[str, int]] = []
    seen: set[tuple[str, ...]] = set()
    for bucket in buckets.values():
        bucket.sort(key=len, reverse=True)
        for i, longer in enumerate(bucket):
            if longer in seen:
                continue
            seen.add(longer)
            total = counts[longer]
            for shorter in bucket[i + 1 :]:
                if shorter not in seen and longer[: len(shorter)] == shorter:
                    total += counts[shorter]
                    seen.add(shorter)
            if total >= min_count:
                clusters.append((original_text[longer], total))
    return clusters
