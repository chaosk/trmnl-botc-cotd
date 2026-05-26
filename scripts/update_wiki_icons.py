#!/usr/bin/env python3
"""Refresh manifest icon_url to direct wiki /images/…/Icon_*.png URLs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MANIFEST_PATH as MANIFEST  # noqa: E402
from wiki_icon_url import fetch_wiki_icon_url  # noqa: E402


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    characters = data.get("characters") or {}

    for slug, char in characters.items():
        name = char.get("name") or slug
        url = fetch_wiki_icon_url(name)
        if url:
            char["icon_url"] = url

    MANIFEST.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    missing = [c.get("name") for c in characters.values() if not c.get("icon_url")]
    print(f"Updated {len(characters)} icon URLs (direct /images/… paths)")
    if missing:
        print(f"Missing ({len(missing)}): {', '.join(missing[:15])}")


if __name__ == "__main__":
    main()
