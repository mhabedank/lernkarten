#!/usr/bin/env python3
"""Copies the demo project into a scratch folder, ready to drive by hand.

The demo project under tests/fixtures/demo-project is a complete miniature
project about an invented archipelago: a learning goal, raw material, ingested
texts, a topic catalog and card files. This puts a copy somewhere you can break
it.

    python3 scripts/demo.py ~/lernkarten-demo          # everything
    python3 scripts/demo.py ~/lernkarten-demo --raw    # only sources + raw
    python3 scripts/demo.py ~/lernkarten-demo --force  # overwrite an old copy

With --raw the copy stops after the goal and the source register: knowledge/,
catalog/ and cards/ stay empty, so /ingest, /catalog and /cards have something
to do — and because goal.md comes along, /catalog has a goal to build from. That
is the version to use when testing the skills themselves; the full copy is for
testing /print and the build script.

The paths in sources.yaml are rewritten to absolute ones, so the copy works
from wherever you put it. The manual checklist is in docs/testing.md.
"""

import argparse
import shutil
import sys
from pathlib import Path

import make_testdata

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "demo-project"
GENERATED = ("knowledge", "catalog", "cards")
SKIP = {"broken", "README.md"}


def absolute_sources(text, raw_dir):
    """Rewrites the relative paths of the fixture register to absolute ones."""
    return text.replace("path: raw/", f"path: {raw_dir}/")


def copy(target, raw_only, force):
    if target.exists():
        if not force:
            raise SystemExit(f"ERROR: {target} exists — pass --force to overwrite it")
        if not (target / "sources.yaml").exists():
            raise SystemExit(
                f"ERROR: {target} exists but is no demo project (no sources.yaml) — "
                "refusing to overwrite a folder that is not ours"
            )
        shutil.rmtree(target)
    target.mkdir(parents=True)

    shutil.copytree(FIXTURE / "raw", target / "raw")
    # goal.md states the target rather than recording work done, so it comes
    # along even with --raw: /catalog needs it to build a goal-driven tree.
    shutil.copy2(FIXTURE / "goal.md", target / "goal.md")
    (target / "sources.yaml").write_text(
        absolute_sources((FIXTURE / "sources.yaml").read_text(encoding="utf-8"), target / "raw"),
        encoding="utf-8",
    )
    for name in GENERATED:
        if raw_only:
            (target / name).mkdir()
        else:
            shutil.copytree(FIXTURE / name, target / name)
    return target


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("target", help="where the copy goes, e.g. ~/lernkarten-demo")
    p.add_argument(
        "--raw",
        action="store_true",
        help="copy only the sources — leave the work for /ingest, /catalog and /cards",
    )
    p.add_argument("--force", action="store_true", help="overwrite an existing demo folder")
    args = p.parse_args()

    if not FIXTURE.is_dir():
        sys.exit(f"ERROR: the demo project is missing at {FIXTURE}")

    # The PDFs, the scan, the image and the DOCX are generated, not versioned.
    try:
        make_testdata.build()
    except make_testdata.BuildError as e:
        print(f"WARNING: no binary material ({e}) — text sources only.", file=sys.stderr)

    target = copy(Path(args.target).expanduser().resolve(), args.raw, args.force)

    print(f"Demo project in {target}")
    if args.raw:
        print("  Sources only — start a session there and run /ingest, /catalog, /cards.")
    else:
        print(f"  {len(list((target / 'cards').glob('*.yaml')))} card files ready to print:")
        print(f"    bin/lernkarten build {target}/cards/*.yaml -o {target}/output/cards.pdf")
    print("  The checklist is in docs/testing.md.")


if __name__ == "__main__":
    main()
