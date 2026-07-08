import json
from pathlib import Path
from typing import Any

from vectoreels.models import LikedPost


def _fix_mojibake(text: str) -> str:
    # Meta's data export tool writes UTF-8 bytes as if each byte were a
    # Latin-1 code point, corrupting any non-ASCII text. Round-tripping
    # through latin-1 undoes it; a string that wasn't corrupted this way
    # simply fails to re-encode/decode and is left untouched.
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _fix_mojibake_recursive(value: Any) -> Any:
    if isinstance(value, str):
        return _fix_mojibake(value)
    if isinstance(value, list):
        return [_fix_mojibake_recursive(item) for item in value]
    if isinstance(value, dict):
        return {key: _fix_mojibake_recursive(item) for key, item in value.items()}
    return value


def parse_liked_posts(raw: bytes | str) -> list[LikedPost]:
    fixed = _fix_mojibake_recursive(json.loads(raw))
    return [LikedPost.model_validate(item) for item in fixed]


def read_liked_posts(path: Path) -> list[LikedPost]:
    return parse_liked_posts(path.read_bytes())
