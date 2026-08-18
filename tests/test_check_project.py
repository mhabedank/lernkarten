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
