"""The project settings file: `lernkarten.yaml`.

A seventh artifact, deliberately outside the six formats Principle I couples
the two halves with. It holds *choices*, never content, and it is gitignored
like everything else a user owns.

What these cases protect is mostly the distinctions that are easy to collapse:
absent is not declined, an unknown key is not a fatal error, and the file a
build reads is the one `setup` wrote.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import settings  # noqa: E402
import yamlio  # noqa: E402


def project(tmp_path, text=None):
    """A project directory with a deck in it, and optionally a settings file."""
    (tmp_path / "cards").mkdir()
    deck = tmp_path / "cards" / "deck.yaml"
    deck.write_text("topic: 'T'\ncards:\n  - front: 'a'\n    back: 'b'\n", encoding="utf-8")
    if text is not None:
        (tmp_path / "lernkarten.yaml").write_text(text, encoding="utf-8")
    return deck


def test_absent_and_empty_are_the_same_thing_and_neither_is_declined(tmp_path):
    """Three states, not two — collapsing any pair breaks the advisory.

    Absent means never asked, so the run says so once. `none` means asked and
    declined, so it says nothing. An empty file is absence: a file that exists
    but answers nothing has not answered anything.
    """
    absent = settings.load(project(tmp_path))
    assert absent.compartments is None and absent.unanswered

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    empty = settings.load(project(empty_dir, ""))
    assert empty.compartments is None and empty.unanswered, "an empty file is absence"

    declined_dir = tmp_path / "declined"
    declined_dir.mkdir()
    declined = settings.load(project(declined_dir, "compartments: none\n"))
    assert declined.compartments is None
    assert not declined.unanswered, "asked and declined is not the same as never asked"


def test_an_answered_file_is_read_back(tmp_path):
    deck = project(
        tmp_path,
        "compartments: 4\ndividers_printed: true\nbox_printed: false\n",
    )
    s = settings.load(deck)
    assert (s.compartments, s.dividers_printed, s.box_printed) == (4, True, False)
    assert not s.unanswered


def test_an_unknown_key_warns_and_the_run_continues(tmp_path):
    """FR-016a. Never fatal, because #67 will add keys to this same file.

    A hard error would make a project written by a newer version unbuildable by
    an older one, which is exactly the additivity FR-019 promises. A typo is
    caught just as reliably, because the warning appears on every run.
    """
    deck = project(tmp_path, "compartments: 4\ncompartment: 3\n")
    s = settings.load(deck)
    assert s.compartments == 4, "the known key still takes effect"
    assert len(s.warnings) == 1
    warning = s.warnings[0]
    assert "compartment" in warning
    assert "lernkarten.yaml" in warning
    assert "compartments" in warning, "the warning names the keys this version knows"


def test_an_invalid_value_on_a_known_key_is_fatal(tmp_path):
    """FR-016b. Unlike an unknown key, an unusable value cannot be carried
    forward: there is no safe reading of `compartments: 5`."""
    deck = project(tmp_path, "compartments: 5\n")
    with pytest.raises(settings.SettingsError) as e:
        settings.load(deck)
    assert "compartments" in str(e.value)
    assert "3" in str(e.value) and "4" in str(e.value), "the error names the accepted values"


def test_a_malformed_file_reports_where(tmp_path):
    deck = project(tmp_path, "compartments: [4\n")
    with pytest.raises((settings.SettingsError, yamlio.YamlError)) as e:
        settings.load(deck)
    assert "lernkarten.yaml" in str(e.value)


def test_the_file_is_found_beside_the_cards_not_in_the_working_directory(tmp_path, monkeypatch):
    """FR-021: the same root a picture path resolves against.

    A file picked up from wherever the command happened to run would make the
    repository's own end-to-end suite depend on a developer's private one —
    `run()` there uses `cwd=ROOT`.
    """
    deck = project(tmp_path, "compartments: 4\n")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "lernkarten.yaml").write_text("compartments: 3\n", encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    assert settings.load(deck).compartments == 4, "the cwd must not win"


def test_saving_writes_the_three_keys_and_reads_back(tmp_path):
    deck = project(tmp_path)
    settings.save(tmp_path, compartments=3, dividers_printed=False, box_printed=True)
    written = (tmp_path / "lernkarten.yaml").read_text(encoding="utf-8")
    assert "compartments: 3" in written
    s = settings.load(deck)
    assert (s.compartments, s.dividers_printed, s.box_printed) == (3, False, True)


def test_write_back_never_creates_the_file(tmp_path):
    """FR-020: a build marks the dividers printed, but only into an answered file.

    Creating one would invent a fourth state — `dividers_printed: true` with no
    `compartments` — that the three-state table does not have.
    """
    project(tmp_path)
    settings.mark_printed(tmp_path, dividers=True)
    assert not (tmp_path / "lernkarten.yaml").exists(), "no file, no write-back"


def test_write_back_only_touches_an_answered_file(tmp_path):
    project(tmp_path, "compartments: none\n")
    settings.mark_printed(tmp_path, dividers=True)
    assert "dividers_printed" not in (tmp_path / "lernkarten.yaml").read_text(encoding="utf-8")

    answered = tmp_path / "answered"
    answered.mkdir()
    deck = project(answered, "compartments: 4\n")
    settings.mark_printed(answered, dividers=True, box=True)
    s = settings.load(deck)
    assert s.dividers_printed and s.box_printed
