#!/usr/bin/env python3
"""Rebuild manifest icon_url from wiki API (uses fetch_wiki_icon_url)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MANIFEST_PATH  # noqa: E402
from wiki_icon_url import fetch_wiki_icon_url  # noqa: E402


def main() -> None:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    characters = data.get("characters") or {}
    missing: list[str] = []

    for name in sorted(characters):
        url = fetch_wiki_icon_url(name)
        time.sleep(0.1)
        if url:
            characters[name]["icon_url"] = url
        else:
            missing.append(name)

    data["characters"] = dict(sorted(characters.items()))
    MANIFEST_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Updated {len(characters)} characters")
    if missing:
        print(f"Missing ({len(missing)}): {', '.join(missing)}")


if __name__ == "__main__":
    main()
