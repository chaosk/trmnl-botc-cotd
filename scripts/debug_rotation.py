#!/usr/bin/env python3
"""
Debug Blood on the Clocktower rotation schedules.

Examples:
  python scripts/debug_rotation.py --start 2026-05-01 today
  python scripts/debug_rotation.py --start 2026-05-01 current-cycle
  python scripts/debug_rotation.py --start 2026-05-01 next 30
  python scripts/debug_rotation.py --start 2026-05-01 cycle 2
  python scripts/debug_rotation.py --start 2026-05-01 cycles 0-5
  python scripts/debug_rotation.py --start 2026-05-01 range 2026-06-01 2026-06-15
  python scripts/debug_rotation.py --start 2026-05-01 --today 2026-05-26 next 7
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from transform import (  # noqa: E402
    DEFAULT_SHUFFLE_SEED,
    CycleSchedule,
    cycle_at,
    day_schedule,
    iter_cycles,
    load_manifest,
    parse_date,
)


def char_label(characters: dict, slug: str) -> str:
    c = characters.get(slug) or {}
    t = c.get("type", "")
    return f"{c.get('name', slug)} ({t})" if t else c.get("name", slug)


def print_cycle(cycle: CycleSchedule, characters: dict, *, mark_date: date | None = None) -> None:
    n = len(cycle.order)
    print(
        f"Cycle {cycle.cycle_index}  "
        f"{cycle.cycle_start.isoformat()} → {cycle.cycle_end.isoformat()}  "
        f"({n} days)"
    )
    if cycle.no_repeat_first:
        print(f"  (first day ≠ {char_label(characters, cycle.no_repeat_first)})")
    for i, slug in enumerate(cycle.order):
        d = cycle.cycle_start + timedelta(days=i)
        marker = " ←" if mark_date and d == mark_date else ""
        print(f"  {d.isoformat()}  day {i + 1}/{n}  {char_label(characters, slug)}{marker}")
    print()


def cmd_today(args: argparse.Namespace, characters: dict, seed: str) -> None:
    d = args.today
    row = day_schedule(args.start, d, characters, seed)
    print(f"Today ({d.isoformat()})")
    print(json.dumps(row, indent=2))


def cmd_current_cycle(args: argparse.Namespace, characters: dict, seed: str) -> None:
    cycle = cycle_at(args.start, args.today, characters, seed)
    print(f"Current cycle for {args.today.isoformat()}\n")
    print_cycle(cycle, characters, mark_date=args.today)


def cmd_next(args: argparse.Namespace, characters: dict, seed: str) -> None:
    n = args.count
    print(f"Next {n} days from {args.today.isoformat()}\n")
    for i in range(n):
        d = args.today + timedelta(days=i)
        row = day_schedule(args.start, d, characters, seed)
        print(
            f"{row['date']}  cycle {row['cycle_index']} day {row['day_in_cycle']}/{row['cycle_length']}  "
            f"{row['name']} ({row['type']})"
        )


def cmd_cycle(args: argparse.Namespace, characters: dict, seed: str) -> None:
    idx = args.index
    found = None
    for cycle in iter_cycles(args.start, characters, seed, max_cycles=idx + 1):
        if cycle.cycle_index == idx:
            found = cycle
            break
    if not found:
        print(f"Cycle {idx} not found (rotation may not have reached it yet).", file=sys.stderr)
        sys.exit(1)
    print()
    print_cycle(found, characters)


def cmd_cycles(args: argparse.Namespace, characters: dict, seed: str) -> None:
    lo, hi = args.range_start, args.range_end
    print(f"Cycles {lo}–{hi}\n")
    for cycle in iter_cycles(args.start, characters, seed, max_cycles=hi + 1):
        if cycle.cycle_index < lo:
            continue
        if cycle.cycle_index > hi:
            break
        n = len(cycle.order)
        first = char_label(characters, cycle.order[0])
        last = char_label(characters, cycle.order[-1])
        print(
            f"  {cycle.cycle_index:3d}  {cycle.cycle_start} → {cycle.cycle_end}  "
            f"{n:3d} days  first={first}  last={last}"
        )


def cmd_range(args: argparse.Namespace, characters: dict, seed: str) -> None:
    d = args.from_date
    end = args.to_date
    print(f"Range {d.isoformat()} → {end.isoformat()}\n")
    while d <= end:
        row = day_schedule(args.start, d, characters, seed)
        print(
            f"{row['date']}  c{row['cycle_index']} {row['day_in_cycle']}/{row['cycle_length']}  "
            f"{row['name']}"
        )
        d += timedelta(days=1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Debug BoTC daily character rotation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--start",
        required=True,
        metavar="YYYY-MM-DD",
        help="Rotation start date (cycle 0 begins)",
    )
    p.add_argument(
        "--today",
        metavar="YYYY-MM-DD",
        default=None,
        help="Anchor date for 'today' / current-cycle / next (default: calendar today)",
    )
    p.add_argument(
        "--seed",
        default=DEFAULT_SHUFFLE_SEED,
        help=f"Shuffle seed (default: {DEFAULT_SHUFFLE_SEED})",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="JSON output where supported (today, next, range)",
    )

    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("today", help="Show assignment for anchor date")

    sub.add_parser("current-cycle", aliases=["current"], help="Full list for anchor's cycle")

    pn = sub.add_parser("next", help="Upcoming N days from anchor")
    pn.add_argument("count", type=int, help="Number of days")

    pc = sub.add_parser("cycle", help="Full list for one cycle index (0-based)")
    pc.add_argument("index", type=int, help="Cycle number")

    pcs = sub.add_parser("cycles", help="Summary of cycle index range")
    pcs.add_argument("range", metavar="N-M", help="e.g. 0-5")

    pr = sub.add_parser("range", help="Day-by-day between two dates")
    pr.add_argument("from_date", metavar="FROM", help="YYYY-MM-DD")
    pr.add_argument("to_date", metavar="TO", help="YYYY-MM-DD")

    return p


def parse_cycle_range(spec: str) -> tuple[int, int]:
    if "-" not in spec:
        n = int(spec)
        return n, n
    a, b = spec.split("-", 1)
    return int(a), int(b)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    start = parse_date(args.start)
    if not start:
        parser.error(f"Invalid --start: {args.start}")

    args.start = start
    args.today = parse_date(args.today) if args.today else date.today()

    manifest = load_manifest()
    characters = manifest.get("characters") or {}
    seed = str(args.seed)

    if args.command == "cycles":
        args.range_start, args.range_end = parse_cycle_range(args.range)

    handlers = {
        "today": cmd_today,
        "current-cycle": cmd_current_cycle,
        "current": cmd_current_cycle,
        "next": cmd_next,
        "cycle": cmd_cycle,
        "cycles": cmd_cycles,
        "range": cmd_range,
    }
    if args.command == "range":
        args.from_date = parse_date(args.from_date)
        args.to_date = parse_date(args.to_date)
        if not args.from_date or not args.to_date:
            parser.error("Invalid range dates")

    handlers[args.command](args, characters, seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
