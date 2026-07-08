from vectoreels.download.formats import (
    iter_media_entries,
    select_best_audio_format,
    select_best_picture_url,
    select_best_video_format,
)

VIDEO_FORMAT = {"url": "https://cdn/video.mp4", "vcodec": "vp09", "acodec": "none", "tbr": 968.1}
LOWER_VIDEO_FORMAT = {"url": "https://cdn/video-lo.mp4", "vcodec": "vp09", "acodec": "none", "tbr": 137.0}
AUDIO_FORMAT = {"url": "https://cdn/audio.m4a", "vcodec": "none", "acodec": "mp4a.40.5", "tbr": 43.9}
JUNK_FORMAT = {"format_id": "1", "url": None, "vcodec": None, "acodec": None, "tbr": None}


def test_select_best_video_format_picks_highest_bitrate() -> None:
    formats = [LOWER_VIDEO_FORMAT, VIDEO_FORMAT, AUDIO_FORMAT, JUNK_FORMAT]
    assert select_best_video_format(formats) == VIDEO_FORMAT


def test_select_best_video_format_returns_none_when_no_video() -> None:
    assert select_best_video_format([AUDIO_FORMAT, JUNK_FORMAT]) is None


def test_select_best_audio_format_picks_audio_only_track() -> None:
    formats = [VIDEO_FORMAT, AUDIO_FORMAT, JUNK_FORMAT]
    assert select_best_audio_format(formats) == AUDIO_FORMAT


def test_select_best_audio_format_returns_none_when_no_audio() -> None:
    assert select_best_audio_format([VIDEO_FORMAT, JUNK_FORMAT]) is None


def test_select_best_picture_url_picks_last_as_highest_resolution() -> None:
    thumbnails = [{"url": "https://cdn/small.jpg"}, {"url": "https://cdn/large.jpg"}]
    assert select_best_picture_url(thumbnails) == "https://cdn/large.jpg"


def test_select_best_picture_url_returns_none_when_empty() -> None:
    assert select_best_picture_url([]) is None


def test_select_best_picture_url_ignores_entries_without_url() -> None:
    thumbnails = [{"url": "https://cdn/ok.jpg"}, {"width": 10}]
    assert select_best_picture_url(thumbnails) == "https://cdn/ok.jpg"


def test_iter_media_entries_returns_single_entry_for_plain_video() -> None:
    info = {"formats": [VIDEO_FORMAT], "thumbnails": []}
    assert iter_media_entries(info) == [info]


def test_iter_media_entries_returns_entries_for_playlist() -> None:
    entry_a = {"formats": [VIDEO_FORMAT]}
    entry_b = {"thumbnails": [{"url": "https://cdn/pic.jpg"}]}
    info = {"entries": [entry_a, entry_b]}
    assert iter_media_entries(info) == [entry_a, entry_b]
