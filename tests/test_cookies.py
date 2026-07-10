from pathlib import Path

from vectoreels.download.cookies import is_valid_cookiefile, write_cookiefile


def test_is_valid_cookiefile_accepts_netscape_header() -> None:
    assert is_valid_cookiefile(b"# Netscape HTTP Cookie File\n\n.instagram.com\tTRUE\t/\n") is True


def test_is_valid_cookiefile_rejects_unrelated_content() -> None:
    assert is_valid_cookiefile(b'{"not": "a cookiefile"}') is False


def test_is_valid_cookiefile_rejects_undecodable_bytes() -> None:
    assert is_valid_cookiefile(b"\xff\xfe\x00\x01") is False


def test_write_cookiefile_writes_content(tmp_path: Path) -> None:
    path = tmp_path / "cookies.txt"

    write_cookiefile(path, b"# Netscape HTTP Cookie File\n")

    assert path.read_bytes() == b"# Netscape HTTP Cookie File\n"


def test_write_cookiefile_replaces_existing_content(tmp_path: Path) -> None:
    path = tmp_path / "cookies.txt"
    path.write_bytes(b"old content")

    write_cookiefile(path, b"new content")

    assert path.read_bytes() == b"new content"
