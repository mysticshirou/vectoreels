from pathlib import Path

from elasticsearch import Elasticsearch

from vectoreels.ingest import read_liked_posts
from vectoreels.process import process_posts
from vectoreels.search import ensure_index, index_posts

DATASET_PATH = Path(__file__).parent / "dataset" / "liked_posts.json"
ELASTICSEARCH_URL = "http://localhost:9200"


def main() -> None:
    posts = read_liked_posts(DATASET_PATH)
    print(f"Loaded {len(posts)} liked posts")

    processed = process_posts(posts)
    print(f"Processed {len(processed)} posts")

    client = Elasticsearch(ELASTICSEARCH_URL)
    ensure_index(client)
    index_posts(client, processed)
    print(f"Indexed {len(processed)} posts into Elasticsearch")


if __name__ == "__main__":
    main()
