#!/usr/bin/env python3
"""Flashcard build: YAML card files -> print-ready PDF.

A4 with 8 cards per page by default (2 x 4, 105 x 74.25 mm — DIN A7), or 16
with --grid a8 (4 x 4, 52.5 x 74.25 mm — DIN A8). Fronts and backs sit on
consecutive pages, backs column-mirrored — duplex print with
"flip on long edge".

The typesetting engine is fetched once on the first build; nothing else has to
be installed. See scripts/engine.py.

Examples:
    python3 scripts/build_pdf.py cards/*.yaml -o output/cards.pdf
    python3 scripts/build_pdf.py cards/*.yaml --topic "Statistics" --subtopic "Bayes"
    python3 scripts/build_pdf.py --check cards/*.yaml
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import engine
import yamlio

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
TEMPLATE = TEMPLATES / "cards.typ"  # imports card.typ, so both are copied along
FONTS = ROOT / "assets" / "fonts"
# The press sheet. Two grids, because those are the two that cut to a standard
# card: 2 x 4 is DIN A7 and 4 x 4 is DIN A8, so a deck still drops into a box
# you can buy. Everything else — card size, the column mirroring that makes
# duplex line up, the crop marks, the page count — derives from these two
# numbers in templates/cards.typ.
GRIDS = {
    "2x4": (2, 4),
    "4x4": (4, 4),
}
GRID_ALIASES = {"a7": "2x4", "a8": "4x4"}
DEFAULT_GRID = GRIDS["2x4"]

# The engine's own fonts plus ours, and nothing the machine happens to have
# installed — so a card looks the same wherever it is printed.
FONT_ARGS = ["--ignore-system-fonts", "--font-path", str(FONTS)]

# Card languages, as the user writes them. The right-hand side is what the
# typesetter wants for hyphenation and quotation marks, and never leaves here.
LANGUAGES = {
    "basque": "eu",
    "catalan": "ca",
    "croatian": "hr",
    "czech": "cs",
    "danish": "da",
    "dutch": "nl",
    "english": "en",
    "estonian": "et",
    "finnish": "fi",
    "french": "fr",
    "galician": "gl",
    "german": "de",
    "greek": "el",
    "hungarian": "hu",
    "icelandic": "is",
    "irish": "ga",
    "italian": "it",
    "latin": "la",
    "latvian": "lv",
    "lithuanian": "lt",
    "norwegian": "nb",
    "polish": "pl",
    "portuguese": "pt",
    "romanian": "ro",
    "russian": "ru",
    "slovak": "sk",
    "slovenian": "sl",
    "spanish": "es",
    "swedish": "sv",
    "turkish": "tr",
    "ukrainian": "uk",
}
CODES = {code: name for name, code in LANGUAGES.items()} | {"no": "norwegian", "en-gb": "english"}
DEFAULT_LANGUAGE = "english"


def resolve_language(name):
    """Normalises a user-facing language name; raises ValueError if unknown."""
    key = str(name).strip().lower().replace("_", "-")
    key = CODES.get(key, CODES.get(key.split("-")[0], key))
    if key not in LANGUAGES:
        raise ValueError(f"unknown language {name!r} — supported: {', '.join(sorted(LANGUAGES))}")
    return key


def grid_name(grid):
    """The canonical `COLSxROWS` spelling of a (columns, rows) pair."""
    return f"{grid[0]}x{grid[1]}"


def supported_grids():
    """The supported grids as the error messages spell them."""
    names = {v: k for k, v in GRID_ALIASES.items()}
    return ", ".join(f"{g} ({names[g].upper()})" for g in GRIDS)


def parse_grid(name):
    """Normalises a grid or its A-series alias; raises ValueError if unusable.

    Mirrors resolve_language: the user-facing spelling comes in, the pair the
    template wants goes out, and nothing else in the file has to know either.
    """
    key = str(name).strip().lower()
    key = GRID_ALIASES.get(key, key)
    if key in GRIDS:
        return GRIDS[key]
    if not re.fullmatch(r"[0-9]+x[0-9]+", key):
        raise ValueError(
            f"unrecognised grid {name!r} — write it as COLSxROWS, e.g. {supported_grids()}"
        )
    raise ValueError(f"unsupported grid {name!r} — supported: {supported_grids()}")


def pages(count, grid):
    """Sheets are printed front and back, so a page count is always even."""
    per_page = grid[0] * grid[1]
    return 2 * ((count + per_page - 1) // per_page)


def resolve_grid(declared, flag=None):
    """The grid this build prints at: the flag, else the decks, else A7.

    `declared` is what load_cards() saw — one (file, value) pair per deck that
    contributes cards, the value None where the deck says nothing.

    An absent key is not an absent opinion: it means A7 (FR-012). So a deck
    asking for A8 beside a deck that says nothing is a real disagreement, and
    is refused rather than guessed at — picking a winner would silently print
    half the cards at a size they were not written for. A7 declared beside
    nothing declared is no disagreement at all: both mean 2 x 4.
    """
    resolved = {}
    for name, value in declared:
        if value is None:
            grid = DEFAULT_GRID
        else:
            # Read every declared value even when the flag is going to win.
            # The flag decides the size; it does not excuse a broken key, and
            # a typo that only surfaces the day someone drops the flag is a
            # bad trade for one dict lookup per deck.
            try:
                grid = parse_grid(value)
            except ValueError as e:
                raise ValueError(f"{name}: {e}") from e
        resolved.setdefault(grid, []).append((name, value))
    if flag is not None:
        return parse_grid(flag)
    if len(resolved) <= 1:
        return next(iter(resolved), DEFAULT_GRID)
    lines = [
        f"  {name}: {f'declares {value}' if value is not None else 'declares no grid'} "
        f"({grid_name(grid)})"
        for grid, decks in resolved.items()
        for name, value in decks
    ]
    raise ValueError(
        "the card files disagree about the grid, and no --grid was given:\n"
        + "\n".join(lines)
        + "\npass --grid to settle it, or make the files agree"
    )


def load_cards(files, topic_filters, subtopic_filters, default_language=DEFAULT_LANGUAGE):
    """Reads the card files and returns the cards, the errors, and the grids.

    The third value is one (file, grid) pair per deck that survives the topic
    filter, the grid None where the deck declares none. resolve_grid() needs
    the file name to be able to name it in a conflict, and these top-level keys
    used to be dropped here.
    """
    cards = []
    errors = []
    declared = []
    for name in files:
        path = Path(name)
        try:
            data = yamlio.load(path.read_text(encoding="utf-8"))
        except (yamlio.YamlError, OSError) as e:
            errors.append(f"{path}: {e}")
            continue
        if not isinstance(data, dict) or "cards" not in data:
            errors.append(f"{path}: expected a mapping with keys 'topic' and 'cards'")
            continue
        topic = str(data.get("topic") or path.stem)
        if topic_filters and not any(f.lower() in topic.lower() for f in topic_filters):
            continue
        declared.append((str(path), None if data.get("grid") is None else str(data["grid"])))
        try:
            language = resolve_language(data.get("language") or default_language)
        except ValueError as e:
            errors.append(f"{path}: {e}")
            continue
        for i, c in enumerate(data["cards"] or [], start=1):
            if not isinstance(c, dict) or "front" not in c or "back" not in c:
                errors.append(f"{path}: card {i}: 'front' and 'back' are required")
                continue
            subtopic = str(c.get("subtopic") or "")
            if subtopic_filters and not any(
                f.lower() in subtopic.lower() for f in subtopic_filters
            ):
                continue
            cards.append(
                {
                    "id": f"{path.stem}-{i}",
                    "topic": topic,
                    "subtopic": subtopic,
                    "front": str(c["front"]),
                    "back": str(c["back"]),
                    "source": str(c.get("source") or ""),
                    "language": language,
                }
            )
    return cards, errors, declared


def main_language(cards, override=None):
    """The document language: what the user asked for, else what the cards are in."""
    if override:
        return override
    counts = Counter(c["language"] for c in cards)
    return counts.most_common(1)[0][0] if counts else DEFAULT_LANGUAGE


def payload(cards):
    """The card data the template renders, with languages as the engine wants them."""
    return [dict(c, lang=LANGUAGES[c["language"]]) for c in cards]


def engine_inputs(margin, logo, grid):
    """The --input pairs every engine call needs.

    Both the compile and the `typst query` below take these. They are built
    here rather than at each call site because the two used to be written out
    separately, and a grid that reached one but not the other would typeset at
    one size while reporting overflow against another — a wrong warning on a
    correct PDF, with nothing to catch it.
    """
    return [
        "--input",
        f"margin={margin:g}",
        "--input",
        f"logo={'true' if logo else 'false'}",
        "--input",
        f"columns={grid[0]}",
        "--input",
        f"rows={grid[1]}",
    ]


def typeset(cards, target, margin, logo, grid, binary, workdir):
    """Runs the engine over `cards`. Returns (ok, message)."""
    for template in TEMPLATES.glob("*.typ"):
        shutil.copy(template, workdir / template.name)
    (workdir / "cards.json").write_text(json.dumps(payload(cards)), encoding="utf-8")
    output = workdir / "cards.pdf"
    result = subprocess.run(
        [
            str(binary),
            "compile",
            *FONT_ARGS,
            *engine_inputs(margin, logo, grid),
            str(workdir / TEMPLATE.name),
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False, result.stderr.strip()
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(output, target)
    return True, result.stderr.strip()


def offending_card(cards, margin, grid, binary, workdir):
    """Typesets card by card to name the one the engine choked on."""
    for card in cards:
        ok, _ = typeset([card], None, margin, False, grid, binary, workdir)
        if not ok:
            return card
    return None


def readable(message):
    """The engine's complaint without its source excerpts and temp paths."""
    lines = []
    for line in message.splitlines():
        stripped = line.strip()
        if stripped.startswith("error:"):
            lines.append(stripped[len("error:") :].strip())
        elif stripped.startswith("= hint:"):
            lines.append("hint: " + stripped[len("= hint:") :].strip())
    return lines or [message.splitlines()[0] if message else "no output"]


def report_failure(cards, message, margin, grid, binary, workdir):
    print("The typesetter rejected the cards:", file=sys.stderr)
    for line in readable(message)[:6]:
        print(f"  {line}", file=sys.stderr)
    culprit = offending_card(cards, margin, grid, binary, workdir)
    if culprit:
        print(
            f"  Offending card: {culprit['id']} — {culprit['topic']}"
            f"{' / ' + culprit['subtopic'] if culprit['subtopic'] else ''}",
            file=sys.stderr,
        )
    else:
        print("  Every card is fine on its own — the problem is in the layout.", file=sys.stderr)


def overflowing(binary, workdir, margin, logo, grid):
    """Card ids whose text does not fit the card — the template flags them."""
    result = subprocess.run(
        [
            str(binary),
            "query",
            *FONT_ARGS,
            *engine_inputs(margin, logo, grid),
            "--field",
            "value",
            str(workdir / TEMPLATE.name),
            "<overflow>",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    try:
        return sorted(set(json.loads(result.stdout or "[]")))
    except json.JSONDecodeError:
        return []


def warn_about_overflow(ids):
    for card_id in ids:
        print(
            f"WARNING: card {card_id} does not fit — shorten it or split it in two.",
            file=sys.stderr,
        )


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("files", nargs="+", help="YAML card files (cards/*.yaml)")
    p.add_argument("-o", "--output", default="output/cards.pdf", help="target PDF")
    p.add_argument(
        "--topic",
        action="append",
        default=[],
        help="only topics containing this text (repeatable)",
    )
    p.add_argument(
        "--subtopic",
        action="append",
        default=[],
        help="only subtopics containing this text",
    )
    p.add_argument(
        "--check", action="store_true", help="only validate and test-typeset, write no PDF"
    )
    p.add_argument(
        "--margin",
        type=float,
        default=5.0,
        metavar="MM",
        help="page margin in mm for printers with a non-printable edge (default: 5, 0 = none)",
    )
    p.add_argument(
        "--grid",
        default=None,
        metavar="COLSxROWS",
        help="cards per A4 sheet: 2x4 (A7, 8 up) or 4x4 (A8, 16 up); the aliases a7 and a8 "
        "work too. Overrides the 'grid' key in the card files "
        "(default: what they say, else 2x4)",
    )
    p.add_argument(
        "--language",
        metavar="NAME",
        help="language of the cards, e.g. german or de — overrides what the card files say "
        f"(default: what they say, else {DEFAULT_LANGUAGE})",
    )
    p.add_argument("--no-logo", action="store_true", help="print the cards without the logo mark")
    args = p.parse_args()

    if not 0 <= args.margin <= 20:
        p.error("--margin must be between 0 and 20 mm")
    override = None
    if args.language:
        try:
            override = resolve_language(args.language)
        except ValueError as e:
            p.error(str(e))

    # A bad --grid is a usage error and exits 2; a bad or contradictory grid in
    # the files is a content error and exits 1, so validate the flag on its own
    # before the files get a say.
    if args.grid is not None:
        try:
            parse_grid(args.grid)
        except ValueError as e:
            p.error(str(e))

    cards, errors, declared = load_cards(
        args.files, args.topic, args.subtopic, override or DEFAULT_LANGUAGE
    )
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors and args.check:
        sys.exit(1)
    if not cards:
        print("No cards left after filtering — nothing to do.", file=sys.stderr)
        sys.exit(1)

    try:
        grid = resolve_grid(declared, args.grid)
    except ValueError as e:
        sys.exit(f"ERROR: {e}")
    if override:
        for c in cards:
            c["language"] = override

    try:
        binary, _ = engine.find()
    except engine.EngineError as e:
        sys.exit(f"ERROR: {e}")

    target = None if args.check else Path(args.output)
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        ok, message = typeset(cards, target, args.margin, not args.no_logo, grid, binary, workdir)
        if not ok:
            report_failure(cards, message, args.margin, grid, binary, workdir)
            sys.exit(1)
        warn_about_overflow(overflowing(binary, workdir, args.margin, not args.no_logo, grid))

    page_count = pages(len(cards), grid)
    languages = ", ".join(sorted({c["language"] for c in cards}))
    if args.check:
        print(
            f"OK: {len(cards)} cards valid ({languages}), "
            f"test build succeeded ({page_count} pages)."
        )
    else:
        print(
            f"OK: {len(cards)} cards ({languages}) -> {target} "
            f"({page_count} pages, duplex, flip on long edge)."
        )


if __name__ == "__main__":
    main()
