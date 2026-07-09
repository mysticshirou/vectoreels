import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Protocol, TypeVar

from vectoreels.models import (
    STAGE_CLEANED,
    STAGE_EMBEDDED,
    STAGE_TITLED,
    GroupedLabelValue,
    LikedPost,
    ProcessedPost,
    SimpleLabelValue,
)
from vectoreels.processing.ownership import find_single_account_captions
from vectoreels.processing.relevance import is_irrelevant_caption

MusicTitleLookup = Callable[[str], str | None]
AudioEmbeddingLookup = Callable[[str], list[float] | None]
StageReporter = Callable[[str], None]

_MUSIC_LOOKUP_WORKERS = 16
_AUDIO_EMBEDDING_WORKERS = 2

LabelValue = SimpleLabelValue | GroupedLabelValue

_T = TypeVar("_T")


class StageIndex(Protocol):
    """The Elasticsearch-backed seam process_and_index_posts is driven
    through: which fbids are already indexed, persisting field updates for
    a batch, and reading back everything sitting at a given stage (from
    this run or a prior one) so a stage's work only ever runs once."""

    def existing_fbids(self, fbids: list[str]) -> set[str]: ...
    def bulk_upsert(self, updates: list[dict[str, Any]]) -> None: ...
    def posts_at_stage(self, stage: int) -> list[ProcessedPost]: ...


_HASHTAG_TOKEN = re.compile(r"#\w+", re.UNICODE)
_EXTRA_SPACES = re.compile(r"[ \t]{2,}")


def extract_url(label_values: list[LabelValue]) -> str:
    for lv in label_values:
        if isinstance(lv, SimpleLabelValue) and lv.label == "URL":
            return lv.value
    raise ValueError("liked post is missing a URL label_value")


def extract_caption(label_values: list[LabelValue]) -> str:
    for lv in label_values:
        if isinstance(lv, SimpleLabelValue) and lv.label == "Caption":
            return lv.value
    return ""


def extract_owner_username(label_values: list[LabelValue]) -> str:
    for lv in label_values:
        if isinstance(lv, GroupedLabelValue) and lv.title == "Owner":
            for group in lv.items:
                if isinstance(group, GroupedLabelValue):
                    for inner in group.items:
                        if isinstance(inner, SimpleLabelValue) and inner.label == "Username":
                            return inner.value
    return ""


def extract_hashtags(label_values: list[LabelValue]) -> list[str]:
    for lv in label_values:
        if isinstance(lv, GroupedLabelValue) and lv.title == "Hashtags":
            return [
                inner.value
                for group in lv.items
                if isinstance(group, GroupedLabelValue)
                for inner in group.items
                if isinstance(inner, SimpleLabelValue) and inner.label == "Name"
            ]
    return []


def clean_caption(caption: str) -> str:
    without_hashtags = _HASHTAG_TOKEN.sub("", caption)
    return _EXTRA_SPACES.sub(" ", without_hashtags).strip()


def process_post(
    post: LikedPost, single_account_captions: frozenset[str] = frozenset()
) -> ProcessedPost:
    caption = clean_caption(extract_caption(post.label_values))
    hashtags = extract_hashtags(post.label_values)
    if is_irrelevant_caption(caption) and caption not in single_account_captions:
        caption = None
        hashtags = []
    return ProcessedPost(
        fbid=post.fbid,
        timestamp=post.timestamp,
        url=extract_url(post.label_values),
        caption=caption,
        hashtags=hashtags,
    )


def _advance_stage(
    index: StageIndex,
    from_stage: int,
    to_stage: int,
    lookup: Callable[[str], _T],
    field_name: str,
    stage_label: str,
    report: StageReporter,
    workers: int,
) -> None:
    """Looks up `field_name` for every post still at `from_stage` (whether
    left there by this run or an earlier one) and upserts each result the
    moment it's ready, batched at the pool's width so a crash mid-stage
    only ever loses an in-flight batch, not the whole stage."""
    posts = index.posts_at_stage(from_stage)
    if not posts:
        return

    report(stage_label)
    total = len(posts)
    batch: list[dict[str, Any]] = []

    def flush() -> None:
        if batch:
            index.bulk_upsert(list(batch))
            batch.clear()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(lookup, post.url): post for post in posts}
        for done, future in enumerate(as_completed(futures), start=1):
            post = futures[future]
            batch.append({"fbid": post.fbid, field_name: future.result(), "stage": to_stage})
            report(f"{stage_label} ({done}/{total})")
            if len(batch) >= workers:
                flush()

    flush()


def process_and_index_posts(
    posts: list[LikedPost],
    index: StageIndex,
    music_title_lookup: MusicTitleLookup | None = None,
    audio_embedding_lookup: AudioEmbeddingLookup | None = None,
    on_stage: StageReporter | None = None,
) -> None:
    def report(stage: str) -> None:
        if on_stage is not None:
            on_stage(stage)

    report("Cleaning captions and hashtags")
    caption_owner_pairs = (
        (clean_caption(extract_caption(post.label_values)), extract_owner_username(post.label_values))
        for post in posts
    )
    single_account_captions = frozenset(find_single_account_captions(caption_owner_pairs))
    processed = [process_post(post, single_account_captions) for post in posts]

    existing = index.existing_fbids([post.fbid for post in processed])
    new_posts = [post for post in processed if post.fbid not in existing]
    if new_posts:
        report(f"Indexing {len(new_posts)} new posts")
        index.bulk_upsert([post.model_dump() for post in new_posts])

    if music_title_lookup is not None:
        _advance_stage(
            index,
            STAGE_CLEANED,
            STAGE_TITLED,
            music_title_lookup,
            "music_title",
            "Looking up song titles",
            report,
            _MUSIC_LOOKUP_WORKERS,
        )

    if audio_embedding_lookup is not None:
        _advance_stage(
            index,
            STAGE_TITLED,
            STAGE_EMBEDDED,
            audio_embedding_lookup,
            "audio_embedding",
            "Downloading and embedding audio",
            report,
            _AUDIO_EMBEDDING_WORKERS,
        )
