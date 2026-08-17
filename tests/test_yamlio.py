"""The YAML reader: scripts/yamlio.py.

A thin layer over PyYAML rather than a parser of its own — what it owns is the
error message and the bootstrap, so that is what is tested here. The parsing
itself is PyYAML's problem and needs no tests from us; that was the point of
retiring scripts/minyaml.py.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import yamlio  # noqa: E402


def test_it_reads_what_the_card_files_use():
    data = yamlio.load(
        "topic: 'Tides'\n"
        "language: german\n"
        "cards:\n"
        "  - subtopic: 'One'\n"
        "    front: 'A question?'\n"
        "    back: 'An answer.'\n"
    )
    assert data["topic"] == "Tides"
    assert data["language"] == "german"
    assert len(data["cards"]) == 1
    assert data["cards"][0]["back"] == "An answer."


def test_a_leading_document_marker_is_fine():
    """Skill frontmatter is handed over with its --- already stripped, but a
    single leading marker still has to parse rather than confuse the reader."""
    assert yamlio.load("---\nname: cards\n") == {"name": "cards"}


def test_an_empty_document_is_none_not_an_error():
    assert yamlio.load("") is None
    assert yamlio.load("# only a comment\n") is None


def test_a_broken_file_names_the_line():
    """The line number is the whole value of the message — without it the user
    has to bisect their own file."""
    with pytest.raises(yamlio.YamlError) as e:
        yamlio.load("a: 1\nb: 2\n  c: 3\n")
    assert "line 3" in str(e.value)


def test_the_message_is_one_line_and_hides_pyyaml_plumbing():
    """PyYAML reports over six lines and calls the input "<unicode string>",
    which means nothing to someone looking at their own card file."""
    with pytest.raises(yamlio.YamlError) as e:
        yamlio.load("cards:\n  - front: 'a'\n      back: 'b'\n")
    message = str(e.value)
    assert "\n" not in message, f"the message should be one line, got: {message!r}"
    assert "unicode string" not in message
    assert "line 3" in message


def test_an_unterminated_quote_names_both_ends():
    """Where it was noticed and where it began, because they differ.

    An unclosed quote is detected at the end of the file but has to be fixed
    where it opened. Reporting only the first would send the reader to the wrong
    place; reporting only the second hides how far the damage ran.
    """
    with pytest.raises(yamlio.YamlError) as e:
        yamlio.load("topic: 'unclosed\ncards:\n")
    message = str(e.value)
    assert "line 1" in message, f"the quote opens on line 1: {message}"
    assert "line 3" in message, f"the stream ends on line 3: {message}"
    assert "\n" not in message


def test_yaml_error_is_a_value_error():
    """Call sites catch it alongside OSError, so it has to stay a ValueError."""
    assert issubclass(yamlio.YamlError, ValueError)


def test_tabs_are_rejected_rather_than_guessed_at():
    with pytest.raises(yamlio.YamlError):
        yamlio.load("cards:\n\t- front: 'a'\n")
