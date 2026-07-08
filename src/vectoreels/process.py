import re

from vectoreels.models import GroupedLabelValue, LikedPost, ProcessedPost, SimpleLabelValue
from vectoreels.relevance import is_irrelevant_caption

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


def process_post(post: LikedPost) -> ProcessedPost:
    caption = clean_caption(extract_caption(post.label_values))
    hashtags = extract_hashtags(post.label_values)
    if is_irrelevant_caption(caption):
        caption = None
        hashtags = []
    return ProcessedPost(
        fbid=post.fbid,
        timestamp=post.timestamp,
        url=extract_url(post.label_values),
        caption=caption,
        hashtags=hashtags,
    )


def process_posts(posts: list[LikedPost]) -> list[ProcessedPost]:
    return [process_post(post) for post in posts]
