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

import build_pdf
import leitner
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


# --- A7 is no longer the default, and saying so is now a gate (BUG-010) ----
#
# The third check of this shape in this file, and the second one's comment
# already explains why: a --grid sweep enforced by a hand-written grep missed
# lines and shipped them. This time the sweep was the *default's own*, and it
# left seventeen sites calling A7 the default across nine files — including the
# --grid help string, which is what a user reads at the moment they care.
A7_TOKEN = re.compile(
    r"\bA7\b|`?\ba7\b`?|\b2\s*[x\u00d7]\s*4\b|\b105\s*[x\u00d7]\s*74\.25\b"
    r"|\b100\s*[x\u00d7]\s*71\.75\b|\b(?:8|eight)\s+(?:cards?|up)\b",
    re.I,
)
A8_TOKEN = re.compile(
    r"\bA8\b|`?\ba8\b`?|\b4\s*[x\u00d7]\s*4\b|\b74\.25\s*[x\u00d7]\s*52\.5\b"
    r"|\b71\.75\s*[x\u00d7]\s*50\b|\b(?:16|sixteen)\s+(?:cards?|up)\b",
    re.I,
)
DEFAULT_WORD = re.compile(r"\bdefaults?\b|\babsent\b|\bomitting\b|\bomit\b|\bsilent\b", re.I)
# Three places an A7 token may legitimately sit beside the word "default", read
# from the surrounding lines: the scale *reference* stays A7 forever and FR-002
# exists precisely to keep it separate from the default; history may say what
# the default used to be; and the mixed-build refusal is about decks
# disagreeing, not about what silence means.
NOT_A_DEFAULT_CLAIM = re.compile(
    r"\breference\b|\bwas\b|\buntil\b|since v|no longer|disagree|refus", re.I
)
# The fourth is the *margin*, which has a default of its own — and this one is
# read off the occurrence rather than the surroundings. README's card-box
# paragraph names the default margin one sentence before it calls A7 the
# default grid; a context-wide exemption swallows the second with the first.
DEFAULT_OF_SOMETHING_ELSE = re.compile(r"\s*(?:margin|sheet size|page size)", re.I)
CLAIM_WINDOW = 45  # how far apart the two may sit and still be one claim
JOIN = 1  # lines joined for detection: a claim may wrap
CONTEXT = 2  # lines either side that may carry the exemption

# The cutting instruction, which follows the grid the same way the sheet
# capacity does: one interior vertical cut at 2x4 and three at 4x4. Narrow on
# purpose — "3 vertical, 5 horizontal cut lines" in a table whose header names
# the grid is correct, and so is design.md's "*not* the A7 card cut down the
# middle", which is about orientation rather than about cutting.
CUT_INSTRUCTION = re.compile(r"down the middle", re.I)
CUT_COUNT = re.compile(r"three (?:across|horizontal)", re.I)

# What borderless printing gives you also follows the grid: `--margin 0` cuts to
# 105 x 74.25 at 2x4 and 74.25 x 52.5 at 4x4. Two sites said the A7 pair without
# saying which grid they meant, which reads as a promise about the default.
BORDERLESS = re.compile(r"--margin 0|\bborderless\b", re.I)


LEITNER_PAGE = ROOT / "docs" / "leitner.html"
# Anything shaped like one of our intervals. Wide enough to catch an invented
# "every 5 days" that the module never defined, which is the direction a
# one-way check would miss.
INTERVAL_SHAPE = re.compile(r"\b(?:daily|weekly|monthly|every \d+ (?:days?|weeks?|months?))\b")


def read_page():
    """docs/leitner.html as text. A seam, so a test can hand in a broken one."""
    return LEITNER_PAGE.read_text(encoding="utf-8") if LEITNER_PAGE.exists() else ""


def check_leitner_intervals(errors):
    """The method page and the printed dividers say the same words.

    Both render from `scripts/leitner.py`, but only the dividers do so
    mechanically — the page is written by hand, so it is the half that can
    drift. Checked in both directions: a missing interval leaves a compartment
    unexplained, and an invented one describes a divider nobody will ever hold.
    """
    if not LEITNER_PAGE.exists():
        errors.append(f"{LEITNER_PAGE.relative_to(ROOT)}: the method page is missing")
        return
    page = read_page()
    defined = {interval for intervals in leitner.INTERVALS.values() for interval in intervals}
    for interval in sorted(defined):
        if interval not in page:
            errors.append(
                f"docs/leitner.html: does not mention '{interval}', which a divider prints "
                "— the page and the paper have to agree"
            )
    for found in sorted(set(INTERVAL_SHAPE.findall(page))):
        if found not in defined:
            errors.append(
                f"docs/leitner.html: mentions '{found}', which scripts/leitner.py does not "
                "define — no divider will ever say it"
            )


CONSTITUTION = ROOT / ".specify" / "memory" / "constitution.md"
SCRIPTS = ROOT / "scripts"
# `A → b, c` or `A, B ← leaves…`; anything after an unbracketed `(` is prose.
GRAPH_LINE = re.compile(r"^([\w, ]+?)\s*(?:→|←)\s*(.*)$")


def real_graph():
    """Which local modules each `scripts/*.py` imports, read from the source."""
    modules = {p.stem for p in SCRIPTS.glob("*.py")}
    graph = {}
    for path in sorted(SCRIPTS.glob("*.py")):
        imported = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*(?:import|from) ([a-z_]+)", line)
            if match and match.group(1) in modules and match.group(1) != path.stem:
                imported.add(match.group(1))
        graph[path.stem] = imported
    return graph


def documented_graph():
    """The graph as Principle VI draws it, from the fenced block after it."""
    text = CONSTITUTION.read_text(encoding="utf-8")
    block = re.search(r"### VI\..*?```\n(.*?)```", text, re.S)
    if not block:
        return {}
    graph = {}
    for line in block.group(1).splitlines():
        line = re.sub(r"\(.*?\)", "", line).strip()
        match = GRAPH_LINE.match(line)
        if not match:
            continue
        targets = match.group(2)
        imports = (
            set()
            if not targets or "leaves" in targets
            else {t.strip() for t in targets.split(",") if t.strip()}
        )
        for module in (m.strip() for m in match.group(1).split(",")):
            graph[module] = imports
    return graph


def check_import_graph(errors):
    """Principle VI's graph has to be the graph the repository actually has.

    A rule that no longer traces to the codebase is stale and should be removed,
    not worked around — Principle VI says so about itself. Deriving the check
    from the source makes that a fact rather than a hope.
    """
    real, documented = real_graph(), documented_graph()
    for module in sorted(set(real) - set(documented)):
        errors.append(
            f"constitution.md: Principle VI's graph does not list scripts/{module}.py, which exists"
        )
    for module in sorted(set(documented) - set(real)):
        errors.append(f"constitution.md: Principle VI's graph lists {module}, which is gone")
    for module in sorted(set(real) & set(documented)):
        if real[module] != documented[module]:
            errors.append(
                f"constitution.md: Principle VI says {module} imports "
                f"{sorted(documented[module]) or 'nothing local'}, but it imports "
                f"{sorted(real[module]) or 'nothing local'}"
            )


def read_skill(name):
    """A skill's body. A seam, so a test can hand in one that says the wrong thing."""
    path = SKILLS / name / "SKILL.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def check_print_skill_relays_setup(errors):
    """`/print` has to pass the build's advisory on rather than swallow it.

    The build says once that the Leitner setup is unanswered; a user driving
    Claude never sees a terminal, so if the skill does not relay it the feature
    is unreachable for exactly the audience this project has.
    """
    if "lernkarten setup" not in read_skill("print"):
        errors.append(
            "skills/print/SKILL.md: does not name `lernkarten setup`, so the build's "
            "advisory has nowhere to go for a user who never opens a terminal"
        )


# The A-series name of the grid an absent `grid:` key means — read from the
# constant, never spelled out, because a literal here would go stale the same
# way the fourteen sites of BUG-010 did.
def default_grid_alias():
    key = {size: name for name, size in build_pdf.GRIDS.items()}[build_pdf.DEFAULT_GRID]
    return {target: alias for alias, target in build_pdf.GRID_ALIASES.items()}.get(key, key)


SCHEMA_GRID = re.compile(r"^grid:\s*([a-z0-9]+)", re.M)


def check_cards_skill_writes_the_default_grid(errors):
    """`/cards` writes a value into the user's file, so it cannot be a stale one.

    Every other claim this file gates is a sentence a reader can discount. This
    one is a literal the model copies into `cards/*.yaml`, where `--grid` at
    print time becomes the only way past it: the deck is pinned to a size the
    card box does not fit and the Leitner dividers refuse — the two problems the
    default was moved to solve (BUG-010, FR-010).
    """
    expected = default_grid_alias()
    for value in SCHEMA_GRID.findall(read_skill("cards")):
        if value != expected:
            errors.append(
                f"skills/cards/SKILL.md: the schema block hands the model 'grid: {value}', "
                f"but an absent key means '{expected}' — /cards would pin every new deck "
                "to the non-default size"
            )


def gated_files():
    """Everything the A7 claims live in — wider than markdown_files().

    Six of BUG-010's sites were a docstring, a comment, a Typst header and the
    --grid help string. A gate that cannot see the file is no better than the
    grep it replaces. `check_docs.py` itself is left out: it is the file that
    *defines* these claims in order to forbid them, the way a linter does not
    lint its own rule table.
    """
    return (
        markdown_files()
        + [f for f in sorted(SCRIPTS.glob("*.py")) if f.name != "check_docs.py"]
        + sorted((ROOT / "templates").glob("*.typ"))
    )


def windows(path):
    """(claim, context, lookahead, wide context, offsets, line number) per line.

    Detection joins a line with the next, because a claim wraps — "`a7` is the /
    default grid" spans a line break in README.md, and a line-scoped rule would
    make the fix depend on where the text happens to wrap. The exemption reads
    wider still: a comment says "the scale reference" a line or two above the
    sentence the exemption is for. `offsets` maps a position in the joined text
    back to the line it came from, so an error names the line a reader has to
    open rather than the one the window happened to start on.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, _ in enumerate(lines):
        joined = lines[i : i + 1 + JOIN]
        offsets, at = [], 0
        for n, line in enumerate(joined):
            offsets.append((at, i + 1 + n))
            at += len(line) + 1
        context = " ".join(lines[max(0, i - CONTEXT) : i + 1 + CONTEXT])
        # One line further than the claim, and only for DEFAULT_OF_SOMETHING_ELSE:
        # "the default / margin only" wraps, and without the lookahead the window
        # that starts one line earlier reports what the next window exempts.
        ahead = " ".join(lines[i : i + 2 + JOIN])
        # The borderless claim needs a wider read: card_scale()'s docstring
        # spends four lines on --margin 0 before it says the word "reference".
        wide = " ".join(lines[max(0, i - 2 * CONTEXT) : i + 1 + 2 * CONTEXT])
        yield " ".join(joined), context, ahead, wide, offsets, i + 1


def line_of(position, offsets):
    """Which source line a position in a joined window came from."""
    line = offsets[0][1]
    for start, number in offsets:
        if position >= start:
            line = number
    return line


def nearest_a7(text, word):
    """The A7 token within the window of `word`, if no A8 token stands between."""
    for token in A7_TOKEN.finditer(text):
        low, high = sorted([word.span(), token.span()])
        if low[1] > high[0] or high[0] - low[1] > CLAIM_WINDOW:
            continue
        if A8_TOKEN.search(text, low[1], high[0]):
            continue
        return token
    return None


def check_a7_is_not_the_default(errors):
    """No file outside specs/ may call A7 what an absent `grid:` key means.

    The default moved in v0.9.0 and its description did not (BUG-010, FR-011).
    """
    for path in gated_files():
        reported = set()
        for claim, context, ahead, _, offsets, _ in windows(path):
            if NOT_A_DEFAULT_CLAIM.search(context):
                continue
            for word in DEFAULT_WORD.finditer(claim):
                if DEFAULT_OF_SOMETHING_ELSE.match(ahead, word.end()):
                    continue
                token = nearest_a7(claim, word)
                if not token:
                    continue
                line = line_of(token.start(), offsets)
                if line not in reported:
                    reported.add(line)
                    errors.append(
                        f"{path.relative_to(ROOT)}:{line}: '{token.group()}' is given as "
                        f"the default near '{word.group()}' — an absent grid key means "
                        f"'{default_grid_alias()}' since v0.9.0"
                    )
                break


def check_cut_count(errors):
    """The cutting instruction follows the grid, the way the capacity does."""
    for path in gated_files():
        reported = set()
        for claim, _, _, _, offsets, _ in windows(path):
            instruction = CUT_INSTRUCTION.search(claim)
            if not instruction or not CUT_COUNT.search(claim) or QUALIFIED.search(claim):
                continue
            line = line_of(instruction.start(), offsets)
            if line not in reported:
                reported.add(line)
                errors.append(
                    f"{path.relative_to(ROOT)}:{line}: the cutting instruction gives one "
                    "vertical cut and three across as a fixed fact — that is the 2x4 "
                    "sheet, and the cut count follows --grid, so name the grid"
                )


def check_borderless_size(errors):
    """`--margin 0` gives an A7 card only at 2x4; say so or say nothing."""
    for path in gated_files():
        reported = set()
        for claim, _, _, wide, offsets, _ in windows(path):
            edge = BORDERLESS.search(claim)
            if not edge or A8_TOKEN.search(claim) or NOT_A_DEFAULT_CLAIM.search(wide):
                continue
            token = nearest_a7(claim, edge)
            if not token:
                continue
            line = line_of(token.start(), offsets)
            if line not in reported:
                reported.add(line)
                errors.append(
                    f"{path.relative_to(ROOT)}:{line}: '{token.group()}' is given as what "
                    "borderless printing produces — that is the 2x4 card, and --margin 0 "
                    f"follows --grid, so name the grid (the default is "
                    f"'{default_grid_alias()}')"
                )


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
    check_cards_skill_writes_the_default_grid(errors)
    check_a7_is_not_the_default(errors)
    check_cut_count(errors)
    check_borderless_size(errors)
    check_leitner_intervals(errors)
    check_print_skill_relays_setup(errors)
    check_import_graph(errors)
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
