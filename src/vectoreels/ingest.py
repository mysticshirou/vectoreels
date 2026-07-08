import json
from pathlib import Path

from vectoreels.models import LikedPost


def read_liked_posts(path: Path) -> list[LikedPost]:
    raw = json.loads(path.read_text())
    return [LikedPost.model_validate(item) for item in raw]
