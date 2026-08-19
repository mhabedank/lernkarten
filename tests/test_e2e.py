"""End-to-end tests: the real command, the real typesetter, a real PDF.

Everything here runs `bin/lernkarten` as a subprocess over the demo project in
tests/fixtures/demo-project — the same way a user or CI would. What the other
test modules do with functions, this does with exit codes and files.

The typesetter is needed for all of it. If this machine has none, the module
skips instead of downloading 30 MB behind your back; set LERNKARTEN_E2E=1 (as
CI does) to let the first test fetch it.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "bin" / "lernkarten"
DEMO = ROOT / "tests" / "fixtures" / "demo-project"
CARDS = sorted(str(p) for p in (DEMO / "cards").glob("*.yaml"))
DEMO_CARD_COUNT = 29

sys.path.insert(0, str(ROOT / "scripts"))

import engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def engine_available():
    """Skips the module unless a typesetter is here (or we may fetch one)."""
    may_fetch = os.environ.get("LERNKARTEN_E2E") == "1"
    try:
        binary, _ = engine.find(fetch_if_missing=may_fetch)
    except engine.EngineError as e:
        pytest.skip(f"no typesetting engine: {e} — set LERNKARTEN_E2E=1 to fetch it")
    return binary


def run(*args):
    """Calls the command the way a user does. Never raises."""
    return subprocess.run(
        [sys.executable, str(CLI), *args], capture_output=True, text=True, cwd=ROOT
    )


def pdf_pages(path):
    """The page count as the PDF itself states it."""
    data = path.read_bytes()
    assert data.startswith(b"%PDF-"), "not a PDF"
    assert data.rstrip().endswith(b"%%EOF"), "PDF was not written completely"
    counts = re.findall(rb"/Count\s+(\d+)", data)
    assert counts, "no page tree in the PDF"
    return max(int(c) for c in counts)


# --- the happy path -------------------------------------------------------


def test_check_accepts_the_demo_cards():
    result = run("check", *CARDS)
    assert result.returncode == 0, result.stderr
    assert f"{DEMO_CARD_COUNT} cards valid" in result.stdout
    assert "english, german, greek, russian" in result.stdout, (
        "every card language in the set should be reported"
    )
    assert "WARNING" not in result.stderr, f"the demo cards should all fit: {result.stderr}"


def test_build_writes_a_pdf_with_one_sheet_per_eight_cards(tmp_path):
    target = tmp_path / "cards.pdf"
    result = run("build", *CARDS, "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert target.exists()
    # 31 cards -> 4 sheets, each with a front and a back page
    assert pdf_pages(target) == 8
    assert "8 pages, duplex" in result.stdout


def test_check_writes_no_pdf(tmp_path):
    target = tmp_path / "nothing.pdf"
    assert run("check", *CARDS, "-o", str(target)).returncode == 0
    assert not target.exists(), "--check must not write a file"


def test_a_topic_filter_narrows_the_build(tmp_path):
    target = tmp_path / "tides.pdf"
    result = run("build", *CARDS, "--topic", "Tides", "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert "8 cards" in result.stdout, result.stdout
    assert pdf_pages(target) == 2


def test_a_subtopic_filter_narrows_the_build(tmp_path):
    result = run("build", *CARDS, "--subtopic", "The six flags", "-o", str(tmp_path / "flags.pdf"))
    assert result.returncode == 0, result.stderr
    assert "3 cards" in result.stdout, result.stdout


def test_a_filter_that_matches_nothing_fails_out_loud(tmp_path):
    result = run("build", *CARDS, "--topic", "Thermodynamics", "-o", str(tmp_path / "x.pdf"))
    assert result.returncode == 1
    assert "No cards left after filtering" in result.stderr


def test_the_layout_options_reach_the_typesetter(tmp_path):
    plain = tmp_path / "plain.pdf"
    borderless = tmp_path / "borderless.pdf"
    assert run("build", *CARDS, "-o", str(plain)).returncode == 0
    assert run("build", *CARDS, "--margin", "0", "--no-logo", "-o", str(borderless)).returncode == 0
    assert pdf_pages(plain) == pdf_pages(borderless) == 8
    assert plain.read_bytes() != borderless.read_bytes(), (
        "--margin/--no-logo changed nothing in the output"
    )


def test_a_pdf_can_hold_four_languages_and_three_scripts(tmp_path):
    """Latin, Greek and Cyrillic have to survive into the PDF as characters.

    The engine renders a glyph its fonts do not have as an empty box without
    saying a word, and drops it from the text layer — so what comes back out of
    the finished PDF is the only honest check that a script is covered.
    """
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is not installed")
    target = tmp_path / "scripts.pdf"
    result = run("build", *CARDS, "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert "english, german, greek, russian" in result.stdout

    # `-enc UTF-8` and an explicit decode: left to itself, pdftotext falls back
    # to the local charset, which on Windows cannot represent Greek or Cyrillic
    # at all, and Python would then read the bytes through the ANSI code page.
    text = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(target), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout

    # Every script is checked before anything is reported. Failing on the first
    # one hides whether the rest arrived, and this is the only place that would
    # notice a font losing a whole alphabet.
    missing = [
        f"{script} ({word!r})"
        for word, script in [
            ("semidiurnal", "Latin"),
            ("halbtägige", "Latin with umlauts"),
            ("σημαίνει", "Greek"),
            ("правило", "Cyrillic"),
        ]
        if word not in text
    ]
    assert not missing, (
        f"these did not survive into the PDF: {', '.join(missing)}\nwhat came out instead:\n{text}"
    )


def test_the_language_flag_overrides_the_card_files(tmp_path):
    result = run("build", *CARDS, "--language", "german", "-o", str(tmp_path / "de.pdf"))
    assert result.returncode == 0, result.stderr
    assert "(german)" in result.stdout, result.stdout


def test_the_output_folder_is_created_on_demand(tmp_path):
    target = tmp_path / "deep" / "down" / "cards.pdf"
    assert run("build", *CARDS, "-o", str(target)).returncode == 0
    assert target.exists()


# --- the unhappy paths, one fixture per failure mode ----------------------


def test_invalid_markup_names_the_offending_card():
    result = run("check", str(DEMO / "broken" / "invalid-markup.yaml"))
    assert result.returncode == 1
    assert "The typesetter rejected the cards" in result.stderr
    assert "invalid-markup-2" in result.stderr, "the broken card has to be named"
    assert "invalid-markup-1" not in result.stderr, "the intact card must not be blamed"


def test_a_backslash_before_a_star_names_the_offending_card():
    """BUG-001: `\\` is a line break only before whitespace.

    Directly before `*` it escapes the star, so the break is lost and the
    remaining delimiter is unclosed. The build must fail and blame the card that
    did it, not the one above it that uses the working `\\ *bold*` form.
    """
    result = run("check", str(DEMO / "broken" / "escaped-linebreak.yaml"))
    assert result.returncode == 1
    assert "The typesetter rejected the cards" in result.stderr
    assert "escaped-linebreak-2" in result.stderr, "the broken card has to be named"
    assert "escaped-linebreak-1" not in result.stderr, "the intact card must not be blamed"


def test_an_overlong_card_warns_but_still_builds(tmp_path):
    target = tmp_path / "overflow.pdf"
    result = run("build", str(DEMO / "broken" / "overflowing.yaml"), "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert "WARNING: card overflowing-2 does not fit" in result.stderr
    assert "overflowing-1" not in result.stderr, "the card that fits must not be flagged"
    assert target.exists(), "a warning is not a reason to withhold the PDF"


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        ("unknown-language.yaml", "unknown language 'klingon'"),
        ("missing-fields.yaml", "card 2: 'front' and 'back' are required"),
        ("not-a-mapping.yaml", "expected a mapping with keys 'topic' and 'cards'"),
        ("malformed.yaml", "line 8"),
    ],
)
def test_a_broken_card_file_is_rejected_with_its_reason(fixture, message):
    result = run("check", str(DEMO / "broken" / fixture))
    assert result.returncode == 1
    assert message in result.stderr, result.stderr


def test_a_broken_file_does_not_take_the_healthy_ones_down(tmp_path):
    """A build over a mixed set reports the bad file and prints the rest."""
    target = tmp_path / "mixed.pdf"
    result = run("build", *CARDS, str(DEMO / "broken" / "missing-fields.yaml"), "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert "ERROR" in result.stderr
    assert pdf_pages(target) == 8, "31 demo cards + the one intact card of the broken file"


def test_an_impossible_margin_is_refused(tmp_path):
    result = run("build", *CARDS, "--margin", "50", "-o", str(tmp_path / "x.pdf"))
    assert result.returncode == 2
    assert "--margin must be between 0 and 20" in result.stderr


def test_an_unknown_language_flag_lists_the_known_ones(tmp_path):
    result = run("build", *CARDS, "--language", "klingon", "-o", str(tmp_path / "x.pdf"))
    assert result.returncode == 2
    assert "unknown language" in result.stderr and "german" in result.stderr


# --- the command itself ---------------------------------------------------


def test_the_engine_reports_itself():
    result = run("engine", "--check")
    assert result.returncode == 0, result.stderr
    assert "typst" in result.stdout.lower()


def test_calling_it_without_a_command_shows_what_it_can_do():
    result = run()
    assert result.returncode == 2
    assert "lernkarten build" in result.stderr


def test_help_is_not_an_error():
    result = run("--help")
    assert result.returncode == 0
    assert "lernkarten check" in result.stderr + result.stdout


def test_the_build_help_documents_the_options():
    result = run("build", "--help")
    assert result.returncode == 0
    for option in (
        "--topic",
        "--subtopic",
        "--margin",
        "--grid",
        "--language",
        "--no-logo",
        "--check",
    ):
        assert option in result.stdout, f"{option} is missing from the help"


# --- the press-sheet grid (feat/card-grid) --------------------------------


def card_grid_per_page(path):
    """The card ids laid out as a grid, page by page: [[row], [row], ...].

    Read from the footer ids with their coordinates rather than from reading
    order — `pdftotext -layout` silently drops ids once the columns get narrow,
    which at A8 is most of them. `-bbox-layout` gives every word an x and a y,
    so the rows and columns can be recovered exactly.
    """
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is not installed")
    xml = subprocess.run(
        ["pdftotext", "-bbox-layout", str(path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout
    pages = []
    for chunk in xml.split("<page ")[1:]:
        words = re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)"[^>]*>([^<]+)</word>', chunk)
        found = [(float(x), float(y), w) for x, y, w in words if re.fullmatch(r"[\w-]+-\d+", w)]
        rows = {}
        for x, y, w in found:
            # One row of cards shares a y to well under a millimetre; round so
            # the grouping survives the typesetter's sub-point placement.
            rows.setdefault(round(y), []).append((x, w))
        pages.append([[w for _, w in sorted(r)] for _, r in sorted(rows.items())])
    return pages


def test_a8_puts_sixteen_cards_on_a_sheet(tmp_path):
    """29 demo cards: 2 x ceil(29/16) = 4 pages, against 8 at the default."""
    target = tmp_path / "a8.pdf"
    result = run("build", *CARDS, "-o", str(target), "--grid", "a8")
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == 4
    assert "4 pages, duplex" in result.stdout


def test_the_a_series_alias_is_the_same_grid(tmp_path):
    alias = tmp_path / "alias.pdf"
    explicit = tmp_path / "explicit.pdf"
    assert run("build", *CARDS, "-o", str(alias), "--grid", "a8").returncode == 0
    assert run("build", *CARDS, "-o", str(explicit), "--grid", "4x4").returncode == 0
    assert pdf_pages(alias) == pdf_pages(explicit) == 4
    # Not a byte comparison: the engine stamps a CreationDate, so two builds of
    # the same input already differ. The layout is what has to match.
    assert card_grid_per_page(alias) == card_grid_per_page(explicit), (
        "a8 and 4x4 must lay the sheet out identically"
    )


def test_no_grid_flag_leaves_the_default_untouched(tmp_path):
    """SC-002: an existing project must build exactly as it did before."""
    target = tmp_path / "default.pdf"
    result = run("build", *CARDS, "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == 8
    assert "8 pages, duplex" in result.stdout


def test_the_backs_are_mirrored_across_the_requested_columns(tmp_path):
    """FR-007: duplex "flip on long edge" only lines up if the backs mirror.

    For every row, the back page must carry that row's ids reversed. At two
    columns that swaps a pair; at four it maps 0<->3 and 1<->2, and nothing but
    a grid-aware mirror gets both right.
    """
    for flag, columns in (("a7", 2), ("a8", 4)):
        target = tmp_path / f"mirror-{flag}.pdf"
        assert run("build", *CARDS, "-o", str(target), "--grid", flag).returncode == 0
        pages = card_grid_per_page(target)
        assert len(pages) >= 2, f"{flag}: expected at least a front and a back page"
        for sheet in range(0, len(pages) - 1, 2):
            front, back = pages[sheet], pages[sheet + 1]
            assert front, f"{flag}: no ids read off sheet {sheet // 2}"
            assert all(len(row) <= columns for row in front), (
                f"{flag}: a row holds more than {columns} cards — {front}"
            )
            assert back == [list(reversed(row)) for row in front], (
                f"{flag}: sheet {sheet // 2} backs are not mirrored across {columns} columns"
            )


def test_check_accepts_the_grid_flag_too():
    """FR-001: both subcommands take it, not just build."""
    result = run("check", *CARDS, "--grid", "a8")
    assert result.returncode == 0, result.stderr
    assert "29 cards valid" in result.stdout


def test_a_zero_margin_cuts_to_the_a_series_sizes(tmp_path):
    """SC-003: the two grids are the two that land on a standard card."""
    sizes = {}
    for flag in ("a7", "a8"):
        target = tmp_path / f"exact-{flag}.pdf"
        assert (
            run("build", *CARDS, "-o", str(target), "--grid", flag, "--margin", "0").returncode == 0
        )
        sizes[flag] = pdf_pages(target)
    # A7 is 8 up and A8 is 16 up, so the same deck halves its sheets.
    assert sizes["a7"] == 8 and sizes["a8"] == 4


def test_an_unsupported_grid_is_refused(tmp_path):
    target = tmp_path / "never.pdf"
    for value in ("3x4", "2x6", "3 x 4", "eight", "0x4"):
        result = run("build", *CARDS, "-o", str(target), "--grid", value)
        assert result.returncode != 0, f"{value} should have been refused"
        assert not target.exists(), f"{value}: no PDF may be written on a refusal"


def test_a_card_that_fits_a7_and_not_a8_is_reported_only_at_a8(tmp_path):
    """FR-010, and the only assertion that catches the grid going missing.

    The overflow set comes from a second engine call that builds its own
    --input list. If the grid reaches the compile call but not that query, the
    PDF is right and every warning is wrong. An assertion of absence cannot see
    it: the demo cards overflow at neither grid, so the query returns nothing
    on the correct and the broken path alike. This card overflows at exactly
    one of the two, which is what makes the difference visible.
    """
    fixture = str(DEMO / "broken" / "overflows-only-at-a8.yaml")

    default = run("check", fixture)
    assert default.returncode == 0, default.stderr
    assert "does not fit" not in default.stderr, "the card fits A7 — nothing to report"

    dense = run("check", fixture, "--grid", "a8")
    assert dense.returncode == 0, dense.stderr
    assert "overflows-only-at-a8-2" in dense.stderr, (
        "the card does not fit A8 and must be reported by id"
    )


def test_an_overlong_card_is_reported_at_both_grids():
    """A regression guard. It passes under the FR-010 bug too, so it is not
    the trap-catcher — that is the test above."""
    fixture = str(DEMO / "broken" / "overflowing.yaml")
    for flag in ([], ["--grid", "a8"]):
        result = run("check", fixture, *flag)
        assert result.returncode == 0, result.stderr
        assert "overflowing-2" in result.stderr, f"not reported with {flag or 'the default'}"


def test_no_demo_card_overflows_at_either_grid():
    """Measured: the corpus fits at 46 % of the writing area. Also a guard
    rather than a trap-catcher, for the same reason."""
    for flag in ([], ["--grid", "a8"]):
        result = run("check", *CARDS, *flag)
        assert result.returncode == 0, result.stderr
        assert "does not fit" not in result.stderr, f"unexpected overflow with {flag or 'default'}"
