from dataclasses import dataclass, field

import requests

from vectoreels.download.extract import extract_reel_info
from vectoreels.download.fetch import fetch_bytes
from vectoreels.download.formats import (
    iter_media_entries,
    select_best_audio_format,
    select_best_picture_url,
    select_best_video_format,
)


@dataclass
class ReelMedia:
    videos: list[bytes] = field(default_factory=list)
    audios: list[bytes] = field(default_factory=list)
    pictures: list[bytes] = field(default_factory=list)


def _try_fetch(url: str, headers: dict[str, str]) -> bytes | None:
    try:
        return fetch_bytes(url, headers)
    except requests.RequestException:
        return None


def download_reel_media(url: str) -> ReelMedia:
    """Downloads whatever audio, video, and pictures are attached to a reel
    URL, fully in memory. Unavailable posts and individual failed fetches
    (expired CDN links, network errors, etc) are silently skipped rather than
    raised, since across a large dataset some fraction of reels are always
    gone.
    """
    info = extract_reel_info(url)
    media = ReelMedia()
    if info is None:
        return media

    headers = info.get("http_headers") or {}
    for entry in iter_media_entries(info):
        formats = entry.get("formats") or []
        video_format = select_best_video_format(formats)
        audio_format = select_best_audio_format(formats)

        if video_format is not None:
            data = _try_fetch(video_format["url"], headers)
            if data is not None:
                media.videos.append(data)
        else:
            picture_url = select_best_picture_url(entry.get("thumbnails") or [])
            if picture_url is not None:
                data = _try_fetch(picture_url, headers)
                if data is not None:
                    media.pictures.append(data)

        if audio_format is not None:
            data = _try_fetch(audio_format["url"], headers)
            if data is not None:
                media.audios.append(data)

    return media
