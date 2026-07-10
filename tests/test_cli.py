import pytest

from vectoreels.cli import build_parser, mapping, reset_index, show, stage_counts


def test_build_parser_accepts_stage_counts() -> None:
    args = build_parser().parse_args(["stage-counts"])
    assert args.command == "stage-counts"
    assert args.func is stage_counts


def test_build_parser_accepts_mapping() -> None:
    args = build_parser().parse_args(["mapping"])
    assert args.func is mapping


def test_build_parser_accepts_reset_index() -> None:
    args = build_parser().parse_args(["reset-index"])
    assert args.func is reset_index


def test_build_parser_accepts_show_with_fbid() -> None:
    args = build_parser().parse_args(["show", "fb123"])
    assert args.func is show
    assert args.fbid == "fb123"


def test_build_parser_show_requires_an_fbid() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["show"])


def test_build_parser_rejects_unknown_command() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["not-a-real-command"])
