#!/usr/bin/env python3
"""Builds the binary half of the test data: PDFs, a scan, an image, a DOCX.

The demo project needs the file types a user really points /sources at, and
those are binaries — which have no place in a git repo. So they are generated
from the text sources under tests/fixtures/demo-project/generators/, with the
typesetting engine the project ships anyway:

    python3 scripts/make_testdata.py           # build what is missing or stale
    python3 scripts/make_testdata.py --force   # build everything again
    python3 scripts/make_testdata.py --check    # report, build nothing

What comes out (all of it .gitignored):

    raw/handbook/kestrel-handbook.pdf    4 pages with a text layer
    raw/handbook/tide-tables-scan.pdf    2 pages of pixels, no text layer
    raw/handbook/tide-almanac.pdf        61 pages — long enough to need chunking
    raw/handbook/damaged.pdf             truncated: extraction has to fail
    raw/images/tide-chart.png            an infographic
    raw/images/harbour-noticeboard.jpg   a photo-like JPEG (needs Pillow)
    raw/office/mail-boat-timetable.docx  a Word document
    raw/field-notes/harbour-log.txt      text that is not UTF-8
    ../zotero/storage/<key>/*.pdf        the attachments of the fake library

The scan is the interesting one: /ingest has to notice that there is no text to
extract and look at the pages instead. A generated PDF of rendered pixels is
the honest way to test that without shipping someone's scanned book.
"""

import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import engine

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "tests" / "fixtures" / "demo-project"
GENERATORS = DEMO / "generators"
RAW = DEMO / "raw"
ZOTERO_STORAGE = ROOT / "tests" / "fixtures" / "zotero" / "storage"

# A scan is a picture of a page: rendered at this resolution, then wrapped in a
# PDF. Enough to read, small enough to build in a second.
SCAN_PPI = 130
SCAN_TILT = 0.6  # degrees — nothing is ever laid on the glass straight

# The Word document, as plain text. Turned into OOXML below; the point is that
# something has to unzip it, not what it says.
DOCX_TITLE = "Mail boat timetable — Kestrel Islands"
DOCX_PARAGRAPHS = [
    "Torvig Harbour is the hub: everything arrives there and is redistributed.",
    "Monday and Thursday: Torvig Harbour 07:00, Fenmouth 08:20, Skarn Landing 10:05.",
    "Tuesday and Friday: Torvig Harbour 07:00, Ovray Cove within the tidal window, "
    "back to Torvig Harbour by 16:30.",
    "Wednesday: mail only as far as Fenmouth; the boat is in Torvig for maintenance.",
    "Saturday: the Bellhorn lighthouse run, weather permitting. No timetable in winter.",
    "The boat waits for the tide, never the other way round. Ovray Cove is only "
    "entered within two hours either side of high water.",
]


# A harbour log in Windows-1252, the encoding old office machines still write.
LATIN1_TEXT = """HAFENLOG TORVIG HARBOUR — Woche 14
(Erfundenes Material, absichtlich in Windows-1252 kodiert.)

Mo  Postboot 07:10 eingelaufen, Nordostwind Stärke 4, Tidenhub 3,4 m
Di  Lotse angefordert (blaue Flagge), Übergabe an der Pier um 11:20
Mi  Hafen wegen Nebel über der Kestrel-Tiefe geschlossen — rote Flagge
Do  Ovray Cove nur zwischen 14:00 und 18:00 anlaufbar, Niedrigwasser 0,3 m
Fr  Wasservorrat knapp auf Skarn Landing — gelbe Flagge gesetzt
Sa  Leuchtturmfahrt Bellhorn, 11 km bei klarer Sicht
So  Ruhetag; Springtide zwei Tage nach Neumond erwartet

Anmerkung des Hafenmeisters: Die Zwölftelregel gilt auch hier — nach drei
Stunden ist die Hälfte des Hubs erreicht. Größe, Maßstab, Überfahrt, § 4.
"""


class BuildError(RuntimeError):
    """A generator failed — with the engine's own complaint attached."""


class MissingTool(BuildError):
    """This machine cannot build that one artifact. Only optional jobs may."""


# Nothing in the standard library writes a JPEG. This used to shell out to
# whichever of sips, magick or convert the machine happened to have, and skip the
# fixture where there was none — which meant it existed on macOS, sometimes on
# Linux, and never on Windows. Pillow is a declared development dependency
# instead: same result on all three platforms, no guessing.
JPEG_QUALITY = 80


def typst(binary, source, target, extra=()):
    """Compiles one typst file. --ignore-system-fonts keeps it reproducible."""
    result = subprocess.run(
        [str(binary), "compile", "--ignore-system-fonts", *extra, str(source), str(target)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise BuildError(f"{Path(source).name}: {result.stderr.strip().splitlines()[0]}")


def build_pdf_with_text(binary, source, target):
    """An ordinary PDF: text layer, several pages, a table."""
    target.parent.mkdir(parents=True, exist_ok=True)
    typst(binary, source, target)


def build_scan(binary, source, target):
    """Renders the pages to images and wraps those in a PDF — no text layer."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        typst(binary, source, work / "page-{p}.png", ["-f", "png", "--ppi", str(SCAN_PPI)])
        pages = sorted(work.glob("page-*.png"))
        if not pages:
            raise BuildError(f"{source.name}: rendered no pages")
        wrapper = "\n".join(
            [
                '#set page(paper: "a4", margin: 0pt, fill: rgb("#f6f5f2"))',
                "\n#pagebreak()\n".join(
                    f'#rotate({SCAN_TILT}deg, image("{p.name}", width: 100%, height: 100%))'
                    for p in pages
                ),
            ]
        )
        (work / "scan.typ").write_text(wrapper, encoding="utf-8")
        typst(binary, work / "scan.typ", work / "scan.pdf")
        shutil.copy(work / "scan.pdf", target)


def build_damaged_pdf(source, target):
    """A PDF that breaks off mid-object — every extractor has to give up."""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes()[:900] + b"\n% the rest of this file was lost\n")


def build_latin1_text(target):
    """A text file that is not UTF-8 — the encoding a naive read trips over."""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(LATIN1_TEXT.encode("cp1252"))


def build_image(binary, source, target):
    """A single-page infographic as PNG."""
    target.parent.mkdir(parents=True, exist_ok=True)
    typst(binary, source, target, ["-f", "png", "--ppi", "150"])


def build_jpeg(binary, source, target):
    """Renders the source to PNG, then re-encodes it as a JPEG with Pillow."""
    # Imported here, not at the top: tests/test_repo_hygiene.py imports this
    # module for its JOBS table alone, and should not need Pillow to do it.
    try:
        from PIL import Image
    except ImportError as e:  # pragma: no cover - depends on the environment
        raise MissingTool(
            f"{target.name}: Pillow is not installed "
            "(python3 -m pip install -r requirements-dev.txt)"
        ) from e

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        png = Path(td) / "page.png"
        typst(binary, source, png, ["-f", "png", "--ppi", "150"])
        # A photographed notice has no transparency, and JPEG cannot store it
        # anyway — flatten onto white rather than let the alpha channel decide.
        with Image.open(png) as rendered:
            photo = rendered.convert("RGB")
        photo.save(target, "JPEG", quality=JPEG_QUALITY)
    if not target.exists():
        raise BuildError(f"{target.name}: Pillow wrote nothing")


def _xml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_docx(target):
    """A minimal but valid .docx — Word, textutil and the docx skill read it."""
    target.parent.mkdir(parents=True, exist_ok=True)
    paragraphs = "".join(
        f'<w:p><w:pPr><w:pStyle w:val="{"Heading1" if i == 0 else "Normal"}"/></w:pPr>'
        f'<w:r><w:t xml:space="preserve">{_xml_escape(text)}</w:t></w:r></w:p>'
        for i, text in enumerate([DOCX_TITLE, *DOCX_PARAGRAPHS])
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraphs}</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
        'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.'
        'openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    )
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)


# Every artifact: where it goes, what it is made from, and how.
# The zotero attachments come last — one of them is a copy of the scan, so the
# scan has to exist by then.
JOBS = [
    (
        RAW / "handbook" / "kestrel-handbook.pdf",
        GENERATORS / "handbook.typ",
        lambda binary, source, target: build_pdf_with_text(binary, source, target),
    ),
    (
        RAW / "handbook" / "tide-tables-scan.pdf",
        GENERATORS / "tide-tables.typ",
        build_scan,
    ),
    (
        RAW / "handbook" / "tide-almanac.pdf",
        GENERATORS / "almanac.typ",
        build_pdf_with_text,
    ),
    (
        RAW / "handbook" / "damaged.pdf",
        RAW / "handbook" / "kestrel-handbook.pdf",
        lambda binary, source, target: build_damaged_pdf(source, target),
    ),
    (
        RAW / "field-notes" / "harbour-log.txt",
        Path(__file__).resolve(),
        lambda binary, source, target: build_latin1_text(target),
    ),
    (
        RAW / "images" / "tide-chart.png",
        GENERATORS / "tide-chart.typ",
        build_image,
    ),
    (
        RAW / "images" / "harbour-noticeboard.jpg",
        GENERATORS / "noticeboard.typ",
        build_jpeg,
    ),
    (
        RAW / "office" / "mail-boat-timetable.docx",
        Path(__file__).resolve(),  # this script is its own source
        lambda binary, source, target: build_docx(target),
    ),
    (
        ZOTERO_STORAGE / "KESTREL01" / "ashwind-currents.pdf",
        GENERATORS / "zotero-paper.typ",
        build_pdf_with_text,
    ),
    (
        ZOTERO_STORAGE / "KESTREL02" / "tide-tables-scan.pdf",
        RAW / "handbook" / "tide-tables-scan.pdf",
        lambda binary, source, target: (
            target.parent.mkdir(parents=True, exist_ok=True),
            shutil.copy(source, target),
        ),
    ),
    (
        ZOTERO_STORAGE / "KESTREL03" / "ferry-statistics.pdf",
        GENERATORS / "zotero-ferry.typ",
        build_pdf_with_text,
    ),
    (
        ZOTERO_STORAGE / "KESTREL04" / "signal-code-offprint.pdf",
        GENERATORS / "zotero-offprint.typ",
        build_pdf_with_text,
    ),
    (
        ZOTERO_STORAGE / "KESTREL09" / "tide-office-cover.pdf",
        GENERATORS / "zotero-cover.typ",
        build_pdf_with_text,
    ),
]


# Artifacts that need something beyond the engine. A job in here that cannot be
# built is reported and skipped; anything else is a failure. The JPEG is here
# only for whoever has not installed requirements-dev.txt — which, unlike the
# old hunt for sips or magick, is a thing they can fix.
OPTIONAL = {RAW / "images" / "harbour-noticeboard.jpg"}


def jpeg_available():
    """Whether a JPEG can be written here — that is, whether Pillow is installed."""
    return importlib.util.find_spec("PIL") is not None


def stale(target, source):
    return not target.exists() or target.stat().st_mtime < source.stat().st_mtime


def build(force=False, dry_run=False):
    """Builds everything that is missing or older than its source."""
    todo = [(t, s, f) for t, s, f in JOBS if force or stale(t, s)]
    if dry_run:
        todo = [(t, s, f) for t, s, f in todo if t not in OPTIONAL or jpeg_available()]
    if not todo or dry_run:
        return [t for t, _, _ in todo]

    try:
        binary, _ = engine.find()
    except engine.EngineError as e:
        raise BuildError(str(e)) from e

    built, skipped = [], []
    for target, source, make in todo:
        try:
            make(binary, source, target)
        except MissingTool as e:
            if target not in OPTIONAL:
                raise
            skipped.append(str(e))
            continue
        built.append(target)
    for message in skipped:
        print(f"SKIPPED: {message}", file=sys.stderr)
    return built


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--force", action="store_true", help="rebuild even what is up to date")
    p.add_argument("--check", action="store_true", help="only say what is missing or stale")
    args = p.parse_args()

    try:
        touched = build(force=args.force, dry_run=args.check)
    except BuildError as e:
        sys.exit(f"ERROR: {e}")

    if args.check:
        if touched:
            print(f"{len(touched)} file(s) missing or stale:", file=sys.stderr)
            for path in touched:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            sys.exit(1)
        print(f"OK: all {len(JOBS)} generated test files are up to date.")
        return

    for path in touched:
        print(f"  {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")
    print(f"OK: {len(touched)} built, {len(JOBS) - len(touched)} already up to date.")


if __name__ == "__main__":
    main()
