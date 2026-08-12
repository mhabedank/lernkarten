#!/usr/bin/env python3
"""Renders the brand graphics under assets/brand/ to PNGs in assets/.

The banner, the pipeline strip, the social card and the example cards are
drawn in Typst, not by hand, so they use the same inks, the same faces and —
for the example cards — the very same card layout the printer gets. Run it
after changing anything under assets/brand/ or templates/:

    python3 scripts/render_brand.py
    python3 scripts/render_brand.py banner        # just one of them

This is a maintenance script, not part of the build. The PNGs it writes are
committed; nobody needs to run it to use the pipeline.
"""

import subprocess
import sys
from pathlib import Path

import engine

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "assets" / "brand"
TARGET = ROOT / "assets"
FONTS = ROOT / "assets" / "fonts"

# Pixels per inch per graphic. The social card is pinned to 72 so it comes out
# at exactly the 1200 x 630 that link previews want.
RESOLUTION = {"social-card": 72}
DEFAULT_RESOLUTION = 108


def render(source, binary):
    target = TARGET / f"{source.stem}.png"
    result = subprocess.run(
        [
            str(binary),
            "compile",
            "--ignore-system-fonts",
            "--font-path",
            str(FONTS),
            "--root",
            str(ROOT),
            "--ppi",
            str(RESOLUTION.get(source.stem, DEFAULT_RESOLUTION)),
            "--format",
            "png",
            str(source),
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: {source.name}", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        return None
    return target


def main():
    wanted = set(sys.argv[1:])
    sources = sorted(p for p in SOURCES.glob("*.typ") if p.stem != "common")
    if wanted:
        sources = [p for p in sources if p.stem in wanted]
        if not sources:
            sys.exit(f"ERROR: no graphic called {', '.join(sorted(wanted))} in {SOURCES}")

    try:
        binary, _ = engine.find()
    except engine.EngineError as e:
        sys.exit(f"ERROR: {e}")

    failed = False
    for source in sources:
        target = render(source, binary)
        if target is None:
            failed = True
            continue
        print(f"OK: {source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
