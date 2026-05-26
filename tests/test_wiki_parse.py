"""Wiki wikitext parsing (release dates only)."""

from wiki_parse import parse_revealed_date, parse_wiki_timestamp

IMP_WIKI = """
\t\t\t\t\t Type
\t\t\t\t\t [[Character Types#Demon|Demon]]
\t\t\t\t\t Artist
\t\t\t\t\t Aidan Roberts
\t\t\t \"We must keep our wits sharp and our sword sharper.\"
== Summary ==
"Each night*, choose a player: they die. If you kill yourself this way, a Minion becomes the Imp."
"""

AL_HADIKHIA_WIKI = """
\t\t\t\t\t Type
\t\t\t\t\t [[Character Types#Demon|Demon]]
\t\t\t\t\t Revealed
\t\t\t\t\t 12/08/2021
\t\t\t \"Alsukut min dhahab.\"
== Summary ==
"Each night*, you may choose 3 players (all players learn who): each silently chooses to live or die, but if all live, all die."
"""

ACROBAT_HTML_WIKI = """
<table>
<tr><td>Type</td><td>[[Character Types#Townsfolk|Townsfolk]]</td></tr>
<tr><td>Artist</td><td>Chloe McDougall</td></tr>
<tr><td>Revealed</td><td>24/05/2020</td></tr>
</table>
<p class='flavour'>"Ladies and gentlemen, hold fast to your hats."</p>
== Summary ==
"Each night*, choose a player: if they are or become drunk or poisoned tonight, you die."
"""

GOD_OF_UG_WIKI = """
 Facts
 Type
 Green
 When
 19/03/2026
 "Me go Ug. Too eas- oh no!"
== Ug ==
"One Ug hat. When wear Ug hat, must speak one sound at a time but vote twice. If fail, pass Ug hat."
"""


def test_parse_revealed_date() -> None:
    assert parse_revealed_date(AL_HADIKHIA_WIKI) == "2021-08-12"
    assert parse_revealed_date(IMP_WIKI) is None


def test_parse_revealed_date_html_table() -> None:
    assert parse_revealed_date(ACROBAT_HTML_WIKI) == "2020-05-24"


def test_parse_revealed_date_when_field() -> None:
    assert parse_revealed_date(GOD_OF_UG_WIKI) == "2026-03-19"


def test_parse_wiki_timestamp() -> None:
    assert parse_wiki_timestamp("2018-06-15T14:30:00Z") == "2018-06-15"
    assert parse_wiki_timestamp("2021-08-12T09:00:00+00:00") == "2021-08-12"
    assert parse_wiki_timestamp("") is None
