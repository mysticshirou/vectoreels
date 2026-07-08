from vectoreels.models import GroupedLabelValue, LikedPost, SimpleLabelValue


def test_parses_simple_label_value() -> None:
    lv = SimpleLabelValue.model_validate({"label": "Title", "value": ""})
    assert lv.label == "Title"
    assert lv.value == ""
    assert lv.href is None


def test_parses_url_label_value_with_href() -> None:
    lv = SimpleLabelValue.model_validate(
        {
            "label": "URL",
            "value": "https://www.instagram.com/reel/abc/",
            "href": "https://www.instagram.com/reel/abc/",
        }
    )
    assert lv.href == "https://www.instagram.com/reel/abc/"


def test_parses_grouped_label_value_with_nested_items() -> None:
    grouped = GroupedLabelValue.model_validate(
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
        }
    )
    assert grouped.title == "Owner"
    assert grouped.items[0].items[1].value == "Andrew"


def test_parses_grouped_label_value_with_empty_items() -> None:
    grouped = GroupedLabelValue.model_validate({"title": "Hashtags", "dict": []})
    assert grouped.items == []


def test_parses_full_liked_post() -> None:
    raw = {
        "timestamp": 1781236053,
        "media": [],
        "label_values": [
            {
                "label": "URL",
                "value": "https://www.instagram.com/reel/DZboESDu61c/",
                "href": "https://www.instagram.com/reel/DZboESDu61c/",
            },
            {"label": "Caption", "value": "levels to ts #fyp #astronomy"},
            {"label": "Title", "value": ""},
            {
                "title": "Hashtags",
                "dict": [{"title": "", "dict": [{"label": "Name", "value": "space"}]}],
            },
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
    post = LikedPost.model_validate(raw)
    assert post.timestamp == 1781236053
    assert post.fbid == "18001694510933948"
    assert post.media == []
    assert isinstance(post.label_values[0], SimpleLabelValue)
    assert isinstance(post.label_values[3], GroupedLabelValue)
