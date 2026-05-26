"""Repository paths shared by maintenance scripts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DATA = ROOT / "data"
MANIFEST_PATH = DATA / "characters_manifest.json"
