import json
from pathlib import Path

from vectoreels.ingestion.ingest import parse_liked_posts, read_liked_posts

RAW_POST = {
    "timestamp": 1781236053,
    "media": [],
    "label_values": [
        {"label": "URL", "value": "https://www.instagram.com/reel/abc/", "href": "https://www.instagram.com/reel/abc/"},
        {"label": "Caption", "value": "hello"},
        {"label": "Title", "value": ""},
        {"title": "Hashtags", "dict": []},
        {
            "title": "Owner",
            "dict": [
                {
                    "title": "",
                    "dict": [
                        {"label": "URL", "value": ""},
                        {"label": "Name", "value": "Andrew"},
                        {"label": "Username", "value": "astrophysicsfeed"},
                    ],
                }
            ],
        },
    ],
    "fbid": "18001694510933948",
}


def test_read_liked_posts_parses_every_entry(tmp_path: Path) -> None:
    dataset = tmp_path / "liked_posts.json"
    dataset.write_text(json.dumps([RAW_POST, RAW_POST]))

    posts = read_liked_posts(dataset)

    assert len(posts) == 2
    assert posts[0].fbid == "18001694510933948"


def test_parse_liked_posts_parses_json_bytes() -> None:
    raw = json.dumps([RAW_POST]).encode()

    posts = parse_liked_posts(raw)

    assert len(posts) == 1
    assert posts[0].fbid == "18001694510933948"


def test_parse_liked_posts_fixes_meta_export_mojibake() -> None:
    # Meta's export tool writes UTF-8 bytes as if each byte were a Latin-1
    # code point, corrupting any non-ASCII text (emoji, accents, CJK, etc).
    correct_caption = "🎬 café — 日本"
    corrupted_caption = correct_caption.encode("utf-8").decode("latin-1")
    post = {**RAW_POST, "label_values": [
        {"label": "URL", "value": "https://www.instagram.com/reel/abc/"},
        {"label": "Caption", "value": corrupted_caption},
    ]}

    posts = parse_liked_posts(json.dumps([post]).encode())

    captions = [lv.value for lv in posts[0].label_values if lv.label == "Caption"]
    assert captions == [correct_caption]


def test_parse_liked_posts_leaves_correctly_encoded_text_unchanged() -> None:
    correct_caption = "plain ascii caption"
    post = {**RAW_POST, "label_values": [
        {"label": "URL", "value": "https://www.instagram.com/reel/abc/"},
        {"label": "Caption", "value": correct_caption},
    ]}

    posts = parse_liked_posts(json.dumps([post]).encode())

    captions = [lv.value for lv in posts[0].label_values if lv.label == "Caption"]
    assert captions == [correct_caption]
