#!/usr/bin/env python3
"""Docs gate: checks skill frontmatter and the internal links of the documentation.

Runs without arguments over the whole repo and is meant as a CI step:

    python3 scripts/check_docs.py

It verifies that:
  * every skill under skills/<name>/SKILL.md has YAML frontmatter with
    'name' (= folder name) and 'description' (mentioning its triggers),
  * every relative markdown link in the docs points at an existing file,
  * the files an open-source repo is expected to ship are present.
"""

import re
import sys
from pathlib import Path

import minyaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
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
    ".github/workflows/ci.yml",
]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CODEBLOCK = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


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
            head = minyaml.load(raw) or {}
        except minyaml.YamlError as e:
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


def markdown_files():
    files = sorted(ROOT.glob("*.md"))
    files += sorted((ROOT / "docs").glob("*.md"))
    files += sorted(SKILLS.glob("*/SKILL.md"))
    return files


def check_links(errors):
    for path in markdown_files():
        # Code blocks show format examples with placeholder paths — skip them
        text = CODEBLOCK.sub("", path.read_text(encoding="utf-8"))
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: dead link -> {target}")


def main():
    errors = []
    check_required_files(errors)
    check_skills(errors)
    check_links(errors)

    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        sys.exit(1)

    count = len(list(SKILLS.glob("*/SKILL.md")))
    print(f"OK: {count} skills, docs links and required files are fine.")


if __name__ == "__main__":
    main()
