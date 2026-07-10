from collections.abc import Iterable
from typing import Any

from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk, scan

from vectoreels.models import ProcessedPost, SearchFilters
from vectoreels.search.query import build_search_query

INDEX_NAME = "reels"

INDEX_MAPPING = {
    "properties": {
        "fbid": {"type": "keyword"},
        "timestamp": {"type": "date", "format": "epoch_second"},
        "url": {"type": "keyword"},
        "caption": {"type": "text"},
        "hashtags": {"type": "keyword"},
        "music_title": {"type": "text"},
        "audio_embedding": {
            "type": "dense_vector",
            "dims": 512,
            "index": True,
            "similarity": "cosine",
        },
        "stage": {"type": "integer"},
    }
}


def to_upsert_actions(index_name: str, updates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "_op_type": "update",
            "_index": index_name,
            "_id": update["fbid"],
            "doc": {k: v for k, v in update.items() if k != "fbid"},
            "doc_as_upsert": True,
        }
        for update in updates
    ]


def _post_from_hit(hit: dict[str, Any]) -> ProcessedPost:
    # fbid is stored as the document _id, not in _source (to_upsert_actions
    # strips it out so it isn't duplicated on every partial update) -- so it
    # has to be merged back in before validating.
    return ProcessedPost.model_validate({**hit["_source"], "fbid": hit["_id"]})


def ensure_index(client: Elasticsearch, index_name: str = INDEX_NAME) -> None:
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, mappings=INDEX_MAPPING)


def existing_fbids(
    client: Elasticsearch, fbids: list[str], index_name: str = INDEX_NAME
) -> set[str]:
    if not fbids:
        return set()
    response = client.mget(index=index_name, ids=fbids, _source=False)
    return {doc["_id"] for doc in response["docs"] if doc.get("found")}


def bulk_upsert(
    client: Elasticsearch, updates: list[dict[str, Any]], index_name: str = INDEX_NAME
) -> None:
    # wait_for so a posts_at_stage() query issued right after this call (the
    # next stage's resumption check) is guaranteed to see these writes,
    # rather than racing Elasticsearch's ~1s background refresh.
    bulk(client, to_upsert_actions(index_name, updates), refresh="wait_for")


def posts_at_stage(
    client: Elasticsearch, stage: int, index_name: str = INDEX_NAME
) -> list[ProcessedPost]:
    hits = scan(client, index=index_name, query={"query": {"term": {"stage": stage}}})
    return [_post_from_hit(hit) for hit in hits]


def count_at_stage(client: Elasticsearch, stage: int, index_name: str = INDEX_NAME) -> int:
    response = client.count(index=index_name, query={"term": {"stage": stage}})
    return int(response["count"])


def get_post(client: Elasticsearch, fbid: str, index_name: str = INDEX_NAME) -> ProcessedPost | None:
    try:
        response = client.get(index=index_name, id=fbid)
    except NotFoundError:
        return None
    return _post_from_hit(response)


class ElasticsearchStageIndex:
    """Bundles the Elasticsearch client behind the StageIndex seam that
    processing.process.process_and_index_posts is injected with, so the
    pipeline logic never talks to Elasticsearch directly."""

    def __init__(self, client: Elasticsearch, index_name: str = INDEX_NAME) -> None:
        self._client = client
        self._index_name = index_name

    def existing_fbids(self, fbids: list[str]) -> set[str]:
        return existing_fbids(self._client, fbids, self._index_name)

    def bulk_upsert(self, updates: list[dict[str, Any]]) -> None:
        bulk_upsert(self._client, updates, self._index_name)

    def posts_at_stage(self, stage: int) -> list[ProcessedPost]:
        return posts_at_stage(self._client, stage, self._index_name)


def search_posts(
    client: Elasticsearch,
    filters: SearchFilters,
    index_name: str = INDEX_NAME,
    size: int = 50,
) -> list[ProcessedPost]:
    response = client.search(index=index_name, size=size, **build_search_query(filters))
    return [_post_from_hit(hit) for hit in response["hits"]["hits"]]
