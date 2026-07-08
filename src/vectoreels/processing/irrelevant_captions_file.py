from pathlib import Path


def read_captions_file(path: Path) -> list[str]:
    return [
        line.replace("\\n", "\n")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_captions_file(path: Path, captions: list[str]) -> None:
    lines = [caption.replace("\n", "\\n") for caption in captions]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
