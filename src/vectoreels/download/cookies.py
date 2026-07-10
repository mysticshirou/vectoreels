from pathlib import Path


def is_valid_cookiefile(content: bytes) -> bool:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return text.startswith("# Netscape HTTP Cookie File") or text.startswith("# HTTP Cookie File")


def write_cookiefile(path: Path, content: bytes) -> None:
    # Not a rename-into-place: Docker bind-mounts a single file at a fixed
    # inode, so replacing it fails with "Device or resource busy". A direct
    # write is safe here because yt-dlp's own write-back to this path is
    # already disabled (see extract.py), so this is the only writer, and it
    # only ever runs as a rare, manual action from the UI.
    path.write_bytes(content)
