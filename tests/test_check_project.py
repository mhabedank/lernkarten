"""Tests for scripts/check_project.py and scripts/demo.py.

Four of the five pipeline steps are done by Claude, so what a test can pin down
is the shape of their output. check_project.py is that gate; these tests build
small broken projects in a temp folder and check that it complains about the
right thing, and that the demo project itself passes.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "tests" / "fixtures" / "demo-project"
sys.path.insert(0, str(ROOT / "scripts"))

import check_project  # noqa: E402
import demo  # noqa: E402

GOOD_SOURCES = """
sources:
  - id: field-notes
    type: folder
    path: raw
"""
GOOD_KNOWLEDGE = """---
source: field-notes
document: "A document"
path: "raw/a.md"
ingested: 2026-08-14
---

""" + ("Enough text to look like a real extraction. " * 10)
GOOD_CATALOG = """# Topics

## Tides

### Rhythm of the tide
How the tide moves.
References: [a](../knowledge/field-notes/a.md)
"""
GOOD_GOAL = """---
goal: 'Read the tide for any hour'
kind: exam
depth: working
updated: 2026-08-14
---

# Learning goal

Be able to read the tide unsupervised.

## Required topics

### Tides
- Rhythm of the tide

## Out of scope

- The history of the tide office
"""

GOOD_CARDS = """topic: 'Tides'
language: english
cards:
  - subtopic: 'Rhythm of the tide'
    front: 'How long is a tidal day?'
    back: '24 h 50 min.'
    source: 'Field notes'
"""


def project(
    tmp_path,
    sources=GOOD_SOURCES,
    knowledge=GOOD_KNOWLEDGE,
    catalog=GOOD_CATALOG,
    cards=GOOD_CARDS,
    knowledge_dir="field-notes",
    goal=None,
):
    """A minimal project on disk; pass None to leave a part out."""
    (tmp_path / "raw").mkdir()
    (tmp_path / "raw" / "a.md").write_text("raw material", encoding="utf-8")
    if sources is not None:
        (tmp_path / "sources.yaml").write_text(sources, encoding="utf-8")
    if knowledge is not None:
        folder = tmp_path / "knowledge" / knowledge_dir
        folder.mkdir(parents=True)
        (folder / "a.md").write_text(knowledge, encoding="utf-8")
    if catalog is not None:
        (tmp_path / "catalog").mkdir()
        (tmp_path / "catalog" / "topics.md").write_text(catalog, encoding="utf-8")
    if cards is not None:
        (tmp_path / "cards").mkdir()
        (tmp_path / "cards" / "tides.yaml").write_text(cards, encoding="utf-8")
    if goal is not None:
        (tmp_path / "goal.md").write_text(goal, encoding="utf-8")
    return tmp_path


def check(path):
    return check_project.check(Path(path), check_project.Report())


def messages(report):
    return " | ".join(report.errors)


def run_checker(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_project.py"), *args],
        capture_output=True,
        text=True,
    )


# --- the demo project, which has to stay valid ----------------------------


def test_the_demo_project_is_consistent():
    report = check(DEMO)
    assert not report.errors, messages(report)


def test_the_demo_project_has_all_four_artifacts():
    counts = check(DEMO).counts
    for what in ("sources", "documents", "topics", "subtopics", "cards"):
        assert counts.get(what), f"the demo project has no {what}"
    assert counts["cards"] == 29


def test_the_demo_project_passes_on_the_command_line():
    result = run_checker(str(DEMO))
    assert result.returncode == 0, result.stderr
    assert "is consistent" in result.stdout


def test_a_minimal_project_is_clean(tmp_path):
    report = check(project(tmp_path))
    assert not report.errors and not report.warnings, messages(report) + " | ".join(report.warnings)


def test_an_empty_project_is_not_an_error(tmp_path):
    """Right after `scripts/demo.py --raw` there is nothing to check yet."""
    report = check(project(tmp_path, knowledge=None, catalog=None, cards=None))
    assert not report.errors, messages(report)


# --- the source register --------------------------------------------------


@pytest.mark.parametrize(
    ("sources", "message"),
    [
        ("sources:\n  - type: folder\n    path: raw\n", "'id' missing"),
        ("sources:\n  - id: Field_Notes\n    type: folder\n    path: raw\n", "kebab-case"),
        (
            "sources:\n  - id: a\n    type: folder\n    path: raw\n"
            "  - id: a\n    type: folder\n    path: raw\n",
            "duplicate id",
        ),
        ("sources:\n  - id: a\n    type: telepathy\n", "unknown type"),
        ("sources:\n  - id: a\n    type: web\n", "'url' missing"),
        ("sources:\n  - id: a\n    type: pdf\n", "'path' missing"),
        ("topics:\n  - a\n", "expected a mapping with the key 'sources'"),
    ],
)
def test_a_broken_source_register_is_reported(tmp_path, sources, message):
    report = check(project(tmp_path, sources=sources, knowledge=None))
    assert any(message in e for e in report.errors), messages(report)


def test_a_source_path_that_is_gone_is_only_a_warning(tmp_path):
    sources = "sources:\n  - id: field-notes\n    type: folder\n    path: nowhere\n"
    report = check(project(tmp_path, sources=sources))
    assert not report.errors, messages(report)
    assert any("does not exist" in w for w in report.warnings)


# --- the ingested texts ---------------------------------------------------


def test_a_knowledge_folder_without_a_source_is_reported(tmp_path):
    report = check(project(tmp_path, knowledge_dir="somewhere-else"))
    assert any("no source with this id" in e for e in report.errors), messages(report)


def document(body="Long enough to pass for a real extraction. " * 10, **fields):
    """A knowledge file with the given frontmatter — a field of None is left out."""
    head = {"source": "field-notes", "document": "A", "path": "raw/a.md", "ingested": "2026-08-14"}
    head.update(fields)
    lines = "\n".join(f'{k}: "{v}"' for k, v in head.items() if v is not None)
    return f"---\n{lines}\n---\n\n{body}"


@pytest.mark.parametrize(
    ("knowledge", "message"),
    [
        ("no frontmatter at all, just text\n", "no readable frontmatter"),
        (document(source="elsewhere"), "is not 'field-notes'"),
        (document(document=None), "'document' missing"),
        (document(path=None), "neither 'path' nor 'url'"),
        (document(ingested="yesterday"), "not a date"),
    ],
)
def test_broken_frontmatter_is_reported(tmp_path, knowledge, message):
    report = check(project(tmp_path, knowledge=knowledge))
    assert any(message in e for e in report.errors), messages(report)


def test_a_url_may_stand_in_for_a_path(tmp_path):
    knowledge = document(path=None, url="https://example.com/")
    assert not check(project(tmp_path, knowledge=knowledge)).errors


def test_a_document_that_was_never_filled_in_warns(tmp_path):
    report = check(project(tmp_path, knowledge=document(body="", pending="/Users/x/a.pdf")))
    assert not report.errors, messages(report)
    assert any("pending" in w for w in report.warnings)


# --- the catalog ----------------------------------------------------------


def test_a_reference_that_points_nowhere_is_reported(tmp_path):
    catalog = GOOD_CATALOG.replace("field-notes/a.md", "field-notes/gone.md")
    report = check(project(tmp_path, catalog=catalog))
    assert any("points nowhere" in e for e in report.errors), messages(report)


def test_a_subtopic_without_a_topic_is_reported(tmp_path):
    report = check(project(tmp_path, catalog="### Orphan\nNo topic above it.\n", cards=None))
    assert any("before any topic" in e for e in report.errors), messages(report)


def test_a_catalog_without_topics_is_reported(tmp_path):
    report = check(project(tmp_path, catalog="Just a sentence.\n", cards=None))
    assert any("no topic" in e for e in report.errors), messages(report)


def test_a_topic_without_subtopics_warns(tmp_path):
    report = check(project(tmp_path, catalog="## Tides\nNothing under it.\n", cards=None))
    assert not report.errors, messages(report)
    assert any("no subtopic" in w for w in report.warnings)


# --- the card files -------------------------------------------------------


@pytest.mark.parametrize(
    ("cards", "message"),
    [
        (
            "topic: 'T'\nlanguage: klingon\ncards:\n  - subtopic: 'Rhythm of the tide'\n"
            "    front: 'Q'\n    back: 'A'\n",
            "unknown language",
        ),
        (
            "topic: 'T'\nlanguage: english\ncards:\n  - subtopic: 'Rhythm of the tide'\n"
            "    front: 'Q'\n",
            "'front' and 'back' are required",
        ),
        ("- front: 'Q'\n  back: 'A'\n", "expected a mapping"),
    ],
)
def test_a_broken_card_file_is_reported(tmp_path, cards, message):
    report = check(project(tmp_path, cards=cards))
    assert any(message in e for e in report.errors), messages(report)


def test_the_same_front_twice_in_one_file_is_reported(tmp_path):
    cards = (
        "topic: 'T'\nlanguage: english\ncards:\n"
        "  - subtopic: 'Rhythm of the tide'\n    front: 'How long is a tidal day?'\n"
        "    back: '24 h 50 min.'\n    source: 'x'\n"
        "  - subtopic: 'Rhythm of the tide'\n    front: 'How long is a tidal day?'\n"
        "    back: 'The same question again.'\n    source: 'x'\n"
    )
    report = check(project(tmp_path, cards=cards))
    assert any("same front as card 1" in e for e in report.errors), messages(report)


def test_a_subtopic_outside_the_catalog_warns(tmp_path):
    cards = GOOD_CARDS.replace("Rhythm of the tide", "Something the catalog never mentions")
    report = check(project(tmp_path, cards=cards))
    assert not report.errors, messages(report)
    assert any("is not in the catalog" in w for w in report.warnings)


# --- the grid key (feat/card-grid) -----------------------------------------


@pytest.mark.parametrize("value", ["a7", "a8", "2x4", "4x4", "A8", "4X4"])
def test_a_supported_grid_is_accepted(tmp_path, value):
    cards = GOOD_CARDS.replace("language: english", f"language: english\ngrid: {value}")
    report = check(project(tmp_path, cards=cards))
    assert not report.errors, messages(report)


@pytest.mark.parametrize("value", ["3x4", "2x6", "1x1"])
def test_an_unsupported_grid_is_reported_with_the_supported_set(tmp_path, value):
    cards = GOOD_CARDS.replace("language: english", f"language: english\ngrid: {value}")
    report = check(project(tmp_path, cards=cards))
    joined = messages(report)
    assert any(value in e for e in report.errors), joined
    assert any("2x4" in e and "4x4" in e for e in report.errors), joined
    assert any(e.startswith("cards/") for e in report.errors), joined


@pytest.mark.parametrize("value", ["eight", "3 x 4", "3,4", "0x4", "-1x4"])
def test_a_malformed_grid_is_reported(tmp_path, value):
    cards = GOOD_CARDS.replace("language: english", f"language: english\ngrid: '{value}'")
    report = check(project(tmp_path, cards=cards))
    assert any(value in e for e in report.errors), messages(report)


def test_a_grid_on_an_individual_card_is_reported(tmp_path):
    """FR-021: one deck is one size, so the key is top level only."""
    cards = GOOD_CARDS.replace(
        "    source: 'Field notes'", "    source: 'Field notes'\n    grid: a8"
    )
    report = check(project(tmp_path, cards=cards))
    assert any("grid" in e and "card 1" in e for e in report.errors), messages(report)


def test_an_overlong_card_warns(tmp_path):
    cards = GOOD_CARDS.replace("24 h 50 min.", "Far too much text. " * 40)
    report = check(project(tmp_path, cards=cards))
    assert any("back is long" in w for w in report.warnings), report.warnings


# --- the command line -----------------------------------------------------


def test_errors_make_the_command_fail(tmp_path):
    project(tmp_path, cards="- front: 'Q'\n  back: 'A'\n")
    result = run_checker(str(tmp_path))
    assert result.returncode == 1
    assert "ERROR" in result.stderr


def test_strict_makes_warnings_fail(tmp_path):
    project(tmp_path, sources=GOOD_SOURCES.replace("path: raw", "path: nowhere"))
    assert run_checker(str(tmp_path)).returncode == 0
    strict = run_checker(str(tmp_path), "--strict")
    assert strict.returncode == 1
    assert "WARNING" in strict.stderr


def test_a_folder_that_is_not_there_is_refused(tmp_path):
    result = run_checker(str(tmp_path / "nope"))
    assert result.returncode == 1
    assert "not a folder" in result.stderr


# --- the demo bootstrap ---------------------------------------------------


def test_the_demo_copy_is_a_valid_project(tmp_path):
    target = demo.copy(tmp_path / "demo", raw_only=False, force=False)
    report = check(target)
    assert not report.errors, messages(report)
    assert len(list((target / "cards").glob("*.yaml"))) == 6
    assert not (target / "broken").exists(), "the broken fixtures are not part of a demo project"


def test_the_demo_copy_makes_the_source_paths_absolute(tmp_path):
    target = demo.copy(tmp_path / "demo", raw_only=False, force=False)
    text = (target / "sources.yaml").read_text(encoding="utf-8")
    assert f"path: {target / 'raw'}/field-notes" in text
    assert "path: raw/" not in text


def test_the_raw_demo_copy_leaves_the_work_undone(tmp_path):
    target = demo.copy(tmp_path / "demo", raw_only=True, force=False)
    assert (target / "sources.yaml").exists()
    assert list((target / "raw").rglob("*.md")), "the raw material has to be there"
    for name in ("knowledge", "catalog", "cards"):
        assert (target / name).is_dir() and not list((target / name).iterdir())
    assert not check(target).errors


def test_an_existing_folder_is_not_overwritten_by_accident(tmp_path):
    target = tmp_path / "demo"
    demo.copy(target, raw_only=True, force=False)
    with pytest.raises(SystemExit, match="--force"):
        demo.copy(target, raw_only=True, force=False)
    demo.copy(target, raw_only=True, force=True)  # with --force it is fine


def test_force_refuses_a_folder_that_is_not_a_demo_project(tmp_path):
    target = tmp_path / "important"
    target.mkdir()
    (target / "thesis.txt").write_text("years of work", encoding="utf-8")
    with pytest.raises(SystemExit, match="no demo project"):
        demo.copy(target, raw_only=False, force=True)
    assert (target / "thesis.txt").exists()


# --- goal.md, the fifth format --------------------------------------------


def test_a_goal_without_kind_is_reported(tmp_path):
    report = check(project(tmp_path, goal=GOOD_GOAL.replace("kind: exam\n", "")))
    assert "kind" in messages(report), messages(report)


def test_an_unknown_depth_is_reported(tmp_path):
    """The message has to name the value and the closed set — 'invalid' helps nobody."""
    report = check(project(tmp_path, goal=GOOD_GOAL.replace("depth: working", "depth: fluent")))
    said = messages(report)
    assert "fluent" in said, said
    assert "awareness" in said and "expert" in said, said


def test_an_unknown_kind_is_reported(tmp_path):
    report = check(project(tmp_path, goal=GOOD_GOAL.replace("kind: exam", "kind: viva")))
    said = messages(report)
    assert "viva" in said, said
    assert "self-study" in said, said


def test_an_updated_that_is_not_a_date_is_reported(tmp_path):
    goal = GOOD_GOAL.replace("updated: 2026-08-14", "updated: soon")
    report = check(project(tmp_path, goal=goal))
    said = messages(report)
    assert "updated" in said and "soon" in said, said


def test_an_area_with_no_topics_is_reported(tmp_path):
    """An empty area is a syllabus that promises a strand and delivers nothing."""
    goal = GOOD_GOAL.replace("### Tides\n- Rhythm of the tide", "### Tides\n\n### Signals\n- Flags")
    report = check(project(tmp_path, goal=goal))
    assert "Tides" in messages(report), messages(report)


def test_a_goal_with_no_area_is_reported(tmp_path):
    goal = GOOD_GOAL.replace("### Tides\n- Rhythm of the tide\n", "")
    report = check(project(tmp_path, goal=goal))
    assert "Required topics" in messages(report) or "area" in messages(report), messages(report)


def test_a_required_topic_missing_from_the_catalog_warns(tmp_path):
    """Drift: the goal moved on and /catalog was never re-run. A warning, not an error."""
    goal = GOOD_GOAL.replace("- Rhythm of the tide", "- Storm surge warnings")
    report = check(project(tmp_path, goal=goal))
    assert not report.errors, messages(report)
    said = " | ".join(report.warnings)
    assert "Storm surge warnings" in said, said


def test_a_good_goal_passes(tmp_path):
    report = check(project(tmp_path, goal=GOOD_GOAL))
    assert not report.errors, messages(report)


def test_a_project_without_a_goal_passes_unchanged(tmp_path):
    """SC-006: the added step costs nothing to a user who does not want it.

    A regression guard, green from the first day — and it must never go red.
    """
    report = check(project(tmp_path))
    assert not report.errors, messages(report)
    assert not report.warnings, report.warnings


# --- Status: gap and out of scope -----------------------------------------

CATALOG_WITH_GAP = """# Topics

## Tides

### Rhythm of the tide
How the tide moves.
References: [a](../knowledge/field-notes/a.md)

### Storm surge
What the goal wants and no document covers.
Status: gap
References: none
"""


def test_a_subtopic_with_neither_references_nor_gap_is_reported(tmp_path):
    """A branch with nothing behind it is either a gap or a mistake."""
    catalog = GOOD_CATALOG + "\n### Storm surge\nNothing behind this one.\n"
    report = check(project(tmp_path, catalog=catalog))
    assert "Storm surge" in messages(report), messages(report)


def test_a_gap_with_no_references_passes(tmp_path):
    report = check(project(tmp_path, catalog=CATALOG_WITH_GAP))
    assert not report.errors, messages(report)


def test_an_unknown_status_is_reported(tmp_path):
    """The message names the subtopic and the value — 'invalid status' helps nobody."""
    catalog = CATALOG_WITH_GAP.replace("Status: gap", "Status: irrelevant")
    report = check(project(tmp_path, catalog=catalog))
    said = messages(report)
    assert "Storm surge" in said, said
    assert "irrelevant" in said, said


def test_out_of_scope_keeps_its_references(tmp_path):
    """Out-of-scope material is marked, not thrown away — the references still resolve."""
    catalog = GOOD_CATALOG.replace(
        "How the tide moves.", "How the tide moves.\nStatus: out of scope"
    )
    report = check(project(tmp_path, catalog=catalog))
    assert not report.errors, messages(report)


def test_a_catalog_with_no_status_lines_is_unchanged(tmp_path):
    """Regression guard: absence of every new line means today's behaviour."""
    report = check(project(tmp_path, catalog=GOOD_CATALOG))
    assert not report.errors, messages(report)
    assert not report.warnings, report.warnings


# --- cards stay inside the goal -------------------------------------------


def test_a_card_for_an_out_of_scope_subtopic_warns(tmp_path):
    """The artifact-level assertion behind US3.

    /cards skipping a marked subtopic is console behaviour and leaves no trace,
    but the card file it did *not* write does. A warning rather than an error:
    naming an out-of-scope subtopic explicitly still generates it (FR-020).
    """
    catalog = GOOD_CATALOG.replace(
        "How the tide moves.", "How the tide moves.\nStatus: out of scope"
    )
    report = check(project(tmp_path, catalog=catalog))
    assert not report.errors, messages(report)
    said = " | ".join(report.warnings)
    assert "Rhythm of the tide" in said, said
    assert "out of scope" in said, said


def test_a_card_for_a_gap_subtopic_warns(tmp_path):
    """A gap has nothing to read, so a card for it was written from thin air."""
    catalog = CATALOG_WITH_GAP
    cards = GOOD_CARDS.replace("subtopic: 'Rhythm of the tide'", "subtopic: 'Storm surge'")
    report = check(project(tmp_path, catalog=catalog, cards=cards))
    said = " | ".join(report.warnings)
    assert "Storm surge" in said and "gap" in said, said


def test_a_card_for_an_ordinary_subtopic_warns_about_nothing(tmp_path):
    """Regression guard: the check only fires on a marked subtopic."""
    report = check(project(tmp_path, catalog=GOOD_CATALOG))
    assert not report.warnings, report.warnings


# --- the research source type ---------------------------------------------

RESEARCH_SOURCES = """
sources:
  - id: field-notes
    type: folder
    path: raw
  - id: surge-research
    type: research
    gap: 'Storm surge'
"""


def test_a_research_source_without_a_gap_is_reported(tmp_path):
    """Assert the message, not merely that something failed.

    `research` was an unknown type before this feature, so an error fires
    either way — a bare `assert report.errors` would be green from the start
    and prove nothing. What has to be red is the missing-`gap` wording.
    """
    sources = RESEARCH_SOURCES.replace("    gap: 'Storm surge'\n", "")
    report = check(project(tmp_path, sources=sources, knowledge_dir="field-notes"))
    said = messages(report)
    assert "surge-research" in said, said
    assert "gap" in said, said


def test_a_research_source_needs_neither_path_nor_url(tmp_path):
    """It was synthesised from the web, so there is no local file to point at."""
    report = check(project(tmp_path, sources=RESEARCH_SOURCES))
    assert not [e for e in report.errors if "surge-research" in e], messages(report)


# --- the catalog as a graph -----------------------------------------------

GRAPH_CATALOG = """# Topics

## Tides
The tide.
Also covers: Access control (cards in cards/security.yaml)

### Rhythm of the tide
How the tide moves.
References: [a](../knowledge/field-notes/a.md)

## Security
Who may do what.

### Access control
Belongs under both.
Parents: Security, Tides
References: [a](../knowledge/field-notes/a.md)
"""


def test_a_two_parent_subtopic_passes(tmp_path):
    report = check(project(tmp_path, catalog=GRAPH_CATALOG))
    assert not report.errors, messages(report)


def test_a_parent_that_is_not_a_topic_is_reported(tmp_path):
    """C-1."""
    catalog = GRAPH_CATALOG.replace("Parents: Security, Tides", "Parents: Security, Weather")
    report = check(project(tmp_path, catalog=catalog))
    said = messages(report)
    assert "Access control" in said and "Weather" in said, said


def test_a_primary_parent_that_is_not_the_heading_is_reported(tmp_path):
    """C-2: the first parent decides the card file, so it must be where it lives."""
    catalog = GRAPH_CATALOG.replace("Parents: Security, Tides", "Parents: Tides, Security")
    report = check(project(tmp_path, catalog=catalog))
    said = messages(report)
    assert "Access control" in said, said
    assert "Tides" in said and "Security" in said, said


def test_a_non_primary_parent_without_a_reciprocal_listing_is_reported(tmp_path):
    """C-3: half an edit is the failure this format actually invites."""
    catalog = GRAPH_CATALOG.replace(
        "Also covers: Access control (cards in cards/security.yaml)\n", ""
    )
    report = check(project(tmp_path, catalog=catalog))
    said = messages(report)
    assert "Access control" in said and "Tides" in said, said


def test_an_also_covers_the_subtopic_does_not_claim_is_reported(tmp_path):
    """C-4: the other half of the same edit."""
    catalog = GRAPH_CATALOG.replace("Parents: Security, Tides", "Parents: Security")
    report = check(project(tmp_path, catalog=catalog))
    said = messages(report)
    assert "Access control" in said, said


def test_a_dangling_related_name_is_reported(tmp_path):
    """C-5."""
    catalog = GRAPH_CATALOG.replace(
        "Belongs under both.", "Belongs under both.\nRelated: Sea level"
    )
    report = check(project(tmp_path, catalog=catalog))
    said = messages(report)
    assert "Sea level" in said, said


def test_a_two_parent_subtopic_counts_once(tmp_path):
    """C-9: written once, so counted once — and handed to check_cards once."""
    report = check(project(tmp_path, catalog=GRAPH_CATALOG))
    assert report.counts["subtopics"] == 2, report.counts


def test_also_covers_is_not_parsed_as_a_subtopic(tmp_path):
    """C-9 again: an `Also covers:` line is a topic attribute, not a heading."""
    subtopics, marked = check_project.check_catalog(
        project(tmp_path, catalog=GRAPH_CATALOG), check_project.Report()
    )
    assert subtopics == {"Rhythm of the tide", "Access control"}, subtopics


# --- thin, but complete (BUG-004 / issue #12) ------------------------------

SPARSE_KNOWLEDGE = """---
source: field-notes
document: "A cover sheet"
path: "raw/a.md"
content: sparse
characters: 68
ingested: 2026-08-14
---

Tide office of Fenmouth. Annual report 2021. Cover sheet.
"""


def test_a_document_marked_sparse_is_not_read_as_a_failed_extraction(tmp_path):
    """FR-047: 'barely any text — did the extraction work?' is the wrong question here.

    It did work. The marker says so, and the warning has to say something the
    reader can act on instead of sending them back to an ingest that is already
    as complete as it will get.
    """
    report = check(project(tmp_path, knowledge=SPARSE_KNOWLEDGE))
    assert not report.errors, messages(report)
    said = " | ".join(report.warnings)
    assert "did the extraction work" not in said, said
    assert "knowledge/field-notes/a.md" not in said, (
        "a correctly marked document is not a finding — warning about it every "
        "run trades a false alarm for a permanent true one"
    )


def test_an_unknown_content_value_is_reported(tmp_path):
    """A marker nothing can act on is worse than no marker."""
    knowledge = SPARSE_KNOWLEDGE.replace("content: sparse", "content: probably-fine")
    report = check(project(tmp_path, knowledge=knowledge))
    said = messages(report)
    assert "probably-fine" in said, said


def test_a_subtopic_backed_only_by_sparse_documents_is_reported(tmp_path):
    """FR-048: a cover page is not evidence that a topic is covered.

    Without this the coverage count is overstated in the one direction that
    matters — the user is told a required topic is covered and gets cards built
    out of form labels.
    """
    report = check(project(tmp_path, knowledge=SPARSE_KNOWLEDGE))
    said = " | ".join(report.warnings)
    assert "Rhythm of the tide" in said, said
    assert "sparse" in said, said


# --- the Typst markup contract (BUG-001 / issue #31) -----------------------

MARKUP_CARDS = """topic: 'Tides'
language: english
cards:
  - subtopic: 'Rhythm of the tide'
    front: 'How long is a tidal day?'
    back: '24 h 50 min.'
    source: 'Field notes'
"""


def markup_cards(back):
    return MARKUP_CARDS.replace("back: '24 h 50 min.'", f"back: {back}")


def test_a_markdown_double_star_is_reported(tmp_path):
    """FR-043: Typst bolds with one star. `**bold**` is two empty strong elements.

    It typesets, so `lernkarten check` passes it and the card prints
    unemphasised — the only signal Typst gives is a warning on the success path,
    which build_pdf.py discards. Nothing but this check can catch it.
    """
    report = check(project(tmp_path, cards=markup_cards("'This is **bold** in markdown.'")))
    said = messages(report)
    assert "card 1" in said, said
    assert "*" in said, said


def test_a_backslash_before_a_markup_character_is_reported(tmp_path):
    """FR-043: `\\` is a line break only before whitespace; before `*` it escapes it.

    A card is one line of YAML, so `'first\\*bold* rest'` yields a literal star,
    no line break, and every star after it shifted by one.
    """
    report = check(project(tmp_path, cards=markup_cards("'First line\\*bold* rest of it.'")))
    said = " | ".join(report.errors + report.warnings)
    assert "card 1" in said, said
    assert "line break" in said, said


def test_the_working_line_break_form_is_not_reported(tmp_path):
    """The documented form — backslash, space, markup — must stay silent.

    Without this the fix could be "flag every backslash", which would make the
    line break unusable and be a worse bug than the one it replaced.
    """
    report = check(project(tmp_path, cards=markup_cards("'First line\\ *bold* rest of it.'")))
    assert not report.errors and not report.warnings, messages(report)


# --- a comma inside a name (BUG-005 / issue #24) ---------------------------

COMMA_CATALOG = """# Topics

## Tides, currents & winds
The water and the air that moves it.
Also covers: Access control (cards in cards/security.yaml)

### Rhythm of the tide
How the tide moves.
References: [a](../knowledge/field-notes/a.md)

## Security
Who may do what.

### Access control
Belongs under both.
Parents: Security, Tides, currents & winds
Related: Rhythm of the tide
References: [a](../knowledge/field-notes/a.md)
"""


def test_a_topic_name_containing_a_comma_validates_clean(tmp_path):
    """FR-049: names are data, and 'Governance, risk & compliance' is an ordinary name.

    `Parents:` is a comma-separated list, so a name with a comma in it used to be
    torn into 'Tides' and 'currents & winds' — neither of which is a topic. One
    name produced five errors, none of which named the real cause.
    """
    report = check(project(tmp_path, catalog=COMMA_CATALOG))
    assert not report.errors, messages(report)


def test_a_comma_bearing_name_is_reached_through_related_and_also_covers(tmp_path):
    """FR-049 at the other two call sites — `Related:` and `Also covers:`.

    The three attribute lines share one splitter, so fixing `Parents:` alone
    would leave two of them broken.
    """
    catalog = COMMA_CATALOG.replace(
        "Related: Rhythm of the tide", "Related: Rhythm of the tide"
    ).replace(
        "### Rhythm of the tide\nHow the tide moves.",
        "### Rhythm of the tide\nHow the tide moves.\nRelated: Access control",
    )
    report = check(project(tmp_path, catalog=catalog))
    assert not report.errors, messages(report)


def test_a_name_before_its_parenthetical_does_not_swallow_the_next_one():
    """An `Also covers:` name carries `(cards in ...)` and may not be the last one.

    The parenthetical sits between a name and the comma after it, so consuming
    it has to happen where it is rather than at the end of the line.
    """
    names = check_project.catalog_names(
        "Access control (cards in cards/security.yaml), Rhythm of the tide",
        {"Access control", "Rhythm of the tide"},
    )
    assert names == ["Access control", "Rhythm of the tide"], names


def test_a_dangling_name_after_a_comma_bearing_one_is_still_reported(tmp_path):
    """FR-049 must not buy silence: what is left over is still split and checked.

    A fix that stops splitting altogether would make this catalog pass, and C-1
    would stop being a check at all.
    """
    catalog = COMMA_CATALOG.replace(
        "Parents: Security, Tides, currents & winds",
        "Parents: Security, Tides, currents & winds, Weather",
    )
    report = check(project(tmp_path, catalog=catalog))
    said = messages(report)
    assert "Weather" in said, said
    assert "currents & winds" not in said, said


def test_a_catalog_with_no_parents_or_related_is_unchanged(tmp_path):
    """Regression guard: absence means today's behaviour."""
    report = check(project(tmp_path, catalog=GOOD_CATALOG))
    assert not report.errors and not report.warnings, messages(report)


def test_an_area_that_is_not_a_top_level_topic_warns(tmp_path):
    """FR-010: each area of the goal becomes its own top-level topic.

    Found by hand during the Wave G reconciliation, where the demo fixture had
    three areas and four topics that did not correspond — so this is a check
    that turns a prompt rule into something a test can hold, rather than
    trusting the catalog skill to have followed it.
    """
    goal = GOOD_GOAL.replace("### Tides", "### Tides and navigation")
    report = check(project(tmp_path, goal=goal))
    assert not report.errors, messages(report)
    said = " | ".join(report.warnings)
    assert "Tides and navigation" in said, said
