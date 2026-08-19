"""Tests for scripts/build_pdf.py — reading card files, languages, engine payload.

The end-to-end typeset is its own CI step (`lernkarten check`); the test here
only runs when an engine is already on the machine, so the suite never
downloads anything.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_pdf  # noqa: E402
import engine  # noqa: E402


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


MINIMAL = """
topic: 'Statistics'
cards:
  - subtopic: 'Bayes'
    front: 'Question'
    back: 'Answer'
    source: 'Lecture 3'
"""


# --- load_cards -----------------------------------------------------------


def test_load_cards_reads_the_fields(tmp_path):
    cards, errors, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", MINIMAL)], [], [])
    assert errors == []
    assert cards == [
        {
            "id": "a-1",
            "topic": "Statistics",
            "subtopic": "Bayes",
            "front": "Question",
            "back": "Answer",
            "source": "Lecture 3",
            "language": "english",
        }
    ]


def test_load_cards_reports_broken_files(tmp_path):
    path = write(tmp_path, "broken.yaml", "topic: 'unclosed\ncards:\n")
    cards, errors, _ = build_pdf.load_cards([path], [], [])
    assert cards == []
    assert len(errors) == 1 and "line 1" in errors[0]


def test_load_cards_reports_missing_required_fields(tmp_path):
    path = write(tmp_path, "b.yaml", "topic: 'T'\ncards:\n  - front: 'front only'\n")
    cards, errors, _ = build_pdf.load_cards([path], [], [])
    assert cards == []
    assert "'front' and 'back' are required" in errors[0]


def test_load_cards_reports_the_wrong_structure(tmp_path):
    path = write(tmp_path, "c.yaml", "- a\n- list\n")
    _, errors, _ = build_pdf.load_cards([path], [], [])
    assert "expected a mapping" in errors[0]


def test_load_cards_falls_back_to_the_filename_as_topic(tmp_path):
    path = write(tmp_path, "no-topic.yaml", "cards:\n  - front: 'f'\n    back: 'b'\n")
    cards, errors, _ = build_pdf.load_cards([path], [], [])
    assert errors == []
    assert cards[0]["topic"] == "no-topic"
    assert cards[0]["source"] == ""


def test_filter_matches_substrings_case_insensitively(tmp_path):
    path = write(tmp_path, "a.yaml", MINIMAL)
    assert build_pdf.load_cards([path], ["statis"], [])[0]
    assert build_pdf.load_cards([path], ["Analysis"], [])[0] == []
    assert build_pdf.load_cards([path], [], ["BAYES"])[0]
    assert build_pdf.load_cards([path], [], ["Markov"])[0] == []


# --- languages ------------------------------------------------------------


def test_languages_are_named_the_way_a_user_would_name_them():
    assert build_pdf.resolve_language("german") == "german"
    assert build_pdf.resolve_language("German") == "german"
    assert build_pdf.resolve_language(" english ") == "english"
    assert build_pdf.resolve_language("de") == "german"
    assert build_pdf.resolve_language("de-AT") == "german"
    assert build_pdf.resolve_language("pt") == "portuguese"


def test_an_unknown_language_names_the_ones_that_work():
    with pytest.raises(ValueError) as e:
        build_pdf.resolve_language("klingon")
    assert "klingon" in str(e.value) and "german" in str(e.value)


def test_a_card_file_declares_its_own_language(tmp_path):
    path = write(
        tmp_path, "de.yaml", "topic: 'T'\nlanguage: german\ncards:\n  - front: 'f'\n    back: 'b'\n"
    )
    cards, errors, _ = build_pdf.load_cards([path], [], [])
    assert errors == []
    assert cards[0]["language"] == "german"


def test_a_card_file_without_a_language_falls_back(tmp_path):
    path = write(tmp_path, "a.yaml", MINIMAL)
    assert build_pdf.load_cards([path], [], [])[0][0]["language"] == "english"
    assert build_pdf.load_cards([path], [], [], "french")[0][0]["language"] == "french"


def test_an_unknown_language_in_a_file_is_reported_not_crashed(tmp_path):
    path = write(
        tmp_path, "x.yaml", "topic: 'T'\nlanguage: elvish\ncards:\n  - front: 'f'\n    back: 'b'\n"
    )
    cards, errors, _ = build_pdf.load_cards([path], [], [])
    assert cards == []
    assert "unknown language" in errors[0] and "elvish" in errors[0]


def test_the_document_language_follows_the_cards_unless_overridden():
    cards = [card(0, "german"), card(1, "german"), card(2, "english")]
    assert build_pdf.main_language(cards) == "german"
    assert build_pdf.main_language(cards, "english") == "english"
    assert build_pdf.main_language([]) == build_pdf.DEFAULT_LANGUAGE


# --- what the template receives -------------------------------------------


def card(i, language="english"):
    return {
        "id": f"c-{i}",
        "topic": "T",
        "subtopic": "S",
        "front": f"F{i}",
        "back": f"B{i}",
        "source": "",
        "language": language,
    }


def test_the_payload_translates_languages_for_the_engine():
    # The user says "german"; the engine wants "de" — that never leaks out.
    data = build_pdf.payload([card(0, "german"), card(1, "english")])
    assert [c["lang"] for c in data] == ["de", "en"]
    assert data[0]["language"] == "german", "the user-facing name is kept too"
    json.dumps(data)  # must survive the trip through the data file


def test_every_card_keeps_an_id_so_failures_can_be_traced():
    assert [c["id"] for c in build_pdf.payload([card(0), card(1)])] == ["c-0", "c-1"]


def test_engine_complaints_are_stripped_of_paths_and_excerpts():
    raw = (
        "error: unknown variable: Var\n"
        "  ┌─ /tmp/whatever/cards.typ:68:7\n"
        "  │\n"
        '68│   eval(card.front, mode: "markup")\n'
        "  = hint: try placing it in quotes\n"
    )
    assert build_pdf.readable(raw) == [
        "unknown variable: Var",
        "hint: try placing it in quotes",
    ]
    assert build_pdf.readable("") == ["no output"]


# --- the bundled example --------------------------------------------------


def test_example_cards_satisfy_the_schema():
    cards, errors, _ = build_pdf.load_cards([str(ROOT / "cards" / "example.yaml")], [], [])
    assert errors == []
    assert cards, "cards/example.yaml is the schema reference and must contain cards"
    assert {c["language"] for c in cards} == {"english"}


def has_engine():
    try:
        engine.find(fetch_if_missing=False)
    except engine.EngineError:
        return False
    return True


@pytest.mark.skipif(not has_engine(), reason="no engine on this machine; CI covers the real build")
def test_the_example_actually_typesets(tmp_path):
    binary, _ = engine.find(fetch_if_missing=False)
    cards, _, _ = build_pdf.load_cards([str(ROOT / "cards" / "example.yaml")], [], [])
    target = tmp_path / "out.pdf"
    grid = build_pdf.DEFAULT_GRID
    ok, message = build_pdf.typeset(cards, target, 5.0, True, grid, binary, tmp_path)
    assert ok, message
    assert target.exists() and target.stat().st_size > 1000
    assert build_pdf.overflowing(binary, tmp_path, 5.0, True, grid) == [], "example cards must fit"


# --- the press-sheet grid (feat/card-grid) --------------------------------


def test_a_grid_is_read_as_columns_and_rows():
    assert build_pdf.parse_grid("2x4") == (2, 4)
    assert build_pdf.parse_grid("4x4") == (4, 4)


def test_the_a_series_aliases_name_the_same_grids():
    assert build_pdf.parse_grid("a7") == build_pdf.parse_grid("2x4") == (2, 4)
    assert build_pdf.parse_grid("a8") == build_pdf.parse_grid("4x4") == (4, 4)


def test_a_grid_is_read_case_insensitively():
    assert build_pdf.parse_grid("A8") == build_pdf.parse_grid(" 4X4 ") == (4, 4)


@pytest.mark.parametrize("value", ["3 x 4", "3,4", "eight", "0x4", "3x0", "-1x4", "", "4x"])
def test_a_malformed_grid_names_the_value(value):
    with pytest.raises(ValueError) as excinfo:
        build_pdf.parse_grid(value)
    assert repr(value) in str(excinfo.value) or value in str(excinfo.value)


@pytest.mark.parametrize("value", ["3x4", "2x6", "1x1", "4x8"])
def test_an_unsupported_grid_lists_what_is_supported(value):
    with pytest.raises(ValueError) as excinfo:
        build_pdf.parse_grid(value)
    message = str(excinfo.value)
    assert "2x4" in message and "4x4" in message, message
    assert "a7" in message.lower() and "a8" in message.lower(), message


def test_the_page_count_follows_the_grid():
    assert build_pdf.pages(29, (2, 4)) == 8
    assert build_pdf.pages(29, (4, 4)) == 4
    assert build_pdf.pages(12, (4, 4)) == 2
    assert build_pdf.pages(12, (2, 4)) == 4


def test_one_card_still_needs_a_front_and_a_back_page():
    assert build_pdf.pages(1, (2, 4)) == 2
    assert build_pdf.pages(1, (4, 4)) == 2


# --- resolving the grid from flag, deck and default (US2) ------------------


def deck(tmp_path, name, grid=None):
    """A one-card file, with or without a top-level `grid:` key."""
    body = (
        MINIMAL
        if grid is None
        else MINIMAL.replace("topic: 'Statistics'", f"topic: 'Statistics'\ngrid: {grid}")
    )
    return write(tmp_path, name, body)


def declared(*files):
    """What load_cards() saw declared, which is what resolve_grid() reads."""
    return build_pdf.load_cards(list(files), [], [])[2]


def test_the_flag_beats_the_deck_and_the_deck_beats_the_default(tmp_path):
    """FR-013: --grid wins over the file, the file wins over A7."""
    a8 = declared(deck(tmp_path, "a8.yaml", "a8"))
    silent = declared(deck(tmp_path, "silent.yaml"))
    assert build_pdf.resolve_grid(a8, "a7") == (2, 4), "the flag overrides the deck"
    assert build_pdf.resolve_grid(a8, None) == (4, 4), "the deck overrides the default"
    assert build_pdf.resolve_grid(silent, None) == (2, 4), "no key means A7"
    assert build_pdf.resolve_grid([], None) == (2, 4), "nothing at all means A7"


def test_two_decks_that_disagree_name_both_files_and_both_values(tmp_path):
    """FR-014: a disagreement fails loudly, and --grid settles it silently."""
    both = declared(deck(tmp_path, "eight.yaml", "a8"), deck(tmp_path, "seven.yaml", "a7"))
    with pytest.raises(ValueError) as excinfo:
        build_pdf.resolve_grid(both, None)
    message = str(excinfo.value)
    assert "eight.yaml" in message and "seven.yaml" in message, message
    assert "4x4" in message and "2x4" in message, message
    assert build_pdf.resolve_grid(both, "a8") == (4, 4), "the flag resolves it"
    assert build_pdf.resolve_grid(both, "a7") == (2, 4)


def test_a_declared_grid_conflicts_with_a_deck_that_declares_nothing(tmp_path):
    """FR-014a: absent is a value too, and the message says which is which."""
    mixed = declared(deck(tmp_path, "eight.yaml", "a8"), deck(tmp_path, "silent.yaml"))
    with pytest.raises(ValueError) as excinfo:
        build_pdf.resolve_grid(mixed, None)
    message = str(excinfo.value)
    assert "eight.yaml" in message and "silent.yaml" in message, message
    assert "4x4" in message and "2x4" in message, message
    assert "declares" in message and "no grid" in message, (
        f"a declared value and an absent one must read differently: {message}"
    )
    # A7 declared beside nothing declared is not a disagreement — both mean 2x4.
    agreeing = declared(deck(tmp_path, "seven.yaml", "a7"), deck(tmp_path, "quiet.yaml"))
    assert build_pdf.resolve_grid(agreeing, None) == (2, 4)
