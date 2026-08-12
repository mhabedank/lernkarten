#!/usr/bin/env python3
"""Flashcard build: YAML card files -> LaTeX -> print-ready PDF.

A4 with 8 cards (105 x 74.25 mm) per page. Fronts and backs sit on
consecutive pages, backs column-mirrored — duplex print with
"flip on long edge".

Examples:
    python3 scripts/build_pdf.py cards/*.yaml -o output/cards.pdf
    python3 scripts/build_pdf.py cards/*.yaml --topic "Statistics" --subtopic "Bayes"
    python3 scripts/build_pdf.py --check cards/*.yaml
"""

import argparse
import re
import shutil
import string
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "cards.tex.in"
CARDS_PER_PAGE = 8  # 2 columns x 4 rows
COLUMNS, ROWS = 2, 4
A4_WIDTH, A4_HEIGHT = 210.0, 297.0  # mm

# Card languages, as the user writes them, mapped to what the typesetter needs
# for hyphenation and quotation marks. Names and ISO 639-1 codes both work; the
# right-hand side never leaves this file.
LANGUAGES = {
    "basque": "basque",
    "catalan": "catalan",
    "croatian": "croatian",
    "czech": "czech",
    "danish": "danish",
    "dutch": "dutch",
    "english": "english",
    "estonian": "estonian",
    "finnish": "finnish",
    "french": "french",
    "galician": "galician",
    "german": "ngerman",
    "hungarian": "magyar",
    "icelandic": "icelandic",
    "irish": "irish",
    "italian": "italian",
    "latin": "latin",
    "latvian": "latvian",
    "lithuanian": "lithuanian",
    "norwegian": "norsk",
    "polish": "polish",
    "portuguese": "portuguese",
    "romanian": "romanian",
    "slovak": "slovak",
    "slovenian": "slovene",
    "spanish": "spanish",
    "swedish": "swedish",
    "turkish": "turkish",
    "welsh": "welsh",
}
CODES = {
    "ca": "catalan",
    "cs": "czech",
    "cy": "welsh",
    "da": "danish",
    "de": "german",
    "en": "english",
    "es": "spanish",
    "et": "estonian",
    "eu": "basque",
    "fi": "finnish",
    "fr": "french",
    "ga": "irish",
    "gl": "galician",
    "hr": "croatian",
    "hu": "hungarian",
    "is": "icelandic",
    "it": "italian",
    "la": "latin",
    "lt": "lithuanian",
    "lv": "latvian",
    "nb": "norwegian",
    "nl": "dutch",
    "no": "norwegian",
    "pl": "polish",
    "pt": "portuguese",
    "ro": "romanian",
    "sk": "slovak",
    "sl": "slovenian",
    "sv": "swedish",
    "tr": "turkish",
}
DEFAULT_LANGUAGE = "english"


def resolve_language(name):
    """Normalises a user-facing language name; raises ValueError if unknown."""
    key = str(name).strip().lower().replace("_", "-")
    key = CODES.get(key.split("-")[0], key)
    if key not in LANGUAGES:
        raise ValueError(f"unknown language {name!r} — supported: {', '.join(sorted(LANGUAGES))}")
    return key


def typesetting_options(main, used):
    """Language options for the template: every language used, `main` in charge."""
    others = sorted(LANGUAGES[lang] for lang in used if lang != main)
    return ",".join([*others, f"main={LANGUAGES[main]}"]) if others else LANGUAGES[main]


def grid(margin):
    """Card dimensions and cut lines for the given page margin (mm)."""
    cw = (A4_WIDTH - 2 * margin) / COLUMNS
    ch = (A4_HEIGHT - 2 * margin) / ROWS
    lines = []
    xs = [margin + i * cw for i in range(COLUMNS + 1)]
    ys = [margin + j * ch for j in range(ROWS + 1)]
    if margin == 0:  # outer edges are paper edges — no lines needed
        xs, ys = xs[1:-1], ys[1:-1]
    for x in xs:
        lines.append(
            f"  \\draw[gray!45, line width=0.1pt] ({x:.3f}mm,0mm) -- ({x:.3f}mm,-{A4_HEIGHT}mm);"
        )
    for y in ys:
        lines.append(
            f"  \\draw[gray!45, line width=0.1pt] (0mm,-{y:.3f}mm) -- ({A4_WIDTH}mm,-{y:.3f}mm);"
        )
    return cw, ch, "\n".join(lines)


def load_cards(files, topic_filters, subtopic_filters, default_language=DEFAULT_LANGUAGE):
    """Reads the YAML files and returns a flat, filtered list of cards."""
    cards = []
    errors = []
    for name in files:
        path = Path(name)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            errors.append(f"{path}: YAML error: {e}")
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


def _page(cells, margin, cw, ch):
    """Turns a list of (column, row, id, latex) cells into one TikZ page."""
    body = "\n".join(
        f"% card: {cid}\n\\cell{{{margin + column * cw:.3f}}}{{{margin + row * ch:.3f}}}{{{latex}}}"
        for column, row, cid, latex in cells
    )
    return (
        "\\begin{tikzpicture}[remember picture, overlay, "
        "shift={(current page.north west)}]\n"
        "\\cutlines\n" + body + "\n\\end{tikzpicture}\\null"
    )


def _in_language(text, language, main):
    """Marks text that is not in the document language, so it hyphenates right."""
    if language == main or not text:
        return text
    return f"\\foreignlanguage{{{LANGUAGES[language]}}}{{{text}}}"


def build_body(cards, margin, cw, ch, main=DEFAULT_LANGUAGE):
    """Builds the LaTeX body: one front and one back page per block of 8."""
    pages = []
    for start in range(0, len(cards), CARDS_PER_PAGE):
        block = cards[start : start + CARDS_PER_PAGE]

        fronts, backs = [], []
        for pos, c in enumerate(block):
            column, row = pos % COLUMNS, pos // COLUMNS
            language = c.get("language", main)
            header = c["topic"] + (
                " \\,\\textperiodcentered\\, " + c["subtopic"] if c["subtopic"] else ""
            )
            header = _in_language(header, language, main)
            front = _in_language(c["front"], language, main)
            back = _in_language(c["back"], language, main)
            fronts.append(
                (column, row, c["id"], f"\\cardfront{{{header}}}{{{front}}}{{{c['id']}}}")
            )
            # Back is column-mirrored for duplex printing along the long edge
            backs.append(
                (
                    1 - column,
                    row,
                    c["id"] + " (back)",
                    f"\\cardback{{{back}}}{{{c['source']}}}{{{c['id']}}}",
                )
            )

        pages.append(_page(fronts, margin, cw, ch))
        pages.append(_page(backs, margin, cw, ch))
    return "\n\\newpage\n".join(pages)


def compile_pdf(tex_source, target_pdf, workdir):
    tex_file = workdir / "cards.tex"
    tex_file.write_text(tex_source, encoding="utf-8")
    # Two runs: TikZ' "remember picture" only knows the page coordinates in the second
    for _ in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_file.name],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            break
    log = (
        (workdir / "cards.log").read_text(encoding="utf-8", errors="replace")
        if (workdir / "cards.log").exists()
        else result.stdout
    )

    if result.returncode != 0:
        report_error(log, tex_file)
        return False

    for line in log.splitlines():
        if line.startswith("Overfull"):
            print(f"WARNING: {line.strip()} — shorten or split that card.", file=sys.stderr)

    if target_pdf is not None:
        target_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(workdir / "cards.pdf", target_pdf)
    return True


def report_error(log, tex_file):
    """Maps the LaTeX error back to the offending card (via the % comment)."""
    print("Typesetting failed:", file=sys.stderr)
    match = re.search(r"^! (.+)$", log, re.MULTILINE)
    if match:
        print(f"  {match.group(1)}", file=sys.stderr)
    if "babel" in log.lower() and re.search(r"Unknown option|not loaded|\.ldf", log):
        print(
            "  Your TeX installation is missing the data for that language.\n"
            "    macOS:  the full MacTeX install covers every language\n"
            "    Debian: sudo apt-get install texlive-lang-all",
            file=sys.stderr,
        )
    line_no = re.search(r"^l\.(\d+)", log, re.MULTILINE)
    if line_no:
        no = int(line_no.group(1))
        source_lines = tex_file.read_text(encoding="utf-8").splitlines()
        for line in reversed(source_lines[: min(no, len(source_lines))]):
            m = re.match(r"% card: (\S+)", line.strip())
            if m:
                print(f"  Offending card: {m.group(1)}", file=sys.stderr)
                break
    print(f"  Full log: {tex_file.with_suffix('.log')}", file=sys.stderr)


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
        "--check", action="store_true", help="only validate and test-compile, write no PDF"
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

    main = main_language(cards, override)
    if override:
        for c in cards:
            c["language"] = override

    cw, ch, cutlines = grid(args.margin)
    template = string.Template(TEMPLATE.read_text(encoding="utf-8"))
    tex = template.substitute(
        cw=f"{cw:.3f}",
        ch=f"{ch:.3f}",
        margin=f"{args.margin:g}",
        language=typesetting_options(main, {c["language"] for c in cards}),
        logo="" if args.no_logo else "\\logomark",
        cutlines=cutlines,
        body=build_body(cards, args.margin, cw, ch, main),
    )

    target = None if args.check else Path(args.output)
    with tempfile.TemporaryDirectory() as td:
        ok = compile_pdf(tex, target, Path(td))
    if not ok:
        sys.exit(1)

    pages = 2 * ((len(cards) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)
    used = sorted({c["language"] for c in cards})
    languages = ", ".join(used)
    if args.check:
        print(
            f"OK: {len(cards)} cards valid ({languages}), test compile succeeded ({pages} pages)."
        )
    else:
        print(
            f"OK: {len(cards)} cards ({languages}) -> {target} "
            f"({pages} pages, duplex, flip on long edge)."
        )


if __name__ == "__main__":
    main()
