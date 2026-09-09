#!/usr/bin/env python3
"""Builds the documentation site, and assembles it into the site the deploy uploads.

Run it without arguments:

    python3 scripts/build_docs.py

It runs Sphinx over docsite/ into _site/docs/, then copies in the three files
the site serves at its root — the landing page, the method page and the
printable card box — and writes _site/.nojekyll. The result is the same shape
GitHub Pages publishes, so what you open locally is what a reader gets, links
out of the documentation tree included.

Those three copies are also made by .github/workflows/pages.yml, in `cp` lines
this script deliberately does not replace. That duplication is the point: the
workflow is never executed by CI, so two tests read its text to know what the
site contains, while this script's copies are what make the local build a
preview rather than a fragment. Both write the same bytes and both are
idempotent.

Nothing here is on a user's path. This module imports no local module — it is
a leaf of Principle VI's graph, and tests/test_docsite_layout.py asserts that
importing Sphinx from anywhere bin/lernkarten can reach is a failure.
"""

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Served at the site root, beside the documentation tree rather than inside it.
# Kept in step with the `cp` block in .github/workflows/pages.yml — see the
# module docstring for why both exist.
ROOT_FILES = [
    (ROOT / "docs" / "index.html", "index.html"),
    (ROOT / "docs" / "leitner.html", "leitner.html"),
    (ROOT / "assets" / "card-box.pdf", "card-box.pdf"),
]


def require_sphinx():
    """The same courtesy scripts/deps.py and scripts/engine.py extend.

    The documentation toolchain is not in requirements-dev.txt on purpose, so
    arriving here without it is the normal first experience rather than a
    mistake, and it deserves the command rather than a traceback.
    """
    try:
        from sphinx.cmd.build import build_main
    except ImportError:
        sys.exit(
            "The documentation toolchain is not installed. Install it with:\n"
            "    python3 -m pip install -r requirements-docs.txt"
        )
    return build_main


def assemble(site):
    """Copies the files the site serves at its root, beside the built docs."""
    for source, name in ROOT_FILES:
        if not source.exists():
            sys.exit(f"{source.relative_to(ROOT)} is missing — the site would serve a 404")
        shutil.copy2(source, site / name)
    (site / ".nojekyll").touch()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--source",
        default=str(ROOT / "docsite"),
        help="the Sphinx source directory (default: docsite/)",
    )
    parser.add_argument(
        "--site",
        default=str(ROOT / "_site"),
        help="where to assemble the site (default: _site/)",
    )
    args = parser.parse_args(argv)

    build_main = require_sphinx()
    source, site = Path(args.source), Path(args.site)
    site.mkdir(parents=True, exist_ok=True)

    # -W: a warning is a failure. That is the whole point of choosing a
    # toolchain with a reference model — a link to something that does not
    # exist stops the build instead of shipping. --keep-going so one dead
    # reference reports all of them rather than the first.
    status = build_main(["-W", "--keep-going", str(source), str(site / "docs")])
    if status:
        return status

    assemble(site)
    print(f"Open {site / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
