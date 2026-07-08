from vectoreels.models import ProcessedPost
from vectoreels.search.search import to_bulk_actions


def test_to_bulk_actions_uses_fbid_as_document_id() -> None:
    post = ProcessedPost(
        fbid="fb1",
        timestamp=123,
        url="https://www.instagram.com/reel/abc/",
        caption="hello",
        hashtags=["a", "b"],
    )

    actions = to_bulk_actions("reels", [post])

    assert actions == [
        {
            "_index": "reels",
            "_id": "fb1",
            "_source": {
                "fbid": "fb1",
                "timestamp": 123,
                "url": "https://www.instagram.com/reel/abc/",
                "caption": "hello",
                "hashtags": ["a", "b"],
            },
        }
    ]


def test_to_bulk_actions_maps_every_post() -> None:
    post = ProcessedPost(fbid="fb1", timestamp=1, url="u", caption="", hashtags=[])
    actions = to_bulk_actions("reels", [post, post, post])
    assert len(actions) == 3
