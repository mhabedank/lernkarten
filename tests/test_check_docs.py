"""The documentation checker itself.

`scripts/check_docs.py` had no coverage at all until the goal-driven catalog
added a rule to it. The rule: a skill description has to name this plugin's
domain, not only its triggers — `/catalog` and `/research` are words any
installed skill might claim, and the plugin ships into environments this repo
cannot inspect.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_docs  # noqa: E402

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
