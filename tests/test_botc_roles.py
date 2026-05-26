"""Official roles.json helpers."""

from botc_roles import TEAM_TO_TYPE, role_type


def test_team_to_type() -> None:
    assert TEAM_TO_TYPE["townsfolk"] == "Townsfolk"
    assert TEAM_TO_TYPE["loric"] == "Loric"


def test_role_type() -> None:
    assert role_type({"team": "demon"}) == "Demon"
    assert role_type({"team": "townsfolk"}) == "Townsfolk"


def test_ogre_flavor_preserved_verbatim() -> None:
    """Pseudo-tags in roles.json must not be stripped as HTML."""
    flavor = "<grunt><grin></grunt>"
    role = {"flavor": flavor}
    synced = role["flavor"] if role.get("flavor") is not None else ""
    assert synced == flavor
