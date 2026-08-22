"""Card ids: the alphabet, the generator, and the splice that writes them.

A card id is the handle a person reads off a printed card and types into a
chat. Everything here is about it staying the same card afterwards.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import cardid  # noqa: E402

# --- the alphabet ------------------------------------------------------------


def test_alphabet_is_crockford_base32():
    assert cardid.ALPHABET == "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    assert len(cardid.ALPHABET) == 32


def test_alphabet_omits_the_characters_people_misread():
    """`I`/`1`, `L`/`1`, `O`/`0` are the pairs a printed card gets wrong.

    `U` is absent for a different reason: it keeps an id from spelling
    something unfortunate on a learning card.
    """
    for c in "ILOU":
        assert c not in cardid.ALPHABET, f"{c} should not be in the alphabet"


# --- validate ----------------------------------------------------------------


def test_validate_accepts_a_well_formed_id():
    assert cardid.validate("A45DK") is None


@pytest.mark.parametrize("bad", ["A45D", "A45DKM", ""])
def test_validate_names_the_length_it_found(bad):
    message = cardid.validate(bad)
    assert message is not None, f"{bad!r} is not 5 characters"
    assert str(len(bad)) in message, f"the message should say how long it was: {message}"


@pytest.mark.parametrize(
    ("bad", "offender"),
    [("A45DI", "I"), ("A45DL", "L"), ("A45DO", "O"), ("A45DU", "U"), ("A4-DK", "-")],
)
def test_validate_names_the_offending_character(bad, offender):
    """Named explicitly, not inferred as the last character.

    `A4-DK` is the case that matters: the offender is in the middle, so a test
    that assumed `bad[-1]` would demand the wrong character and pass only by
    accident on the others.
    """
    message = cardid.validate(bad)
    assert message is not None, f"{bad!r} is outside the alphabet"
    assert offender in message, f"the message should name {offender!r}: {message}"


@pytest.mark.parametrize("bad", [None, 12345, ["A45DK"], {}])
def test_validate_names_the_type_when_it_is_not_a_string(bad):
    message = cardid.validate(bad)
    assert message is not None, f"{bad!r} is not a string"
    assert type(bad).__name__ in message, f"the message should name the type: {message}"


# --- normalise ---------------------------------------------------------------


def test_normalise_upper_cases():
    assert cardid.normalise("a45dk") == "A45DK"


@pytest.mark.parametrize(
    ("typed", "meant"),
    [("A45DO", "A45D0"), ("A45DI", "A45D1"), ("A45DL", "A45D1"), ("a45do", "A45D0")],
)
def test_normalise_folds_the_confusable_characters(typed, meant):
    """Someone reading `0` as `O` off a card must still resolve the card."""
    assert cardid.normalise(typed) == meant


def test_normalise_leaves_u_alone():
    """`U` has no numeric twin — it is excluded, not folded."""
    assert cardid.normalise("A45DU") == "A45DU"


# --- generate ----------------------------------------------------------------


def test_generate_produces_ids_of_the_right_shape_and_never_repeats():
    """Ten thousand draws, enough to force redraws against a growing set."""
    taken = set()
    for _ in range(10_000):
        new = cardid.generate(taken)
        assert cardid.validate(new) is None, f"generated an invalid id: {new!r}"
        assert new not in taken, f"generated a duplicate: {new!r}"
        taken.add(new)
    assert len(taken) == 10_000


def test_generate_avoids_ids_already_taken():
    taken = {"A45DK", "QT8M2"}
    for _ in range(200):
        assert cardid.generate(taken) not in taken


# --- the redraw has to stop (FR-003b) ----------------------------------------


def test_generate_gives_up_rather_than_spinning_forever(monkeypatch):
    """Exhaustion has to surface as an error, not as a hang.

    At five characters this is unreachable in practice — 33.5 million ids
    against a few hundred cards. It is specified anyway because the failure it
    replaces is the worst kind: a command that never returns and never says why.

    Shrinking the alphabet to two symbols makes the whole space 2**5 = 32 ids,
    so handing over all 32 genuinely exhausts it.
    """
    monkeypatch.setattr(cardid, "ALPHABET", "01")
    everything = {f"{n:05b}" for n in range(32)}
    assert len(everything) == 32

    with pytest.raises(cardid.CardIdError) as e:
        cardid.generate(everything)

    message = str(e.value)
    assert "32" in message, f"the error should say how many ids are in use: {message}"
    assert "attempt" in message.lower(), f"the error should name the bound it hit: {message}"


# --- the splice: adding a key without rewriting the file ---------------------
#
# The inputs below are string constants ON PURPOSE. They must NOT be read from
# cards/example.yaml or tests/fixtures/demo-project/cards/, because those files
# gain ids later in this feature — after which insert_ids would insert nothing,
# and `remove_ids(insert_ids(src)) == src` would quietly reduce to `src == src`
# and pass forever while testing nothing. This is the feature's central
# byte-fidelity guarantee; its input has to be one no later change can neuter.

DECK_LF = """# A deck with comments, quoting and non-ASCII text.
topic: 'Gezeiten'          # the comment must survive
language: german
grid: a7
cards:
  - subtopic: 'Grundlagen'
    front: 'Was heißt halbtägig?'
    back: 'Zwei Hoch\\ und zwei Niedrigwasser.'   # a line break, then a comment
    source: 'Feldnotizen 2'
  - subtopic: 'Größen'
    front: 'Wie ist der Tidenhub $R$ definiert?'
    back: 'Höhe des Hochwassers minus Höhe des Niedrigwassers.'
"""

DECK_CRLF = DECK_LF.replace("\n", "\r\n")

DECK_WITH_ONE_ID = """topic: 'Mixed'
cards:
  - id: A45DK
    subtopic: 'Kept'
    front: 'a'
    back: 'b'
  - subtopic: 'Needs one'
    front: 'c'
    back: 'd'
"""


def _counter():
    """Deterministic ids, so a failure shows a diff rather than noise."""
    seq = iter(["QT8M2", "V9WXY", "3KP7R", "ZB6NS", "H2J4T"])
    return lambda: next(seq)


def test_insert_ids_actually_inserts_them():
    """Guards the round-trip below: if nothing is inserted it proves nothing."""
    out = cardid.insert_ids(DECK_LF, _counter())
    assert out != DECK_LF, "insert_ids returned the input unchanged"
    assert "id: QT8M2" in out
    assert "id: V9WXY" in out


@pytest.mark.parametrize(("name", "src"), [("LF", DECK_LF), ("CRLF", DECK_CRLF)])
def test_round_trip_is_byte_exact(name, src):
    """`remove_ids(insert_ids(src))` must give back every byte of `src`.

    Stated as a round-trip rather than "nothing outside the key changes",
    because writing `id` as the first key necessarily moves the `- ` sequence
    dash onto the new line. Stripping the id line alone would leave invalid
    YAML, which is what shows the movement to be structural, not cosmetic.
    """
    assert cardid.remove_ids(cardid.insert_ids(src, _counter())) == src


def test_the_comments_and_the_card_text_survive():
    out = cardid.insert_ids(DECK_LF, _counter())
    assert "# the comment must survive" in out
    assert "'Was heißt halbtägig?'" in out
    assert "'Zwei Hoch\\ und zwei Niedrigwasser.'" in out
    assert out.count("#") == DECK_LF.count("#")


def test_line_endings_are_preserved():
    out = cardid.insert_ids(DECK_CRLF, _counter())
    assert "\r\n" in out
    assert out.replace("\r\n", "").count("\n") == 0, "a bare LF leaked into a CRLF file"


def test_insert_ids_is_idempotent():
    once = cardid.insert_ids(DECK_LF, _counter())
    twice = cardid.insert_ids(once, _counter())
    assert twice == once


def test_an_existing_id_is_left_byte_identical():
    out = cardid.insert_ids(DECK_WITH_ONE_ID, _counter())
    assert "id: A45DK" in out, "the pre-existing id was altered"
    assert out.count("id:") == 2, "the second card should have gained exactly one id"


def test_the_spliced_file_still_parses_to_the_same_cards():
    import yamlio

    before = yamlio.load(DECK_LF)["cards"]
    after = yamlio.load(cardid.insert_ids(DECK_LF, _counter()))["cards"]
    assert len(before) == len(after)
    for b, a in zip(before, after, strict=True):
        assert {k: v for k, v in a.items() if k != "id"} == b


# --- shapes the splice must refuse rather than corrupt -----------------------
#
# Found by the pre-implementation cross-model review and reproduced here. Both
# are legal YAML that a user could plausibly write, and in both the splice's
# assumption — "the first key's mark sits just after a `- ` prefix" — is false.
# Refusing is the honest answer: this feature adds a key, it does not reformat
# anyone's file, and a corrupted deck is far worse than an unhandled one.

FLOW_STYLE = """topic: 'Flow'
cards:
  - {subtopic: 'a', front: 'b', back: 'c'}
"""

ALIASED = """defaults: &card
  subtopic: 'Shared'
  front: 'a'
  back: 'b'
cards:
  - *card
  - *card
"""


@pytest.mark.parametrize(
    ("src", "expected"),
    [(FLOW_STYLE, "flow style"), (ALIASED, "alias")],
    ids=["flow-style", "aliased"],
)
def test_insert_ids_refuses_a_shape_it_cannot_splice(src, expected):
    """The message has to name the shape and say what to do about it.

    The expected wording is stated here rather than derived from the test id —
    deriving it once demanded "aliased" from a message that correctly says
    "alias", which is the test being clever rather than the code being wrong.
    """
    with pytest.raises(cardid.CardIdError) as e:
        cardid.insert_ids(src, _counter())
    message = str(e.value).lower()
    assert expected in message, f"the error should name the shape: {message}"
    assert "then add ids" in message, f"the error should say how to proceed: {message}"


def test_block_scalars_and_quoted_keys_are_accepted():
    """The review also flagged these; they were probed and are safe.

    Kept as a test so the guard stays narrow — refusing more than necessary
    would turn a safety check into a usability problem.
    """
    ok = """topic: 'Fine'
cards:
  - 'subtopic': 'quoted key'
    front: |
      a block scalar
      over two lines
    back: 'b'
  -
    subtopic: 'dash on its own line'
    front: 'c'
    back: 'd'
"""
    out = cardid.insert_ids(ok, _counter())
    assert out.count("id:") == 2
    assert cardid.remove_ids(out) == ok


# --- backfill and reassign: the writing path ---------------------------------

DECK_A = """topic: 'Deck A'
cards:
  - id: A45DK
    subtopic: 'One'
    front: 'a'
    back: 'b'
"""

DECK_B = """topic: 'Deck B'
cards:
  - id: A45DK
    subtopic: 'One'
    front: 'c'
    back: 'd'
"""

PLAIN = """topic: 'Plain'
cards:
  - subtopic: 'One'
    front: 'a'
    back: 'b'
  - subtopic: 'Two'
    front: 'c'
    back: 'd'
"""


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_backfill_gives_every_card_an_id(tmp_path):
    path = _write(tmp_path, "plain.yaml", PLAIN)
    cardid.backfill([path])
    written = path.read_text(encoding="utf-8")
    assert written.count("- id: ") == 2
    assert cardid.remove_ids(written) == PLAIN


def test_backfill_is_idempotent(tmp_path):
    path = _write(tmp_path, "plain.yaml", PLAIN)
    cardid.backfill([path])
    once = path.read_text(encoding="utf-8")
    cardid.backfill([path])
    assert path.read_text(encoding="utf-8") == once


def test_backfill_leaves_an_existing_id_alone(tmp_path):
    path = _write(tmp_path, "mixed.yaml", DECK_WITH_ONE_ID)
    cardid.backfill([path])
    written = path.read_text(encoding="utf-8")
    assert "id: A45DK" in written
    assert written.count("- id: ") == 2


def test_backfill_never_repeats_an_id_across_files(tmp_path):
    a = _write(tmp_path, "a.yaml", PLAIN)
    b = _write(tmp_path, "b.yaml", PLAIN)
    cardid.backfill([a, b])
    import re as _re

    ids = _re.findall(r"- id: (\S+)", a.read_text() + b.read_text())
    assert len(ids) == 4 and len(set(ids)) == 4, ids


def test_backfill_writes_nothing_at_all_when_one_file_is_unusable(tmp_path):
    """FR-007: all of them or none — never a half-migrated project."""
    good = _write(tmp_path, "good.yaml", PLAIN)
    bad = _write(tmp_path, "bad.yaml", "topic: 'unclosed\ncards:\n")
    before = good.read_text(encoding="utf-8")

    with pytest.raises(cardid.CardIdError) as e:
        cardid.backfill([good, bad])

    assert "bad.yaml" in str(e.value), f"the message has to name the file: {e.value}"
    assert good.read_text(encoding="utf-8") == before, "a healthy file was written anyway"


def test_backfill_needs_no_engine_and_no_network(tmp_path, monkeypatch):
    """FR-012: this is the first thing a user runs on a fresh checkout."""
    import socket

    monkeypatch.setattr(socket, "socket", _forbidden("network"))
    path = _write(tmp_path, "plain.yaml", PLAIN)
    cardid.backfill([path])
    assert path.read_text(encoding="utf-8").count("- id: ") == 2


def _forbidden(what):
    def boom(*_a, **_k):
        raise AssertionError(f"{what} must not be needed here")

    return boom


def test_reassign_keeps_the_first_and_moves_the_later_one(tmp_path):
    """FR-013b: first occurrence wins, by the order given on the command line."""
    a = _write(tmp_path, "a.yaml", DECK_A)
    b = _write(tmp_path, "b.yaml", DECK_B)
    changes = cardid.reassign([a, b])

    assert "id: A45DK" in a.read_text(encoding="utf-8"), "the first file keeps its id"
    assert "id: A45DK" not in b.read_text(encoding="utf-8"), "the later one had to move"
    assert len(changes) == 1
    assert changes[0]["old"] == "A45DK" and changes[0]["new"] != "A45DK"


def test_swapping_the_arguments_reassigns_the_other_card(tmp_path):
    """SC-008: this is what makes 'the user steers it' true rather than said."""
    a = _write(tmp_path, "a.yaml", DECK_A)
    b = _write(tmp_path, "b.yaml", DECK_B)
    cardid.reassign([b, a])
    assert "id: A45DK" in b.read_text(encoding="utf-8")
    assert "id: A45DK" not in a.read_text(encoding="utf-8")


def test_reassign_leaves_one_pass_with_no_duplicates(tmp_path):
    """FR-013d: a replacement that itself clashes has to be redrawn."""
    import re as _re

    files = [_write(tmp_path, f"{n}.yaml", DECK_A) for n in "abcd"]
    cardid.reassign(files)
    ids = _re.findall(r"- id: (\S+)", "".join(f.read_text() for f in files))
    assert len(ids) == 4, ids
    assert len(set(ids)) == 4, f"one pass left duplicates behind: {ids}"


def test_reassign_does_nothing_when_there_is_nothing_to_resolve(tmp_path):
    a = _write(tmp_path, "a.yaml", DECK_A)
    before = a.read_text(encoding="utf-8")
    assert cardid.reassign([a]) == []
    assert a.read_text(encoding="utf-8") == before


def test_reassign_targets_the_right_card_in_a_mixed_deck(tmp_path):
    """The index a duplicate is found at is not the card's position.

    `ids_in` skips cards that have no id, so in a deck whose first card is
    id-less the second card's id comes back at index 1 — and rewriting "card 1"
    would edit the wrong card, or silently edit nothing.
    """
    first = _write(tmp_path, "first.yaml", DECK_A)  # one card, id A45DK
    mixed = _write(
        tmp_path,
        "mixed.yaml",
        """topic: 'Mixed'
cards:
  - subtopic: 'No id here'
    front: 'x'
    back: 'y'
  - id: A45DK
    subtopic: 'Collides'
    front: 'z'
    back: 'w'
""",
    )
    cardid.reassign([first, mixed])

    assert "id: A45DK" in first.read_text(encoding="utf-8"), "the first file keeps its id"
    after = mixed.read_text(encoding="utf-8")
    assert "id: A45DK" not in after, f"the duplicate was not reassigned: {after}"
    assert after.count("- id: ") == 1, f"an id was added to the id-less card: {after}"
    assert "front: 'x'" in after and "front: 'z'" in after, "the cards themselves changed"


# --- an id the user did not put first ----------------------------------------
#
# The contract says the reader must accept `id` anywhere in the card; writing it
# first is only what /cards and backfill do. So remove_ids has to leave such a
# card alone — it undoes the shape insert_ids writes and nothing else.

ID_LAST = """cards:
  - front: 'a'
    back: 'b'
    id: A45DK
"""

ID_MIDDLE = """cards:
  - front: 'a'
    id: A45DK
    back: 'b'
"""


@pytest.mark.parametrize("src", [ID_LAST, ID_MIDDLE], ids=["id-last", "id-in-the-middle"])
def test_remove_ids_leaves_an_id_the_user_placed_alone(src):
    """It used to merge the card's real first key away — silent data loss.

    `cards_in` reports has_id for *any* key called id, but pairs it with the
    *first* key's position. Treating the two as the same thing deleted the
    `front:` line of a card whose id happened to sit lower down.
    """
    assert cardid.remove_ids(src) == src


@pytest.mark.parametrize("src", [ID_LAST, ID_MIDDLE], ids=["id-last", "id-in-the-middle"])
def test_insert_ids_does_not_add_a_second_id_to_such_a_card(src):
    assert cardid.insert_ids(src, _counter()) == src


@pytest.mark.parametrize("src", [ID_LAST, ID_MIDDLE], ids=["id-last", "id-in-the-middle"])
def test_the_round_trip_still_holds_for_such_a_card(src):
    assert cardid.remove_ids(cardid.insert_ids(src, _counter())) == src
