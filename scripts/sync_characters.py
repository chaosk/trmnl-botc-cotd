#!/usr/bin/env python3
"""
Sync Blood on the Clocktower characters into characters_manifest.json.

Role text (name, type, ability, flavor) comes from official botc-release roles.json.
Wiki is used for icon URLs and first_available (Revealed/When, else page creation date).

Usage:
  python scripts/sync_characters.py
  python scripts/sync_characters.py --limit 5   # smoke test
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ability_format import format_ability_brackets  # noqa: E402
from botc_roles import fetch_roles, role_type  # noqa: E402
from wiki_icon_url import fetch_wiki_icon_url  # noqa: E402
from wiki_parse import parse_revealed_date, parse_wiki_timestamp  # noqa: E402

WIKI_API = "https://wiki.bloodontheclocktower.com/api.php"
WIKI_BASE = "https://wiki.bloodontheclocktower.com"
USER_AGENT = "trmnl-botc-cotd-plugin/1.0"
HTTP_TIMEOUT = 30.0

from _paths import MANIFEST_PATH  # noqa: E402


def wiki_request(params: dict) -> dict:
    query = urllib.parse.urlencode({**params, "format": "json"})
    url = f"{WIKI_API}?{query}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=HTTP_TIMEOUT) as resp:
        return json.load(resp)


def fetch_icon_url(title: str) -> str:
    url = fetch_wiki_icon_url(title)
    if not url:
        raise ValueError(f"No wiki icon found for {title!r}")
    return url


def fetch_page_created_date(title: str) -> str | None:
    """Wiki page creation date from logevents (fallback when Revealed/When is missing)."""
    data = wiki_request(
        {
            "action": "query",
            "list": "logevents",
            "letype": "create",
            "letitle": title,
            "lelimit": "1",
        }
    )
    events = data.get("query", {}).get("logevents", [])
    if not events:
        return None
    return parse_wiki_timestamp(events[0].get("timestamp", ""))


def fetch_page_wikitext(title: str) -> str:
    data = wiki_request(
        {
            "action": "query",
            "titles": title,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
        }
    )
    for page in data.get("query", {}).get("pages", {}).values():
        if page.get("missing"):
            return ""
        revisions = page.get("revisions") or []
        if revisions:
            return revisions[0].get("slots", {}).get("main", {}).get("*", "") or ""
    return ""


def wiki_page_url(title: str) -> str:
    path = title.replace(" ", "_")
    return f"{WIKI_BASE}/{urllib.parse.quote(path)}"


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {
        "generated_at": date.today().isoformat(),
        "characters": {},
    }


def sync_character(
    role: dict,
    existing: dict | None,
    today: str,
) -> dict:
    name = role["name"]
    wikitext = fetch_page_wikitext(name)
    time.sleep(0.15)  # be polite to wiki

    revealed = parse_revealed_date(wikitext)
    if revealed:
        first_available = revealed
    else:
        created = fetch_page_created_date(name)
        time.sleep(0.1)
        if created:
            first_available = created
        elif existing and existing.get("first_available"):
            first_available = existing["first_available"]
        else:
            first_available = today

    return {
        "name": name,
        "type": role_type(role),
        "ability": format_ability_brackets(role.get("ability") or ""),
        # Verbatim from roles.json (e.g. Ogre uses <grunt> tags, not HTML).
        "flavor": role["flavor"] if role.get("flavor") is not None else "",
        "wiki_url": wiki_page_url(name),
        "icon_url": fetch_icon_url(name),
        "first_available": first_available,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Only sync first N roles (test)")
    args = parser.parse_args()

    print("Fetching roles.json from botc-release...")
    roles = fetch_roles()
    roles.sort(key=lambda r: r["name"])
    if args.limit:
        roles = roles[: args.limit]

    manifest = load_manifest()
    characters: dict = manifest.setdefault("characters", {})
    today = date.today().isoformat()

    allowed = {r["name"] for r in roles}
    for slug in list(characters):
        if slug not in allowed:
            del characters[slug]

    print(f"Syncing {len(roles)} characters...")
    for i, role in enumerate(roles, 1):
        name = role["name"]
        try:
            characters[name] = sync_character(role, characters.get(name), today)
            if i % 10 == 0 or i == len(roles):
                print(f"  [{i}/{len(roles)}] {name}")
        except Exception as exc:
            print(f"  ERROR {name}: {exc}")

    manifest["generated_at"] = today
    manifest["character_count"] = len(characters)
    manifest["characters"] = dict(sorted(characters.items()))

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {MANIFEST_PATH} ({len(characters)} characters)")


if __name__ == "__main__":
    main()
