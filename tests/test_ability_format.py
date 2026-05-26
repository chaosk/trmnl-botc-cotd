"""Ability bracket → markdown bold formatting."""

from ability_format import format_ability_brackets


def test_brackets_become_bold() -> None:
    assert (
        format_ability_brackets("There are extra Outsiders in play. [+2 Outsiders]")
        == "There are extra Outsiders in play. **[+2 Outsiders]**"
    )


def test_multiple_brackets() -> None:
    assert format_ability_brackets("[-1 or +1 Outsider] and [No Demon]") == (
        "**[-1 or +1 Outsider]** and **[No Demon]**"
    )


def test_skips_already_bold() -> None:
    assert format_ability_brackets("already **[+2 Outsiders]** here") == (
        "already **[+2 Outsiders]** here"
    )


def test_empty_unchanged() -> None:
    assert format_ability_brackets("") == ""
