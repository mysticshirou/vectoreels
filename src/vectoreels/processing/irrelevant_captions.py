"""Loads captions seen across many unrelated reels, carrying no information
about what the reel is actually about. Edit irrelevant_captions.txt directly
to add more — it's meant to change rarely, by hand, rather than through the
dataset upload.
"""

from pathlib import Path

from vectoreels.processing.irrelevant_captions_file import read_captions_file

_CAPTIONS_FILE = Path(__file__).parent / "irrelevant_captions.txt"

IRRELEVANT_CAPTIONS: list[str] = read_captions_file(_CAPTIONS_FILE)
