"""The documentation checker itself.

`scripts/check_docs.py` had no coverage at all until the goal-driven catalog
added a rule to it. The rule: a skill description has to name this plugin's
domain, not only its triggers — `/catalog` and `/research` are words any
installed skill might claim, and the plugin ships into environments this repo
cannot inspect.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_docs  # noqa: E402
import check_project  # noqa: E402

DOMAIN = "flashcard"


def write_skill(root, name, description):
    """A minimal skill folder, valid apart from whatever the caller is testing."""
    folder = root / "skills" / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: >-\n  {description}\n---\n\n# /{name}\n",
        encoding="utf-8",
    )
    return root / "skills"


def shipped_descriptions():
    """Every skill this repo actually ships, as {name: description}."""
    out = {}
    for folder in sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir()):
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        head = check_docs.yamlio.load(text.split("---\n", 2)[1]) or {}
        out[folder.name] = str(head.get("description") or "")
    return out


def test_a_description_with_triggers_but_no_domain_word_is_reported(tmp_path, monkeypatch):
    """Triggers alone are not enough — a generic name has to resolve to us."""
    skills = write_skill(
        tmp_path,
        "catalog",
        "Build or update a topic catalog from the ingested knowledge. "
        'Triggers: /catalog, "build the topic catalog".',
    )
    monkeypatch.setattr(check_docs, "SKILLS", skills)
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)

    errors = []
    check_docs.check_skills(errors)

    assert errors, "a description naming no domain word was accepted"
    assert any(DOMAIN in e for e in errors), f"the message does not say what is missing: {errors}"
    assert any("catalog/SKILL.md" in e.replace("\\", "/") for e in errors), (
        f"the message does not name the file at fault: {errors}"
    )


def test_a_description_naming_the_domain_passes(tmp_path, monkeypatch):
    """The regression guard for the rule above — it must not reject a good one."""
    skills = write_skill(
        tmp_path,
        "catalog",
        "Build or update a topic catalog for the flashcards. "
        'Triggers: /catalog, "build the topic catalog".',
    )
    monkeypatch.setattr(check_docs, "SKILLS", skills)
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)

    errors = []
    check_docs.check_skills(errors)

    assert not errors, errors


def test_every_shipped_skill_names_the_domain():
    """FR-026, asserted against the requirement rather than against the rule.

    Written before the rule exists, so it goes red on the two descriptions that
    say what the step does without saying what it is *for*.
    """
    offenders = [
        name
        for name, description in shipped_descriptions().items()
        if DOMAIN not in description.lower()
    ]
    assert not offenders, (
        f"these skill descriptions name no domain word, so a generic slash command "
        f"cannot resolve to them: {offenders}"
    )


def write_versions(root, pyproject, plugin, marketplace):
    """The three files that carry a version, each with one written into it."""
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "lernkarten"\nversion = "{pyproject}"\n', encoding="utf-8"
    )
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "lernkarten", "version": plugin}), encoding="utf-8"
    )
    (root / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps(
            {"name": "mhabedank", "plugins": [{"name": "lernkarten", "version": marketplace}]}
        ),
        encoding="utf-8",
    )


def test_versions_that_disagree_are_reported(tmp_path, monkeypatch):
    """The drift that survived the whole of v0.3.0 unnoticed."""
    write_versions(tmp_path, pyproject="0.2.0", plugin="0.3.0", marketplace="0.3.0")
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)

    errors = []
    check_docs.check_versions(errors)

    assert errors, "three files disagreeing on the version were accepted"
    assert any("pyproject.toml" in e for e in errors), (
        f"the message does not name the file that is out of step: {errors}"
    )
    assert any("0.2.0" in e and "0.3.0" in e for e in errors), (
        f"the message does not show both versions, so it cannot be acted on: {errors}"
    )


def test_versions_that_agree_pass(tmp_path, monkeypatch):
    """The regression guard for the rule above — it must not reject a good release."""
    write_versions(tmp_path, pyproject="0.3.1", plugin="0.3.1", marketplace="0.3.1")
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)

    errors = []
    check_docs.check_versions(errors)

    assert not errors, errors


def test_the_shipped_versions_agree():
    """Asserted against the repo itself, not against a fixture.

    A release bumps three files by hand and nothing compared them, so
    pyproject.toml sat at 0.2.0 from the initial commit through v0.3.0.
    """
    errors = []
    check_docs.check_versions(errors)

    assert not errors, errors


# --- /cards writes the grid the default actually is (FR-010) --------------


def write_cards_skill(root, grid):
    folder = root / "skills" / "cards"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        f"---\nname: cards\n---\n\n```yaml\ntopic: 'T'\ngrid: {grid}\n```\n",
        encoding="utf-8",
    )


def test_the_cards_skill_offering_the_wrong_grid_is_reported(tmp_path, monkeypatch):
    """The one site in BUG-010 that writes a value rather than a sentence."""
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    write_cards_skill(tmp_path, "a7" if check_docs.default_grid_alias() != "a7" else "a8")

    errors = []
    check_docs.check_cards_skill_writes_the_default_grid(errors)

    assert any("skills/cards/SKILL.md" in e for e in errors), errors
    assert any("pin every new deck" in e for e in errors), errors


def test_the_cards_skill_offering_the_default_grid_passes(tmp_path, monkeypatch):
    """Read from DEFAULT_GRID, so moving the default again moves this with it."""
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    write_cards_skill(tmp_path, check_docs.default_grid_alias())

    errors = []
    check_docs.check_cards_skill_writes_the_default_grid(errors)

    assert not errors, errors


# --- A7 is not the default any more, and that is gated (FR-011, SC-011) ---


def gated_project(tmp_path, monkeypatch, **files):
    """A tree with only the files a case needs, everywhere the gate looks."""
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    monkeypatch.setattr(check_docs, "SCRIPTS", tmp_path / "scripts")
    (tmp_path / "skills").mkdir()
    for name, text in files.items():
        path = tmp_path / name.replace("__", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_a_doc_calling_a7_the_default_is_reported(tmp_path, monkeypatch):
    """The claim BUG-010 left in seventeen places."""
    gated_project(tmp_path, monkeypatch, **{"README.md": "Omitting the key prints at A7.\n"})

    errors = []
    check_docs.check_a7_is_not_the_default(errors)

    assert any("README.md:1" in e for e in errors), errors
    assert any("a8" in e for e in errors), errors


def test_a_claim_that_wraps_is_still_reported(tmp_path, monkeypatch):
    """README.md splits "`a7` is the / default grid" across a line break.

    A line-scoped rule makes the fix depend on where the text happens to wrap,
    which is the reason check_print_order reads a paragraph rather than a line.
    """
    gated_project(
        tmp_path,
        monkeypatch,
        **{"README.md": "An a7 card is 100 mm wide, and a7 is the\ndefault grid, so check.\n"},
    )

    errors = []
    check_docs.check_a7_is_not_the_default(errors)

    assert errors, "a claim split over two lines is still one claim"


def test_naming_a8_as_the_default_passes(tmp_path, monkeypatch):
    gated_project(
        tmp_path,
        monkeypatch,
        **{"README.md": "16 cards at the default a8 grid, or 8 at a7.\n"},
    )

    errors = []
    check_docs.check_a7_is_not_the_default(errors)

    assert not errors, errors


def test_the_scale_reference_and_the_default_margin_are_not_default_claims(tmp_path, monkeypatch):
    """FR-002's whole point: the reference stays A7 and is not the default.

    And `--margin` has a default of its own. Both sit one word from an A7 token
    all over build_pdf.py, and a gate that cannot tell them apart is a gate
    somebody switches off.
    """
    gated_project(
        tmp_path,
        monkeypatch,
        **{
            "docs__design.md": "The reference is the A7 card, not the default.\n",
            "scripts__build_pdf.py": "# The A7 card at the default margin is 100 x 71.75.\n",
        },
    )

    errors = []
    check_docs.check_a7_is_not_the_default(errors)

    assert not errors, errors


def test_the_gate_reads_python_and_typst_too(tmp_path, monkeypatch):
    """Six of BUG-010's sites were outside markdown_files() (FR-012)."""
    gated_project(
        tmp_path,
        monkeypatch,
        **{
            "scripts__build_pdf.py": '"""A4 with 8 cards per page by default (2 x 4, DIN A7)."""\n',
            "templates__cards.typ": "// 2 x 4 is DIN A7 (8 up, the default).\n",
        },
    )

    errors = []
    check_docs.check_a7_is_not_the_default(errors)

    assert any("build_pdf.py" in e for e in errors), errors
    assert any("cards.typ" in e for e in errors), errors


def test_the_cutting_instruction_has_to_name_its_grid(tmp_path, monkeypatch):
    """One vertical cut and three across is the 2x4 sheet, not the default."""
    gated_project(
        tmp_path,
        monkeypatch,
        **{"README.md": "Cut the long line down the middle first, then the three across.\n"},
    )

    errors = []
    check_docs.check_cut_count(errors)

    assert any("cut count follows --grid" in e for e in errors), errors


def test_a_cutting_instruction_that_names_its_grid_passes(tmp_path, monkeypatch):
    gated_project(
        tmp_path,
        monkeypatch,
        **{"README.md": "At --grid a7, cut down the middle, then the three across.\n"},
    )

    errors = []
    check_docs.check_cut_count(errors)

    assert not errors, errors


# --- the sheet capacity is not a fixed fact (SC-009) -----------------------


def test_a_doc_claiming_a_fixed_sheet_capacity_is_reported(tmp_path, monkeypatch):
    """SC-009 as a gate rather than as a grep somebody remembers to run."""
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    (tmp_path / "skills").mkdir()
    (tmp_path / "README.md").write_text("The PDF puts 8 cards on an A4 page.\n", encoding="utf-8")

    errors = []
    check_docs.check_sheet_capacity(errors)

    assert any("8 cards" in e for e in errors), errors
    assert any("README.md" in e for e in errors), errors


def test_a_doc_that_qualifies_the_capacity_passes(tmp_path, monkeypatch):
    """The number is fine when it is tied to a grid rather than to the sheet."""
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    (tmp_path / "skills").mkdir()
    (tmp_path / "README.md").write_text(
        "The PDF puts 8 cards on an A4 page at --grid a7, or 16 at a8.\n", encoding="utf-8"
    )

    errors = []
    check_docs.check_sheet_capacity(errors)

    assert not errors, errors


def test_no_shipped_doc_claims_a_fixed_sheet_capacity():
    """Asserted against the repo itself.

    The sweep for feat/card-grid was enforced by a hand-written grep, which
    searched for 'eight cards' and '8 cards to' and so walked straight past
    'A4, 8 cards per page' in the /print description and 'puts 8 cards on an
    A4 page' in the README. Both shipped in v0.4.0.
    """
    errors = []
    check_docs.check_sheet_capacity(errors)

    assert not errors, errors


# --- the printing instruction is not one instruction (SC-006) --------------


def test_a_doc_giving_duplex_as_the_only_instruction_is_reported(tmp_path, monkeypatch):
    """The same class of staleness as the sheet capacity, one release later.

    'duplex, flip on long edge' was the way to print until --sides existed. A
    doc that still states it as *the* way is wrong rather than merely dated,
    and the last sweep of this kind was a hand-written grep that missed two
    lines and shipped them.
    """
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    (tmp_path / "skills").mkdir()
    (tmp_path / "README.md").write_text(
        "Then print: duplex, flip on long edge, 100 % scale.\n", encoding="utf-8"
    )

    errors = []
    check_docs.check_print_order(errors)

    assert any("README.md" in e for e in errors), errors
    assert any("duplex" in e for e in errors), errors


def test_a_doc_that_names_the_other_order_passes(tmp_path, monkeypatch):
    """Naming the mode is the fix, not deleting the word.

    Without this the gate would be satisfiable by removing 'duplex' from every
    sentence, which loses the instruction the reader came for.
    """
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    (tmp_path / "skills").mkdir()
    (tmp_path / "README.md").write_text(
        "Duplex printer: flip on long edge. One-sided printer: `--sides simplex`.\n",
        encoding="utf-8",
    )

    errors = []
    check_docs.check_print_order(errors)

    assert not errors, errors


def test_no_shipped_doc_gives_duplex_as_the_only_instruction():
    """Asserted against the repo itself — this is the sweep, enforced.

    Red until every printing instruction names the order it belongs to. The
    failure output is the work list.
    """
    errors = []
    check_docs.check_print_order(errors)

    assert not errors, errors


def test_the_order_may_be_named_anywhere_in_the_same_paragraph(tmp_path, monkeypatch):
    """Prose wraps, and the gate must not fight the wrapping.

    An instruction spans a paragraph, unlike a sheet-capacity claim, which is
    one short clause. Scoping this check to the physical line would force the
    qualifying word onto the same line as 'duplex' and make the fix depend on
    where the text happens to break.
    """
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    (tmp_path / "skills").mkdir()
    (tmp_path / "README.md").write_text(
        "1. Choose **duplex, flip on long edge** — short edge puts the back\n"
        "   upside down. On a one-sided printer use `--sides simplex` instead.\n"
        "\n"
        "A later paragraph that says duplex on its own is still reported.\n",
        encoding="utf-8",
    )

    errors = []
    check_docs.check_print_order(errors)

    assert len(errors) == 1, errors
    assert "later paragraph" not in " ".join(errors)


def test_a_markdown_example_in_inline_code_is_not_a_dead_link(tmp_path, monkeypatch):
    """Docs have to be able to *show* markdown syntax without being it.

    skills/ingest/SKILL.md tells the model to write
    `![Figure: caption](figures/<id>/<slug>.png)` into a knowledge document.
    That is an example of a path to write, not a path that exists — the same
    reason fenced code blocks are already skipped.
    """
    doc = tmp_path / "docs"
    doc.mkdir()
    (doc / "workflow.md").write_text(
        "Write `![Figure: caption](figures/<id>/<slug>.png)` into the body.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    errors = []
    check_docs.check_links(errors)
    assert errors == [], errors


def test_a_real_dead_link_outside_code_is_still_reported(tmp_path, monkeypatch):
    doc = tmp_path / "docs"
    doc.mkdir()
    (doc / "workflow.md").write_text("See [the design](design.md).\n", encoding="utf-8")
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    monkeypatch.setattr(check_docs, "SKILLS", tmp_path / "skills")
    errors = []
    check_docs.check_links(errors)
    assert any("design.md" in e for e in errors), errors


# --- the method page cannot drift from the dividers (US4) -------------------


def test_the_method_page_must_carry_every_interval_the_dividers_print(tmp_path, monkeypatch):
    """FR-017: one definition, two renders.

    `scripts/leitner.py` is the single source. A compartment that says "weekly"
    on paper and something else on screen is the failure this check exists to
    make impossible — and it is checkable in both directions, so neither a
    missing interval nor an invented one gets through.
    """
    page = ROOT / "docs" / "leitner.html"
    assert page.exists(), "docs/leitner.html does not exist yet"

    original = page.read_text(encoding="utf-8")
    missing = original.replace("every 3 days", "", 1)
    assert missing != original, "the page never mentioned 'every 3 days'"

    errors = []
    monkeypatch.setattr(check_docs, "read_page", lambda: missing)
    check_docs.check_leitner_intervals(errors)
    assert errors, "an interval dropped from the page must be reported"
    assert "every 3 days" in " ".join(errors)


def test_the_method_page_may_not_invent_an_interval(monkeypatch):
    errors = []
    monkeypatch.setattr(check_docs, "read_page", lambda: "<p>every 5 days</p>")
    check_docs.check_leitner_intervals(errors)
    assert errors, "an interval the module does not define must be reported"
    assert "every 5 days" in " ".join(errors)


def test_the_shipped_page_agrees_with_the_module():
    errors = []
    check_docs.check_leitner_intervals(errors)
    assert not errors, errors


def test_the_print_skill_offers_the_setup_command(monkeypatch):
    """Principle XI for a prompt change: the only assertable artifact.

    In `check_docs.py`, not `check_project.py`. That gate validates a *user's*
    project; `skills/*/SKILL.md` belongs to this repository and is already read
    here (`check_skills`). See issue #89 for the constitution wording.
    """
    errors = []
    monkeypatch.setattr(check_docs, "read_skill", lambda name: "print the cards and stop")
    check_docs.check_print_skill_relays_setup(errors)
    assert errors, "a print skill that never mentions the setup command must be reported"
    assert "lernkarten setup" in " ".join(errors)

    monkeypatch.undo()
    errors = []
    check_docs.check_print_skill_relays_setup(errors)
    assert not errors, errors


def test_the_constitutions_import_graph_matches_the_real_imports():
    """Principle VI documents the graph; nothing checked that it was true.

    It drifted: `cardid` and `figures` existed and were imported for releases
    without appearing in it, and `build_pdf -> cardid` with them. A contributor
    writing an acyclicity test against the *document* would have produced a
    test that passed while the repository disagreed with it — which is the
    failure Principle VI's own governance clause is about.
    """
    errors = []
    check_docs.check_import_graph(errors)
    assert not errors, errors


def test_a_module_missing_from_the_graph_is_reported(monkeypatch):
    documented = check_docs.documented_graph()
    dropped = dict(documented)
    dropped.pop("build_pdf", None)
    monkeypatch.setattr(check_docs, "documented_graph", lambda: dropped)

    errors = []
    check_docs.check_import_graph(errors)
    assert errors, "a module the graph forgets must be reported"
    assert "build_pdf" in " ".join(errors)


# --- The enumeration tier table (011) ---------------------------------------
#
# The first check in this repository about a skill's own text. Constitution XI
# puts it here rather than in check_project.py: the rule is about what
# `skills/cards/SKILL.md` must *contain*, not about what /cards writes into a
# user's project.


TIERLESS_SKILL = """---
name: cards
description: Generate flashcards about a topic.
---

## Style rules

- Write the cards well.
"""

TIERED_SKILL = """---
name: cards
description: Generate flashcards about a topic.
---

## Style rules

| items | shape |
|---|---|
| 1-2 | a sentence |
| 3-5 | a flat `#list`, exactly n items |
| 6-8 | one card, grouped: `#list([*Discover*: a, b], [*Define*: c, d])` |
| 9+ | an anchor card plus one card per group |
"""


def test_a_cards_skill_without_a_tier_table_is_reported(tmp_path, monkeypatch):
    skill = tmp_path / "SKILL.md"
    skill.write_text(TIERLESS_SKILL, encoding="utf-8")
    monkeypatch.setattr(check_docs, "CARDS_SKILL", skill)
    errors = []
    check_docs.check_enumeration_tiers(errors)
    assert errors, "a skill with no tier table has to be reported"
    assert any("tier" in e for e in errors), errors


def test_a_cards_skill_with_the_tier_table_passes(tmp_path, monkeypatch):
    skill = tmp_path / "SKILL.md"
    skill.write_text(TIERED_SKILL, encoding="utf-8")
    monkeypatch.setattr(check_docs, "CARDS_SKILL", skill)
    errors = []
    check_docs.check_enumeration_tiers(errors)
    assert not errors, errors


def test_the_shipped_cards_skill_states_the_tiers():
    errors = []
    check_docs.check_enumeration_tiers(errors)
    assert not errors, errors


def test_the_tier_table_agrees_with_the_checker_constants():
    """The one place the table and the code could drift, closed by a test.

    `check_docs.py` cannot import `check_project` — constitution VI documents
    the import graph and `check_docs.check_import_graph` enforces it — so the
    numeric half of the agreement lives here, where a test may import both.
    """
    skill = (ROOT / "skills" / "cards" / "SKILL.md").read_text(encoding="utf-8")
    flat, grouped = check_project.FLAT_MAX, check_project.GROUPED_MAX
    assert f"| 3\u2013{flat} |" in skill or f"| 3-{flat} |" in skill, (
        f"the flat tier has to end at {flat}, the value check_project uses"
    )
    assert f"| {flat + 1}\u2013{grouped} |" in skill or f"| {flat + 1}-{grouped} |" in skill, (
        f"the grouped tier has to run {flat + 1} to {grouped}"
    )
    assert f"| {grouped + 1}+ |" in skill, f"the top tier has to start at {grouped + 1}"


# --- the documentation site is inside the gates (FR-037, SC-011) ---


def test_check_docs_covers_the_docsite(tmp_path, monkeypatch):
    """Every page under `docsite/` is a file the four gates can see.

    Asserting this against the real repository would pass today and prove
    nothing: `docsite/` does not exist yet, and an empty set satisfies
    "returns every one of them". So the tree is built here instead, which is
    also the only way to show the glob is *recursive* — the two existing globs
    are not, and a page two levels down is the normal case rather than the
    exception.

    What is at stake is not tidiness. Six drift gates and the dead-link check
    read this list, and they exist because this repository shipped the same
    contradiction twice. A page outside it could claim eight cards to an A4
    sheet and no gate would object.
    """
    gated_project(
        tmp_path,
        monkeypatch,
        **{
            "docsite__index.md": "# The site\n",
            "docsite__user__workflow.md": "# The workflow\n",
            "docsite__contributing__design.md": "# The design\n",
        },
    )

    found = {p.relative_to(tmp_path).as_posix() for p in check_docs.markdown_files()}
    expected = {
        "docsite/index.md",
        "docsite/user/workflow.md",
        "docsite/contributing/design.md",
    }
    assert expected <= found, (
        f"markdown_files() misses {sorted(expected - found)}. Every drift gate and the "
        f"dead-link check read this list, so a page it cannot see is a page no gate "
        f"guards. It returned {sorted(found)}"
    )
