"""Cycle-locked rotation logic."""

from __future__ import annotations

from datetime import date, timedelta

from transform import cycle_order, resolve_character, roster_at


def test_mid_cycle_new_character(
    characters: dict, shuffle_seed: str, rotation_start: date
) -> None:
    order0 = roster_at(rotation_start, characters, shuffle_seed)
    n0 = len(order0)

    chars_copy = dict(characters)
    chars_copy["NewTestChar"] = {
        "name": "NewTestChar",
        "type": "Townsfolk",
        "ability": "Test",
        "flavor": "",
        "wiki_url": "https://example.com",
        "icon_url": "https://example.com/x.png",
        "first_available": "2026-01-15",
    }

    order_mid = roster_at(rotation_start, chars_copy, shuffle_seed)
    assert len(order_mid) == n0
    assert "NewTestChar" not in order_mid

    after_cycle = rotation_start + timedelta(days=n0)
    order_next = roster_at(after_cycle, chars_copy, shuffle_seed)
    assert "NewTestChar" in order_next


def test_no_repeat_across_cycle_boundary(
    characters: dict, shuffle_seed: str, rotation_start: date
) -> None:
    order0 = cycle_order(rotation_start, characters, shuffle_seed)
    n0 = len(order0)
    last_day = rotation_start + timedelta(days=n0 - 1)
    first_next_cycle = rotation_start + timedelta(days=n0)

    last_char = resolve_character(
        rotation_start, last_day, characters, shuffle_seed
    )[0]["slug"]
    first_char = resolve_character(
        rotation_start, first_next_cycle, characters, shuffle_seed
    )[0]["slug"]

    assert last_char != first_char

    order1 = cycle_order(first_next_cycle, characters, shuffle_seed, last_char)
    assert order1[0] != last_char

    cycle_start = rotation_start
    last_slug: str | None = None
    for _ in range(5):
        order = cycle_order(cycle_start, characters, shuffle_seed, last_slug)
        if last_slug is not None:
            assert order[0] != last_slug
        last_slug = order[-1]
        cycle_start += timedelta(days=len(order))
