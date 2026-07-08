from pathlib import Path

from vectoreels.ingest import read_liked_posts

DATASET_PATH = Path(__file__).parent / "dataset" / "liked_posts.json"


def main() -> None:
    posts = read_liked_posts(DATASET_PATH)
    print(f"Loaded {len(posts)} liked posts")
    print(posts[0].model_dump_json(indent=2))


if __name__ == "__main__":
    main()
