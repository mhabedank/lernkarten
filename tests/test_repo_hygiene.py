"""Guards what a release must and must not ship.

Two kinds of claim live here. The first is that the repo stays
subject-agnostic: only the tools are versioned, while sources, ingested texts,
the catalog and the generated cards belong to the user and stay local. The
second is about the text of the versioned documentation — that it does not
still promise five commands, and that the README points a reader at the live
landing page while keeping the contributor's reference to the file.

The second kind is why this module is not called `test_no_user_content`. How a
page is *built* is a different question and lives in `test_landing_page.py`.
"""

import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import make_testdata  # noqa: E402
import yamlio  # noqa: E402

# Everything below these paths is user content — except for the exceptions.
BLOCKED = ("knowledge/", "catalog/", "cards/", "figures/", "output/")
ALLOWED = {
    "knowledge/.gitkeep",
    "catalog/.gitkeep",
    "cards/.gitkeep",
    "figures/.gitkeep",
    "cards/example.yaml",
}

# The landing page, and the two strings that pin where the README links it.
# Neither anchor is prose: a badge URL and a committed file path move only when
# somebody means to move them, while a sentence can be rewritten by any copy
# edit. See specs/003-readme-landing-link/research.md R2.
LANDING_URL = "https://mhabedank.github.io/lernkarten/"
BADGE_ANCHOR = "Claude_Code-plugin"
SCREENSHOT_ANCHOR = "assets/example-cards.png"
# The same page as a file rather than a URL — what a contributor edits.
LANDING_SOURCE = "docs/index.html"


def versioned_files():
    """Every path git tracks, verbatim — see `ignored()` for why that is fiddly."""
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("not a git repository")
    lines = result.stdout.decode("utf-8").splitlines()
    return [line for line in lines if line]


def test_versioned_files_are_reported_unquoted():
    """A quoted name would slip straight past the guard below.

    git wraps anything non-ASCII in quotes and octal escapes, and
    `"knowledge/\\303\\274ber.md"` starts with a quote rather than with
    `knowledge/` — so the check for user content would wave through exactly the
    file it exists to catch. The demo project ships a path with an umlaut, so
    this is not hypothetical.
    """
    files = versioned_files()
    assert any(not f.isascii() for f in files), (
        "no non-ASCII path is versioned any more — this test has stopped proving anything"
    )
    assert not [f for f in files if f.startswith('"')], "git quoted a path instead of reporting it"


def test_no_user_content_in_the_repo():
    intruders = [f for f in versioned_files() if f.startswith(BLOCKED) and f not in ALLOWED]
    assert not intruders, (
        f"user content must not be versioned (see .gitignore and CONTRIBUTING.md): {intruders}"
    )


def test_no_personal_source_register_in_the_repo():
    assert "sources.yaml" not in versioned_files(), (
        "sources.yaml holds the user's sources — only sources.example.yaml is versioned"
    )


def test_no_personal_learning_goal_in_the_repo():
    """`goal.md` states what its author is studying — the fifth user-content format."""
    intruders = [
        f
        for f in versioned_files()
        if Path(f).name == "goal.md" and not f.startswith("tests/fixtures/")
    ]
    assert not intruders, f"goal.md holds the user's learning goal and stays local: {intruders}"


def test_example_source_register_is_valid():
    data = yamlio.load((ROOT / "sources.example.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict) and data.get("sources"), "key 'sources' missing"

    ids = set()
    required_field = {"folder": "path", "pdf": "path", "web": "url", "zotero": None}
    for entry in data["sources"]:
        assert entry.get("id"), f"entry without id: {entry}"
        assert entry["id"] not in ids, f"duplicate id: {entry['id']}"
        ids.add(entry["id"])
        assert entry.get("type") in required_field, f"unknown type: {entry.get('type')}"
        field = required_field[entry["type"]]
        assert field is None or entry.get(field), f"{entry['id']}: '{field}' missing"


def ignored(paths):
    """The subset of `paths` that .gitignore keeps out of the repo.

    Three things have to be got right, or the answer cannot be compared with
    the question:

    * `core.quotePath=false`, or git wraps anything non-ASCII in quotes and
      octal escapes — and on Windows, where the separator is a backslash, that
      is every single path.
    * bytes rather than `text=True`, because a text-mode stdin translates the
      newline between paths into CRLF on Windows and git then reads the
      carriage return as part of the file name.
    * split on line breaks, not on whitespace, so a name with a space in it
      survives.
    """
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "check-ignore", "--stdin"],
        cwd=ROOT,
        input="\n".join(paths).encode("utf-8"),
        capture_output=True,
        check=False,
    )
    if result.returncode > 1:
        pytest.skip("not a git repository")
    lines = result.stdout.decode("utf-8").splitlines()
    return {line.strip() for line in lines if line.strip()}


@pytest.mark.parametrize(
    "path",
    [
        "output/two words.pdf",
        "output/über.pdf",
    ],
)
def test_ignored_hands_back_exactly_what_it_was_given(path):
    """The answer has to stay comparable with the question.

    git quotes any path it thinks unusual — non-ASCII, backslashes — and
    splitting its output on whitespace tears a name with a space in half.
    Either one makes the result uncomparable with the input, which is how the
    generated test data came back "not ignored" on Windows: there every path
    arrives with backslash separators, so git quoted all of them.
    """
    assert ignored([path]) == {path}


def fixture_files():
    files = [p for p in (ROOT / "tests" / "fixtures").rglob("*") if p.is_file()]
    assert files, "the demo project is missing — the end-to-end tests run against it"
    generated = {t.resolve() for t, _, _ in make_testdata.JOBS}
    # as_posix(), not str(): git speaks forward slashes on every platform, and a
    # backslash-separated path matches none of the .gitignore patterns.
    return (
        [p.relative_to(ROOT).as_posix() for p in files if p.resolve() not in generated],
        [p.relative_to(ROOT).as_posix() for p in files if p.resolve() in generated],
    )


def test_the_demo_project_is_not_swallowed_by_gitignore():
    """`sources.yaml`, `goal.md` and `*.pdf` match at every level — the fixture must survive."""
    versioned, _ = fixture_files()
    assert not ignored(versioned), (
        f"these test files would never be committed: {sorted(ignored(versioned))}"
    )


def test_the_demo_learning_goal_survives_gitignore():
    """The negation pattern, checked on its own.

    `goal.md` has no slash, so it matches at every directory level — the same
    hazard `sources.yaml` has. Without `!tests/fixtures/**/goal.md` the fixture's
    copy is silently uncommittable, and the demo project loses the artifact the
    whole goal-driven catalog is built on.
    """
    goal = ROOT / "tests/fixtures/demo-project/goal.md"
    assert goal.exists(), "the demo project has no goal.md"
    relative = goal.relative_to(ROOT).as_posix()
    assert not ignored([relative]), (
        f"{relative} is ignored — .gitignore needs !tests/fixtures/**/goal.md"
    )


def test_the_generated_test_data_stays_out_of_the_repo():
    """Binaries belong in nobody's git history — they are built, not committed."""
    _, generated = fixture_files()
    if not generated:
        pytest.skip("run scripts/make_testdata.py first")
    assert ignored(generated) == set(generated), (
        f"generated test data is not ignored: {sorted(set(generated) - ignored(generated))}"
    )


def test_gitignore_covers_the_user_paths():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    for pattern in (
        "sources.yaml",
        "goal.md",
        "knowledge/*",
        "catalog/*",
        "cards/*",
        "figures/*",
        "output/",
    ):
        assert pattern in lines, f".gitignore does not cover {pattern}"


def test_the_repo_does_not_still_promise_five_commands():
    """The pipeline is seven steps now, two of them optional.

    A release whose landing page promises five commands while the plugin has
    seven is not a release. `specs/` is exempt: it records what was true when
    each feature was specified.
    """
    offenders = []
    for name in versioned_files():
        if name.startswith("specs/") or not name.endswith((".md", ".html", ".typ", ".yaml")):
            continue
        path = ROOT / name
        if not path.exists():
            continue
        if "five commands" in path.read_text(encoding="utf-8", errors="ignore").lower():
            offenders.append(name)
    assert not offenders, f"these still promise five commands: {offenders}"


def test_the_readme_points_a_newcomer_at_the_landing_page():
    """The live page has to be reachable from the top of the README.

    It used to be named once, 168 lines down, inside the design section, which
    is where a reader who wants to *see* the project before reading about it
    never gets to. The opening block is everything above the first `## `
    heading; within it the link sits between the last badge and the first
    screenshot.
    """
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    heading = re.search(r"^## ", text, re.MULTILINE)
    assert heading, "README.md has no '## ' heading to bound its opening block"
    opening = text[: heading.start()]

    for anchor in (BADGE_ANCHOR, SCREENSHOT_ANCHOR):
        assert anchor in opening, (
            f"README.md: {anchor!r} is gone from the opening block — this test's anchors moved"
        )

    assert LANDING_URL in opening, (
        f"README.md does not link {LANDING_URL} above its first '## ' heading"
    )
    assert opening.index(BADGE_ANCHOR) < opening.index(LANDING_URL), (
        f"README.md links {LANDING_URL} above the badge row instead of below it"
    )
    assert opening.index(LANDING_URL) < opening.index(SCREENSHOT_ANCHOR), (
        f"README.md links {LANDING_URL} after the {SCREENSHOT_ANCHOR} screenshot"
    )


def test_the_readme_still_names_the_landing_page_source():
    """The contributor's half of the same page, and it must survive the newcomer's.

    This passes on `main` on purpose. It guards behaviour that already exists:
    the design section points at the file somebody edits, which is a different
    thing from the URL the opening block now points at. Deduplicating the two
    would cost a reader who is looking for the source. Proved load-bearing by
    deleting the link and watching this fail — see FR-005b.
    """
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    section = re.search(r"^## The design\n(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    assert section, "README.md has no '## The design' section to hold the source reference"
    assert f"]({LANDING_SOURCE})" in section.group(1), (
        f"README.md: '## The design' no longer links {LANDING_SOURCE}"
    )


# ---------------------------------------------------------------------------
# The card box — a committed binary, and the principle that has to name it.
#
# Principle VIII forbids committed binaries with one deliberate exception. The
# exception is a *named list*, and a list is only a rule while something checks
# that it is complete: the fonts under assets/fonts/ had been committed for
# months while VIII still said "the brand PNGs" and nothing else. So this asserts
# the whole list rather than the one file feature 007 adds — the next binary
# cannot slip past unnamed either.
# ---------------------------------------------------------------------------

CONSTITUTION = ROOT / ".specify" / "memory" / "constitution.md"

# What counts as *text* here — everything else under assets/ is a binary and has
# to be named. The allowlist runs this way round on purpose: listing the binary
# formats instead would mean a committed .zip, .ico or .mp4 was not merely
# unnamed but unchecked, and the whole point of this guard is that it cannot be
# outgrown. SVG is on the list because it reviews as text in a diff.
ASSET_TEXT_SUFFIXES = {
    ".svg",
    ".typ",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".css",
    ".html",
    ".license",
}


def named_by(path, pattern):
    """`assets/*.png` covers assets/banner.png and *not* assets/sub/deep.png.

    fnmatch alone gets this wrong: its `*` crosses `/`, so a top-level rule
    would silently admit a binary in a directory nobody has reviewed. Matching
    the depth as well is the whole fix. (PurePath.full_match would do it, but it
    lands in 3.13 and the floor is 3.12.)
    """
    return fnmatch(path, pattern) and path.count("/") == pattern.count("/")


def principle_viii():
    """The text of Principle VIII, up to the next principle heading."""
    text = CONSTITUTION.read_text(encoding="utf-8")
    section = re.search(r"^### VIII\..*?$(.*?)(?=^### )", text, re.MULTILINE | re.DOTALL)
    assert section, "constitution.md has no '### VIII.' section — this test's anchor moved"
    return section.group(1)


def test_every_committed_binary_under_assets_is_named_in_principle_viii():
    """A named exception that does not name everything is not an exception.

    VIII's list is matched as backticked globs, not as prose: `assets/*.png`
    covers the four brand renders without naming each, and a path that no glob
    matches is a binary the constitution does not admit to carrying.
    """
    binaries = [
        f
        for f in versioned_files()
        if f.startswith("assets/") and Path(f).suffix.lower() not in ASSET_TEXT_SUFFIXES
    ]
    assert binaries, "no committed binaries under assets/ — this test has stopped proving anything"

    patterns = re.findall(r"`([^`]+)`", principle_viii())
    unnamed = [f for f in binaries if not any(named_by(f, p) for p in patterns)]
    assert not unnamed, (
        "Principle VIII forbids committed binaries and names its exceptions. "
        f"These are committed and named nowhere in it: {sorted(unnamed)}"
    )


# ---------------------------------------------------------------------------
# The box itself: committable, committed, the right shape, and the right bytes.
#
# `pdf_page_size_mm` is imported from test_e2e rather than copied. That module
# imports `engine` and globs the demo cards at import time — both harmless here,
# and cheaper than a second regex that could drift from the first.
# ---------------------------------------------------------------------------

from test_e2e import pdf_page_size_mm  # noqa: E402

BOX = "assets/card-box.pdf"

# The bytes that were folded. Nothing in this repository can regenerate this
# file (Principle VIII names it as the exception that gives up regenerability),
# so the checksum is what "unchanged" means. A re-export would pass every other
# assertion in this module while quietly invalidating the physical validation
# the whole feature rests on.
BOX_SHA256 = "abecbcabb0c0dd2712d4929843913e38740cbe0a84d77b8f3d88fd007263b446"


def test_the_card_box_is_committable():
    """`*.pdf` is a build-leftover rule, and this file is not a build leftover."""
    assert ignored([BOX]) == set(), (
        f"{BOX} is swallowed by .gitignore — the negation has to sit *below* the "
        "`*.pdf` rule, because .gitignore is last-match-wins"
    )


def test_the_card_box_is_versioned():
    assert BOX in versioned_files(), (
        f"{BOX} is not tracked — it exists in one working copy and nowhere else"
    )


def test_the_card_box_is_one_portrait_sheet():
    """One page a home printer takes without being asked anything.

    Not `== (210.0, 297.0)`: this sheet's MediaBox is 595.2 x 841.8 pt, a
    Quartz approximation of A4 rather than the exact 595.276 x 841.89, so the
    helper returns (209.97, 296.97). Every other caller in the suite asserts
    strict equality because every other PDF is written by the pinned engine.
    This one was not, and a strict assertion here could never pass.
    """
    path = ROOT / BOX
    width, height = pdf_page_size_mm(path)
    assert width < height, f"the box sheet is not portrait: {width} x {height} mm"
    assert abs(width - 210) <= 0.5 and abs(height - 297) <= 0.5, (
        f"the box sheet is not A4 within printing tolerance: {width} x {height} mm"
    )
    pages = len(re.findall(rb"/Type\s*/Page[^s]", path.read_bytes()))
    assert pages == 1, f"the box is {pages} pages — it has to print as one sheet"


def test_the_card_box_is_the_sheet_that_was_folded():
    """See BOX_SHA256. This is the only provenance the artifact has."""
    import hashlib

    digest = hashlib.sha256((ROOT / BOX).read_bytes()).hexdigest()
    assert digest == BOX_SHA256, (
        "assets/card-box.pdf has changed. It has no source in this repository, so "
        "the folded, physically validated artifact is these bytes and no others. "
        "If the change is deliberate, re-fold the box before updating this hash."
    )


# The box is one you print now, not one you buy. Two files justified the two
# grids by the boxes you could buy for them, and both are wrong as of feature
# 007. Unlike the "five commands" guard below, this one must reach `.py`:
# scripts/build_pdf.py is one of the two offenders, and an extension filter
# copied from that test would wave it straight through.
TEXT_SUFFIXES = (".md", ".html", ".typ", ".yaml", ".yml", ".py")


def test_nothing_still_says_the_box_is_one_you_buy():
    """`specs/` is exempt: it records what was true when each feature was written.

    So is this file, which cannot hold the phrase it searches for and also pass.
    The "five commands" guard below avoids the same trap only by accident — its
    filter excludes `.py`, and it lives in a `.py` file.
    """
    offenders = []
    for name in versioned_files():
        if name.startswith("specs/") or name == "tests/test_repo_hygiene.py":
            continue
        if not name.endswith(TEXT_SUFFIXES):
            continue
        path = ROOT / name
        if not path.exists():
            continue
        if "you can buy" in path.read_text(encoding="utf-8", errors="ignore"):
            offenders.append(name)
    assert not offenders, (
        f"these still say a deck's box is one you buy, but it now ships: {offenders}"
    )


def test_the_design_doc_describes_the_box():
    """docs/design.md governs everything visible, and the box is now shipped."""
    text = (ROOT / "docs" / "design.md").read_text(encoding="utf-8")
    section = re.search(r"^## The box\n(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    assert section, "docs/design.md has no '## The box' section"
    body = section.group(1).lower()
    for anchor in ("a8", "71.75", "73"):
        assert anchor in body, (
            f"docs/design.md '## The box' does not state {anchor!r} — the card size and "
            "the grid it fits are what a reader needs before printing it"
        )


def test_the_readme_names_the_box():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "card-box.pdf" in text, (
        "README.md does not name the box — it is a shipped artifact and the readme "
        "describes what the project produces"
    )


def test_contributing_says_how_the_version_is_chosen():
    """The rule lived only in git history, and inferring it went wrong once.

    v0.7.3 was first released as v0.8.0 because the pull request carried a
    `feat:` prefix, and the tag had to be withdrawn. The prefix describes the
    commit; the version describes what changed for a user. If that is not
    written down, the next release decides it by archaeology again.
    """
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "## Releases" in text, "CONTRIBUTING.md does not say how a release is versioned"
    for word in ("patch", "minor"):
        assert word in text.lower(), f"the versioning rule does not mention {word}"


def test_contributing_names_the_files_that_carry_the_version():
    """A fourth version file would leave the instructions quietly wrong.

    `scripts/check_docs.py` fails CI when the three drift apart, so a
    contributor who bumps only the ones CONTRIBUTING.md happens to name gets a
    red build and no idea why.
    """
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    checked = {"pyproject.toml", ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"}
    docs = (ROOT / "scripts" / "check_docs.py").read_text(encoding="utf-8")
    assert all(name in docs for name in checked), (
        "check_docs.py no longer compares these three files — this test is stale"
    )
    missing = [name for name in checked if name not in text]
    assert not missing, f"CONTRIBUTING.md does not name every file carrying the version: {missing}"


def test_whole_deck_page_counts_are_derived_not_typed():
    """A typed page count is why the demo deck could not grow.

    `tests/test_e2e.py` asserts how many pages the whole demo deck fills. Written
    as a literal, every one of those assertions goes silently wrong the moment a
    card is added — which is what pinned the deck at 32 cards while #49 was
    built, and made a test-file inconvenience decide what the fixture could
    contain. Derived from DEMO_CARD_COUNT, adding a card updates them by itself.
    """
    text = (ROOT / "tests" / "test_e2e.py").read_text(encoding="utf-8")
    for name in ("DEMO_A7_PAGES", "DEMO_A8_PAGES"):
        assert name in text, f"{name} is not defined — whole-deck page counts are still typed"

    # Literal comparisons that remain must be about a locally built deck, never
    # about *CARDS. These are the only ones allowed, each named by its subject.
    allowed = {
        "12 cards at 4 x 4",
        "12 cards at 2 x 4",
        "14 cards at 4 x 4",
        "signals.yaml",
        "one_figure_card",
        "one_deck",
    }
    offenders = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not re.search(r"pdf_pages\([a-z_]+\)\s*==\s*\d+", line):
            continue
        window = "\n".join(lines[max(0, i - 12) : i + 1])
        if "*CARDS" in window and not any(a in window for a in allowed):
            offenders.append(f"{i + 1}: {line.strip()}")
    assert not offenders, "whole-deck page counts typed as literals:\n" + "\n".join(offenders)
