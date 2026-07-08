from vectoreels.models import SearchFilters
from vectoreels.search.query import build_search_query, parse_date_to_epoch, to_search_filters


def test_build_search_query_with_no_filters_matches_all() -> None:
    assert build_search_query(SearchFilters()) == {"query": {"match_all": {}}}


def test_build_search_query_with_description_matches_caption() -> None:
    query = build_search_query(SearchFilters(description="a shoebill stork"))
    assert query == {
        "query": {"bool": {"must": [{"match": {"caption": "a shoebill stork"}}]}}
    }


def test_build_search_query_with_keywords_filters_hashtags() -> None:
    query = build_search_query(SearchFilters(keywords=["space", "fyp"]))
    assert query == {
        "query": {"bool": {"filter": [{"terms": {"hashtags": ["space", "fyp"]}}]}}
    }


def test_build_search_query_with_date_range() -> None:
    query = build_search_query(SearchFilters(date_from=100, date_to=200))
    assert query == {
        "query": {"bool": {"filter": [{"range": {"timestamp": {"gte": "100", "lte": "200"}}}]}}
    }


def test_build_search_query_with_only_date_from() -> None:
    query = build_search_query(SearchFilters(date_from=100))
    assert query == {
        "query": {"bool": {"filter": [{"range": {"timestamp": {"gte": "100"}}}]}}
    }


def test_build_search_query_combines_all_filters() -> None:
    query = build_search_query(
        SearchFilters(keywords=["space"], description="stars", date_from=100, date_to=200)
    )
    assert query == {
        "query": {
            "bool": {
                "must": [{"match": {"caption": "stars"}}],
                "filter": [
                    {"terms": {"hashtags": ["space"]}},
                    {"range": {"timestamp": {"gte": "100", "lte": "200"}}},
                ],
            }
        }
    }


def test_parse_date_to_epoch_start_of_day() -> None:
    assert parse_date_to_epoch("2026-01-15") == 1768435200


def test_parse_date_to_epoch_end_of_day() -> None:
    assert parse_date_to_epoch("2026-01-15", end_of_day=True) == 1768521599


def test_to_search_filters_treats_blank_strings_as_absent() -> None:
    filters = to_search_filters(keywords=[], description="", date_from="", date_to="")
    assert filters == SearchFilters()


def test_to_search_filters_parses_dates_and_keeps_keywords() -> None:
    filters = to_search_filters(
        keywords=["space", "fyp"],
        description="a shoebill stork",
        date_from="2026-01-15",
        date_to="2026-01-15",
    )
    assert filters == SearchFilters(
        keywords=["space", "fyp"],
        description="a shoebill stork",
        date_from=1768435200,
        date_to=1768521599,
    )
