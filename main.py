from pathlib import Path

from vectoreels.ingest import read_liked_posts
from vectoreels.process import process_posts

DATASET_PATH = Path(__file__).parent / "dataset" / "liked_posts.json"


def main() -> None:
    posts = read_liked_posts(DATASET_PATH)
    print(f"Loaded {len(posts)} liked posts")

    processed = process_posts(posts)
    print(f"Processed {len(processed)} posts")
    print(processed[0].model_dump_json(indent=2))


if __name__ == "__main__":
    main()
