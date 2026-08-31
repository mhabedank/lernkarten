#!/usr/bin/env python3
"""Getting a picture out of a source and into figures/ — what /ingest calls.

Three jobs a prompt cannot do for itself:

    extract   pull the raster figures off the pages of a PDF
    fetch     download one picture from a URL
    place     put a judged keeper into figures/<source-id>/<slug>.<ext>

Everything *else* about figures is a judgement, and judgements belong in
skills/ingest/SKILL.md: whether a picture teaches something the transcription
cannot, what to call it, what its caption says. This module only moves bytes,
and it applies the one rule check_project.py later validates — that a kept
figure lives under figures/<source-id>/ with a kebab-case name.

Called with an explicit --project, the way scripts/zotero_ingest.py is: this
file lives in the plugin cache, and leaving the destination to whatever the
working directory happens to be is how an ingest ends up somewhere nobody looks.

    python3 scripts/figures.py extract doc.pdf --project . --source-id handbook
    python3 scripts/figures.py fetch https://…/chart.png --project . --source-id site
    python3 scripts/figures.py place .figures-staging/handbook/p3-1.png \\
        --project . --source-id handbook --slug tide-curve

pypdfium2 is optional and only `extract` needs it. Without it that verb exits 3
and says which document lost its figures; every other path is unaffected, and
the ingest carries on. See scripts/deps.py FIGURES.

**Raster figures only.** A chart drawn as vector paths is not an image object
and is not extracted; /ingest falls back to looking at the page, which is what
it already does for a scan.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import deps

# Two sets, not one. What the *engine can print* is a property of the pinned
# typst and lives in build_pdf.IMAGE_FORMATS; what the *web hands back* is a
# property of the web, and is wider. Conflating them is BUG-008: AVIF is served
# constantly and typst 0.15.1 refuses it, so a single list either rejects a
# quarter of real picture URLs or lets a card name something unprintable.
#
# Downloadable. A picture here may still be refused as a *card* picture, with a
# message that says which of the two problems it has.
NETWORK_FORMATS = ("png", "jpg", "jpeg", "gif", "svg", "webp", "avif")
# What `place` will put in figures/, because the engine can print it. Kept equal
# to build_pdf.IMAGE_FORMATS by tests/test_build_pdf.py rather than by an
# import: this module must not pull the PDF build in to name six strings.
IMAGE_FORMATS = ("png", "jpg", "jpeg", "gif", "svg", "webp")

# What a response has to start with to be the thing it claims. Content-Type is
# a hint from a server that may be careless; the bytes are not.
MAGIC = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)

# Says who we are. Cloudflare blocks the *empty* case, not any particular
# client, so an honest product token is enough — impersonating a browser would
# be the thing FR-016 forbids.
#
# No version in it deliberately. The version lives in exactly three files and
# check_docs.py compares them; a fourth copy here would drift, and a server
# operator wanting to identify this tool needs the name and the repository, not
# the build.
USER_AGENT = "lernkarten (+https://github.com/mhabedank/lernkarten)"
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*$")
STAGING = ".figures-staging"
# Below this a picture is an icon, a rule or a spacer, not something worth
# printing on a card at 30 mm across.
MIN_PIXELS = 64
# Set by the test suite to take the degraded path deliberately. A user reaches
# it by not having the package, which is the normal state.
PDFIUM_UNAVAILABLE = False


def fail(message):
    """One line on stderr, no traceback. The caller turns this into an exit code."""
    print(f"ERROR: {message}", file=sys.stderr)


def staging_dir(project, source_id):
    folder = Path(project) / STAGING / source_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def load_pdfium():
    """pypdfium2, or None. Imported here so nothing else pays for it."""
    if PDFIUM_UNAVAILABLE:
        return None
    try:
        deps.activate_optional(deps.FIGURES)
        import pypdfium2

        return pypdfium2
    except (deps.DependencyError, ImportError):
        return None


def page_range(spec, total):
    """`"1-4"`, `"3"` or None -> the page numbers to look at.

    The same slice `sources.yaml` already spells for a `type: pdf` source, so a
    source that ingests two pages of a forty-page book does not have its
    figures pulled off the other thirty-eight.
    """
    if not spec:
        return range(1, total + 1)
    first, _, last = str(spec).partition("-")
    try:
        start = int(first)
        end = int(last) if last else start
    except ValueError:
        raise ValueError("write it as N or N-M") from None
    if start < 1 or end < start:
        raise ValueError("write it as N or N-M, counting from 1")
    return range(start, min(end, total) + 1)


def extract(args):
    """Raster figures off the pages of a PDF, as a manifest for the model to judge."""
    pdfium = load_pdfium()
    if pdfium is None:
        fail(
            f"{Path(args.pdf).name}: no PDF renderer, so its figures were not extracted "
            "— the text is unaffected (pip install pypdfium2)"
        )
        return 3

    folder = staging_dir(args.project, args.source_id)
    candidates, skipped = {}, []
    document = pdfium.PdfDocument(str(args.pdf))
    try:
        wanted = page_range(args.pages, len(document))
    except ValueError as e:
        fail(f"--pages {args.pages}: {e}")
        return 1
    for number, page in enumerate(document, start=1):
        if number not in wanted:
            continue
        for image in (o for o in page.get_objects() if isinstance(o, pdfium.PdfImage)):
            width, height = image.get_px_size()
            where = f"page {number}"
            if width < MIN_PIXELS or height < MIN_PIXELS:
                skipped.append({"at": where, "why": f"{width}x{height} is smaller than a figure"})
                continue
            data = image.get_bitmap().to_pil()
            digest = hashlib.sha256(data.tobytes()).hexdigest()[:12]
            # Content-addressed, so the same picture on four pages is one
            # candidate. A logo in a running header is furniture, and offering
            # it once per page would grow a logo card in every deck.
            if digest in candidates:
                candidates[digest]["repeated_on"] += 1
                continue
            target = folder / f"p{number}-{len(candidates) + 1}.png"
            data.save(target)
            candidates[digest] = {
                "at": where,
                "file": str(target),
                "width": width,
                "height": height,
                "repeated_on": 1,
            }

    manifest = {"candidates": list(candidates.values()), "skipped": skipped}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


def sniff(content_type, data):
    """The format of a response, or None. The bytes win over the header.

    A server's Content-Type is a hint from something that may be careless; the
    leading bytes are the thing itself. SVG and AVIF have no short magic number
    worth trusting, so they fall back to the declared type — which is safe,
    because being wrong about them costs a clear message rather than a bad card.
    """
    for prefix, name in MAGIC:
        if data.startswith(prefix):
            return name
    if data[4:12] == b"ftypavif":
        return "avif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    declared = (content_type or "").split(";")[0].strip().lower()
    if declared == "image/svg+xml" and b"<svg" in data[:512].lower():
        return "svg"
    if declared.startswith("image/"):
        candidate = declared.removeprefix("image/")
        if candidate in NETWORK_FORMATS:
            return candidate
    return None


def fetch(args):
    """One picture from a URL, with urllib — no dependency for what is in the box.

    The *response* decides what this is, never the URL. A CDN path carries no
    extension to read (181 of 851 real URLs had none), and a `.png` that serves
    an error page is not a picture however it is spelled. Checking the name
    first is BUG-008.
    """
    origin = urllib.parse.urlparse(args.url)

    class SameHostOnly(urllib.request.HTTPRedirectHandler):
        """A source is a place the user chose; a redirect is not that choice."""

        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if urllib.parse.urlparse(newurl).netloc != origin.netloc:
                raise urllib.error.HTTPError(newurl, code, f"redirects to {newurl}", headers, fp)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(SameHostOnly)
    # On the opener, not the request: a redirect builds a fresh request, and a
    # header set on the first one would not survive it.
    opener.addheaders = [("User-Agent", USER_AGENT)]

    try:
        # No credentials, ever: only what the page would hand anyone.
        with opener.open(args.url, timeout=30) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "")
    except Exception as e:  # noqa: BLE001 — one line out, whatever went wrong
        fail(f"{args.url}: {e}")
        return 1

    kind = sniff(content_type, data)
    if kind is None:
        declared = (content_type or "no Content-Type").split(";")[0].strip()
        fail(f"{args.url}: the response is {declared}, not a picture")
        return 1

    # The URL may name no file at all, so the name comes from what came back.
    stem = Path(urllib.parse.unquote(origin.path)).stem or "picture"
    target = staging_dir(args.project, args.source_id) / f"{stem}.{kind}"
    target.write_bytes(data)
    print(str(target))
    return 0


def place(args):
    """Move a judged keeper into figures/<source-id>/<slug>.<ext>."""
    source = Path(args.source)
    if not source.is_file():
        fail(f"{source}: nothing to place")
        return 1
    if not SLUG.match(args.slug):
        fail(f"'{args.slug}' is not kebab-case — lower case, digits and single hyphens")
        return 1
    suffix = source.suffix.lower()
    kind = suffix.lstrip(".")
    # Three different problems, three different messages. They used to share
    # one, which sent the user looking in the wrong place (BUG-008): "not a
    # picture" reads like the file is broken when the truth is that it is a
    # perfectly good picture in a format the typesetter cannot print.
    if kind in NETWORK_FORMATS and kind not in IMAGE_FORMATS:
        fail(
            f"{source.name}: {kind.upper()} is a real picture, and the typesetter cannot "
            f"read it — convert it first, e.g. `sips -s format png {source.name}` or any "
            "image editor, then place the PNG"
        )
        return 1
    if kind not in IMAGE_FORMATS:
        fail(f"{source.name}: not a picture this engine reads ({', '.join(IMAGE_FORMATS)})")
        return 1

    folder = Path(args.project) / "figures" / args.source_id
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{args.slug}{suffix}"
    relative = target.relative_to(Path(args.project)).as_posix()

    if target.exists() and not args.force:
        # The same picture twice is the incremental path working, not a clash:
        # a second /ingest must not grow the store.
        if target.read_bytes() == source.read_bytes():
            print(relative)
            return 0
        fail(f"{relative}: already holds a different picture — pass --force to replace it")
        return 1

    # A copy, never a move. The original is the user's, and a figure lifted off
    # a PDF page has no original to move anyway.
    shutil.copyfile(source, target)
    print(relative)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    verbs = parser.add_subparsers(dest="verb", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", required=True, help="the project root to write into")
    common.add_argument("--source-id", required=True, help="the source these pictures came from")

    one = verbs.add_parser("extract", parents=[common], help="raster figures off a PDF's pages")
    one.add_argument("pdf")
    one.add_argument(
        "--pages",
        help="only these pages, as N or N-M — the same slice sources.yaml spells",
    )
    one.set_defaults(run=extract)

    two = verbs.add_parser("fetch", parents=[common], help="download one picture from a URL")
    two.add_argument("url")
    two.set_defaults(run=fetch)

    three = verbs.add_parser("place", parents=[common], help="keep a picture as a figure")
    three.add_argument("source", help="the staged file to keep")
    three.add_argument("--slug", required=True, help="kebab-case name for the figure")
    three.add_argument("--force", action="store_true", help="replace a different picture")
    three.set_defaults(run=place)

    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
