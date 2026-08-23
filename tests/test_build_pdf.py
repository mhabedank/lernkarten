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
            # Was "a-1", the file stem and the card's position. MINIMAL declares
            # no id, and an absent id is now the empty string — while `ref`
            # keeps the positional label so diagnostics can still name the card.
            "id": "",
            "ref": "a-1",
            "topic": "Statistics",
            "subtopic": "Bayes",
            "front": "Question",
            "back": "Answer",
            "source": "Lecture 3",
            "language": "english",
            # A face without a picture is the empty string, never a missing
            # key — the same bargain `id` strikes, and for the same reason:
            # templates/card.typ reads both fields unconditionally.
            "front_image": "",
            "back_image": "",
        }
    ]


# --- pictures on a card ----------------------------------------------------
#
# A path is relative to the project root, and the project root is the parent of
# the directory the card file sits in. So a deck under test has to go into
# cards/, the way the pipeline writes one — not into tmp_path itself.

PNG = b"\x89PNG\r\n\x1a\n"  # a file with the right name; the engine judges the rest

WITH_PICTURE = """
topic: 'Statistics'
cards:
  - id: A45DK
    subtopic: 'Bayes'
    front: 'Question'
    back: 'Answer'
    back_image: 'figures/demo/chart.png'
"""


def deck_with_picture(tmp_path, deck=WITH_PICTURE, pictures=("figures/demo/chart.png",)):
    (tmp_path / "cards").mkdir(exist_ok=True)
    for relative in pictures:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(PNG)
    return write(tmp_path / "cards", "deck.yaml", deck)


def test_load_cards_carries_the_picture_keys(tmp_path):
    cards, errors, _ = build_pdf.load_cards([deck_with_picture(tmp_path)], [], [])
    assert errors == []
    assert cards[0].get("front_image") == ""
    assert cards[0].get("back_image") == str(
        (tmp_path / "figures" / "demo" / "chart.png").resolve()
    )


def test_a_picture_path_resolves_against_the_project_root(tmp_path, monkeypatch):
    """A deck that only builds from one working directory is not portable."""
    deck = deck_with_picture(tmp_path)
    monkeypatch.chdir(tmp_path)
    inside, errors_inside, _ = build_pdf.load_cards([deck], [], [])
    monkeypatch.chdir(ROOT)
    outside, errors_outside, _ = build_pdf.load_cards([deck], [], [])
    assert errors_inside == [] and errors_outside == []
    assert inside[0].get("back_image"), "the resolved path has to be there at all"
    assert inside[0].get("back_image") == outside[0].get("back_image")


# --- the card id comes from the file, not from the card's position ----------
#
# It used to be f"{path.stem}-{i}", which meant inserting a card, deleting one
# or renaming the file silently renamed every id after it — the defect this
# feature exists to remove.

WITH_IDS = """
topic: 'Statistics'
cards:
  - id: A45DK
    subtopic: 'Bayes'
    front: 'First'
    back: 'a'
  - id: QT8M2
    subtopic: 'Bayes'
    front: 'Second'
    back: 'b'
"""

MIXED = """
topic: 'Statistics'
cards:
  - id: A45DK
    subtopic: 'Bayes'
    front: 'Has one'
    back: 'a'
  - subtopic: 'Bayes'
    front: 'Has none'
    back: 'b'
"""


def test_load_cards_takes_the_id_from_the_file(tmp_path):
    cards, errors, _ = build_pdf.load_cards([write(tmp_path, "deck.yaml", WITH_IDS)], [], [])
    assert errors == []
    assert [c["id"] for c in cards] == ["A45DK", "QT8M2"]


def test_a_card_without_an_id_gets_the_empty_string(tmp_path):
    """Never a missing key: the template reads `card.id` unconditionally."""
    cards, errors, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", MINIMAL)], [], [])
    assert errors == []
    assert cards[0]["id"] == ""


def test_the_id_is_never_derived_from_the_file_name(tmp_path):
    cards, _, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", MINIMAL)], [], [])
    assert "a-1" not in [c["id"] for c in cards]


def test_a_deck_can_mix_cards_with_and_without_ids(tmp_path):
    cards, errors, _ = build_pdf.load_cards([write(tmp_path, "deck.yaml", MIXED)], [], [])
    assert errors == []
    assert [c["id"] for c in cards] == ["A45DK", ""]


def test_renaming_the_file_does_not_change_any_id(tmp_path):
    """The defect in one assertion: the stem was the id's prefix."""
    before, _, _ = build_pdf.load_cards([write(tmp_path, "topic-a.yaml", WITH_IDS)], [], [])
    after, _, _ = build_pdf.load_cards([write(tmp_path, "topic-b.yaml", WITH_IDS)], [], [])
    assert [c["id"] for c in before] == [c["id"] for c in after]


def test_inserting_a_card_before_another_does_not_move_its_id(tmp_path):
    inserted = WITH_IDS.replace(
        "cards:\n",
        "cards:\n  - id: V9WXY\n    subtopic: 'New'\n    front: 'Inserted'\n    back: 'x'\n",
        1,
    )
    original, _, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", WITH_IDS)], [], [])
    grown, _, _ = build_pdf.load_cards([write(tmp_path, "b.yaml", inserted)], [], [])
    by_front = {c["front"]: c["id"] for c in grown}
    for card in original:
        assert by_front[card["front"]] == card["id"], card["front"]


def test_filtering_by_subtopic_does_not_change_an_id(tmp_path):
    path = write(tmp_path, "a.yaml", WITH_IDS)
    everything, _, _ = build_pdf.load_cards([path], [], [])
    filtered, _, _ = build_pdf.load_cards([path], [], ["Bayes"])
    assert [c["id"] for c in filtered] == [c["id"] for c in everything]


# --- `ref`: how a diagnostic names a card, which is not the same job ---------
#
# The id is the name a person quotes, so it must not move when the deck is
# edited. A warning only has to *locate* the card in the file, and position is
# perfectly good for that. Keeping them separate is what stops a legacy deck
# with no ids from emitting "WARNING: card  does not fit" with nothing in it.


def test_ref_is_the_id_when_the_card_has_one(tmp_path):
    cards, _, _ = build_pdf.load_cards([write(tmp_path, "deck.yaml", WITH_IDS)], [], [])
    assert [c["ref"] for c in cards] == ["A45DK", "QT8M2"]


def test_ref_falls_back_to_the_position_when_there_is_no_id(tmp_path):
    """A blind warning is worse than a positional one."""
    cards, _, _ = build_pdf.load_cards([write(tmp_path, "overflowing.yaml", MINIMAL)], [], [])
    assert cards[0]["ref"] == "overflowing-1"
    assert cards[0]["id"] == "", "the printed id stays empty; only the diagnostic falls back"


def test_every_card_in_a_mixed_deck_still_gets_a_usable_ref(tmp_path):
    cards, _, _ = build_pdf.load_cards([write(tmp_path, "deck.yaml", MIXED)], [], [])
    refs = [c["ref"] for c in cards]
    assert refs == ["A45DK", "deck-2"]
    assert all(refs), "no card may end up with an empty diagnostic label"


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


def test_a_deck_declaring_a_bad_grid_is_refused_even_when_the_flag_overrides(tmp_path):
    """The flag decides the size; it does not excuse a broken key (G1).

    --grid wins over the deck (FR-013), but a deck whose own `grid:` is
    unsupported or malformed is still wrong, and the contract calls it an
    error unconditionally. Overriding used to skip the check entirely.
    """
    bad = declared(deck(tmp_path, "typo.yaml", "3x4"))
    with pytest.raises(ValueError) as excinfo:
        build_pdf.resolve_grid(bad, "a8")
    message = str(excinfo.value)
    assert "3x4" in message, message
    assert "typo.yaml" in message, f"the file has to be named, or which of six is it: {message}"

    # And the same value with no flag names the file too, which it did not before.
    with pytest.raises(ValueError) as excinfo:
        build_pdf.resolve_grid(bad, None)
    assert "typo.yaml" in str(excinfo.value), str(excinfo.value)

    # A good deck still bends to the flag.
    good = declared(deck(tmp_path, "fine.yaml", "a7"))
    assert build_pdf.resolve_grid(good, "a8") == (4, 4)


# --- the sheet turns, and the card scales (BUG-007) ------------------------


def test_the_sheet_turns_so_the_card_stays_landscape():
    """FR-024/SC-010: each A-series halving flips the orientation.

    A7 tiles a portrait A4 at 2 x 4. A8 landscape is 74 x 52, which does not
    tile a portrait sheet at all (2.83 columns) — so the sheet turns instead,
    and 4 x 4 on a landscape A4 is exact.
    """
    assert build_pdf.sheet((2, 4)) == (210, 297)
    assert build_pdf.sheet((4, 4)) == (297, 210)


def test_every_supported_grid_gives_a_landscape_card():
    """FR-024 asserted over the whole allowlist, not just the two we know.

    A flashcard is wider than it is tall. This was assumed everywhere and
    written down nowhere, which is how a portrait A8 passed every gate.
    """
    for name, grid in build_pdf.GRIDS.items():
        sheet_w, sheet_h = build_pdf.sheet(grid)
        cw, ch = sheet_w / grid[0], sheet_h / grid[1]
        assert cw > ch, f"{name} gives a {cw} x {ch} card, which is portrait"


def test_the_card_scale_follows_the_grid():
    """FR-025: one uniform scale, so every proportion is preserved."""
    assert build_pdf.card_scale((2, 4), 5.0) == 1.0
    assert round(build_pdf.card_scale((4, 4), 5.0), 4) == 0.6969
    # At margin 0 the two cards are exactly similar, so the scale is 1/sqrt(2).
    assert round(build_pdf.card_scale((4, 4), 0.0), 4) == 0.7071


@pytest.mark.parametrize("margin", [0.0, 5.0, 10.0, 20.0])
def test_a7_is_never_rescaled_at_any_margin(margin):
    """SC-002: the default grid must render exactly as it does today.

    The scale is taken against the A7 card *at the same margin*, not against a
    fixed 100 x 71.75. Against the fixed pair, --margin 0 would scale A7 up by
    3.5 % and --margin 10 down by 5 %, changing output nobody asked to change.
    """
    assert build_pdf.card_scale((2, 4), margin) == 1.0


def test_the_denser_grid_is_never_scaled_up():
    for margin in (0.0, 5.0, 10.0):
        assert build_pdf.card_scale((4, 4), margin) < 1.0


# --- the print order (feat/simplex-print-order) ----------------------------


def test_the_two_print_orders_are_named_and_duplex_is_the_default():
    """FR-001. The default is a value, not the absence of one."""
    assert build_pdf.SIDES == ("duplex", "simplex")
    assert build_pdf.DEFAULT_SIDES == "duplex"


def test_the_engine_is_told_the_print_order():
    """The compile and the overflow query must see the same page order.

    engine_inputs() exists because the two used to build their arguments
    separately; `sides` joins the list under the same rule rather than being
    passed at one call site.
    """
    grid = build_pdf.DEFAULT_GRID
    for sides in build_pdf.SIDES:
        pairs = build_pdf.engine_inputs(5.0, True, grid, sides)
        assert f"sides={sides}" in pairs, pairs
        assert pairs[pairs.index(f"sides={sides}") - 1] == "--input"


def test_the_duplex_note_is_the_sentence_it_has_always_been():
    """Five end-to-end assertions read this string. It does not get to move."""
    assert build_pdf.print_order_note(8, "duplex") == "duplex, flip on long edge"


def test_the_simplex_note_names_both_page_ranges():
    """FR-006/SC-004: the two print jobs, and the scale that ruins them."""
    note = build_pdf.print_order_note(8, "simplex")
    assert note.startswith("simplex:")
    assert "pages 1-4" in note and "pages 5-8" in note, note
    assert "100 %" in note and "long edge" in note, note


def test_a_one_page_range_is_written_as_one_page():
    """'pages 1-1' reads like a bug, and a single sheet is the first thing
    anyone tries the flag on."""
    note = build_pdf.print_order_note(2, "simplex")
    assert "page 1" in note and "page 2" in note, note
    assert "1-1" not in note and "2-2" not in note, note


# --- the five operations that used to move an id (SC-002) --------------------
#
# Each of these silently renamed cards under the old scheme. Together they are
# the reason the feature exists: an id quoted in a conversation has to still
# name the same card after the conversation causes an edit.

PARTIAL = Path(__file__).resolve().parent / "fixtures" / "demo-project" / "partial"


def _ids_by_front(cards):
    return {c["front"]: c["id"] for c in cards}


def test_a_deck_part_way_through_migration_still_builds(tmp_path):
    """Some cards with ids, some without — the state a real project sits in."""
    cards, errors, _ = build_pdf.load_cards([str(PARTIAL / "partial-ids.yaml")], [], [])
    assert errors == []
    assert len(cards) == 4
    assert [c["id"] for c in cards] == ["7QH3W", "", "MJ0K8", ""]
    assert all(c["ref"] for c in cards), "every card still needs a diagnostic label"


def test_deleting_a_card_before_another_does_not_move_its_id(tmp_path):
    shortened = WITH_IDS.replace(
        "  - id: A45DK\n    subtopic: 'Bayes'\n    front: 'First'\n    back: 'a'\n", "", 1
    )
    full, _, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", WITH_IDS)], [], [])
    fewer, _, _ = build_pdf.load_cards([write(tmp_path, "b.yaml", shortened)], [], [])
    assert _ids_by_front(fewer)["Second"] == _ids_by_front(full)["Second"] == "QT8M2"


def test_editing_a_card_does_not_change_its_id(tmp_path):
    """The case that rules out deriving the id from the card's content.

    Editing is exactly the moment a conversation about a card leads to — so an
    id that changed here would break at the one point it is most needed.
    """
    edited = WITH_IDS.replace("front: 'First'", "front: 'First, corrected'").replace(
        "back: 'a'", "back: 'a much better answer'"
    )
    before, _, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", WITH_IDS)], [], [])
    after, _, _ = build_pdf.load_cards([write(tmp_path, "b.yaml", edited)], [], [])
    assert after[0]["id"] == before[0]["id"] == "A45DK"
    assert after[0]["front"] != before[0]["front"], "the edit has to have happened"


def test_reordering_the_cards_does_not_change_any_id(tmp_path):
    lines = WITH_IDS.strip().splitlines()
    head, first, second = lines[:2], lines[2:6], lines[6:]
    reordered = "\n".join(head + second + first) + "\n"
    before, _, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", WITH_IDS)], [], [])
    after, _, _ = build_pdf.load_cards([write(tmp_path, "b.yaml", reordered)], [], [])
    assert _ids_by_front(after) == _ids_by_front(before)


def test_the_five_operations_together_leave_every_id_where_it_was(tmp_path):
    """SC-002 as one assertion, so a regression in any of the five shows here."""
    grown = WITH_IDS.replace(
        "cards:\n",
        "cards:\n  - id: V9WXY\n    subtopic: 'New'\n    front: 'Inserted'\n    back: 'x'\n",
        1,
    ).replace("front: 'Second'", "front: 'Second, edited'")
    original, _, _ = build_pdf.load_cards([write(tmp_path, "topic-a.yaml", WITH_IDS)], [], [])
    path = write(tmp_path, "renamed.yaml", grown)
    changed, _, _ = build_pdf.load_cards([path], [], [])
    filtered, _, _ = build_pdf.load_cards([path], [], ["Bayes"])

    assert _ids_by_front(changed)["First"] == original[0]["id"]
    assert _ids_by_front(changed)["Second, edited"] == original[1]["id"]
    assert {c["id"] for c in filtered} <= {c["id"] for c in changed}


# --- the footer when a card has no id (FR-005) -------------------------------


def test_the_payload_carries_the_empty_id_rather_than_dropping_the_key(tmp_path):
    """card.typ reads `card.id` unconditionally, so the key must always be there."""
    cards, _, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", MINIMAL)], [], [])
    payload = json.loads(json.dumps(cards))  # the shape that reaches the template
    assert "id" in payload[0] and payload[0]["id"] == ""
    assert "ref" in payload[0] and payload[0]["ref"]


# --- id validation on the `lernkarten check` path ----------------------------
#
# `bin/lernkarten check` dispatches to build_pdf with --check; it never calls
# check_project.py. Validation added only there would leave `lernkarten check`
# reporting OK on a deck with two cards sharing an id — which is exactly what
# SC-004 says must not happen. So the rules live in load_cards' errors channel,
# the same one the schema errors already use.

BROKEN = Path(__file__).resolve().parent / "fixtures" / "demo-project" / "broken"


def test_load_cards_reports_a_duplicate_id_naming_both_cards():
    _, errors, _ = build_pdf.load_cards([str(BROKEN / "duplicate-id.yaml")], [], [])
    assert errors, "a duplicate id has to reach the check path, not only check_project"
    assert any("A45DK" in e and "card 1" in e and "card 2" in e for e in errors), errors


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("bad-alphabet-id.yaml", "I"),
        ("wrong-length-id.yaml", "4"),
        ("non-string-id.yaml", "int"),
    ],
)
def test_load_cards_reports_an_unusable_id(fixture, expected):
    _, errors, _ = build_pdf.load_cards([str(BROKEN / fixture)], [], [])
    assert any(expected in e for e in errors), f"{fixture}: {errors}"


def test_a_duplicate_across_two_files_is_still_a_duplicate(tmp_path):
    """Ids are unique per project, so the check cannot be per file."""
    a = write(tmp_path, "a.yaml", WITH_IDS)
    b = write(tmp_path, "b.yaml", WITH_IDS)
    _, errors, _ = build_pdf.load_cards([a, b], [], [])
    assert any("A45DK" in e for e in errors), errors


def test_a_deck_with_no_ids_produces_no_errors(tmp_path):
    """US2: absent is not an error, however many cards are missing one."""
    _, errors, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", MINIMAL)], [], [])
    assert errors == []


def test_a_deck_with_no_ids_is_advised_once_not_once_per_card(tmp_path, capsys):
    """US2 scenario 2: exit 0, and one line for the run — not one per card.

    A per-card advisory on a 300-card deck would bury the output it is printed
    alongside, which is how a helpful nudge becomes noise people learn to skip.
    """
    body = "".join(
        f"  - subtopic: 'Bayes'\n    front: 'Q{n}'\n    back: 'A{n}'\n" for n in range(5)
    )
    many = "topic: 'Statistics'\ncards:\n" + body
    cards, errors, _ = build_pdf.load_cards([write(tmp_path, "a.yaml", many)], [], [])
    assert errors == [], "a missing id is never an error"
    assert len(cards) == 5

    build_pdf.advise_about_ids(cards)
    lines = [ln for ln in capsys.readouterr().err.splitlines() if ln.strip()]
    assert len(lines) == 1, f"one advisory per run, got {len(lines)}: {lines}"
    assert "backfill" in lines[0], lines[0]


def test_no_advisory_when_every_card_has_an_id(tmp_path, capsys):
    cards, _, _ = build_pdf.load_cards([write(tmp_path, "deck.yaml", WITH_IDS)], [], [])
    build_pdf.advise_about_ids(cards)
    assert capsys.readouterr().err == ""


def test_a_filtered_build_still_validates_the_cards_it_filters_out(tmp_path):
    """A duplicate id is a fact about the file, not about the slice printed.

    The validation used to sit inside the per-card loop, after the subtopic
    filter, so `--subtopic` quietly skipped the cards it excluded — and the
    duplicate they collided with went unreported.
    """
    deck = WITH_IDS.replace("id: QT8M2", "id: A45DK").replace(
        "subtopic: 'Bayes'\n    front: 'Second'", "subtopic: 'Markov'\n    front: 'Second'"
    )
    path = write(tmp_path, "deck.yaml", deck)

    _, unfiltered, _ = build_pdf.load_cards([path], [], [])
    _, filtered, _ = build_pdf.load_cards([path], [], ["Bayes"])
    assert any("A45DK" in e for e in unfiltered), unfiltered
    assert any("A45DK" in e for e in filtered), (
        f"the duplicate is outside the filter but still in the file: {filtered}"
    )
