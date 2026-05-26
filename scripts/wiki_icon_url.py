"""Wiki character icon URL helpers — resolve via MediaWiki imageinfo."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

WIKI_API = "https://wiki.bloodontheclocktower.com/api.php"
USER_AGENT = "trmnl-botc-plugin/1.0"
HTTP_TIMEOUT = 30.0

_ICON_FILE_RE = re.compile(r"^File:Icon[_\s]*(.+)\.png$", re.IGNORECASE)


def _name_icon_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _file_icon_key(file_title: str) -> str:
    m = _ICON_FILE_RE.match(file_title.strip())
    if not m:
        return ""
    return re.sub(r"[^a-z0-9]", "", m.group(1).lower())


def wiki_icon_filename_candidates(name: str) -> list[str]:
    """
    Possible on-wiki file names.

    Most use Icon_<slug>.png; some concatenate words (Icon_stormcatcher.png).
    """
    slug = name.replace(" ", "_")
    compact = re.sub(r"[^a-z0-9]", "", name.lower())
    seen: set[str] = set()
    out: list[str] = []

    def add(stem: str) -> None:
        fn = f"Icon_{stem}.png"
        if fn not in seen:
            seen.add(fn)
            out.append(fn)

    add(slug.replace("'", "").lower())
    add(slug.lower())
    add(slug.replace("'", "_").lower())
    if compact:
        add(compact)
    return out


def _wiki_request(params: dict) -> dict | None:
    query = urllib.parse.urlencode({**params, "format": "json"})
    url = f"{WIKI_API}?{query}"
    env = os.environ.copy()
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        env.pop(key, None)
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with opener.open(req, timeout=HTTP_TIMEOUT) as resp:
            return json.load(resp)
    except Exception:
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "-A",
                    USER_AGENT,
                    "--max-time",
                    str(int(HTTP_TIMEOUT)),
                    url,
                ],
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
            return None


def _imageinfo_url(file_title: str) -> str | None:
    """file_title: 'File:Icon_foo.png' or 'File:Icon foo.png'."""
    data = _wiki_request(
        {
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url",
        }
    )
    if not data:
        return None
    for page in data.get("query", {}).get("pages", {}).values():
        if page.get("missing") is not None:
            continue
        info = page.get("imageinfo")
        if info and info[0].get("url"):
            url = info[0]["url"]
            if "/images/" in url:
                return url
    return None


def _icon_from_wiki_page(name: str) -> str | None:
    """Pick the character's Icon_*.png from images listed on their wiki page."""
    data = _wiki_request(
        {
            "action": "query",
            "titles": name,
            "prop": "images",
            "imlimit": "50",
        }
    )
    if not data:
        return None

    want = _name_icon_key(name)
    for page in data.get("query", {}).get("pages", {}).values():
        if page.get("missing") is not None:
            continue
        for img in page.get("images", []):
            title = img.get("title", "")
            if not title.startswith("File:Icon") or "logo" in title.lower():
                continue
            if _file_icon_key(title) != want:
                continue
            url = _imageinfo_url(title)
            if url:
                return url
    return None


def fetch_wiki_icon_url(name: str) -> str | None:
    """Resolve a working /images/…/Icon_*.png URL, or None if not on the wiki."""
    for filename in wiki_icon_filename_candidates(name):
        url = _imageinfo_url(f"File:{filename}")
        if url:
            return url

    return _icon_from_wiki_page(name)
