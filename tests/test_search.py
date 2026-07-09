from vectoreels.search.search import _post_from_hit, to_upsert_actions


def test_post_from_hit_recovers_fbid_from_the_document_id() -> None:
    hit = {
        "_id": "fb1",
        "_source": {
            "timestamp": 1,
            "url": "https://www.instagram.com/reel/abc/",
            "caption": "hi",
            "hashtags": [],
            "music_title": None,
            "audio_embedding": None,
            "stage": 1,
        },
    }

    assert _post_from_hit(hit).fbid == "fb1"


def test_to_upsert_actions_upserts_by_fbid() -> None:
    actions = to_upsert_actions("reels", [{"fbid": "fb1", "stage": 2, "music_title": "Song"}])

    assert actions == [
        {
            "_op_type": "update",
            "_index": "reels",
            "_id": "fb1",
            "doc": {"stage": 2, "music_title": "Song"},
            "doc_as_upsert": True,
        }
    ]


def test_to_upsert_actions_maps_every_update() -> None:
    update = {"fbid": "fb1", "stage": 1}
    actions = to_upsert_actions("reels", [update, update, update])
    assert len(actions) == 3
