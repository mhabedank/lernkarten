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


def test_the_shipped_docsite_is_covered():
    """And the same holds for the pages this repository actually ships.

    The monkeypatched case above is the one that can be red, and it stays.
    This one cannot fail for the reason that one can — but it fails if
    somebody adds a page in a shape the glob does not reach, which the fixture
    tree cannot anticipate because it only contains what it was told to.
    """
    docsite = check_docs.ROOT / "docsite"
    shipped = {p.relative_to(check_docs.ROOT).as_posix() for p in docsite.rglob("*.md")}
    covered = {p.relative_to(check_docs.ROOT).as_posix() for p in check_docs.markdown_files()}

    assert shipped, "docsite/ holds no pages — this assertion has nothing to check"
    assert shipped <= covered, (
        f"these shipped pages are outside markdown_files(): {sorted(shipped - covered)}"
    )


# --- Wave G: no doc claims one step is the only one that goes online (FR-034) ---


def test_a_doc_claiming_the_only_step_that_reaches_the_network_is_reported(tmp_path, monkeypatch):
    """G1 — the claim `/research-gaps` shipped with, and it was never true."""
    gated_project(
        tmp_path,
        monkeypatch,
        **{
            "skills__research-gaps__SKILL.md": (
                "**This is the only step that reaches the network**, and the only one\n"
                "that puts material into the project the user did not choose.\n"
            )
        },
    )

    errors = []
    check_docs.check_network_claim_is_not_exclusive(errors)

    assert errors, "an exclusivity claim about the network must be reported"
    assert any("research-gaps/SKILL.md" in e.replace("\\", "/") for e in errors), (
        f"the message does not name the file at fault: {errors}"
    )


def test_a_true_sentence_about_a_push_reaching_the_network_passes(tmp_path, monkeypatch):
    """G2 — CONTRIBUTING.md:82, verbatim. The gate is scoped to the exclusivity.

    A bare `reaches the network` substring would fire here, on a sentence about
    git that says nothing about which pipeline step goes online.
    """
    gated_project(
        tmp_path,
        monkeypatch,
        **{
            "CONTRIBUTING.md": (
                "Install the local hook once, and an accidental push to `main` fails "
                "before it\neven reaches the network:\n"
            )
        },
    )

    errors = []
    check_docs.check_network_claim_is_not_exclusive(errors)

    assert not errors, errors


def test_no_shipped_doc_claims_one_step_is_the_only_one_online():
    """G3 — over the real gated set, which is what FR-034 is about."""
    errors = []
    check_docs.check_network_claim_is_not_exclusive(errors)
    assert not errors, errors


# --- Wave C: /sources weighs a source against the learning goal (FR-001 - FR-009) ---

GOAL_FIT_SENTENCES = {
    "reads the goal": "Before writing an entry, read `goal.md`.",
    "advisory": (
        "The assessment is advisory and never blocking: the entry is written whatever the "
        "verdict, and the run does not pause to ask."
    ),
    "at registration": (
        "The assessment happens at registration. A listing does not re-assess what is "
        "already registered."
    ),
}


def sources_skill(without=(), sentences=None):
    """A synthetic `sources` skill carrying every rule but the named one.

    One negative case per rule: a case whose input is missing *everything* would
    pass against a check that forgot to assert one of them.
    """
    parts = sentences if sentences is not None else GOAL_FIT_SENTENCES
    body = "\n\n".join(text for key, text in parts.items() if key not in without)
    return f"# /sources\n\n## Goal fit\n\n{body}\n"


def with_sources_skill(monkeypatch, body):
    monkeypatch.setattr(check_docs, "read_skill", lambda name: body if name == "sources" else "")


def test_a_sources_skill_that_never_names_the_goal_file_is_reported(monkeypatch):
    """C1 — the whole of piece A hangs off reading `goal.md` (FR-001)."""
    with_sources_skill(monkeypatch, "# /sources\n\nRegister, list or remove knowledge sources.\n")

    errors = []
    check_docs.check_sources_skill_reads_the_goal(errors)

    assert errors, "a sources skill that never names goal.md must be reported"
    assert any("goal.md" in e for e in errors), (
        f"the message does not say what is missing: {errors}"
    )
    assert any("sources/SKILL.md" in e.replace("\\", "/") for e in errors), errors


def test_a_sources_skill_that_does_not_call_the_assessment_advisory_is_reported(monkeypatch):
    """C2 — advisory and never blocking, or the register stops being the user's (FR-002)."""
    with_sources_skill(monkeypatch, sources_skill(without=("advisory",)))

    errors = []
    check_docs.check_sources_skill_reads_the_goal(errors)

    assert errors, "a sources skill that never says the assessment is advisory must be reported"
    assert any("advisory" in e for e in errors), f"the message does not name the rule: {errors}"


def test_a_sources_skill_that_does_not_say_when_the_assessment_happens_is_reported(monkeypatch):
    """C3 — at registration, and a listing does not re-judge the register (FR-008)."""
    with_sources_skill(monkeypatch, sources_skill(without=("at registration",)))

    errors = []
    check_docs.check_sources_skill_reads_the_goal(errors)

    assert errors, "a sources skill that never says when the assessment happens must be reported"
    assert any("at registration" in e for e in errors), (
        f"the message does not name the rule: {errors}"
    )


def test_the_shipped_sources_skill_reads_the_goal():
    """C5, first half — the guard over the file that ships."""
    errors = []
    check_docs.check_sources_skill_reads_the_goal(errors)
    assert not errors, errors


GOAL_FIT_SENTENCES.update(
    {
        "warning": (
            "An off-goal warning names the source `id` and the line of `goal.md` it conflicts with."
        ),
        "kind and depth": (
            "Reason from the `kind` and the `depth` in `goal.md`, and say which of the two "
            "you used."
        ),
        "no goal": (
            "With no `goal.md` there is no assessment and no warning, and at most one line "
            "per run points at `/learning-goal`."
        ),
        "never invent": (
            "Never invent a claim about a source you have not looked at: where you reason "
            "from the URL, the `note` and the `type` alone, say so."
        ),
    }
)


def test_a_sources_skill_that_does_not_say_what_a_warning_names_is_reported(monkeypatch):
    """C6 — a bare "this looks off-goal" is the thing FR-003 forbids."""
    with_sources_skill(monkeypatch, sources_skill(without=("warning",)))

    errors = []
    check_docs.check_sources_skill_reads_the_goal(errors)

    assert errors, "a sources skill that never says what an off-goal warning names is a defect"
    assert any("FR-003" in e for e in errors), f"the message does not name the rule: {errors}"


def test_a_sources_skill_that_does_not_reason_from_kind_and_depth_is_reported(monkeypatch):
    """C7 — and it has to say which of the two it used (FR-005)."""
    with_sources_skill(monkeypatch, sources_skill(without=("kind and depth",)))

    errors = []
    check_docs.check_sources_skill_reads_the_goal(errors)

    assert errors, "a sources skill that never names `kind` and `depth` must be reported"
    assert any("FR-005" in e for e in errors), f"the message does not name the rule: {errors}"


def test_a_sources_skill_that_does_not_handle_an_absent_goal_is_reported(monkeypatch):
    """C8 — no goal, no assessment, and one pointer per run rather than one per source."""
    with_sources_skill(monkeypatch, sources_skill(without=("no goal",)))

    errors = []
    check_docs.check_sources_skill_reads_the_goal(errors)

    assert errors, "a sources skill that never says what happens without a goal is a defect"
    assert any("FR-006" in e for e in errors), f"the message does not name the rule: {errors}"


def test_a_sources_skill_that_may_invent_a_claim_about_a_source_is_reported(monkeypatch):
    """C9 — the rule `/research-gaps` already holds, applied to a source nobody read."""
    with_sources_skill(monkeypatch, sources_skill(without=("never invent",)))

    errors = []
    check_docs.check_sources_skill_reads_the_goal(errors)

    assert errors, "a sources skill that never refuses to invent a claim must be reported"
    assert any("FR-009" in e for e in errors), f"the message does not name the rule: {errors}"


ARCHIVE_REACH_SENTENCE = (
    "Registering an archive as `type: web` with `depth: 1` reaches the index page plus the "
    "posts on the same domain linked from it, capped at 20. Say so at registration."
)


def test_a_sources_skill_that_does_not_state_the_archive_reach_is_reported(monkeypatch):
    """C4 — a user registering a ten-year archive learns the reach here, or at /ingest."""
    with_sources_skill(monkeypatch, sources_skill())

    errors = []
    check_docs.check_sources_skill_states_the_archive_reach(errors)

    assert errors, "a sources skill that never states the archive reach must be reported"
    assert any("FR-029" in e for e in errors), f"the message does not name the rule: {errors}"
    assert any("sources/SKILL.md" in e.replace("\\", "/") for e in errors), errors


def test_a_sources_skill_stating_the_archive_reach_passes(monkeypatch):
    with_sources_skill(monkeypatch, sources_skill() + "\n" + ARCHIVE_REACH_SENTENCE + "\n")

    errors = []
    check_docs.check_sources_skill_states_the_archive_reach(errors)

    assert not errors, errors


def test_the_shipped_sources_skill_states_the_archive_reach():
    """C5, second half — the guard over the file that ships."""
    errors = []
    check_docs.check_sources_skill_states_the_archive_reach(errors)
    assert not errors, errors


# --- Wave D: the discovery mode of /sources — C1, the neutral contract ---

# One sentence per rule, and every one of them class-neutral: not a word here
# names practitioner material, an incident, a post-mortem or a company blog.
# Case D5 is what holds that, by deleting the addendum and expecting silence.
DISCOVERY_SENTENCES = {
    "discover": "Entered as `/sources --discover`, or the same request in words.",
    "writes nothing": "Discovery writes nothing until the user picks.",
    "counts": (
        "Say how many candidates you found and how many you are showing. Group them by the "
        "area of the goal they serve, and list every area — including the ones where "
        "nothing was found."
    ),
    "caps": "Show at most 3 candidates per area and at most 10 in one run.",
    "credibility": (
        "Credibility is one sentence naming what the source is and what it is not, never a "
        "score and never a rating."
    ),
    "class": "Each candidate says which class of material it is, in its own words.",
    "never invent": "Never invent a candidate: what you did not retrieve is not a candidate.",
    "paywalled": (
        "Paywalled or login-gated material is reported as found and never proposed, and you "
        "never enter credentials."
    ),
    "already registered": "A source already in `sources.yaml` is never proposed.",
    "no goal": (
        "With no goal there is nothing to search for: point at `/learning-goal` and write nothing."
    ),
    "no network": ("With no network, say you could not search, write nothing and exit cleanly."),
    "ordinary path": "Picked entries go through the ordinary registration path.",
    "seam": (
        "Write no documents into `knowledge/` and create no `type: research` entry — that is "
        "what `/research-gaps` does."
    ),
    "network": "`/sources` reaches the network only in discovery mode.",
}


def discovery_skill(without=()):
    """A synthetic `sources` skill carrying every discovery rule but the named one."""
    return sources_skill(without=without, sentences=DISCOVERY_SENTENCES)


@pytest.mark.parametrize(
    ("rule", "needle"),
    [
        ("discover", "--discover"),
        ("counts", "FR-027"),
        ("caps", "R3"),
        ("credibility", "FR-018"),
        ("paywalled", "FR-023"),
        ("already registered", "FR-024"),
        ("no goal", "FR-025"),
        ("no network", "FR-026"),
        ("ordinary path", "FR-020"),
        ("network", "FR-033"),
        ("writes nothing", "until the user picks"),
        ("never invent", "FR-021"),
        ("seam", "FR-022"),
        ("class", "FR-017"),
    ],
    ids=[
        "D1-no-discovery-mode",
        "D1a-counts-and-grouping",
        "D1b-caps",
        "D1c-credibility-is-a-sentence",
        "D1d-paywalled",
        "D1e-already-registered",
        "D1f-no-goal",
        "D1g-no-network",
        "D1h-ordinary-registration-path",
        "D1i-network-only-in-discovery",
        "D2-writes-nothing-until-picked",
        "D3-never-invent",
        "D4-the-research-gaps-seam",
        "D8-the-class-of-material",
    ],
)
def test_a_discovery_contract_missing_one_rule_is_reported(monkeypatch, rule, needle):
    """D1, D1a-D1i, D2-D4, D8 — one negative case per rule, so a failure names it.

    A single case whose input is missing *everything* would pass against a check
    that forgot to assert one of these rules.
    """
    with_sources_skill(monkeypatch, discovery_skill(without=(rule,)))

    errors = []
    check_docs.check_sources_skill_carries_the_discovery_contract(errors)

    assert errors, f"a discovery contract missing '{rule}' must be reported"
    assert any(needle in e for e in errors), f"the message does not name the rule: {errors}"
    assert any("sources/SKILL.md" in e.replace("\\", "/") for e in errors), errors


def test_a_complete_synthetic_discovery_contract_passes(monkeypatch):
    """The other half of the per-rule cases: the full text reports nothing."""
    with_sources_skill(monkeypatch, discovery_skill())

    errors = []
    check_docs.check_sources_skill_carries_the_discovery_contract(errors)

    assert not errors, errors


def test_the_shipped_sources_skill_carries_the_discovery_contract():
    """D7, first half — the guard over the file that ships."""
    errors = []
    check_docs.check_sources_skill_carries_the_discovery_contract(errors)
    assert not errors, errors


# --- Wave D: C2, the practitioner addendum (FR-019) ---

ADDENDUM_TEXT = """### Practitioner material

For practitioner material the credibility sentence names two more things: that a
company's account of its own incident is a primary source and an interested one,
and that material like this is published only by the parties who came through
the incident, so the cases that ended badly are not among what can be found.
"""


def test_a_sources_skill_without_the_practitioner_addendum_is_reported(monkeypatch):
    """D6 — the addendum is a check of its own, so it can fail on its own."""
    with_sources_skill(monkeypatch, discovery_skill())

    errors = []
    check_docs.check_sources_skill_carries_the_practitioner_addendum(errors)

    assert errors, "a sources skill missing the practitioner addendum must be reported"
    assert any("FR-019" in e for e in errors), f"the message does not name the rule: {errors}"
    assert any("sources/SKILL.md" in e.replace("\\", "/") for e in errors), errors


def test_a_synthetic_skill_carrying_the_addendum_passes(monkeypatch):
    with_sources_skill(monkeypatch, discovery_skill() + "\n" + ADDENDUM_TEXT)

    errors = []
    check_docs.check_sources_skill_carries_the_practitioner_addendum(errors)

    assert not errors, errors


def test_the_shipped_sources_skill_carries_the_practitioner_addendum():
    """D7, second half — the guard over the file that ships."""
    errors = []
    check_docs.check_sources_skill_carries_the_practitioner_addendum(errors)
    assert not errors, errors


# --- Wave D: the two layers come apart (FR-039, SC-016) ---

# The heading the practitioner addendum opens with, in `skills/sources/SKILL.md`.
# The excision below finds the sub-section by this exact string, so renaming the
# heading fails here by name instead of silently cutting nothing.
ADDENDUM_HEADING = "### Practitioner material"

# Words a neutral C1 assertion may not contain. A check that named one of them
# would be a rule about one class of material written into the contract that is
# supposed to hold for all of them.
CLASS_WORDS = ("practitioner", "incident", "post-mortem", "postmortem", "company blog")


def without_the_addendum(body):
    """Cut from the addendum heading to the next heading of equal or higher level."""
    lines = body.splitlines(keepends=True)
    start = [i for i, line in enumerate(lines) if line.strip() == ADDENDUM_HEADING]
    assert start, f"no line reading {ADDENDUM_HEADING!r} to cut from"
    first = start[0]
    rest = [i for i in range(first + 1, len(lines)) if re.match(r"^#{1,3}\s", lines[i])]
    return "".join(lines[:first] + lines[rest[0] if rest else len(lines) :])


def test_the_neutral_contract_survives_deleting_the_addendum(monkeypatch):
    """D5 — a guard, and deliberately not a red artifact.

    It runs against synthetic text through the `read_skill` seam, so the state of
    the shipped skill is irrelevant to it: once the neutral check exists it
    passes. The only way to make it fail is to write a *non-neutral* C1 check,
    which is the defect FR-039 exists to prevent — so a red here would be the
    defect, not the discipline. D5b is the half that tests SC-016 against the
    file that ships; neither replaces the other.
    """
    with_sources_skill(monkeypatch, without_the_addendum(discovery_skill() + "\n" + ADDENDUM_TEXT))

    errors = []
    check_docs.check_sources_skill_carries_the_discovery_contract(errors)

    assert not errors, f"a C1 assertion depends on the addendum: {errors}"

    # The entry condition is C1-level too: it is the same whatever a candidate
    # turns out to be, so an addendum touches none of it either.
    for rules in (check_docs.DISCOVERY_RULES, check_docs.EXPLICIT_REQUEST_RULES):
        written = " ".join(
            what + " " + " ".join(p.pattern for p in patterns) for what, patterns in rules
        ).lower()
        for word in CLASS_WORDS:
            assert word not in written, f"a neutral C1 assertion names '{word}'"


def test_excising_the_addendum_from_the_shipped_skill_fails_exactly_one_check(monkeypatch):
    """D5b — separability, asserted against the file that ships (SC-016).

    No synthetic text: SC-016 is a claim about `skills/sources/SKILL.md`, and a
    synthetic version of this test — written by the same author, against text
    that author wrote to pass — could not be false. The neutral check greps the
    whole body, so a token it demands that happened to be stated only inside the
    addendum would break SC-016 with nothing noticing.

    **Five checks**: every function that reads `skills/sources/SKILL.md`. One of
    them fails on the excision and four stay green, which is SC-016's "exactly
    one" over the complete set rather than over whichever subset existed when
    this case was written.
    """
    body = check_docs.read_skill("sources")
    assert ADDENDUM_HEADING in body, (
        f"the shipped sources skill carries no line reading {ADDENDUM_HEADING!r}, so the "
        "excision below would cut nothing and this test would pass for the wrong reason"
    )

    with_sources_skill(monkeypatch, without_the_addendum(body))

    reported = []
    check_docs.check_sources_skill_carries_the_practitioner_addendum(reported)
    assert reported, "excising the addendum has to fail the addendum check"

    for check in (
        check_docs.check_sources_skill_carries_the_discovery_contract,
        check_docs.check_sources_skill_reads_the_goal,
        check_docs.check_sources_skill_states_the_archive_reach,
        check_docs.check_sources_skill_states_the_explicit_request,
    ):
        clean = []
        check(clean)
        assert not clean, f"{check.__name__} depends on the addendum sub-section: {clean}"


# --- Wave E: discovery is entered only when the user asks (FR-035, FR-036) ---

# Class-neutral, like the C1 sentences above: the entry condition is the same
# whatever a candidate turns out to be, so no sentence here names a class of
# material and no addendum touches any of it (FR-039).
SILENCE_SENTENCES = {
    "explicit request": ("Discovery is entered only on an explicit request, made at invocation."),
    "never offered": (
        "It never starts by itself, it is never offered as a follow-up at the end of an "
        "ordinary run, and it is never the default of any invocation."
    ),
    "ordinary run": (
        "An ordinary run — registering a source the user named, listing the register, "
        "removing a source — neither enters discovery nor mentions it: no candidate, no "
        "proposal, no closing line suggesting the user could go looking."
    ),
}


def silence_skill(without=()):
    """A synthetic `sources` skill carrying every explicit-request rule but the named one."""
    return sources_skill(without=without, sentences=SILENCE_SENTENCES)


@pytest.mark.parametrize(
    ("rule", "needle"),
    [
        ("explicit request", "only on an explicit request"),
        ("never offered", "follow-up"),
        ("ordinary run", "FR-036"),
    ],
    ids=[
        "E3-entered-only-on-an-explicit-request",
        "E3-never-offered-by-itself",
        "E3-an-ordinary-run-is-silent",
    ],
)
def test_a_sources_skill_that_may_start_discovery_by_itself_is_reported(monkeypatch, rule, needle):
    """E3 — one negative case per rule, so a failure names the rule that left the prompt.

    A single case whose input states none of the three would pass against a check
    that forgot to assert one of them.
    """
    with_sources_skill(monkeypatch, silence_skill(without=(rule,)))

    errors = []
    check_docs.check_sources_skill_states_the_explicit_request(errors)

    assert errors, f"a sources skill missing '{rule}' must be reported"
    assert any(needle in e for e in errors), f"the message does not name the rule: {errors}"
    assert any("sources/SKILL.md" in e.replace("\\", "/") for e in errors), errors


def test_a_synthetic_skill_stating_the_explicit_request_passes(monkeypatch):
    """The other half of the per-rule cases: the full text reports nothing."""
    with_sources_skill(monkeypatch, silence_skill())

    errors = []
    check_docs.check_sources_skill_states_the_explicit_request(errors)

    assert not errors, errors


def test_the_shipped_sources_skill_states_the_explicit_request():
    """E3, the shipped half — the guard over the file that ships."""
    errors = []
    check_docs.check_sources_skill_states_the_explicit_request(errors)
    assert not errors, errors


# --- Wave E: no other step points at discovery (FR-037) ---

# A pointer somebody adds is the form the drift takes, so the gate is a token
# check over the five skills that may not carry it. `/research-gaps` is not one
# of them and cannot be — FR-034 makes it state the seam against
# `/sources --discover` — which is recorded in spec § Assumptions.
POINTER = "Once you are done, `/sources --discover` will find you more material.\n"


def with_skill(monkeypatch, which, body):
    """Hand one named skill a body; every other skill reads as empty."""
    monkeypatch.setattr(check_docs, "read_skill", lambda name: body if name == which else "")


@pytest.mark.parametrize(
    "skill",
    ["catalog", "ingest", "cards", "print", "learning-goal"],
    ids=["E1-catalog", "E2-ingest", "E2-cards", "E2-print", "E2a-learning-goal"],
)
def test_a_skill_that_points_at_discovery_is_reported(monkeypatch, skill):
    """E1, E2, E2a — the gate fires, and the message names the file."""
    with_skill(monkeypatch, skill, f"# /{skill}\n\n{POINTER}")

    errors = []
    check_docs.check_discovery_is_not_offered_elsewhere(errors)

    assert errors, f"`--discover` in skills/{skill}/SKILL.md must be reported"
    assert any(f"skills/{skill}/SKILL.md" in e for e in errors), (
        f"the message does not name the file: {errors}"
    )


def test_the_ordinary_word_discovered_is_not_the_token(monkeypatch):
    """The scoping half, the shape of wave G's G2.

    `skills/catalog/SKILL.md` says a step "gets discovered at all" and
    `scripts/build_pdf.py` uses the word too. The gate is the exact token
    `--discover`, never the English word.
    """
    with_skill(monkeypatch, "catalog", "# /catalog\n\nSay so once, or no step gets discovered.\n")

    errors = []
    check_docs.check_discovery_is_not_offered_elsewhere(errors)

    assert not errors, errors


def test_no_shipped_skill_but_sources_points_at_discovery():
    """E4 — the shipped-repo guard, and the point is that it stays green."""
    errors = []
    check_docs.check_discovery_is_not_offered_elsewhere(errors)
    assert not errors, errors


def test_the_gate_never_reads_the_sources_skill(monkeypatch):
    """Neither wave-E function reads the other's text.

    `skills/sources/SKILL.md` carries `--discover` by design, so a gate that
    happened to read it would report the sentence the feature asks for.
    """
    with_skill(monkeypatch, "sources", f"# /sources\n\n{POINTER}")

    errors = []
    check_docs.check_discovery_is_not_offered_elsewhere(errors)

    assert not errors, errors


# --- Wave F: the experience-report rule in three prompts (FR-010 - FR-015) ---

# FR-013 binds `/catalog` and `/cards` alike, so both are held to the same four
# contents. The sentences are written out here rather than built from the check's
# own rule table: a synthetic input derived from the thing under test could not
# be false.
MATERIAL_BASE_SENTENCES = {
    "which subtopic": (
        "Name which subtopic the warning is about and what it rests on — the documents "
        "named or counted — and say that nothing covering the topic in general is among "
        "them."
    ),
    "why it is skewed": (
        "Write out why that base is skewed: write-ups like these get published by the "
        "parties who came through the incident and had an account they were willing to "
        "show, and whoever it ended badly for publishes nothing."
    ),
    "what it means": (
        "Say what that means for the cards: they show how a survived failure unfolded, "
        "not what it takes to fail for good."
    ),
    "what would balance it": (
        "Say what would balance it — a general account or a reference work on the topic."
    ),
    "own words": (
        'Write it in your own words. There is no phrase to copy, and "a selected sample" '
        "names the effect instead of stating it."
    ),
    "advisory": "The warning is advisory: it blocks nothing and refuses nothing.",
}

EXPERIENCE_SENTENCES = {
    "ingest": {
        "writes the marker": (
            "A document whose subject is a reported case is written with `nature: experience`."
        ),
        "absence is the other state": (
            "Everything else gets no `nature:` key at all — absence is the other state."
        ),
    },
    "catalog": {
        "evidence not rule": (
            "A `nature: experience` document is evidence about one situation, never a "
            "statement of a general rule."
        ),
        "coverage of the rule": (
            "A required topic covered only by experience reports is reported as such, never "
            "presented as coverage of the rule."
        ),
        **MATERIAL_BASE_SENTENCES,
    },
    "cards": {
        "about the case": (
            "A card drawn from a `nature: experience` document is phrased about the reported "
            "case and names it through the existing `source:` key."
        ),
        "not a general rule": ("It is never phrased as an unattributed general rule."),
        "the scale": (
            "A fact that depends on the scale or the circumstances of the case carries them "
            "rather than dropping them."
        ),
        **MATERIAL_BASE_SENTENCES,
    },
}


def experience_skills(skill=None, without=()):
    """The three synthetic skills, with one rule missing from one of them."""
    return {
        name: "\n\n".join(
            text for key, text in sentences.items() if not (name == skill and key in without)
        )
        for name, sentences in EXPERIENCE_SENTENCES.items()
    }


def with_skills(monkeypatch, bodies):
    monkeypatch.setattr(check_docs, "read_skill", lambda name: bodies.get(name, ""))


@pytest.mark.parametrize(
    ("skill", "rule", "needle"),
    [
        ("ingest", "writes the marker", "nature: experience"),
        ("ingest", "absence is the other state", "no `nature:` key"),
        ("catalog", "evidence not rule", "FR-010"),
        ("catalog", "coverage of the rule", "FR-014"),
        ("catalog", "which subtopic", "FR-013.1"),
        ("catalog", "why it is skewed", "FR-013.2"),
        ("catalog", "what it means", "FR-013.3"),
        ("catalog", "what would balance it", "FR-013.4"),
        ("catalog", "own words", "own words"),
        ("catalog", "advisory", "advisory"),
        ("cards", "about the case", "FR-011"),
        ("cards", "not a general rule", "unattributed"),
        ("cards", "the scale", "FR-012"),
        ("cards", "which subtopic", "FR-013.1"),
        ("cards", "why it is skewed", "FR-013.2"),
        ("cards", "what it means", "FR-013.3"),
        ("cards", "what would balance it", "FR-013.4"),
        ("cards", "own words", "own words"),
        ("cards", "advisory", "advisory"),
    ],
)
def test_a_skill_that_lost_the_experience_rule_is_reported(monkeypatch, skill, rule, needle):
    """F1, F2, F3 — one negative case per rule per skill, so a failure names both.

    The FR-013 rows appear twice on purpose: the requirement binds `/catalog`
    **and** `/cards`, and the assertion made of the second is the same one made
    of the first.
    """
    with_skills(monkeypatch, experience_skills(skill=skill, without=(rule,)))

    errors = []
    check_docs.check_skills_carry_the_experience_rule(errors)

    assert errors, f"skills/{skill}/SKILL.md missing '{rule}' must be reported"
    named = [e for e in errors if f"skills/{skill}/SKILL.md" in e]
    assert named, f"the message does not name the file at fault: {errors}"
    assert any(needle in e for e in named), f"the message does not name the rule: {named}"


def test_three_complete_synthetic_skills_pass(monkeypatch):
    """The other half of the per-rule cases: the full text reports nothing."""
    with_skills(monkeypatch, experience_skills())

    errors = []
    check_docs.check_skills_carry_the_experience_rule(errors)

    assert not errors, errors


def test_the_shipped_skills_carry_the_experience_rule():
    """F4 — the guard over the three files that ship."""
    errors = []
    check_docs.check_skills_carry_the_experience_rule(errors)
    assert not errors, errors
