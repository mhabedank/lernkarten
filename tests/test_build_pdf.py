"""Tests for scripts/build_pdf.py — grid, YAML loading, page assembly.

Deliberately compiles no LaTeX: the pdflatex trial run is its own CI step
(`build_pdf.py --check`), these tests run without a TeX installation.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_pdf  # noqa: E402


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


# --- grid -----------------------------------------------------------------


def test_grid_splits_a4_into_eight_cards():
    cw, ch, _ = build_pdf.grid(margin=0)
    assert (cw, ch) == pytest.approx((105.0, 74.25))
    assert cw * build_pdf.COLUMNS == pytest.approx(build_pdf.A4_WIDTH)
    assert ch * build_pdf.ROWS == pytest.approx(build_pdf.A4_HEIGHT)
    assert build_pdf.COLUMNS * build_pdf.ROWS == build_pdf.CARDS_PER_PAGE


def test_grid_subtracts_the_margin():
    cw, ch, _ = build_pdf.grid(margin=5)
    assert (cw, ch) == pytest.approx((100.0, 71.75))


def test_grid_without_margin_draws_no_outer_edges():
    _, _, borderless = build_pdf.grid(margin=0)
    _, _, with_margin = build_pdf.grid(margin=5)
    # 3 column and 5 row lines with a margin; without one, 2 outer edges drop each
    assert len(with_margin.splitlines()) == 8
    assert len(borderless.splitlines()) == 4


# --- load_cards -----------------------------------------------------------

MINIMAL = """
topic: "Statistics"
cards:
  - subtopic: "Bayes"
    front: "Question"
    back: "Answer"
    source: "Lecture 3"
"""


def test_load_cards_reads_the_fields(tmp_path):
    cards, errors = build_pdf.load_cards([write(tmp_path, "a.yaml", MINIMAL)], [], [])
    assert errors == []
    assert cards == [
        {
            "id": "a-1",
            "topic": "Statistics",
            "subtopic": "Bayes",
            "front": "Question",
            "back": "Answer",
            "source": "Lecture 3",
            "language": "english",
        }
    ]


def test_load_cards_reports_broken_yaml(tmp_path):
    path = write(tmp_path, "broken.yaml", "topic: 'unclosed\ncards: [")
    cards, errors = build_pdf.load_cards([path], [], [])
    assert cards == []
    assert len(errors) == 1 and "YAML error" in errors[0]


def test_load_cards_reports_missing_required_fields(tmp_path):
    path = write(tmp_path, "b.yaml", 'topic: "T"\ncards:\n  - front: "front only"\n')
    cards, errors = build_pdf.load_cards([path], [], [])
    assert cards == []
    assert "'front' and 'back' are required" in errors[0]


def test_load_cards_reports_the_wrong_structure(tmp_path):
    path = write(tmp_path, "c.yaml", "- a\n- list\n")
    _, errors = build_pdf.load_cards([path], [], [])
    assert "expected a mapping" in errors[0]


def test_load_cards_falls_back_to_the_filename_as_topic(tmp_path):
    path = write(tmp_path, "no-topic.yaml", 'cards:\n  - front: "f"\n    back: "b"\n')
    cards, errors = build_pdf.load_cards([path], [], [])
    assert errors == []
    assert cards[0]["topic"] == "no-topic"
    assert cards[0]["source"] == ""


def test_filter_matches_substrings_case_insensitively(tmp_path):
    path = write(tmp_path, "a.yaml", MINIMAL)
    assert build_pdf.load_cards([path], ["statis"], [])[0]
    assert build_pdf.load_cards([path], ["Analysis"], [])[0] == []
    assert build_pdf.load_cards([path], [], ["BAYES"])[0]
    assert build_pdf.load_cards([path], [], ["Markov"])[0] == []


# --- build_body -----------------------------------------------------------


def card(i, language="english"):
    return {
        "id": f"c-{i}",
        "topic": "T",
        "subtopic": "S",
        "front": f"F{i}",
        "back": f"B{i}",
        "source": "",
        "language": language,
    }


def test_build_body_pairs_front_and_back_pages():
    cw, ch, _ = build_pdf.grid(margin=5)
    for count, expected in [(1, 2), (8, 2), (9, 4), (17, 6)]:
        body = build_pdf.build_body([card(i) for i in range(count)], 5, cw, ch)
        pages = body.split("\\newpage")
        assert len(pages) == expected, f"{count} cards"


def test_back_is_column_mirrored():
    cw, ch, _ = build_pdf.grid(margin=0)
    front, back = build_pdf.build_body([card(0)], 0, cw, ch).split("\\newpage")
    # Card 0 sits in column 0 on the front (x=0) and in column 1 on the back (x=cw)
    assert "\\cell{0.000}" in front
    assert f"\\cell{{{cw:.3f}}}" in back
    assert "F0" in front and "B0" in back


def test_header_joins_topic_and_subtopic():
    cw, ch, _ = build_pdf.grid(margin=5)
    body = build_pdf.build_body([card(0)], 5, cw, ch)
    assert "T \\,\\textperiodcentered\\, S" in body

    without = dict(card(0), subtopic="")
    assert "\\textperiodcentered" not in build_pdf.build_body([without], 5, cw, ch)


def test_every_card_carries_an_id_comment_for_troubleshooting():
    cw, ch, _ = build_pdf.grid(margin=5)
    body = build_pdf.build_body([card(0)], 5, cw, ch)
    assert "% card: c-0\n" in body
    assert "% card: c-0 (back)\n" in body


# --- languages ------------------------------------------------------------


def test_languages_are_named_the_way_a_user_would_name_them():
    assert build_pdf.resolve_language("german") == "german"
    assert build_pdf.resolve_language("German") == "german"
    assert build_pdf.resolve_language(" english ") == "english"
    # ISO codes and locale tags work too
    assert build_pdf.resolve_language("de") == "german"
    assert build_pdf.resolve_language("de-AT") == "german"
    assert build_pdf.resolve_language("pt") == "portuguese"


def test_an_unknown_language_names_the_ones_that_work():
    with pytest.raises(ValueError) as e:
        build_pdf.resolve_language("klingon")
    assert "klingon" in str(e.value) and "german" in str(e.value)


def test_the_typesetting_names_stay_inside_the_build():
    # The user says "german"; the typesetter needs "ngerman" — that never leaks out.
    assert build_pdf.typesetting_options("german", {"german"}) == "ngerman"
    assert build_pdf.typesetting_options("english", {"english"}) == "english"
    assert (
        build_pdf.typesetting_options("english", {"english", "german", "french"})
        == "french,ngerman,main=english"
    )


def test_a_card_file_declares_its_own_language(tmp_path):
    path = write(
        tmp_path, "de.yaml", 'topic: "T"\nlanguage: german\ncards:\n  - front: "f"\n    back: "b"\n'
    )
    cards, errors = build_pdf.load_cards([path], [], [])
    assert errors == []
    assert cards[0]["language"] == "german"


def test_a_card_file_without_a_language_falls_back(tmp_path):
    path = write(tmp_path, "a.yaml", MINIMAL)
    assert build_pdf.load_cards([path], [], [])[0][0]["language"] == "english"
    assert build_pdf.load_cards([path], [], [], "french")[0][0]["language"] == "french"


def test_an_unknown_language_in_a_file_is_reported_not_crashed(tmp_path):
    path = write(
        tmp_path, "x.yaml", 'topic: "T"\nlanguage: elvish\ncards:\n  - front: "f"\n    back: "b"\n'
    )
    cards, errors = build_pdf.load_cards([path], [], [])
    assert cards == []
    assert "unknown language" in errors[0] and "elvish" in errors[0]


def test_the_document_language_follows_the_cards_unless_overridden():
    cards = [card(0, "german"), card(1, "german"), card(2, "english")]
    assert build_pdf.main_language(cards) == "german"
    assert build_pdf.main_language(cards, "english") == "english"
    assert build_pdf.main_language([]) == build_pdf.DEFAULT_LANGUAGE


def test_only_cards_in_a_foreign_language_are_marked_up():
    cw, ch, _ = build_pdf.grid(margin=5)
    body = build_pdf.build_body([card(0, "german"), card(1, "english")], 5, cw, ch, "german")
    assert body.count("\\foreignlanguage{english}") == 3  # header, front, back
    assert "\\foreignlanguage{ngerman}" not in body, "the main language needs no markup"


# --- template -------------------------------------------------------------


def test_template_placeholders_match_what_the_build_supplies():
    import string

    template = string.Template(build_pdf.TEMPLATE.read_text(encoding="utf-8"))
    supplied = {"cw", "ch", "margin", "language", "logo", "cutlines", "body"}
    used = {
        m.group("named") or m.group("braced") for m in template.pattern.finditer(template.template)
    }
    assert used - {None} == supplied


def test_template_draws_the_logo_mark_and_the_build_can_switch_it_off():
    template = build_pdf.TEMPLATE.read_text(encoding="utf-8")
    assert "\\newcommand{\\logomark}" in template
    assert "${logo}" in template


# --- bundled example file -------------------------------------------------


def test_example_cards_satisfy_the_schema():
    cards, errors = build_pdf.load_cards([str(ROOT / "cards" / "example.yaml")], [], [])
    assert errors == []
    assert cards, "cards/example.yaml is the schema reference and must contain cards"
    for c in cards:
        assert '"' not in c["front"] + c["back"], (
            f"{c['id']}: ASCII double quotes terminate the YAML string"
        )
