from pathlib import Path

from vectoreels.download.extract import extract_reel_info
from vectoreels.download.formats import iter_media_entries, select_music_title


def get_music_title(url: str, cookiefile: str | Path | None = None) -> str | None:
    info = extract_reel_info(url, cookiefile=cookiefile)
    if info is None:
        return None
    for entry in iter_media_entries(info):
        title = select_music_title(entry)
        if title is not None:
            return title
    return None
