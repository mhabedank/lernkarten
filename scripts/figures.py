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

# Kept in step with build_pdf.IMAGE_FORMATS by the test suite rather than by an
# import: this module must not pull the PDF build in just to name six strings.
IMAGE_FORMATS = ("png", "jpg", "jpeg", "gif", "svg", "webp")
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
    for number, page in enumerate(document, start=1):
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


def fetch(args):
    """One picture from a URL, with urllib — no dependency for what is in the box."""
    origin = urllib.parse.urlparse(args.url)

    class SameHostOnly(urllib.request.HTTPRedirectHandler):
        """A source is a place the user chose; a redirect is not that choice."""

        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if urllib.parse.urlparse(newurl).netloc != origin.netloc:
                raise urllib.error.HTTPError(newurl, code, f"redirects to {newurl}", headers, fp)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(SameHostOnly)
    name = Path(urllib.parse.unquote(origin.path)).name or "picture"
    if Path(name).suffix.lower().lstrip(".") not in IMAGE_FORMATS:
        fail(f"{args.url}: not a picture this engine reads ({', '.join(IMAGE_FORMATS)})")
        return 1
    try:
        # No credentials, ever: only what the page would hand anyone.
        with opener.open(urllib.request.Request(args.url), timeout=30) as response:
            data = response.read()
    except Exception as e:  # noqa: BLE001 — one line out, whatever went wrong
        fail(f"{args.url}: {e}")
        return 1

    target = staging_dir(args.project, args.source_id) / name
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
    if suffix.lstrip(".") not in IMAGE_FORMATS:
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
