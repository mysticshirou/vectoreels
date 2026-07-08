import pytest

from vectoreels.models import GroupedLabelValue, LikedPost, ProcessedPost, SimpleLabelValue
from vectoreels.process import (
    clean_caption,
    extract_caption,
    extract_hashtags,
    extract_url,
    process_post,
    process_posts,
)


def _simple(label: str, value: str) -> SimpleLabelValue:
    return SimpleLabelValue(label=label, value=value)


def _hashtags(*names: str) -> GroupedLabelValue:
    return GroupedLabelValue(
        title="Hashtags",
        dict=[GroupedLabelValue(title="", dict=[_simple("Name", name)]) for name in names],
    )


def test_extract_url_finds_top_level_url() -> None:
    label_values = [_simple("URL", "https://www.instagram.com/reel/abc/"), _simple("Caption", "hi")]
    assert extract_url(label_values) == "https://www.instagram.com/reel/abc/"


def test_extract_url_raises_when_missing() -> None:
    with pytest.raises(ValueError):
        extract_url([_simple("Caption", "hi")])


def test_extract_caption_returns_value() -> None:
    label_values = [_simple("Caption", "hello world")]
    assert extract_caption(label_values) == "hello world"


def test_extract_caption_returns_empty_when_missing() -> None:
    assert extract_caption([_simple("Title", "")]) == ""


def test_extract_hashtags_returns_names_in_order() -> None:
    label_values = [_hashtags("space", "astronomy", "fyp")]
    assert extract_hashtags(label_values) == ["space", "astronomy", "fyp"]


def test_extract_hashtags_returns_empty_list_when_no_tags() -> None:
    label_values = [_hashtags()]
    assert extract_hashtags(label_values) == []


def test_extract_hashtags_returns_empty_list_when_absent() -> None:
    assert extract_hashtags([_simple("Caption", "hi")]) == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("levels to ts #fyp #astronomy #space #science", "levels to ts"),
        ("no tags here", "no tags here"),
        ("leading tag\n#tag1 #tag2", "leading tag"),
        ("mid #tag sentence", "mid sentence"),
        ("", ""),
        ("#OnlyHashtags", ""),
        ("Unicode caption #cafénow stays", "Unicode caption stays"),
    ],
)
def test_clean_caption_strips_hashtag_tokens(raw: str, expected: str) -> None:
    assert clean_caption(raw) == expected


def test_process_post_assembles_processed_post() -> None:
    post = LikedPost(
        timestamp=123,
        media=[],
        fbid="fb1",
        label_values=[
            _simple("URL", "https://www.instagram.com/reel/abc/"),
            _simple("Caption", "levels to ts #fyp #astronomy"),
            _simple("Title", ""),
            _hashtags("fyp", "astronomy"),
        ],
    )

    result = process_post(post)

    assert result == ProcessedPost(
        fbid="fb1",
        timestamp=123,
        url="https://www.instagram.com/reel/abc/",
        caption="levels to ts",
        hashtags=["fyp", "astronomy"],
    )


def test_process_posts_maps_over_all_posts() -> None:
    post = LikedPost(
        timestamp=1,
        media=[],
        fbid="fb1",
        label_values=[_simple("URL", "https://www.instagram.com/reel/abc/")],
    )

    result = process_posts([post, post])

    assert len(result) == 2
    assert all(p.fbid == "fb1" for p in result)
