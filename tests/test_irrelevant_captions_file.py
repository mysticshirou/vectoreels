from pathlib import Path

from vectoreels.irrelevant_captions_file import read_captions_file, write_captions_file


def test_read_captions_file_reads_one_caption_per_line(tmp_path: Path) -> None:
    path = tmp_path / "irrelevant_captions.txt"
    path.write_text("Follow for more!\nLink in bio\n")

    assert read_captions_file(path) == ["Follow for more!", "Link in bio"]


def test_read_captions_file_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "irrelevant_captions.txt"
    path.write_text("Follow for more!\n\n\nLink in bio\n")

    assert read_captions_file(path) == ["Follow for more!", "Link in bio"]


def test_write_then_read_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "irrelevant_captions.txt"

    write_captions_file(path, ["First caption", "Second one"])

    assert read_captions_file(path) == ["First caption", "Second one"]


def test_write_then_read_round_trips_embedded_newlines(tmp_path: Path) -> None:
    path = tmp_path / "irrelevant_captions.txt"

    write_captions_file(path, ["Line one\nLine two"])

    assert read_captions_file(path) == ["Line one\nLine two"]
