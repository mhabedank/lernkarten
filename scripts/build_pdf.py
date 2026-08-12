#!/usr/bin/env python3
"""Flashcard build: YAML card files -> print-ready PDF.

A4 with 8 cards (105 x 74.25 mm) per page. Fronts and backs sit on
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
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import engine
import minyaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "cards.typ"
CARDS_PER_PAGE = 8

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


def load_cards(files, topic_filters, subtopic_filters, default_language=DEFAULT_LANGUAGE):
    """Reads the card files and returns a flat, filtered list of cards."""
    cards = []
    errors = []
    for name in files:
        path = Path(name)
        try:
            data = minyaml.load(path.read_text(encoding="utf-8"))
        except (minyaml.YamlError, OSError) as e:
            errors.append(f"{path}: {e}")
            continue
        if not isinstance(data, dict) or "cards" not in data:
            errors.append(f"{path}: expected a mapping with keys 'topic' and 'cards'")
            continue
        topic = str(data.get("topic") or path.stem)
        if topic_filters and not any(f.lower() in topic.lower() for f in topic_filters):
            continue
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
    return cards, errors


def main_language(cards, override=None):
    """The document language: what the user asked for, else what the cards are in."""
    if override:
        return override
    counts = Counter(c["language"] for c in cards)
    return counts.most_common(1)[0][0] if counts else DEFAULT_LANGUAGE


def payload(cards):
    """The card data the template renders, with languages as the engine wants them."""
    return [dict(c, lang=LANGUAGES[c["language"]]) for c in cards]


def typeset(cards, target, margin, logo, binary, workdir):
    """Runs the engine over `cards`. Returns (ok, message)."""
    shutil.copy(TEMPLATE, workdir / TEMPLATE.name)
    (workdir / "cards.json").write_text(json.dumps(payload(cards)), encoding="utf-8")
    output = workdir / "cards.pdf"
    result = subprocess.run(
        [
            str(binary),
            "compile",
            "--ignore-system-fonts",  # the engine's own fonts, same output everywhere
            "--input",
            f"margin={margin:g}",
            "--input",
            f"logo={'true' if logo else 'false'}",
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


def offending_card(cards, margin, binary, workdir):
    """Typesets card by card to name the one the engine choked on."""
    for card in cards:
        ok, _ = typeset([card], None, margin, False, binary, workdir)
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


def report_failure(cards, message, margin, binary, workdir):
    print("The typesetter rejected the cards:", file=sys.stderr)
    for line in readable(message)[:6]:
        print(f"  {line}", file=sys.stderr)
    culprit = offending_card(cards, margin, binary, workdir)
    if culprit:
        print(
            f"  Offending card: {culprit['id']} — {culprit['topic']}"
            f"{' / ' + culprit['subtopic'] if culprit['subtopic'] else ''}",
            file=sys.stderr,
        )
    else:
        print("  Every card is fine on its own — the problem is in the layout.", file=sys.stderr)


def overflowing(binary, workdir, margin, logo):
    """Card ids whose text does not fit the card — the template flags them."""
    result = subprocess.run(
        [
            str(binary),
            "query",
            "--ignore-system-fonts",
            "--input",
            f"margin={margin:g}",
            "--input",
            f"logo={'true' if logo else 'false'}",
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

    cards, errors = load_cards(args.files, args.topic, args.subtopic, override or DEFAULT_LANGUAGE)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors and args.check:
        sys.exit(1)
    if not cards:
        print("No cards left after filtering — nothing to do.", file=sys.stderr)
        sys.exit(1)
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
        ok, message = typeset(cards, target, args.margin, not args.no_logo, binary, workdir)
        if not ok:
            report_failure(cards, message, args.margin, binary, workdir)
            sys.exit(1)
        warn_about_overflow(overflowing(binary, workdir, args.margin, not args.no_logo))

    pages = 2 * ((len(cards) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)
    languages = ", ".join(sorted({c["language"] for c in cards}))
    if args.check:
        print(f"OK: {len(cards)} cards valid ({languages}), test build succeeded ({pages} pages).")
    else:
        print(
            f"OK: {len(cards)} cards ({languages}) -> {target} "
            f"({pages} pages, duplex, flip on long edge)."
        )


if __name__ == "__main__":
    main()
