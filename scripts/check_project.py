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
import dataclasses
import re
import sys
from pathlib import Path

import build_pdf
import yamlio

SOURCE_TYPES = {"folder": "path", "pdf": "path", "web": "url", "zotero": None}
GOAL_KINDS = ("exam", "meeting", "interview", "self-study")
GOAL_DEPTHS = ("awareness", "working", "expert")
LOCAL_TYPES = {"folder", "pdf"}
ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*$")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# The attribute lines a catalog entry may carry, as `Key: value` in its body.
ATTRIBUTE = re.compile(r"^(Status|Parents|Also covers|Related|References|Goal):(.*)$")
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


def topic_key(text):
    """A required topic and a catalog heading, reduced to something comparable.

    Deliberately loose. A goal bullet is prose ("Rhythm of the tide, and how far
    high water shifts") while the heading is a label ("Rhythm of the tide"), so
    exact equality would report drift on a correct catalog. This is a warning
    telling the user to re-run /catalog; one that cries wolf gets ignored.
    """
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def parse_goal(text):
    """The areas of `## Required topics` as {area: [topic, ...]}, in order."""
    areas = {}
    current = None
    in_required = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            in_required = line[3:].strip().lower() == "required topics"
            current = None
        elif in_required and line.startswith("### "):
            current = line[4:].strip()
            areas.setdefault(current, [])
        elif in_required and current and line.startswith("- "):
            areas[current].append(line[2:].strip())
    return areas


def check_goal(project, report):
    """goal.md: what the user is trying to learn, and the criterion for everything else.

    Absent is valid and means today's behaviour — the whole feature is opt-in.
    Returns the required topics, which check_catalog uses for the drift warning.
    """
    path = project / "goal.md"
    if not path.exists():
        return set()

    where = "goal.md"
    report.count("goals")
    head, body = frontmatter(path.read_text(encoding="utf-8"))
    if head is None:
        report.error(where, "no YAML frontmatter — 'goal', 'kind', 'depth' and 'updated' go there")
        return set()

    for key in ("goal", "kind", "depth", "updated"):
        if not head.get(key):
            report.error(where, f"'{key}' missing — the frontmatter needs it")

    kind = head.get("kind")
    if kind and kind not in GOAL_KINDS:
        report.error(where, f"'kind: {kind}' is not one of {', '.join(GOAL_KINDS)}")

    depth = head.get("depth")
    if depth and depth not in GOAL_DEPTHS:
        report.error(where, f"'depth: {depth}' is not one of {', '.join(GOAL_DEPTHS)}")

    updated = head.get("updated")
    if updated and not DATE.match(str(updated)):
        report.error(where, f"'updated' is not a date (YYYY-MM-DD): {updated}")

    areas = parse_goal(body)
    if not areas:
        report.error(
            where, "'## Required topics' holds no area (###) — nothing to build a catalog from"
        )
    required = set()
    for area, topics in areas.items():
        if not topics:
            report.error(where, f"area '{area}' lists no required topic")
        required.update(topics)
    return required


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


@dataclasses.dataclass
class Entry:
    """One `##` topic or `###` subtopic, with the attribute lines in its body."""

    kind: str  # "topic" (##) or "subtopic" (###)
    name: str
    heading: str | None  # for a subtopic, the topic it sits under — None if orphaned
    attributes: dict

    def attribute(self, key):
        return self.attributes.get(key.lower())


@dataclasses.dataclass
class Catalog:
    """`catalog/topics.md` as a structure, in the order it was written."""

    entries: list

    @property
    def topics(self):
        return [e for e in self.entries if e.kind == "topic"]

    @property
    def subtopics(self):
        return [e for e in self.entries if e.kind == "subtopic"]


def parse_catalog(text):
    """Read the catalog into a structure. Reports nothing — that is the caller's job.

    Kept pure and separate so the rules that read `Status:`, `Parents:`,
    `Also covers:` and `Related:` have something to hang on, and so the parsing
    can be unit-tested without going through a whole project folder.
    """
    entries = []
    current = None  # the entry whose body we are inside
    heading = None  # the most recent `##`, which a subtopic belongs under

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("### "):
            current = Entry(kind="subtopic", name=line[4:].strip(), heading=heading, attributes={})
            entries.append(current)
        elif line.startswith("## "):
            heading = line[3:].strip()
            current = Entry(kind="topic", name=heading, heading=None, attributes={})
            entries.append(current)
        elif current is not None:
            match = ATTRIBUTE.match(line)
            if match:
                key, value = match.group(1).lower(), match.group(2).strip()
                # A repeated key keeps the first: References: may wrap onto a
                # second line, and that continuation is not a new attribute.
                current.attributes.setdefault(key, value)

    return Catalog(entries=entries)


def check_catalog(project, report, required=()):
    """catalog/topics.md: topics with subtopics, descriptions and live links."""
    path = project / "catalog" / "topics.md"
    if not path.exists():
        return set()

    text = path.read_text(encoding="utf-8")
    catalog = parse_catalog(text)
    subtopics = set()
    seen = {}
    for entry in catalog.entries:
        if entry.kind == "topic":
            # A repeated `## name` starts the list again, as the line scan did.
            seen[entry.name] = []
            report.count("topics")
            continue
        if entry.heading is None or entry.heading not in seen:
            report.error("catalog/topics.md", f"subtopic '{entry.name}' before any topic (##)")
        else:
            seen[entry.heading].append(entry.name)
        subtopics.add(entry.name)
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

    # Drift: goal.md asks for something the catalog never got. A warning, because
    # the fix is to re-run /catalog rather than to edit the file by hand.
    names = [topic_key(n) for n in list(seen) + list(subtopics)]
    for topic in required:
        key = topic_key(topic)
        if not any(key in name or name in key for name in names):
            report.warn(
                "catalog/topics.md",
                f"goal.md requires '{topic}', which is nowhere in the catalog — re-run /catalog",
            )
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
    required = check_goal(project, report)
    source_ids = check_sources(project, report)
    check_knowledge(project, source_ids, report)
    subtopics = check_catalog(project, report, required)
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
