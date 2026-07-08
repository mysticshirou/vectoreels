import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from vectoreels.models import GroupedLabelValue, LikedPost, ProcessedPost, SimpleLabelValue
from vectoreels.processing.ownership import find_single_account_captions
from vectoreels.processing.relevance import is_irrelevant_caption

MusicTitleLookup = Callable[[str], str | None]
AudioEmbeddingLookup = Callable[[str], list[float] | None]
StageReporter = Callable[[str], None]

_MUSIC_LOOKUP_WORKERS = 16
_AUDIO_EMBEDDING_WORKERS = 2

LabelValue = SimpleLabelValue | GroupedLabelValue

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


def process_posts(
    posts: list[LikedPost],
    music_title_lookup: MusicTitleLookup | None = None,
    audio_embedding_lookup: AudioEmbeddingLookup | None = None,
    on_stage: StageReporter | None = None,
) -> list[ProcessedPost]:
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

    if music_title_lookup is not None:
        report("Looking up song titles")
        with ThreadPoolExecutor(max_workers=_MUSIC_LOOKUP_WORKERS) as executor:
            titles = executor.map(music_title_lookup, (post.url for post in processed))
            processed = [
                post.model_copy(update={"music_title": title})
                for post, title in zip(processed, titles, strict=True)
            ]

    if audio_embedding_lookup is not None:
        report("Downloading and embedding audio")
        with ThreadPoolExecutor(max_workers=_AUDIO_EMBEDDING_WORKERS) as executor:
            embeddings = executor.map(audio_embedding_lookup, (post.url for post in processed))
            processed = [
                post.model_copy(update={"audio_embedding": embedding})
                for post, embedding in zip(processed, embeddings, strict=True)
            ]

    return processed
