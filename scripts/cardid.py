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

import argparse
import secrets
import sys
from pathlib import Path

import yamlio

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


def _read_all(paths):
    """Every file's text, or one error naming the first file that failed.

    Reading everything before writing anything is what makes the whole run
    all-or-nothing: a project half-migrated because the fourth file was
    unreadable is worse than one not migrated at all.
    """
    texts = {}
    for path in paths:
        path = Path(path)
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except OSError as e:
            raise CardIdError(f"{path}: cannot be read — {e}") from e
        try:
            cards_in(texts[path])  # parses, and rejects a shape we cannot splice
        except yamlio.YamlError as e:
            raise CardIdError(f"{path}: {e}") from e
        except CardIdError as e:
            raise CardIdError(f"{path}: {e}") from e
    return texts


def ids_in(src):
    """Every id declared in `src`, as (card position, id), in file order.

    The position is the card's own, counting from one — not its position among
    the cards that happen to have an id. In a deck whose first card is id-less
    the two differ, and rewriting by the wrong one edits the wrong card.
    """
    data = yamlio.load(src)
    if not isinstance(data, dict):
        return []
    found = []
    for position, card in enumerate(data.get("cards") or [], start=1):
        if isinstance(card, dict) and isinstance(card.get("id"), str):
            found.append((position, card["id"]))
    return found


def backfill(paths):
    """Assign ids across `paths`, all of them or none.

    Returns the paths that changed. Needs no engine and no network: this is
    the first thing a user runs on a fresh checkout, before anything has been
    downloaded.
    """
    texts = _read_all(paths)
    taken = {normalise(i) for src in texts.values() for _, i in ids_in(src)}

    def fresh():
        new = generate(taken)
        taken.add(normalise(new))
        return new

    written = []
    for path, src in texts.items():
        out = insert_ids(src, fresh)
        if out != src:
            path.write_text(out, encoding="utf-8")
            written.append(path)
    return written


def reassign(paths):
    """Resolve duplicate ids across `paths`, first occurrence winning.

    Files are considered in the order given, cards in file order, and the first
    card seen carrying an id keeps it. That is the only rule the user can
    steer: argument order is theirs, so putting the deck whose ids they quote
    first preserves those ids.

    Returns one record per reassignment, for a report that has to say what it
    cost as well as what it changed.
    """
    texts = _read_all(paths)
    seen = {}
    taken = {normalise(i) for src in texts.values() for _, i in ids_in(src)}
    changes = []

    for path, src in texts.items():
        out = src
        for index, old in ids_in(src):
            key = normalise(old)
            if key not in seen:
                seen[key] = (path, index)
                continue
            # A replacement is drawn against every id in the combined set, so
            # resolving one duplicate cannot create another (FR-013d).
            new = generate(taken)
            taken.add(normalise(new))
            seen[normalise(new)] = (path, index)
            out = _replace_id(out, index, new)
            changes.append({"file": path, "card": index, "old": old, "new": new})
        if out != src:
            path.write_text(out, encoding="utf-8")
    return changes


def _replace_id(src, index, new):
    """Rewrite the id of the `index`-th card, leaving every other byte alone."""
    lines = src.splitlines(keepends=True)
    for position, (line_no, column, has_id) in enumerate(cards_in(src), start=1):
        if position != index or not has_id:
            continue
        line = lines[line_no]
        head = line[:column]
        rest = line[column:]
        value = rest.split(":", 1)[1]
        keep = len(value) - len(value.lstrip())
        newline = _newline_of(line)
        lines[line_no] = f"{head}id:{value[:keep]}{new}{newline}"
        break
    return "".join(lines)


def report_reassignments(changes, out=sys.stderr):
    """Say what changed, and what it cost.

    The cost is the point: a reassigned id stops resolving in the conversation
    that quoted it, and orphans any revision history recorded against it. A
    report that listed only the substitution would hide the one thing the user
    needs to know.
    """
    if not changes:
        return
    for change in changes:
        print(
            f"REASSIGNED: {change['file']} card {change['card']}: "
            f"{change['old']} -> {change['new']}",
            file=out,
        )
    print(
        f"  {len(changes)} id(s) changed. The old ids no longer name these cards: "
        "a past conversation quoting one now points at nothing, and any revision "
        "history kept against it is orphaned.",
        file=out,
    )


def main():
    """The `lernkarten id` subcommand.

    One of the two flags is required. Neither backfilling nor reassigning is
    what should happen when someone types the command with no flag and hits
    return — reassignment in particular changes an id a user may have quoted
    somewhere this tool cannot see.
    """
    parser = argparse.ArgumentParser(
        prog="lernkarten id",
        description="Give cards a short, stable id, or resolve ids that collide.",
    )
    what = parser.add_mutually_exclusive_group(required=True)
    what.add_argument(
        "--backfill",
        action="store_true",
        help="give every card that has no id one, leaving existing ids alone",
    )
    what.add_argument(
        "--reassign",
        action="store_true",
        help="resolve duplicate ids; the first file on the command line keeps its own",
    )
    parser.add_argument("files", nargs="+", help="card files, e.g. cards/*.yaml")
    args = parser.parse_args()

    paths = [Path(f) for f in args.files]
    try:
        if args.backfill:
            written = backfill(paths)
            if written:
                print(f"OK: ids written to {len(written)} file(s).")
            else:
                print("OK: every card already has an id.")
        else:
            changes = reassign(paths)
            report_reassignments(changes)
            if not changes:
                print("OK: no id is used twice.")
    except CardIdError as e:
        sys.exit(f"ERROR: {e}")
    return 0


if __name__ == "__main__":
    main()
