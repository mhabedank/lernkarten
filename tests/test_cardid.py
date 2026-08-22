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
