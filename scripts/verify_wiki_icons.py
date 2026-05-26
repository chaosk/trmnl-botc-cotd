#!/usr/bin/env python3
"""Check manifest icon_url values and optionally refresh broken ones."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import MANIFEST_PATH  # noqa: E402
from wiki_icon_url import fetch_wiki_icon_url  # noqa: E402


def http_status(url: str) -> int:
    try:
        r = subprocess.run(
            [
                "curl",
                "-sS",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "-L",
                "--max-time",
                "20",
                url,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return int(r.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return -1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Re-resolve and update broken icon_url entries in the manifest",
    )
    args = parser.parse_args()

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    characters = data.get("characters") or {}

    broken: list[str] = []
    for name, char in sorted(characters.items()):
        url = char.get("icon_url") or ""
        if http_status(url) != 200:
            broken.append(name)

    print(f"Checked {len(characters)} icons — {len(broken)} not HTTP 200")
    for name in broken:
        print(f"  {name}: {characters[name].get('icon_url')}")

    if not args.fix or not broken:
        return 1 if broken else 0

    fixed = 0
    for name in broken:
        url = fetch_wiki_icon_url(name)
        time.sleep(0.12)
        if not url or http_status(url) != 200:
            print(f"  FAIL resolve {name}: {url!r}")
            continue
        characters[name]["icon_url"] = url
        fixed += 1
        print(f"  fixed {name} -> {url}")

    data["characters"] = dict(sorted(characters.items()))
    MANIFEST_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Updated manifest ({fixed}/{len(broken)} fixed)")
    return 0 if fixed == len(broken) else 1


if __name__ == "__main__":
    raise SystemExit(main())
