from collections.abc import Iterable

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

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
    }
}


def to_bulk_actions(index_name: str, posts: Iterable[ProcessedPost]) -> list[dict[str, object]]:
    return [
        {"_index": index_name, "_id": post.fbid, "_source": post.model_dump()}
        for post in posts
    ]


def ensure_index(client: Elasticsearch, index_name: str = INDEX_NAME) -> None:
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, mappings=INDEX_MAPPING)


def index_posts(
    client: Elasticsearch, posts: list[ProcessedPost], index_name: str = INDEX_NAME
) -> None:
    bulk(client, to_bulk_actions(index_name, posts))


def search_posts(
    client: Elasticsearch,
    filters: SearchFilters,
    index_name: str = INDEX_NAME,
    size: int = 50,
) -> list[ProcessedPost]:
    response = client.search(index=index_name, size=size, **build_search_query(filters))
    return [ProcessedPost.model_validate(hit["_source"]) for hit in response["hits"]["hits"]]
