"""Wiki icon filename resolution."""

from wiki_icon_url import (
    _file_icon_key,
    _name_icon_key,
    wiki_icon_filename_candidates,
)


def test_wiki_icon_filename_candidates_includes_compact() -> None:
    names = wiki_icon_filename_candidates("Storm Catcher")
    assert "Icon_storm_catcher.png" in names
    assert "Icon_stormcatcher.png" in names


def test_icon_keys_match() -> None:
    assert _name_icon_key("Storm Catcher") == "stormcatcher"
    assert _file_icon_key("File:Icon stormcatcher.png") == "stormcatcher"
    assert _file_icon_key("File:Icon_stormcatcher.png") == "stormcatcher"
    assert _name_icon_key("Deus ex Fiasco") == "deusexfiasco"
    assert _file_icon_key("File:Icon deusexfiasco.png") == "deusexfiasco"
    assert _name_icon_key("God of Ug") == "godofug"
