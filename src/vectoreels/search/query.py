from datetime import datetime, timezone

from vectoreels.models import SearchFilters


def parse_date_to_epoch(date: str, end_of_day: bool = False) -> int:
    parsed = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if end_of_day:
        parsed = parsed.replace(hour=23, minute=59, second=59)
    return int(parsed.timestamp())


def to_search_filters(
    keywords: list[str],
    description: str | None,
    date_from: str | None,
    date_to: str | None,
    song: str | None = None,
) -> SearchFilters:
    return SearchFilters(
        keywords=keywords,
        description=description or None,
        song=song or None,
        date_from=parse_date_to_epoch(date_from) if date_from else None,
        date_to=parse_date_to_epoch(date_to, end_of_day=True) if date_to else None,
    )


def build_search_query(filters: SearchFilters) -> dict[str, object]:
    must: list[dict[str, object]] = []
    filter_: list[dict[str, object]] = []

    if filters.description:
        must.append({"match": {"caption": filters.description}})

    if filters.song:
        must.append({"match": {"music_title": filters.song}})

    if filters.keywords:
        filter_.append({"terms": {"hashtags": filters.keywords}})

    if filters.date_from is not None or filters.date_to is not None:
        # Elasticsearch's epoch_second date format only parses range bounds
        # correctly as strings; a bare JSON number is read as epoch millis.
        date_range: dict[str, str] = {}
        if filters.date_from is not None:
            date_range["gte"] = str(filters.date_from)
        if filters.date_to is not None:
            date_range["lte"] = str(filters.date_to)
        filter_.append({"range": {"timestamp": date_range}})

    if not must and not filter_:
        return {"query": {"match_all": {}}}

    bool_query: dict[str, object] = {}
    if must:
        bool_query["must"] = must
    if filter_:
        bool_query["filter"] = filter_
    return {"query": {"bool": bool_query}}
