#!/usr/bin/env python3
"""Docs gate: checks skill frontmatter and the internal links of the documentation.

Runs without arguments over the whole repo and is meant as a CI step:

    python3 scripts/check_docs.py

It verifies that:
  * every skill under skills/<name>/SKILL.md has YAML frontmatter with
    'name' (= folder name) and 'description' (mentioning its triggers),
  * the three files carrying a version agree on it,
  * every relative markdown link in the docs points at an existing file,
  * the files an open-source repo is expected to ship are present.
"""

import json
import re
import sys
import tomllib
from pathlib import Path

import yamlio

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

# Every skill description has to tie itself to this plugin, not only name its
# triggers: the plugin ships into environments this repo cannot inspect, where
# `/catalog` or `/research` may already mean something else.
DOMAIN_WORD = "flashcard"
REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CLAUDE.md",
    "sources.example.yaml",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "templates/cards.typ",
    "templates/card.typ",
    "bin/lernkarten",
    "assets/logo.svg",
    "assets/logo-mono.svg",
    "assets/fonts/README.md",
    "docs/workflow.md",
    "docs/design.md",
    "docs/index.html",
    "docs/testing.md",
    # The test data every test runs against. Its register is let back in past
    # .gitignore by hand, so it is worth guarding that it is still there.
    "tests/fixtures/demo-project/sources.yaml",
    "tests/fixtures/demo-project/generators/handbook.typ",
    "tests/fixtures/zotero/library.json",
    ".github/workflows/ci.yml",
]
# A release bumps a version in three places by hand. Nothing compared them
# until now, so pyproject.toml sat at 0.2.0 from the initial commit through
# v0.3.0 while both manifests moved on. plugin.json is the reference: it is
# the manifest Claude Code actually reads when the plugin is installed.
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
PLUGIN_NAME = "lernkarten"
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CODEBLOCK = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
# `![Figure: caption](figures/<id>/<slug>.png)` is a path to *write*, not one
# that exists. Docs have to be able to show markdown syntax without being it,
# which is the same reason code blocks are skipped.
INLINE_CODE = re.compile(r"`[^`\n]*`")


def check_required_files(errors):
    for name in REQUIRED_FILES:
        if not (ROOT / name).exists():
            errors.append(f"required file missing: {name}")


def check_skills(errors):
    folders = sorted(p for p in SKILLS.iterdir() if p.is_dir()) if SKILLS.is_dir() else []
    if not folders:
        errors.append(f"no skills found under {SKILLS.relative_to(ROOT)}")
        return

    for folder in folders:
        path = folder / "SKILL.md"
        if not path.exists():
            errors.append(f"{folder.relative_to(ROOT)}: SKILL.md missing")
            continue

        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            errors.append(f"{path.relative_to(ROOT)}: no YAML frontmatter")
            continue

        raw = text.split("---\n", 2)[1]
        try:
            head = yamlio.load(raw) or {}
        except yamlio.YamlError as e:
            errors.append(f"{path.relative_to(ROOT)}: frontmatter is not valid YAML: {e}")
            continue

        if head.get("name") != folder.name:
            errors.append(
                f"{path.relative_to(ROOT)}: 'name: {head.get('name')}' "
                f"does not match the folder '{folder.name}'"
            )
        description = str(head.get("description") or "")
        if len(description) < 20:
            errors.append(f"{path.relative_to(ROOT)}: 'description' missing or too short")
        elif "Triggers" not in description:
            errors.append(
                f"{path.relative_to(ROOT)}: 'description' names no triggers — "
                "without them Claude Code finds the skill less reliably"
            )
        elif DOMAIN_WORD not in description.lower():
            errors.append(
                f"{path.relative_to(ROOT)}: 'description' names no domain word — "
                f"say '{DOMAIN_WORD}s' somewhere, or a generic trigger like /catalog "
                "resolves to whichever other installed skill claimed it first"
            )


def read_versions(errors):
    """{path: version} for each of the three files, skipping any we cannot read."""
    found = {}

    path = ROOT / "pyproject.toml"
    try:
        found["pyproject.toml"] = tomllib.loads(path.read_text(encoding="utf-8"))["project"][
            "version"
        ]
    except (OSError, tomllib.TOMLDecodeError, KeyError) as e:
        errors.append(f"pyproject.toml: no [project] version to read ({e})")

    path = ROOT / PLUGIN_MANIFEST
    try:
        found[PLUGIN_MANIFEST] = json.loads(path.read_text(encoding="utf-8"))["version"]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        errors.append(f"{PLUGIN_MANIFEST}: no version to read ({e})")

    name = ".claude-plugin/marketplace.json"
    path = ROOT / name
    try:
        plugins = json.loads(path.read_text(encoding="utf-8"))["plugins"]
        entry = next(p for p in plugins if p.get("name") == PLUGIN_NAME)
        found[name] = entry["version"]
    except (OSError, json.JSONDecodeError, KeyError, StopIteration) as e:
        errors.append(f"{name}: no version for '{PLUGIN_NAME}' to read ({e})")

    return found


def check_versions(errors):
    found = read_versions(errors)
    expected = found.get(PLUGIN_MANIFEST)
    if expected is None:
        return

    for name, version in found.items():
        if name != PLUGIN_MANIFEST and version != expected:
            errors.append(
                f"{name}: version {version} does not match {PLUGIN_MANIFEST} "
                f"({expected}) — a release bumps all three together"
            )


def markdown_files():
    files = sorted(ROOT.glob("*.md"))
    files += sorted((ROOT / "docs").glob("*.md"))
    files += sorted(SKILLS.glob("*/SKILL.md"))
    return files


def check_links(errors):
    for path in markdown_files():
        # Code shows format examples with placeholder paths — skip it, fenced
        # and inline alike.
        text = CODEBLOCK.sub("", path.read_text(encoding="utf-8"))
        text = INLINE_CODE.sub("", text)
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: dead link -> {target}")


# The A4 sheet held eight cards until --grid made the number a setting. A doc
# still stating it as a fixed property of the sheet is wrong rather than merely
# stale, so it is a gate and not a habit: the sweep that introduced --grid was
# enforced by a hand-written grep, which missed "A4, 8 cards per page" in the
# /print description and "puts 8 cards on an A4 page" in the README, and both
# shipped. The number is fine when something nearby ties it to a grid.
SHEET_CAPACITY = re.compile(
    r"\b(?:8|eight|16|sixteen)\s+cards?\s+(?:per|on|to|a)\s+(?:an?\s+)?"
    r"(?:A4\s+)?(?:sheet|page|A4)\b",
    re.I,
)
QUALIFIED = re.compile(r"grid|a7|a8|2\s*[x\u00d7]\s*4|4\s*[x\u00d7]\s*4", re.I)


def check_sheet_capacity(errors):
    for path in markdown_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            claim = SHEET_CAPACITY.search(line)
            if claim and not QUALIFIED.search(line):
                errors.append(
                    f"{path.relative_to(ROOT)}: '{claim.group().strip()}' states the sheet "
                    "capacity as a fixed fact — it follows --grid, so name the grid"
                )


# 'duplex, flip on long edge' was the way to print until --sides existed; now
# it is one of two, and a doc still giving it as *the* instruction sends a
# reader with a one-sided printer to a stack of wasted paper. Same shape as
# check_sheet_capacity above and there for the same reason: the --grid sweep
# was enforced by a hand-written grep, missed two lines, and shipped them. The
# word is fine wherever the sentence says which order it is talking about.
PRINT_ORDER = re.compile(r"\bduplex\b|\bflip on (?:the )?long edge\b", re.I)
NAMES_THE_ORDER = re.compile(r"simplex|one[- ]sided|--sides|two[- ]pass|both orders", re.I)


def check_print_order(errors):
    # Scoped to the paragraph, not the line: an instruction spans a paragraph,
    # unlike a capacity claim, and a line-scoped rule would make the fix depend
    # on where the text happens to wrap.
    for path in markdown_files():
        for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
            claim = PRINT_ORDER.search(block)
            if claim and not NAMES_THE_ORDER.search(block):
                errors.append(
                    f"{path.relative_to(ROOT)}: '{claim.group().strip()}' gives one print "
                    "order as the only instruction — it follows --sides, so name the order"
                )


def main():
    errors = []
    check_required_files(errors)
    check_versions(errors)
    check_skills(errors)
    check_links(errors)
    check_sheet_capacity(errors)
    check_print_order(errors)

    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        sys.exit(1)

    count = len(list(SKILLS.glob("*/SKILL.md")))
    version = read_versions([]).get(PLUGIN_MANIFEST, "?")
    print(f"OK: {count} skills, version {version}, docs links and required files are fine.")


if __name__ == "__main__":
    main()
