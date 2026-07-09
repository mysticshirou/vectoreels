from typing import Any

import pytest

from vectoreels.processing.irrelevant_captions import IRRELEVANT_CAPTIONS
from vectoreels.models import (
    STAGE_CLEANED,
    STAGE_EMBEDDED,
    STAGE_TITLED,
    GroupedLabelValue,
    LikedPost,
    ProcessedPost,
    SimpleLabelValue,
)
from vectoreels.processing.process import (
    clean_caption,
    extract_caption,
    extract_hashtags,
    extract_owner_username,
    extract_url,
    process_and_index_posts,
    process_post,
)


class FakeStageIndex:
    def __init__(self, existing: list[ProcessedPost] | None = None) -> None:
        self.docs: dict[str, dict[str, Any]] = {p.fbid: p.model_dump() for p in existing or []}

    def existing_fbids(self, fbids: list[str]) -> set[str]:
        return {fbid for fbid in fbids if fbid in self.docs}

    def bulk_upsert(self, updates: list[dict[str, Any]]) -> None:
        for update in updates:
            fbid = update["fbid"]
            self.docs.setdefault(fbid, {"fbid": fbid})
            self.docs[fbid].update({k: v for k, v in update.items() if k != "fbid"})

    def posts_at_stage(self, stage: int) -> list[ProcessedPost]:
        return [
            ProcessedPost.model_validate(doc) for doc in self.docs.values() if doc.get("stage") == stage
        ]


def _simple(label: str, value: str) -> SimpleLabelValue:
    return SimpleLabelValue(label=label, value=value)


def _hashtags(*names: str) -> GroupedLabelValue:
    return GroupedLabelValue(
        title="Hashtags",
        dict=[GroupedLabelValue(title="", dict=[_simple("Name", name)]) for name in names],
    )


def _owner(username: str) -> GroupedLabelValue:
    return GroupedLabelValue(
        title="Owner",
        dict=[
            GroupedLabelValue(
                title="",
                dict=[_simple("URL", ""), _simple("Name", "Some Name"), _simple("Username", username)],
            )
        ],
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


def test_extract_owner_username_finds_username() -> None:
    label_values = [_owner("astrophysicsfeed")]
    assert extract_owner_username(label_values) == "astrophysicsfeed"


def test_extract_owner_username_returns_empty_when_absent() -> None:
    assert extract_owner_username([_simple("Caption", "hi")]) == ""


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


def test_process_post_nulls_out_caption_and_hashtags_when_caption_is_irrelevant() -> None:
    post = LikedPost(
        timestamp=123,
        media=[],
        fbid="fb1",
        label_values=[
            _simple("URL", "https://www.instagram.com/reel/abc/"),
            _simple("Caption", IRRELEVANT_CAPTIONS[0] + " #fyp #space"),
            _hashtags("fyp", "space"),
        ],
    )

    result = process_post(post)

    assert result.caption is None
    assert result.hashtags == []


def test_process_and_index_posts_keeps_caption_when_dominant_owner_shares_it() -> None:
    # 9 out of 10 posts sharing this irrelevant-looking caption are from the
    # same account -> it's actually that account's running theme, not spam.
    shared_caption = IRRELEVANT_CAPTIONS[0]
    dominant_posts = [
        LikedPost(
            timestamp=i,
            media=[],
            fbid=f"dominant-{i}",
            label_values=[
                _simple("URL", "https://www.instagram.com/reel/abc/"),
                _simple("Caption", shared_caption),
                _owner("same_account"),
            ],
        )
        for i in range(9)
    ]
    outlier_post = LikedPost(
        timestamp=100,
        media=[],
        fbid="outlier",
        label_values=[
            _simple("URL", "https://www.instagram.com/reel/abc/"),
            _simple("Caption", shared_caption),
            _owner("someone_else"),
        ],
    )
    index = FakeStageIndex()

    process_and_index_posts(dominant_posts + [outlier_post], index)

    assert all(doc["caption"] == shared_caption for doc in index.docs.values())


def test_process_and_index_posts_nulls_caption_when_no_dominant_owner() -> None:
    shared_caption = IRRELEVANT_CAPTIONS[0]
    posts = [
        LikedPost(
            timestamp=i,
            media=[],
            fbid=f"fb{i}",
            label_values=[
                _simple("URL", "https://www.instagram.com/reel/abc/"),
                _simple("Caption", shared_caption),
                _owner(f"account_{i}"),
            ],
        )
        for i in range(10)
    ]
    index = FakeStageIndex()

    process_and_index_posts(posts, index)

    assert all(doc["caption"] is None for doc in index.docs.values())


def test_process_and_index_posts_upserts_new_posts_at_cleaned_stage() -> None:
    post = LikedPost(
        timestamp=1,
        media=[],
        fbid="fb1",
        label_values=[_simple("URL", "https://www.instagram.com/reel/abc/")],
    )
    index = FakeStageIndex()

    process_and_index_posts([post], index)

    assert index.docs["fb1"]["stage"] == STAGE_CLEANED
    assert index.docs["fb1"]["music_title"] is None
    assert index.docs["fb1"]["audio_embedding"] is None


def test_process_and_index_posts_skips_posts_already_indexed() -> None:
    already_indexed = ProcessedPost(
        fbid="fb1",
        timestamp=1,
        url="https://www.instagram.com/reel/abc/",
        caption="original caption",
        hashtags=[],
        stage=STAGE_EMBEDDED,
    )
    index = FakeStageIndex(existing=[already_indexed])
    post = LikedPost(
        timestamp=1,
        media=[],
        fbid="fb1",
        label_values=[
            _simple("URL", "https://www.instagram.com/reel/abc/"),
            _simple("Caption", "a totally different caption"),
        ],
    )

    process_and_index_posts([post], index)

    assert index.docs["fb1"]["caption"] == "original caption"
    assert index.docs["fb1"]["stage"] == STAGE_EMBEDDED


def test_process_and_index_posts_looks_up_titles_for_cleaned_posts() -> None:
    posts = [
        LikedPost(
            timestamp=i,
            media=[],
            fbid=f"fb{i}",
            label_values=[_simple("URL", f"https://www.instagram.com/reel/{i}/")],
        )
        for i in range(3)
    ]
    titles_by_url = {
        "https://www.instagram.com/reel/0/": "Song A",
        "https://www.instagram.com/reel/2/": "Song B",
    }
    index = FakeStageIndex()

    process_and_index_posts(posts, index, music_title_lookup=titles_by_url.get)

    titled = {p.fbid: p.music_title for p in index.posts_at_stage(STAGE_TITLED)}
    assert titled == {"fb0": "Song A", "fb1": None, "fb2": "Song B"}


def test_process_and_index_posts_resumes_embedding_from_a_prior_titled_stage() -> None:
    # Simulates a laptop closing mid-embedding-run in an earlier upload: the
    # post is already at STAGE_TITLED in the index, from before this call.
    # It should be picked up for embedding even though this upload carries
    # no LikedPosts at all.
    already_titled = ProcessedPost(
        fbid="fb1",
        timestamp=1,
        url="https://www.instagram.com/reel/abc/",
        caption="hi",
        hashtags=[],
        music_title="Song A",
        stage=STAGE_TITLED,
    )
    index = FakeStageIndex(existing=[already_titled])

    process_and_index_posts(
        [], index, audio_embedding_lookup=lambda url: [1.0, 0.0]
    )

    embedded = index.posts_at_stage(STAGE_EMBEDDED)
    assert len(embedded) == 1
    assert embedded[0].fbid == "fb1"
    assert embedded[0].audio_embedding == [1.0, 0.0]


def test_process_and_index_posts_skips_a_stage_with_no_lookup() -> None:
    post = LikedPost(
        timestamp=1,
        media=[],
        fbid="fb1",
        label_values=[_simple("URL", "https://www.instagram.com/reel/abc/")],
    )
    index = FakeStageIndex()

    process_and_index_posts([post], index, audio_embedding_lookup=lambda url: [1.0])

    # music_title_lookup wasn't given, so the post never advances past
    # STAGE_CLEANED even though an audio lookup was available.
    assert index.docs["fb1"]["stage"] == STAGE_CLEANED


def test_process_and_index_posts_reports_only_caption_and_indexing_stages_without_lookups() -> None:
    post = LikedPost(
        timestamp=1,
        media=[],
        fbid="fb1",
        label_values=[_simple("URL", "https://www.instagram.com/reel/abc/")],
    )
    stages: list[str] = []
    index = FakeStageIndex()

    process_and_index_posts([post], index, on_stage=stages.append)

    assert stages == ["Cleaning captions and hashtags", "Indexing 1 new posts"]


def test_process_and_index_posts_reports_a_stage_per_active_lookup() -> None:
    post = LikedPost(
        timestamp=1,
        media=[],
        fbid="fb1",
        label_values=[_simple("URL", "https://www.instagram.com/reel/abc/")],
    )
    stages: list[str] = []
    index = FakeStageIndex()

    process_and_index_posts(
        [post],
        index,
        music_title_lookup=lambda url: None,
        audio_embedding_lookup=lambda url: None,
        on_stage=stages.append,
    )

    assert stages == [
        "Cleaning captions and hashtags",
        "Indexing 1 new posts",
        "Looking up song titles",
        "Looking up song titles (1/1)",
        "Downloading and embedding audio",
        "Downloading and embedding audio (1/1)",
    ]


def test_process_and_index_posts_reports_progress_per_completed_lookup() -> None:
    posts = [
        LikedPost(
            timestamp=i,
            media=[],
            fbid=f"fb{i}",
            label_values=[_simple("URL", f"https://www.instagram.com/reel/{i}/")],
        )
        for i in range(5)
    ]
    stages: list[str] = []
    index = FakeStageIndex()

    process_and_index_posts(posts, index, music_title_lookup=lambda url: None, on_stage=stages.append)

    progress = [s for s in stages if s.startswith("Looking up song titles (")]
    counts = sorted(int(s.split("(")[1].split("/")[0]) for s in progress)
    assert counts == [1, 2, 3, 4, 5]
