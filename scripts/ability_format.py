"""Format character ability text when syncing from roles.json."""

from __future__ import annotations

import re

_ABILITY_BRACKET_RE = re.compile(r"\[[^\]]+\]")


def format_ability_brackets(text: str) -> str:
    """Turn [setup modifier] segments into markdown bold for TRMNL rendering."""
    if not text:
        return text

    def repl(match: re.Match[str]) -> str:
        start = match.start()
        end = match.end()
        if start >= 2 and text[start - 2 : start] == "**":
            return match.group(0)
        if end + 2 <= len(text) and text[end : end + 2] == "**":
            return match.group(0)
        return f"**{match.group(0)}**"

    return _ABILITY_BRACKET_RE.sub(repl, text)
