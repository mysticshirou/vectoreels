from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.extractor.instagram import InstagramIE
from yt_dlp.utils import ExtractorError


def extract_reel_info(url: str) -> dict[str, Any] | None:
    """Extracts raw yt-dlp info for a reel URL, or None if the post is
    permanently unavailable (deleted, restricted, login-walled, etc).

    Calls the Instagram extractor directly rather than going through
    YoutubeDL.extract_info(), because that wrapper raises and discards the
    result for photo-only posts (it only accepts results with video
    formats), even though the extractor itself already fetched full-resolution
    picture URLs into `thumbnails`.
    """
    with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        ie = InstagramIE(ydl)
        try:
            return ie._real_extract(url)
        except ExtractorError:
            return None
