import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence

from vectoreels.processing.irrelevant_captions import IRRELEVANT_CAPTIONS

DEFAULT_THRESHOLD = 0.95

_WORD_PATTERN = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    return _WORD_PATTERN.findall(text.lower())


def to_bag_of_words(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def cosine_similarity(a: Mapping[str, int], b: Mapping[str, int]) -> float:
    shared_terms = set(a) & set(b)
    dot_product = sum(a[term] * b[term] for term in shared_terms)
    norm_a = math.sqrt(sum(count * count for count in a.values()))
    norm_b = math.sqrt(sum(count * count for count in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def is_irrelevant_caption(
    caption: str,
    reference_captions: Sequence[str] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> bool:
    if not caption:
        return False
    references = IRRELEVANT_CAPTIONS if reference_captions is None else reference_captions
    caption_vector = to_bag_of_words(caption)
    return any(
        cosine_similarity(caption_vector, to_bag_of_words(reference)) >= threshold
        for reference in references
    )
