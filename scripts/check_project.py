#!/usr/bin/env python3
"""Project gate: checks a lernkarten project against the documented contracts.

Four of the five steps are done by Claude, not by a script — so what can be
tested is their output. This walks a project folder and verifies that the files
the skills write have the shape the next step expects:

    python3 scripts/check_project.py                       # the current folder
    python3 scripts/check_project.py ~/flashcards --strict  # warnings fail too

Checked: the source register, the frontmatter of every ingested text, the
structure and references of the topic catalog, and the schema of the card
files. What it cannot check is whether the content is any good — that is what
reading a printed card is for.

Errors mean "the next step will trip over this" and end in exit code 1;
warnings are style questions and only fail with --strict.
"""

import argparse
import re
import sys
from pathlib import Path

import build_pdf
import yamlio

SOURCE_TYPES = {"folder": "path", "pdf": "path", "web": "url", "zotero": None}
LOCAL_TYPES = {"folder", "pdf"}
ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*$")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Front at most ~2 lines, back at most ~6 — the card is only 100 x 72 mm.
MAX_FRONT = 120
MAX_BACK = 400


class Report:
    """Errors, warnings and the counts worth printing at the end."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.counts = {}

    def error(self, where, message):
        self.errors.append(f"{where}: {message}")

    def warn(self, where, message):
        self.warnings.append(f"{where}: {message}")

    def count(self, what, n=1):
        self.counts[what] = self.counts.get(what, 0) + n


def read_yaml(path, report):
    """Parses a YAML file, reporting instead of raising. None on failure."""
    try:
        return yamlio.load(path.read_text(encoding="utf-8"))
    except (yamlio.YamlError, OSError) as e:
        report.error(path.name, str(e))
        return None


def frontmatter(text):
    """The frontmatter block of a knowledge file as a dict, and the body."""
    if not text.startswith("---\n"):
        return None, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return None, text
    try:
        return yamlio.load(parts[1]) or {}, parts[2]
    except yamlio.YamlError:
        return None, parts[2]


# --- the four artifacts ---------------------------------------------------


def check_sources(project, report):
    """sources.yaml: unique ids, known types, the required field per type."""
    path = project / "sources.yaml"
    if not path.exists():
        report.warn("sources.yaml", "no source register yet — /sources writes it")
        return set()

    data = read_yaml(path, report)
    if data is None:
        return set()
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        report.error("sources.yaml", "expected a mapping with the key 'sources'")
        return set()

    ids = set()
    for entry in data["sources"]:
        if not isinstance(entry, dict):
            report.error("sources.yaml", f"entry is not a mapping: {entry!r}")
            continue
        source_id = str(entry.get("id") or "")
        where = f"sources.yaml [{source_id or '?'}]"
        if not source_id:
            report.error(where, "'id' missing")
        elif not ID.match(source_id):
            report.error(where, f"'{source_id}' is not a kebab-case id")
        elif source_id in ids:
            report.error(where, "duplicate id")
        else:
            ids.add(source_id)

        kind = entry.get("type")
        if kind not in SOURCE_TYPES:
            report.error(where, f"unknown type {kind!r} — one of {', '.join(SOURCE_TYPES)}")
            continue
        field = SOURCE_TYPES[kind]
        if field and not entry.get(field):
            report.error(where, f"'{field}' missing for type {kind}")
            continue
        if kind in LOCAL_TYPES:
            target = Path(str(entry[field])).expanduser()
            if not target.is_absolute():
                target = project / target
            if not target.exists():
                report.warn(where, f"{entry[field]} does not exist (yet)")
        report.count("sources")
    return ids


def check_knowledge(project, source_ids, report):
    """knowledge/<source-id>/*.md: one document per file, frontmatter intact."""
    root = project / "knowledge"
    if not root.is_dir():
        return
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        if source_ids and folder.name not in source_ids:
            report.error(
                f"knowledge/{folder.name}",
                "no source with this id — the folder is named after the source it came from",
            )
        for path in sorted(folder.glob("*.md")):
            where = f"knowledge/{folder.name}/{path.name}"
            report.count("documents")
            head, body = frontmatter(path.read_text(encoding="utf-8"))
            if head is None:
                report.error(where, "no readable frontmatter block")
                continue
            if head.get("source") != folder.name:
                report.error(where, f"'source: {head.get('source')}' is not '{folder.name}'")
            if not head.get("document"):
                report.error(where, "'document' missing")
            if not (head.get("path") or head.get("url")):
                report.error(where, "neither 'path' nor 'url' — where did this come from?")
            ingested = str(head.get("ingested") or "")
            if not DATE.match(ingested):
                shown = ingested or "missing"
                report.error(where, f"'ingested' is not a date (YYYY-MM-DD): {shown}")
            if head.get("pending"):
                report.warn(where, "still marked 'pending' — the text was never filled in")
            elif len(body.strip()) < 200:
                report.warn(where, "barely any text — did the extraction work?")


def check_catalog(project, report):
    """catalog/topics.md: topics with subtopics, descriptions and live links."""
    path = project / "catalog" / "topics.md"
    if not path.exists():
        return set()

    text = path.read_text(encoding="utf-8")
    subtopics = set()
    topic = None
    seen = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            topic = line[3:].strip()
            seen[topic] = []
            report.count("topics")
        elif line.startswith("### "):
            name = line[4:].strip()
            if topic is None:
                report.error("catalog/topics.md", f"subtopic '{name}' before any topic (##)")
            else:
                seen[topic].append(name)
            subtopics.add(name)
            report.count("subtopics")

    if not seen:
        report.error("catalog/topics.md", "no topic (##) found")
    for name, children in seen.items():
        if not children:
            report.warn("catalog/topics.md", f"topic '{name}' has no subtopic (###)")

    for target in LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (path.parent / target.split("#", 1)[0]).resolve().exists():
            report.error("catalog/topics.md", f"reference points nowhere -> {target}")
    return subtopics


def check_cards(project, subtopics, report):
    """cards/*.yaml: the schema /print reads, plus the card-style limits."""
    root = project / "cards"
    if not root.is_dir():
        return
    for path in sorted(root.glob("*.yaml")):
        where = f"cards/{path.name}"
        data = read_yaml(path, report)
        if data is None:
            continue
        if not isinstance(data, dict) or "cards" not in data:
            report.error(where, "expected a mapping with the keys 'topic' and 'cards'")
            continue
        if not data.get("topic"):
            report.warn(where, "'topic' missing — the file name is used instead")
        if not data.get("language"):
            report.warn(where, "'language' missing — printing falls back to english")
        else:
            try:
                build_pdf.resolve_language(data["language"])
            except ValueError as e:
                report.error(where, str(e))

        fronts = {}
        for i, card in enumerate(data["cards"] or [], start=1):
            report.count("cards")
            if not isinstance(card, dict) or "front" not in card or "back" not in card:
                report.error(where, f"card {i}: 'front' and 'back' are required")
                continue
            front, back = str(card["front"]), str(card["back"])
            if front.strip().lower() in fronts:
                report.error(where, f"card {i}: same front as card {fronts[front.strip().lower()]}")
            else:
                fronts[front.strip().lower()] = i
            if not card.get("subtopic"):
                report.warn(where, f"card {i}: no subtopic")
            elif subtopics and card["subtopic"] not in subtopics:
                report.warn(where, f"card {i}: subtopic '{card['subtopic']}' is not in the catalog")
            if len(front) > MAX_FRONT:
                report.warn(where, f"card {i}: front is long ({len(front)} characters)")
            if len(back) > MAX_BACK:
                report.warn(where, f"card {i}: back is long ({len(back)} characters)")
            if not card.get("source"):
                report.warn(where, f"card {i}: no source reference")


def check(project, report):
    source_ids = check_sources(project, report)
    check_knowledge(project, source_ids, report)
    subtopics = check_catalog(project, report)
    check_cards(project, subtopics, report)
    return report


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("project", nargs="?", default=".", help="the project folder (default: .)")
    p.add_argument("--strict", action="store_true", help="let warnings fail as well")
    args = p.parse_args()

    project = Path(args.project).expanduser()
    if not project.is_dir():
        sys.exit(f"ERROR: {project} is not a folder")

    report = check(project, Report())
    for w in report.warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in report.errors:
        print(f"ERROR: {e}", file=sys.stderr)

    summary = ", ".join(f"{n} {what}" for what, n in report.counts.items()) or "nothing found"
    if report.errors:
        print(f"{len(report.errors)} error(s) in {project} ({summary}).", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {project} is consistent ({summary}, {len(report.warnings)} warning(s)).")
    if report.warnings and args.strict:
        sys.exit("--strict: the warnings above count as failures")


if __name__ == "__main__":
    main()
