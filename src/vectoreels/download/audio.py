from pathlib import Path
from typing import Any

import requests

from vectoreels.download.extract import extract_reel_info
from vectoreels.download.fetch import fetch_bytes
from vectoreels.download.formats import (
    iter_media_entries,
    select_best_audio_format,
    select_music_download_url,
)


def _select_audio_url(entry: dict[str, Any]) -> str | None:
    audio_format = select_best_audio_format(entry.get("formats") or [])
    if audio_format is not None:
        return audio_format["url"]
    return select_music_download_url(entry)


def download_reel_audio(url: str, cookiefile: str | Path | None = None) -> bytes | None:
    """Downloads one representative audio clip for a reel URL: the video's own
    audio track for reels, or the attached music track for photo/carousel
    posts. Returns None if the post is unavailable or carries no audio at all.
    """
    info = extract_reel_info(url, cookiefile=cookiefile)
    if info is None:
        return None

    headers = info.get("http_headers") or {}
    for entry in iter_media_entries(info):
        audio_url = _select_audio_url(entry)
        if audio_url is None:
            continue
        try:
            return fetch_bytes(audio_url, headers)
        except requests.RequestException:
            continue

    return None
