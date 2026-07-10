import argparse
import json
import os
from collections.abc import Callable

from elasticsearch import Elasticsearch

from vectoreels.models import STAGE_NAMES
from vectoreels.search.search import INDEX_NAME, INDEX_MAPPING, count_at_stage, ensure_index, get_post

ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")


def stage_counts(client: Elasticsearch, args: argparse.Namespace) -> None:
    for stage, name in STAGE_NAMES.items():
        print(f"stage {stage} ({name}): {count_at_stage(client, stage)}")


def mapping(client: Elasticsearch, args: argparse.Namespace) -> None:
    response = client.indices.get_mapping(index=INDEX_NAME)
    print(json.dumps(response.body, indent=2))


def reset_index(client: Elasticsearch, args: argparse.Namespace) -> None:
    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
    ensure_index(client)
    print(f"reset {INDEX_NAME}")


def show(client: Elasticsearch, args: argparse.Namespace) -> None:
    post = get_post(client, args.fbid)
    if post is None:
        print(f"no post found for fbid {args.fbid}")
        return
    print(post.model_dump_json(indent=2))


def _add_show_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("fbid")


Handler = Callable[[Elasticsearch, argparse.Namespace], None]
ArgConfigurator = Callable[[argparse.ArgumentParser], None]

# Add a new command by adding a handler above and registering it below (with
# an arg configurator if it takes arguments); build_parser wires up its
# subcommand automatically.
COMMANDS: dict[str, tuple[Handler, ArgConfigurator | None]] = {
    "stage-counts": (stage_counts, None),
    "mapping": (mapping, None),
    "reset-index": (reset_index, None),
    "show": (show, _add_show_args),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vectoreels")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, (handler, add_args) in COMMANDS.items():
        subparser = subparsers.add_parser(name)
        if add_args is not None:
            add_args(subparser)
        subparser.set_defaults(func=handler)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    client = Elasticsearch(ELASTICSEARCH_URL)
    args.func(client, args)
