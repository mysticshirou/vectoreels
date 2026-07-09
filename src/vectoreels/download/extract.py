from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.extractor.instagram import InstagramIE
from yt_dlp.utils import ExtractorError


def _capture_carousel_media(product_info: Any) -> list[dict[str, Any]]:
    info = product_info[0] if isinstance(product_info, list) else product_info
    return info.get("carousel_media") or [info]


def extract_reel_info(url: str, cookiefile: str | Path | None = None) -> dict[str, Any] | None:
    """Extracts raw yt-dlp info for a reel URL, or None if the post is
    permanently unavailable (deleted, restricted, login-walled, etc).

    Calls the Instagram extractor directly rather than going through
    YoutubeDL.extract_info(), because that wrapper raises and discards the
    result for photo-only posts (it only accepts results with video
    formats), even though the extractor itself already fetched full-resolution
    picture URLs into `thumbnails`.

    yt-dlp's own entry-building (`_extract_product_media`) drops the raw
    `music_metadata` field it already fetched for photo/carousel posts, so it
    never surfaces attached-music info. This temporarily monkeypatches
    `InstagramIE._extract_product` to capture the raw carousel items and
    re-attach `music_metadata` to the corresponding entries by position
    (`_extract_product` builds entries from `carousel_media` in order, so a
    positional zip is a safe correspondence). Like the direct `_real_extract`
    call above, this reaches into yt-dlp internals that aren't public API and
    could break on an upstream update.
    """
    ydl_opts: dict[str, Any] = {"quiet": True, "no_warnings": True}
    if cookiefile is not None:
        ydl_opts["cookiefile"] = str(cookiefile)

    captured: list[list[dict[str, Any]]] = []
    original_extract_product = InstagramIE._extract_product

    def capturing_extract_product(self: InstagramIE, product_info: Any, *args: Any, **kwargs: Any) -> Any:
        captured.append(_capture_carousel_media(product_info))
        return original_extract_product(self, product_info, *args, **kwargs)

    InstagramIE._extract_product = capturing_extract_product  # type: ignore[method-assign]
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ie = InstagramIE(ydl)
            try:
                info = ie._real_extract(url)
            except ExtractorError:
                return None
            finally:
                # Concurrent lookups share one cookiefile. yt-dlp writes updated
                # session cookies back to it on close by default; with many
                # threads doing that against the same path, one thread's write
                # races another's read and corrupts the file for everyone. We
                # only need the cookies for auth, not to persist rotated ones,
                # so disable the write (load already happened above, inside
                # _real_extract's login check).
                ydl.params["cookiefile"] = None
    finally:
        InstagramIE._extract_product = original_extract_product  # type: ignore[method-assign]

    if not captured:
        return info

    entries = info.get("entries")
    if entries is not None:
        for entry, raw_item in zip(entries, captured[-1], strict=False):
            entry["music_metadata"] = raw_item.get("music_metadata")
    elif captured[-1]:
        # A lone (non-carousel) photo post never enters _extract_product's
        # playlist branch, so `info` itself is the single entry.
        info["music_metadata"] = captured[-1][0].get("music_metadata")

    return info
