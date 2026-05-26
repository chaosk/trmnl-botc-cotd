"""
Blood on the Clocktower daily character transform for TRMNL.

Cycle-locked roster with per-cycle deterministic shuffle.
"""
import hashlib
import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterator

MANIFEST_FILENAME = "characters_manifest.json"
DEFAULT_SHUFFLE_SEED = "botc-trmnl-cotd-v1"
DEFAULT_MANIFEST_URL = (
    "https://raw.githubusercontent.com/chaosk/trmnl-botc-cotd/master/data/characters_manifest.json"
)
MANIFEST_HTTP_TIMEOUT = 30.0

JsonDict = dict[str, Any]
_manifest_cache: JsonDict | None = None

@dataclass(frozen=True)
class CycleSchedule:
    cycle_index: int
    cycle_start: date
    cycle_end: date  # exclusive
    order: tuple[str, ...]
    no_repeat_first: str | None


# --- Dates & plugin settings ------------------------------------------------


def parse_date(value: str | None) -> date | None:
    if not value or not str(value).strip():
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def custom_fields_from_input(input_data: JsonDict) -> JsonDict:
    """Merge custom field values from all shapes trmnlp/TRMNL use."""
    plugin_settings = (input_data.get("trmnl") or {}).get("plugin_settings") or {}
    fields = (
        input_data.get("custom_fields")
        or input_data.get("custom_fields_values")
        or plugin_settings.get("custom_fields_values")
        or plugin_settings.get("custom_fields")
        or {}
    )
    return fields if isinstance(fields, dict) else {}


def start_date_from_input(input_data: JsonDict) -> date | None:
    val = input_data.get("start_date")
    if val not in (None, ""):
        return parse_date(str(val))

    val = custom_fields_from_input(input_data).get("start_date")
    if val not in (None, ""):
        return parse_date(str(val))
    return None


def shuffle_seed_from_input(
    input_data: JsonDict, manifest: JsonDict | None = None
) -> str:
    for val in (
        input_data.get("shuffle_seed"),
        custom_fields_from_input(input_data).get("shuffle_seed"),
    ):
        if val not in (None, ""):
            return str(val).strip()

    if manifest:
        legacy = manifest.get("shuffle_seed")
        if legacy not in (None, ""):
            return str(legacy).strip()

    return DEFAULT_SHUFFLE_SEED


def show_qr_code_from_input(input_data: JsonDict) -> bool:
    """Whether to render the wiki QR corner (default on)."""
    for val in (
        input_data.get("show_qr_code"),
        custom_fields_from_input(input_data).get("show_qr_code"),
    ):
        if val is None:
            continue
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        if s in ("false", "0", "no", "off"):
            return False
        return True
    return True


# --- Manifest ----------------------------------------------------------------


def resolve_manifest_path() -> Path | None:
    """
    Locate characters_manifest.json on disk (local dev / Docker preview).

    Returns None when no file is found — TRMNL Serverless only deploys transform.py.
    """
    here = Path(__file__).resolve().parent
    candidates: list[Path] = []

    plugin_root = os.environ.get("TRMNLP_PLUGIN_ROOT", "").strip()
    if plugin_root:
        candidates.append(Path(plugin_root) / "data" / MANIFEST_FILENAME)

    candidates.extend(
        [
            Path("/plugin/data") / MANIFEST_FILENAME,
            Path.cwd() / "data" / MANIFEST_FILENAME,
        ]
    )

    for parent in [here, *here.parents, Path.cwd(), *Path.cwd().parents]:
        candidates.append(parent / "data" / MANIFEST_FILENAME)

    seen: set[Path] = set()
    for path in candidates:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    return None


def manifest_url() -> str:
    return (
        os.environ.get("BOTC_MANIFEST_URL", "").strip()
        or os.environ.get("MANIFEST_URL", "").strip()
        or DEFAULT_MANIFEST_URL
    )


def fetch_manifest_from_url(url: str) -> JsonDict:
    req = urllib.request.Request(
        url, headers={"User-Agent": "trmnl-botc-cotd/1.0"}
    )
    with urllib.request.urlopen(req, timeout=MANIFEST_HTTP_TIMEOUT) as resp:
        data = json.load(resp)
    if not isinstance(data, dict):
        raise ValueError("Manifest response was not a JSON object")
    return data


def load_manifest() -> JsonDict:
    global _manifest_cache
    if _manifest_cache is not None:
        return _manifest_cache

    path = resolve_manifest_path()
    if path is not None:
        with path.open(encoding="utf-8") as f:
            _manifest_cache = json.load(f)
            return _manifest_cache

    url = manifest_url()
    try:
        _manifest_cache = fetch_manifest_from_url(url)
        return _manifest_cache
    except Exception as exc:
        raise FileNotFoundError(
            f"characters_manifest.json not found locally and could not fetch from {url}: {exc}"
        ) from exc


def load_characters(manifest: JsonDict) -> JsonDict:
    characters = manifest.get("characters") or {}
    if not characters:
        raise ValueError("Character manifest is empty. Run scripts/sync_characters.py.")
    return characters


# --- Rotation ----------------------------------------------------------------


def stable_hash(*parts: str) -> int:
    data = "|".join(parts).encode("utf-8")
    return int(hashlib.sha256(data).hexdigest(), 16)


def first_available(char: JsonDict) -> date | None:
    return parse_date(char.get("first_available", ""))


def roster_at(cycle_start: date, characters: JsonDict, shuffle_seed: str) -> list[str]:
    eligible = [
        slug
        for slug, char in characters.items()
        if (available := first_available(char)) is not None and available <= cycle_start
    ]
    return sorted(
        eligible,
        key=lambda slug: stable_hash(shuffle_seed, cycle_start.isoformat(), slug),
    )


def cycle_order(
    cycle_start: date,
    characters: JsonDict,
    shuffle_seed: str,
    no_repeat_first: str | None = None,
) -> list[str]:
    """
    Per-cycle shuffle. If no_repeat_first is set (last character of previous cycle),
    that slug cannot be first in this cycle — so no character appears two days in a row
    across a cycle boundary.
    """
    order = roster_at(cycle_start, characters, shuffle_seed)
    if no_repeat_first and len(order) > 1 and order[0] == no_repeat_first:
        return order[1:] + [no_repeat_first]
    return order


def iter_cycles(
    start: date,
    characters: JsonDict,
    shuffle_seed: str,
    *,
    through: date | None = None,
    max_cycles: int | None = None,
) -> Iterator[CycleSchedule]:
    """Yield each cycle's schedule from cycle 0 onward."""
    cycle_start = start
    cycle_index = 0
    last_slug: str | None = None

    while True:
        if max_cycles is not None and cycle_index >= max_cycles:
            return

        order = tuple(cycle_order(cycle_start, characters, shuffle_seed, last_slug))
        if not order:
            raise ValueError("No characters available for cycle")

        cycle_end = cycle_start + timedelta(days=len(order))
        yield CycleSchedule(
            cycle_index=cycle_index,
            cycle_start=cycle_start,
            cycle_end=cycle_end,
            order=order,
            no_repeat_first=last_slug,
        )

        if through is not None and through < cycle_end:
            return

        last_slug = order[-1]
        cycle_start = cycle_end
        cycle_index += 1


def cycle_at(
    start: date, on_date: date, characters: JsonDict, shuffle_seed: str
) -> CycleSchedule:
    """Return the cycle that contains on_date."""
    if on_date < start:
        on_date = start
    for cycle in iter_cycles(start, characters, shuffle_seed, through=on_date):
        if cycle.cycle_start <= on_date < cycle.cycle_end:
            return cycle
    raise ValueError(f"No cycle found for {on_date.isoformat()}")


def character_on_date(
    start: date, on_date: date, characters: JsonDict, shuffle_seed: str
) -> tuple[JsonDict, CycleSchedule, int]:
    """Return (character dict with slug, cycle, 1-based day_in_cycle)."""
    cycle = cycle_at(start, on_date, characters, shuffle_seed)
    day_index = (on_date - cycle.cycle_start).days
    slug = cycle.order[day_index]
    char = {**characters[slug], "slug": slug}
    return char, cycle, day_index + 1


def resolve_character(
    start: date, today: date, characters: JsonDict, shuffle_seed: str
) -> tuple[JsonDict, int, int, int]:
    """Return (character, 1-based cycle_index, day_in_cycle, cycle_length)."""
    char, cycle, day_in_cycle = character_on_date(
        start, today, characters, shuffle_seed
    )
    return char, cycle.cycle_index + 1, day_in_cycle, len(cycle.order)


def day_schedule(
    start: date, on_date: date, characters: JsonDict, shuffle_seed: str
) -> JsonDict:
    """One calendar day's assignment (for debug_rotation.py)."""
    char, cycle, day_in_cycle = character_on_date(
        start, on_date, characters, shuffle_seed
    )
    return {
        "date": on_date.isoformat(),
        "slug": char["slug"],
        **character_fields(char),
        "cycle_index": cycle.cycle_index + 1,
        "day_in_cycle": day_in_cycle,
        "cycle_length": len(cycle.order),
        "cycle_start": cycle.cycle_start.isoformat(),
        "cycle_end": cycle.cycle_end.isoformat(),
    }


# --- TRMNL entrypoint --------------------------------------------------------


def plugin_error(message: str) -> JsonDict:
    return {"error": message}


def character_fields(char: JsonDict) -> JsonDict:
    """Liquid merge fields for one character."""
    return {
        "name": char.get("name", ""),
        "type": char.get("type", ""),
        "ability": char.get("ability", ""),
        "flavor": char.get("flavor", ""),
        "icon_url": char.get("icon_url", ""),
        "wiki_url": char.get("wiki_url", ""),
    }


def merge_output(
    char: JsonDict,
    *,
    start: date,
    today: date,
    cycle: CycleSchedule,
    day_in_cycle: int,
    show_qr_code: bool,
) -> JsonDict:
    return {
        **character_fields(char),
        "cycle_index": cycle.cycle_index + 1,
        "day_in_cycle": day_in_cycle,
        "cycle_length": len(cycle.order),
        "start_date": start.isoformat(),
        "today": today.isoformat(),
        "show_qr_code": show_qr_code,
    }


def run(input_data: JsonDict) -> JsonDict:
    start = start_date_from_input(input_data)
    if not start:
        return plugin_error("Set a start date (YYYY-MM-DD) in plugin settings.")

    try:
        manifest = load_manifest()
        characters = load_characters(manifest)
        shuffle_seed = shuffle_seed_from_input(input_data, manifest)
    except FileNotFoundError as exc:
        return plugin_error(f"Could not load character manifest: {exc}")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return plugin_error(f"Could not load character manifest: {exc}")

    today = date.today()
    try:
        char, cycle, day_in_cycle = character_on_date(
            start, today, characters, shuffle_seed
        )
    except ValueError as exc:
        return plugin_error(str(exc))

    return merge_output(
        char,
        start=start,
        today=today,
        cycle=cycle,
        day_in_cycle=day_in_cycle,
        show_qr_code=show_qr_code_from_input(input_data),
    )
