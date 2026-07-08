import json
from pathlib import Path

from vectoreels.ingest import parse_liked_posts, read_liked_posts

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
