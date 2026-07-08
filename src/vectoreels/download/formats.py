from typing import Any


def _has_url(entry: dict[str, Any]) -> bool:
    return bool(entry.get("url"))


def select_best_video_format(formats: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [f for f in formats if _has_url(f) and f.get("vcodec") not in (None, "none")]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.get("tbr") or 0)


def select_best_audio_format(formats: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        f
        for f in formats
        if _has_url(f) and f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.get("tbr") or 0)


def select_best_picture_url(thumbnails: list[dict[str, Any]]) -> str | None:
    candidates = [t for t in thumbnails if _has_url(t)]
    if not candidates:
        return None
    # yt-dlp's Instagram extractor returns thumbnails ascending by resolution.
    return candidates[-1]["url"]


def iter_media_entries(info: dict[str, Any]) -> list[dict[str, Any]]:
    entries = info.get("entries")
    return list(entries) if entries is not None else [info]
