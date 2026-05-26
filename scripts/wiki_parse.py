"""Parse release dates from Blood on the Clocktower wiki wikitext."""

from __future__ import annotations

import re
from datetime import datetime


def _infobox_section(wikitext: str) -> str:
    """Content before Summary / Appears in (infobox — wikitext or HTML layout)."""
    before_summary = re.split(r"==\s*Summary\s*==", wikitext, maxsplit=1, flags=re.I)[0]
    end = re.search(
        r"(?:Appears in|Character Showcase|Related Jinxes)",
        before_summary,
        re.IGNORECASE,
    )
    return before_summary[: end.start()] if end else before_summary


def _parse_revealed_match(m: re.Match[str]) -> str | None:
    try:
        return datetime.strptime(m.group(1).strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def parse_revealed_date(wikitext: str) -> str | None:
    box = _infobox_section(wikitext)
    for pattern in (
        r"<td>\s*Revealed\s*</td>\s*<td>\s*(\d{1,2}/\d{1,2}/\d{4})\s*</td>",
        r"<td>\s*When\s*</td>\s*<td>\s*(\d{1,2}/\d{1,2}/\d{4})\s*</td>",
        r"Revealed\s+(\d{1,2}/\d{1,2}/\d{4})",
        r"When\s+(\d{1,2}/\d{1,2}/\d{4})",
    ):
        m = re.search(pattern, box, re.IGNORECASE | re.DOTALL)
        if m:
            return _parse_revealed_match(m)
    return None


def parse_wiki_timestamp(timestamp: str) -> str | None:
    """MediaWiki ISO timestamp (e.g. 2018-06-15T14:30:00Z) -> YYYY-MM-DD."""
    if not timestamp or not timestamp.strip():
        return None
    ts = timestamp.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts).date().isoformat()
    except ValueError:
        return None
