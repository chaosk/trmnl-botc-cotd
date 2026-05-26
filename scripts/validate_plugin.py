#!/usr/bin/env python3
"""Validate plugin files without trmnlp (offline smoke check)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DATA = ROOT / "data"

REQUIRED_SRC = [
    "settings.yml",
    "transform.py",
    "shared.liquid",
    "full.liquid",
    "half_horizontal.liquid",
    "half_vertical.liquid",
    "quadrant.liquid",
]

LIQUID_MARKERS = {
    "shared.liquid": [
        "character_card",
        "character_text",
        "title_bar",
        "wiki_qr",
        "qr_code: 3",
        "flex flex--col",
        "data-clamp",
        "text--gray-45",
    ],
    "full.liquid": [
        "layout layout--col",
        "botc-layout",
        "character_card",
        "wiki_qr",
    ],
    "half_horizontal.liquid": [
        "layout layout--row",
        "botc-layout",
        "layout--center",
        "character_card",
    ],
    "half_vertical.liquid": [
        "layout layout--col",
        "botc-layout",
        "character_card",
    ],
    "quadrant.liquid": ["layout layout--col", "botc-layout", "character_card"],
}


def main() -> int:
    errors: list[str] = []

    for name in REQUIRED_SRC:
        if not (SRC / name).exists():
            errors.append(f"Missing src/{name}")

    manifest_path = DATA / "characters_manifest.json"
    if not manifest_path.exists():
        errors.append("Missing data/characters_manifest.json")

    chars: dict = {}
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        chars = data.get("characters") or {}
        if len(chars) < 100:
            errors.append(f"Manifest only has {len(chars)} characters (expected ~183)")
        if len(chars) > 190:
            errors.append(f"Manifest has {len(chars)} characters (expected ~183)")
        for slug in ("Alchemist", "Imp", "Drunk"):
            if slug not in chars:
                errors.append(f"Manifest missing {slug}")

    layout_files = (
        "full.liquid",
        "half_horizontal.liquid",
        "half_vertical.liquid",
        "quadrant.liquid",
    )
    for fname, markers in LIQUID_MARKERS.items():
        text = (SRC / fname).read_text(encoding="utf-8")
        for m in markers:
            if m not in text:
                errors.append(f"{fname} missing '{m}'")
        if fname in layout_files and "view view--" in text:
            errors.append(
                f"{fname} must not include view wrapper (TRMNL adds view--* automatically)"
            )

    settings_text = (SRC / "settings.yml").read_text(encoding="utf-8")
    if "keyname: shuffle_seed" not in settings_text:
        errors.append("settings.yml missing shuffle_seed custom field")

    transform_text = (SRC / "transform.py").read_text(encoding="utf-8")
    if "DEFAULT_MANIFEST_URL" not in transform_text:
        errors.append("transform.py missing GitHub manifest fallback URL")
    if "shuffle_seed_from_input" not in transform_text:
        errors.append("transform.py missing shuffle_seed_from_input")

    sys.path.insert(0, str(SRC))
    import importlib.util

    spec = importlib.util.spec_from_file_location("transform", SRC / "transform.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["transform"] = mod
    spec.loader.exec_module(mod)
    out = None
    for payload in (
        {"custom_fields": {"start_date": "2026-05-01"}},
        {
            "trmnl": {
                "plugin_settings": {
                    "custom_fields_values": {"start_date": "2026-05-01"}
                }
            }
        },
    ):
        out = mod.run(payload)
        if out.get("error"):
            errors.append(f"transform error: {out}")
            break
    if out and not out.get("error") and not out.get("name"):
        errors.append("transform returned no character name")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    print(
        f"OK: {len(chars)} characters, today={out.get('name')}, cycle={out.get('cycle_index')}/{out.get('cycle_length')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
