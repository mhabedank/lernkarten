#!/usr/bin/env python3
"""Card ids: a short, stable handle for one card.

A card id is five characters of Crockford Base32 — `0-9A-Z` without `I`, `L`,
`O` or `U`, the pairs people get wrong reading a printed card and typing it
into a chat. It is stored in the card file as a per-card `id:` key, assigned
once, and never changed by editing, moving or renaming the card. The one
exception is a collision between decks that were assigned independently, which
the writing path resolves and reports.

**Why this is not in `yamlio.py`.** That module is deliberately a thin reader
for the YAML this project owns, and it is a leaf that `build_pdf`,
`check_project` and `check_docs` all import. Card ids are domain knowledge — an
alphabet, a generator, a collision policy — and putting them in the format
reader would widen a leaf that everything depends on. `cardid` is a leaf of its
own: it imports `yamlio` and the standard library, and nothing else.

Everything here works with no typesetting engine, no network and no state
outside the card files themselves.
"""

import secrets  # noqa: F401  - the generator uses it once implemented

import yamlio  # noqa: F401  - compose() for the splice, once implemented

# The 32 symbols, in Crockford's order. `I`, `L`, `O` and `U` are absent.
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# How many characters an id has. Fixed project-wide and not configurable.
LENGTH = 5

# Crockford's decoding rules: reading is case-insensitive, and the three
# characters left out of the alphabet because they look like digits map back to
# the digit they were mistaken for. `U` is not here — it has no numeric twin and
# was excluded so an id cannot spell something unfortunate on a printed card.
FOLD = {"I": "1", "L": "1", "O": "0"}

# How many times to redraw before giving up. Generous enough that a real
# project never reaches it — at five characters the space is 33.5 million — and
# finite so that an exhausted space is an error with a sentence rather than a
# command that hangs.
DRAW_LIMIT = 1000


class CardIdError(ValueError):
    """An id that cannot be used, or a file that cannot be spliced safely."""


def generate(taken):
    """A fresh id not present in `taken`.

    Draws from `secrets` rather than `random`: the ids end up printed on paper
    and quoted in conversation, and a predictable sequence would make two
    projects started the same way collide far more often than the arithmetic
    suggests.
    """
    for _ in range(DRAW_LIMIT):
        candidate = "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))
        if candidate not in taken:
            return candidate
    raise CardIdError(
        f"could not find a free id in {DRAW_LIMIT} attempts with {len(taken)} already in use "
        f"— the {len(ALPHABET)}**{LENGTH} id space is effectively full"
    )


def normalise(text):
    """An id folded to its canonical form for comparison.

    What a person types is not always what is printed: `O` for `0`, `l` for
    `1`, lower case for upper. Folding here means the id they read off the card
    resolves to the card they meant.
    """
    if not isinstance(text, str):
        return text
    return "".join(FOLD.get(c, c) for c in text.upper())


def validate(text):
    """None if `text` is a usable id, else a phrase saying what is wrong.

    The phrase is the whole point: a message that says only "invalid id" sends
    the reader back to the file to work out which rule they broke.
    """
    if not isinstance(text, str):
        return f"expected a string, found {type(text).__name__}"
    if len(text) != LENGTH:
        return f"expected {LENGTH} characters, found {len(text)}"
    outside = [c for c in text.upper() if c not in ALPHABET]
    if outside:
        return f"{outside[0]!r} is not in the alphabet (Crockford Base32 leaves out I, L, O and U)"
    return None


def cards_in(src):
    """Where each card sits in `src`, from the parser's own marks.

    The positions come from PyYAML, never from scanning the text ourselves.
    That is the whole reason this can add a key without reformatting the file:
    the parser already knows where every card starts, so the edit is a splice
    at a known offset rather than a re-serialisation.

    Each entry is (line, column, has_id) for the card's *first key*, 0-based.
    """
    node = yamlio.compose(src)
    if node is None or not hasattr(node, "value"):
        return []
    cards = None
    for key, value in node.value:
        if getattr(key, "value", None) == "cards":
            cards = value
    if cards is None or not getattr(cards, "value", None):
        return []

    seen = set()
    found = []
    for item in cards.value:
        pairs = getattr(item, "value", None)
        if not pairs:
            continue
        # An alias reuses one node, so two cards share a single set of marks and
        # the splice would write twice at the same offset.
        if id(item) in seen:
            raise CardIdError(
                "this deck uses a YAML alias to repeat a card, so two cards share "
                "one position in the file and an id cannot be written to each. "
                "Write the cards out separately, then add ids."
            )
        seen.add(id(item))
        # A flow-style card is one line inside braces; there is no place to put a
        # key on its own line without rewriting the card.
        if getattr(item, "flow_style", False):
            raise CardIdError(
                "this deck writes a card in flow style ({...}) on one line, which "
                "leaves nowhere to insert an id without reformatting the card. "
                "Write it as an indented block, then add ids."
            )
        first_key = pairs[0][0]
        has_id = any(getattr(k, "value", None) == "id" for k, _ in pairs)
        found.append((first_key.start_mark.line, first_key.start_mark.column, has_id))
    return found


def _newline_of(line):
    """The line ending `line` uses, so a CRLF file stays a CRLF file."""
    if line.endswith("\r\n"):
        return "\r\n"
    return "\n" if line.endswith("\n") else ""


def insert_ids(src, gen):
    """`src` with an `id:` first key spliced into every card that lacks one.

    `gen` is called once per card that needs an id. Writing the key first means
    the `- ` sequence dash moves onto the new line — the one byte outside the
    inserted key that changes, and the reason preservation is specified as a
    round-trip rather than as "nothing else moves".
    """
    positions = cards_in(src)
    if not positions:
        return src
    lines = src.splitlines(keepends=True)
    for line_no, column, has_id in reversed(positions):
        if has_id:
            continue
        line = lines[line_no]
        newline = _newline_of(line)
        lines[line_no] = f"{line[:column]}id: {gen()}{newline}" + " " * column + line[column:]
    return "".join(lines)


def remove_ids(src):
    """The exact inverse of `insert_ids`.

    Public because the guarantee worth asserting is
    `remove_ids(insert_ids(src)) == src`, and a test cannot assert that against
    a private helper. Only the shape `insert_ids` produces is undone — an `id`
    a user wrote somewhere else in the card is left alone.
    """
    positions = cards_in(src)
    if not positions:
        return src
    lines = src.splitlines(keepends=True)
    for line_no, column, has_id in reversed(positions):
        if not has_id or line_no + 1 >= len(lines):
            continue
        prefix = lines[line_no][:column]
        following = lines[line_no + 1]
        if following[:column].strip():
            continue  # the next line is not this card's second key
        if prefix.strip() == "-":
            # `- id: X` / `  subtopic: …` — put the dash back on the next line.
            lines[line_no : line_no + 2] = [prefix + following[column:]]
        elif not prefix.strip():
            # The card's dash is on a line of its own, so the id line is plain
            # indented text and deleting it is the whole inverse.
            del lines[line_no]
        # anything else is an id the user placed themselves; leave it alone
    return "".join(lines)


def backfill(paths):
    """Assign ids across `paths`, all of them or none."""
    return []


def reassign(paths):
    """Resolve duplicate ids across `paths`, first occurrence winning."""
    return []


def main():
    """The `lernkarten id` subcommand."""
    return 0


if __name__ == "__main__":
    main()
