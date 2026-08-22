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
import cardid
import yamlio

# `research` carries no location: /research-gaps synthesised it from the web,
# so what identifies it is the gap it was created to close.
SOURCE_TYPES = {
    "folder": "path",
    "pdf": "path",
    "web": "url",
    "zotero": None,
    "research": None,
}
GOAL_KINDS = ("exam", "meeting", "interview", "self-study")
GOAL_DEPTHS = ("awareness", "working", "expert")
# A subtopic is either covered, wanted-but-uncovered, or unwanted. Absent means
# covered, so a catalog written before the goal-driven step stays valid.
# `content:` in a knowledge document says how much the extraction yielded. Only
# `sparse` is defined: it means the extraction succeeded and there is little
# there — a cover sheet, a form template — which is a different thing from a
# scan with no text layer, and the two used to be written identically (BUG-004).
CONTENT_STATES = ("sparse",)
CATALOG_STATUS = ("gap", "out of scope")
LOCAL_TYPES = {"folder", "pdf"}
ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*$")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# The attribute lines a catalog entry may carry, as `Key: value` in its body.
ATTRIBUTE = re.compile(r"^(Status|Parents|Also covers|Related|References|Goal):(.*)$")
# `Also covers: Access control (cards in cards/security.yaml)` — the parenthetical
# is prose for the reader, not part of the name.
PARENTHETICAL = re.compile(r"\s*\([^)]*\)\s*$")
LEADING_PARENTHETICAL = re.compile(r"^\([^)]*\)")
# `front`/`back` are Typst markup, and two of its rules are ones a model trained
# on markdown gets wrong (BUG-001). Both are *accepted* by the typesetter, so
# `lernkarten check` cannot see them and this is the only gate that can.
# `**bold**` is markdown: Typst reads it as two empty strong elements around
# unemphasised text, and only warns — on the success path, where build_pdf.py
# discards stderr.
MARKDOWN_BOLD = re.compile(r"(?<!\\)\*\*")
# A backslash is a line break only before whitespace. Before a markup character
# it escapes that character, so `line\*bold*` loses the break, gains a literal
# star and shifts every star after it.
ESCAPED_MARKUP = re.compile(r"\\([*_#@<>$`])")
# Front at most ~2 lines, back at most ~6. These do not depend on the grid: a
# denser grid renders the same card at a uniform scale (build_pdf.card_scale),
# so the two are proportionally identical and hold the same text. They were
# split per grid until BUG-007, when the A8 card was believed to be the A7 card
# with its width halved. Measured through the real command, a back first
# overflows at 500 characters at a7 and 520 at the scaled a8, so 400 is the
# conservative warning threshold for both.
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
    Returns (required topics, area names); check_catalog uses both for the drift
    warnings.
    """
    path = project / "goal.md"
    if not path.exists():
        return set(), set()

    where = "goal.md"
    report.count("goals")
    head, body = frontmatter(path.read_text(encoding="utf-8"))
    if head is None:
        report.error(where, "no YAML frontmatter — 'goal', 'kind', 'depth' and 'updated' go there")
        return set(), set()

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
    return required, set(areas)


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
        if kind == "research" and not entry.get("gap"):
            report.error(
                where,
                "'gap' missing for type research — it names the catalog subtopic "
                "this source was created to close",
            )
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
    """knowledge/<source-id>/*.md: one document per file, frontmatter intact.

    Returns the paths of the documents marked `content: sparse`, relative to the
    project — the catalog check needs them to see a subtopic that rests on
    nothing but cover sheets.
    """
    root = project / "knowledge"
    sparse = set()
    if not root.is_dir():
        return sparse
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
            content = head.get("content")
            if content is not None and str(content) not in CONTENT_STATES:
                report.error(
                    where,
                    f"'content: {content}' is not one of {', '.join(CONTENT_STATES)}",
                )
                content = None
            if head.get("pending"):
                report.warn(where, "still marked 'pending' — the text was never filled in")
            elif content == "sparse":
                # Silence, deliberately. The marker's whole job is to answer
                # "did the extraction work?" with yes, and warning about a
                # correctly marked document every run would replace a false
                # alarm with a permanent true one. Where thinness has a
                # consequence — a subtopic resting on nothing else — check_catalog
                # says so, because that is where the user can act on it.
                pass
            elif len(body.strip()) < 200:
                report.warn(where, "barely any text — did the extraction work?")
            if content == "sparse":
                sparse.add(path.resolve())
    return sparse


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


def catalog_names(line, known=()):
    """The names on a `Parents:`, `Related:` or `Also covers:` line.

    The separator is a comma and a name may contain one — "Governance, risk &
    compliance" is an ordinary thing to call a topic. So `known` is matched
    first, longest name before shorter, and only what is left over is split.
    Without it this splits on every comma, which tears such a name into pieces
    that match nothing and makes all five graph checks fire at once (BUG-005).

    Matching the known names rather than quoting them keeps the format
    unchanged, so every catalog written before this stays valid. What remains
    after the known names are taken out is still split and still reported as
    dangling — that is what C-1 and C-5 are for, and a fix that stopped
    splitting would silently retire them.

    An `Also covers:` entry carries `(cards in cards/x.yaml)` after the name so a
    reader knows where to look — that parenthetical is prose, and comparing names
    with it attached makes every reciprocity check fail on a catalog that follows
    the contract.
    """
    text = (line or "").strip()
    candidates = sorted({name for name in known if name}, key=len, reverse=True)
    names = []
    while text:
        name = next((c for c in candidates if _name_ends_here(text, c)), None)
        if name is None:
            head, _, text = text.partition(",")
            name = head
        else:
            text = LEADING_PARENTHETICAL.sub("", text[len(name) :].lstrip()).lstrip()
            text = text[1:] if text.startswith(",") else text
        name = PARENTHETICAL.sub("", name.strip()).strip()
        if name:
            names.append(name)
        text = text.strip()
    return names


def _name_ends_here(text, candidate):
    """Does `text` start with `candidate` as a whole name rather than a prefix?

    "Tides" must not match inside "Tides, currents & winds", so the character
    after the candidate has to end the name: nothing, the separator, or the
    `(cards in ...)` parenthetical.
    """
    if not text.startswith(candidate):
        return False
    rest = text[len(candidate) :].lstrip()
    return rest == "" or rest.startswith(",") or rest.startswith("(")


def check_graph(catalog, subtopics, report):
    """The catalog is a graph: containment is many-to-many, association is symmetric.

    Nothing here checks for cycles. Topics contain subtopics and the catalog stays
    two levels deep, so edges only ever run topic -> subtopic and the graph is
    bipartite. The invariants that matter are reciprocity ones, because the failure
    this format actually invites is half an edit.
    """
    where = "catalog/topics.md"
    topics = {entry.name for entry in catalog.topics}
    by_name = {entry.name: entry for entry in catalog.subtopics}

    borrowed = {}
    for entry in catalog.topics:
        for name in catalog_names(entry.attribute("also covers"), subtopics):
            borrowed.setdefault(entry.name, []).append(name)

    for entry in catalog.subtopics:
        parents = catalog_names(entry.attribute("parents"), topics)
        if parents:
            for parent in parents:  # C-1
                if parent not in topics:
                    report.error(
                        where,
                        f"subtopic '{entry.name}': 'Parents:' names '{parent}', "
                        "which is not a topic in this catalog",
                    )
            if parents[0] != entry.heading:  # C-2
                report.error(
                    where,
                    f"subtopic '{entry.name}': the primary parent is '{parents[0]}' "
                    f"but it sits under '{entry.heading}' — the first parent decides "
                    "which card file it lands in, so the two must agree",
                )
            for parent in parents[1:]:  # C-3
                if entry.name not in borrowed.get(parent, []):
                    report.error(
                        where,
                        f"subtopic '{entry.name}': '{parent}' is listed as a parent "
                        f"but '## {parent}' carries no 'Also covers:' line naming it",
                    )
        for name in catalog_names(entry.attribute("related"), subtopics):  # C-5
            if name not in subtopics:
                report.error(
                    where,
                    f"subtopic '{entry.name}': 'Related:' names '{name}', "
                    "which is not a subtopic of this catalog",
                )

    for topic, names in borrowed.items():  # C-4
        for name in names:
            entry = by_name.get(name)
            if entry is None:
                report.error(
                    where,
                    f"topic '{topic}': 'Also covers:' names '{name}', "
                    "which is not a subtopic of this catalog",
                )
            elif topic not in catalog_names(entry.attribute("parents"), topics):
                report.error(
                    where,
                    f"topic '{topic}': 'Also covers:' claims '{name}', but that "
                    "subtopic's own 'Parents:' does not list it back",
                )


def check_catalog(project, report, required=(), areas=(), sparse=()):
    """catalog/topics.md: topics with subtopics, descriptions and live links."""
    path = project / "catalog" / "topics.md"
    if not path.exists():
        return set(), {}

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

    marked = {}
    for entry in catalog.subtopics:
        status = entry.attribute("status")
        if status in CATALOG_STATUS:
            marked[entry.name] = status
        if status is not None and status not in CATALOG_STATUS:
            report.error(
                "catalog/topics.md",
                f"subtopic '{entry.name}': 'Status: {status}' is not one of "
                f"{', '.join(CATALOG_STATUS)}",
            )
        references = (entry.attribute("references") or "").strip()
        if (not references or references.lower() == "none") and status != "gap":
            report.error(
                "catalog/topics.md",
                f"subtopic '{entry.name}' has no references and is not marked "
                "'Status: gap' — a branch with nothing behind it is either a gap "
                "or a mistake",
            )
        if sparse and status is None:
            resolved = [
                (path.parent / target.split("#", 1)[0]).resolve()
                for target in LINK.findall(references)
                if not target.startswith(("http://", "https://", "mailto:", "#"))
            ]
            if resolved and all(document in sparse for document in resolved):
                # A warning rather than an error: it is a real subtopic backed by
                # real documents, and the user may know the cover sheet is all
                # there is. What they may not do is find out by accident.
                report.warn(
                    "catalog/topics.md",
                    f"subtopic '{entry.name}': every reference is marked "
                    "'content: sparse' — a cover sheet or a form template is not "
                    "enough to build cards from. Treat this as a gap, or ingest "
                    "the document itself",
                )

    check_graph(catalog, subtopics, report)

    for target in LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (path.parent / target.split("#", 1)[0]).resolve().exists():
            report.error("catalog/topics.md", f"reference points nowhere -> {target}")

    # Drift: goal.md asks for something the catalog never got. A warning, because
    # the fix is to re-run /catalog rather than to edit the file by hand.
    # FR-010: each area of the goal is its own top-level topic. A warning, not an
    # error — the catalog may simply predate the goal, and re-running fixes it.
    topic_keys = {topic_key(name) for name in seen}
    for area in areas:
        if topic_key(area) not in topic_keys:
            report.warn(
                "catalog/topics.md",
                f"goal.md area '{area}' is not a top-level topic (##) — each area "
                "becomes its own topic, so re-run /catalog",
            )

    names = [topic_key(n) for n in list(seen) + list(subtopics)]
    for topic in required:
        key = topic_key(topic)
        if not any(key in name or name in key for name in names):
            report.warn(
                "catalog/topics.md",
                f"goal.md requires '{topic}', which is nowhere in the catalog — re-run /catalog",
            )
    return subtopics, marked


def _check_id(card, where, index, ids_seen, report, strict):
    """The `id` key: absent is fine, present and wrong is not.

    Absent can never be an error — a deck written before ids existed is still a
    valid deck, and making it one would turn a new feature into a breaking
    change. Under `--strict` it is a nudge, because that gate judges what
    /cards produced and /cards is supposed to write one.

    Nothing here writes. This runs inside a CI gate, and a gate that repaired
    the tree would stop being able to fail (FR-013a).
    """
    if "id" not in card:
        if strict:
            report.warn(
                where,
                f"card {index}: no 'id' — /cards assigns one on write; "
                "`lernkarten id --backfill` fills in a deck written by hand",
            )
        return

    problem = cardid.validate(card["id"])
    if problem is not None:
        report.error(where, f"card {index}: unusable 'id' — {problem}")
        return

    key = cardid.normalise(card["id"])
    if key in ids_seen:
        first_where, first_index = ids_seen[key]
        report.error(
            where,
            f"card {index}: id {card['id']} is already used by card {first_index} "
            f"in {first_where} — an id has to name one card",
        )
        return
    ids_seen[key] = (where, index)


def check_cards(project, subtopics, report, marked=None, strict=False):
    """cards/*.yaml: the schema /print reads, plus the card-style limits.

    The limits follow the grid the deck declares, because "too long" is a
    question about a card of a particular width. `strict` only adds the nudge
    to declare one at all — a deck without the key is a valid A7 deck.
    """
    root = project / "cards"
    if not root.is_dir():
        return
    # Ids are unique across the project, not per file, so this outlives the loop.
    # Keyed by the normalised id: `a45dk` and `A45DK` are one id to a reader, so
    # they have to be one id here too (FR-004).
    ids_seen = {}
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
        # The grid is optional and absent means A7, so only a value that is
        # there and wrong is worth reporting. One deck is one size, which is
        # why the key belongs at the top level and nowhere else.
        if data.get("grid") is not None:
            try:
                build_pdf.parse_grid(data["grid"])
            except ValueError as e:
                report.error(where, str(e))
        elif strict:
            report.warn(
                where,
                "no 'grid' key — the deck prints at A7 (2x4), which is the right default "
                "but not a statement. /cards writes the size the deck was written for; "
                "add 'grid: a7' to say so",
            )
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
            _check_id(card, where, i, ids_seen, report, strict)
            if not card.get("subtopic"):
                report.warn(where, f"card {i}: no subtopic")
            elif subtopics and card["subtopic"] not in subtopics:
                report.warn(where, f"card {i}: subtopic '{card['subtopic']}' is not in the catalog")
            elif (marked or {}).get(card["subtopic"]):
                # A warning, not an error: /cards generates a marked subtopic when
                # the user names it explicitly, and that card is legitimate.
                status = marked[card["subtopic"]]
                report.warn(
                    where,
                    f"card {i}: subtopic '{card['subtopic']}' is marked "
                    f"'Status: {status}' in the catalog",
                )
            if len(front) > MAX_FRONT:
                report.warn(where, f"card {i}: front is long ({len(front)} characters)")
            if len(back) > MAX_BACK:
                report.warn(where, f"card {i}: back is long ({len(back)} characters)")
            if "grid" in card:
                report.error(
                    where,
                    f"card {i}: 'grid' belongs at the top level, not on a card — "
                    "one deck is one size",
                )
            if not card.get("source"):
                report.warn(where, f"card {i}: no source reference")
            check_markup(where, i, front, back, report)


def check_markup(where, i, front, back, report):
    """The two Typst rules a markdown habit gets wrong, on one card.

    Both are errors of meaning rather than of syntax: the typesetter accepts
    them and prints something else. So this is an error where the answer is
    unambiguous (`**` is never right) and a warning where it is not — `\\*` is
    also how you write a literal star, and refusing it would make escaping
    impossible.
    """
    for side, text in (("front", front), ("back", back)):
        if MARKDOWN_BOLD.search(text):
            report.error(
                where,
                f"card {i}: '{side}' uses '**' — that is markdown. Typst bolds with a "
                "single '*' ('*bold*', '_italic_'); '**...**' is two empty strong "
                "elements and prints unemphasised",
            )
        found = ESCAPED_MARKUP.search(text)
        if found:
            report.warn(
                where,
                f"card {i}: '{side}' has a backslash directly before '{found.group(1)}'. "
                "A backslash is a line break only before whitespace — here it escapes "
                f"the '{found.group(1)}' instead. Write '\\ ' if you meant the break; "
                "ignore this if you meant the literal character",
            )


def check(project, report, strict=False):
    required, areas = check_goal(project, report)
    source_ids = check_sources(project, report)
    sparse = check_knowledge(project, source_ids, report)
    subtopics, marked = check_catalog(project, report, required, areas, sparse)
    check_cards(project, subtopics, report, marked, strict=strict)
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

    report = check(project, Report(), strict=args.strict)
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
