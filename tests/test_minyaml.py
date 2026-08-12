"""Tests for scripts/minyaml.py — the reader that replaces the PyYAML dependency.

It only has to understand the files this project owns, so the tests pin exactly
that: what our card files, source registers and skill frontmatter contain.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import minyaml  # noqa: E402


def test_reads_a_card_file():
    data = minyaml.load(
        "# a comment\n"
        "topic: 'Probability'\n"
        "language: german\n"
        "cards:\n"
        "  - subtopic: 'Bayes'\n"
        "    front: 'Question?'\n"
        "    back: 'Answer'\n"
        "  - subtopic: 'Other'\n"
        "    front: 'Q2'\n"
        "    back: 'A2'\n"
    )
    assert data == {
        "topic": "Probability",
        "language": "german",
        "cards": [
            {"subtopic": "Bayes", "front": "Question?", "back": "Answer"},
            {"subtopic": "Other", "front": "Q2", "back": "A2"},
        ],
    }


def test_reads_scalars_the_way_yaml_does():
    data = minyaml.load(
        "count: 3\nratio: 1.5\nyes_please: true\nnope: false\nnothing:\nplain: some text\n"
    )
    assert data == {
        "count": 3,
        "ratio": 1.5,
        "yes_please": True,
        "nope": False,
        "nothing": None,
        "plain": "some text",
    }


def test_quotes_protect_their_contents():
    data = minyaml.load(
        "hash: 'a # not a comment'\n"
        'colon: "key: value inside"\n'
        "apostrophe: 'it''s fine'\n"
        'escaped: "a \\" and a \\\\"\n'
        "trailing: plain  # this one is a comment\n"
    )
    assert data["hash"] == "a # not a comment"
    assert data["colon"] == "key: value inside"
    assert data["apostrophe"] == "it's fine"
    assert data["escaped"] == 'a " and a \\'
    assert data["trailing"] == "plain"


def test_backslashes_survive_single_quotes():
    # Card text uses a backslash for a line break, which must not be eaten
    data = minyaml.load("back: 'first line \\ second line'\n")
    assert data["back"] == "first line \\ second line"


def test_reads_a_source_register():
    data = minyaml.load(
        "sources:\n"
        "  - id: lecture-notes\n"
        "    type: folder\n"
        "    path: ~/Documents/Statistics\n"
        "    pattern: '*.pdf'\n"
        "  - id: wiki\n"
        "    type: web\n"
        "    url: https://en.wikipedia.org/wiki/Bayes\n"
        "    depth: 1\n"
        "    login: true\n"
    )
    assert data["sources"][0]["path"] == "~/Documents/Statistics"
    assert data["sources"][1] == {
        "id": "wiki",
        "type": "web",
        "url": "https://en.wikipedia.org/wiki/Bayes",
        "depth": 1,
        "login": True,
    }


def test_a_list_may_sit_at_its_key_indentation():
    assert minyaml.load("items:\n- one\n- two\n") == {"items": ["one", "two"]}


def test_reads_folded_and_literal_blocks():
    folded = minyaml.load("description: >-\n  first line\n  second line\n")
    assert folded["description"] == "first line second line"

    literal = minyaml.load("text: |\n  line one\n  line two\n")
    assert literal["text"] == "line one\nline two\n"

    stripped = minyaml.load("text: |-\n  only line\n")
    assert stripped["text"] == "only line"


def test_document_markers_are_ignored():
    assert minyaml.load("---\nname: cards\n---\n") == {"name": "cards"}


@pytest.mark.parametrize(
    "text",
    [
        "key: 'unterminated\n",
        'key: "unterminated\n',
        "key: value\nkey: again\n",
        "inline: [1, 2, 3]\n",
        "mapping: {a: 1}\n",
        "just some prose\n",
    ],
)
def test_refuses_what_it_cannot_read(text):
    with pytest.raises(minyaml.YamlError):
        minyaml.load(text)


def test_errors_name_the_line():
    with pytest.raises(minyaml.YamlError, match="line 3"):
        minyaml.load("a: 1\nb: 2\nc: 'oops\n")


# --- the real files -------------------------------------------------------


def test_reads_every_file_this_repo_ships():
    paths = [ROOT / "sources.example.yaml", *sorted((ROOT / "cards").glob("*.yaml"))]
    paths += sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert len(paths) >= 7
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            text = text.split("---\n", 2)[1]
        data = minyaml.load(text)
        assert isinstance(data, dict) and data, path
