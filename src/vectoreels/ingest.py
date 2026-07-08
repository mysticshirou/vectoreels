import json
from pathlib import Path

from vectoreels.models import LikedPost


def parse_liked_posts(raw: bytes | str) -> list[LikedPost]:
    return [LikedPost.model_validate(item) for item in json.loads(raw)]


def read_liked_posts(path: Path) -> list[LikedPost]:
    return parse_liked_posts(path.read_text())
