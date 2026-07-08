#!/usr/bin/env python3
import argparse
from pathlib import Path

from vectoreels.ingestion.ingest import read_liked_posts
from vectoreels.processing.irrelevant_captions_file import read_captions_file, write_captions_file
from vectoreels.processing.mining import cluster_captions
from vectoreels.processing.ownership import find_single_account_captions
from vectoreels.processing.process import clean_caption, extract_caption, extract_owner_username
from vectoreels.processing.relevance import tokenize

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_DATASET_PATH = PROJECT_ROOT / "dataset" / "liked_posts.json"
CAPTIONS_FILE_PATH = PROJECT_ROOT / "src" / "vectoreels" / "processing" / "irrelevant_captions.txt"


def is_already_covered(candidate: str, existing: list[str]) -> bool:
    candidate_tokens = tuple(tokenize(candidate))
    for entry in existing:
        entry_tokens = tuple(tokenize(entry))
        shorter, longer = sorted([candidate_tokens, entry_tokens], key=len)
        if longer[: len(shorter)] == shorter:
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find captions repeated across many reels (including truncated "
        "variants of the same text) and append them as candidates to "
        "irrelevant_captions.py"
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--min-count", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", help="print candidates without writing")
    args = parser.parse_args()

    posts = read_liked_posts(args.dataset)
    captions = [clean_caption(extract_caption(post.label_values)) for post in posts]
    owners = [extract_owner_username(post.label_values) for post in posts]
    single_account_captions = find_single_account_captions(zip(captions, owners, strict=True))

    clusters = cluster_captions(captions, min_count=args.min_count)
    clusters.sort(key=lambda item: item[1], reverse=True)

    existing = read_captions_file(CAPTIONS_FILE_PATH)

    new_entries: list[str] = []
    for text, count in clusters:
        if text in single_account_captions:
            print(f"[skip, single account]  ({count:>5}x) {text!r}")
            continue
        if is_already_covered(text, existing) or is_already_covered(text, new_entries):
            print(f"[skip, already covered] ({count:>5}x) {text!r}")
            continue
        print(f"[new candidate]         ({count:>5}x) {text!r}")
        new_entries.append(text)

    if not new_entries:
        print("\nNo new candidates found.")
        return

    if args.dry_run:
        print(f"\nDry run: {len(new_entries)} new candidate(s) found, not written.")
        return

    write_captions_file(CAPTIONS_FILE_PATH, existing + new_entries)
    print(f"\nAppended {len(new_entries)} new candidate(s) to {CAPTIONS_FILE_PATH}")


if __name__ == "__main__":
    main()
