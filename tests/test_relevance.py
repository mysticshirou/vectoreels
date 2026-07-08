import pytest

from vectoreels.irrelevant_captions import IRRELEVANT_CAPTIONS
from vectoreels.relevance import cosine_similarity, is_irrelevant_caption, to_bag_of_words


def test_to_bag_of_words_lowercases_and_counts_repeated_words() -> None:
    assert to_bag_of_words("Cat cat DOG") == {"cat": 2, "dog": 1}


def test_to_bag_of_words_ignores_punctuation() -> None:
    assert to_bag_of_words("wow!! amazing...") == {"wow": 1, "amazing": 1}


def test_cosine_similarity_identical_vectors_is_one() -> None:
    vector = {"cat": 1, "dog": 2}
    assert cosine_similarity(vector, vector) == pytest.approx(1.0)


def test_cosine_similarity_disjoint_vectors_is_zero() -> None:
    assert cosine_similarity({"cat": 1}, {"dog": 1}) == 0.0


def test_cosine_similarity_handles_different_dimensions() -> None:
    a = {"cat": 1, "dog": 1}
    b = {"dog": 1, "bird": 1, "fish": 1}
    # shared term "dog": dot=1, norm_a=sqrt(2), norm_b=sqrt(3)
    assert cosine_similarity(a, b) == pytest.approx(1 / (2**0.5 * 3**0.5))


def test_cosine_similarity_empty_vector_is_zero() -> None:
    assert cosine_similarity({}, {"cat": 1}) == 0.0


def test_is_irrelevant_caption_flags_near_duplicate() -> None:
    refs = ["Follow for more content like this"]
    caption = "follow for more content like this!!"
    assert is_irrelevant_caption(caption, reference_captions=refs, threshold=0.95)


def test_is_irrelevant_caption_does_not_flag_unrelated_caption() -> None:
    refs = ["Follow for more content like this"]
    caption = "My dog just learned a new trick today"
    assert not is_irrelevant_caption(caption, reference_captions=refs, threshold=0.95)


def test_is_irrelevant_caption_empty_caption_is_never_flagged() -> None:
    assert not is_irrelevant_caption("", reference_captions=["anything"])


def test_is_irrelevant_caption_uses_embedded_list_by_default() -> None:
    assert is_irrelevant_caption(IRRELEVANT_CAPTIONS[0]) is True
