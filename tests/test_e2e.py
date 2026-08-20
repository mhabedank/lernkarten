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
    # 29 cards at 8 up -> 4 sheets, each with a front and a back page.
    # The count is DEMO_CARD_COUNT; issue #23 inherited '31' from this comment.
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
    assert pdf_pages(target) == 8, "29 demo cards + the one intact card of the broken file"


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


def bbox_pages(path):
    """Every word with its coordinates, page by page: [[(x, y, word), ...], ...].

    Read with coordinates rather than in reading order — `pdftotext -layout`
    silently drops words once the columns get narrow, which at A8 is most of
    them. `-bbox-layout` gives every word an x and a y, so rows and columns can
    be recovered exactly.

    Both readers below are built on this one, so the two guards that decide
    "this tool cannot answer" live in a single place.
    """
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is not installed")
    result = subprocess.run(
        ["pdftotext", "-bbox-layout", str(path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # Not every pdftotext on PATH is poppler's, and -bbox-layout is not
    # universal: GitHub's windows-latest image carries one that takes the call
    # and returns no page elements. Read the exit code and look for a page
    # before trusting the output — an empty parse used to travel three frames
    # and arrive as "expected at least a front and a back page", which blames
    # the build for a limitation of the reader. A tool that cannot answer is a
    # skip; a tool that answers and finds nothing is still a failure below.
    xml = result.stdout
    if result.returncode != 0 or "<page " not in xml:
        pytest.skip(
            "the pdftotext on PATH produced no -bbox-layout page elements "
            f"(exit {result.returncode}): {result.stderr.strip()[:200] or 'no stderr'}"
        )
    pages = []
    for chunk in xml.split("<page ")[1:]:
        words = re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)"[^>]*>([^<]+)</word>', chunk)
        pages.append([(float(x), float(y), w) for x, y, w in words])
    return pages


def card_grid_per_page(path):
    """The card ids laid out as a grid, page by page: [[row], [row], ...]."""
    pages = []
    for words in bbox_pages(path):
        rows = {}
        for x, y, w in words:
            if not re.fullmatch(r"[\w-]+-\d+", w):
                continue
            # One row of cards shares a y to well under a millimetre; round so
            # the grouping survives the typesetter's sub-point placement.
            rows.setdefault(round(y), []).append((x, w))
        pages.append([[w for _, w in sorted(r)] for _, r in sorted(rows.items())])
    return pages


def test_a_pdftotext_without_bbox_support_skips_instead_of_blaming_the_pdf(monkeypatch):
    """Not every `pdftotext` on PATH is poppler's.

    GitHub's windows-latest image carries one that takes the call and returns
    no bbox XML. That used to come back as an empty page list and surface as
    "expected at least a front and a back page" — a reader limitation reported
    as a broken build. It has to skip, and say which tool let it down.
    """
    monkeypatch.setattr(shutil, "which", lambda _name: "pdftotext")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 99, "", "unknown option '-bbox-layout'"),
    )
    with pytest.raises(pytest.skip.Exception) as excinfo:
        card_grid_per_page(Path("irrelevant.pdf"))
    assert "bbox" in str(excinfo.value).lower(), excinfo.value


def test_a_pdftotext_that_returns_bbox_xml_without_pages_also_skips(monkeypatch):
    """Exit 0 but nothing usable is the same class of problem."""
    monkeypatch.setattr(shutil, "which", lambda _name: "pdftotext")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "<html><body></body></html>", ""),
    )
    with pytest.raises(pytest.skip.Exception):
        card_grid_per_page(Path("irrelevant.pdf"))


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


def test_a_card_that_fits_one_grid_and_not_the_other_is_reported_only_there(tmp_path):
    """FR-010, and the only assertion that catches the grid going missing.

    The overflow set comes from a second engine call that builds its own
    --input list — now including the sheet orientation and the scale. If any of
    them reaches the compile call but not that query, the PDF is right and every
    warning is wrong. An assertion of absence cannot see it: the demo cards
    overflow at neither grid, so the query returns nothing on the correct and
    the broken path alike. This card overflows at exactly one of the two.

    The direction inverted with BUG-007. A8 used to be the A7 card with its
    width halved, holding 46 % of the area, so a card could fit A7 and overflow
    A8. A8 is now a uniformly scaled A7 card that keeps about 3 % more width, so
    it holds slightly *more* — measured, first overflow at 520 characters
    against A7's 500. Nothing fits A7 and overflows A8 any more; the
    discriminating card is the one that overflows A7 and fits A8.
    """
    fixture = str(DEMO / "broken" / "overflows-only-at-a7.yaml")

    default = run("check", fixture)
    assert default.returncode == 0, default.stderr
    assert "overflows-only-at-a7-2" in default.stderr, (
        f"the 507-character back does not fit A7 and must be reported by id: {default.stderr}"
    )

    dense = run("check", fixture, "--grid", "a8")
    assert dense.returncode == 0, dense.stderr
    assert "does not fit" not in dense.stderr, (
        f"the same card fits the scaled A8 card — nothing to report: {dense.stderr}"
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


# --- a deck that declares its own grid (US2) -------------------------------

GRIDS = DEMO / "grids"


def test_a_deck_that_declares_a8_prints_at_a8_without_a_flag(tmp_path):
    """FR-012/FR-013: 12 cards at 16 up is one sheet — a front page and a back."""
    target = tmp_path / "declared.pdf"
    result = run("build", str(GRIDS / "tides-a8.yaml"), "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == 2, "12 cards at 4 x 4 fit on one sheet"
    assert "2 pages, duplex" in result.stdout


def test_the_flag_overrides_what_the_deck_declares(tmp_path):
    """FR-013: --grid a7 prints the same 12 cards 8 up, so two sheets."""
    target = tmp_path / "overridden.pdf"
    result = run("build", str(GRIDS / "tides-a8.yaml"), "--grid", "a7", "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == 4, "12 cards at 2 x 4 need two sheets"
    assert "4 pages, duplex" in result.stdout


def test_two_decks_that_disagree_about_the_grid_are_refused(tmp_path):
    """FR-014: no flag, two declared grids — the build names both files."""
    target = tmp_path / "conflict.pdf"
    result = run(
        "build", str(GRIDS / "tides-a8.yaml"), str(GRIDS / "tides-a7.yaml"), "-o", str(target)
    )
    assert result.returncode != 0
    assert "tides-a8.yaml" in result.stderr and "tides-a7.yaml" in result.stderr, result.stderr
    assert not target.exists(), "a refused build writes no PDF"


def test_the_flag_settles_a_disagreement(tmp_path):
    target = tmp_path / "settled.pdf"
    result = run(
        "build",
        str(GRIDS / "tides-a8.yaml"),
        str(GRIDS / "tides-a7.yaml"),
        "--grid",
        "a8",
        "-o",
        str(target),
    )
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == 2, "14 cards at 4 x 4 still fit on one sheet"


# --- a grid the build cannot honour (US4) ----------------------------------

UNSUPPORTED = ["2x6", "3x4", "1x1", "4x8"]
# A value starting with a dash has to be written --grid=VALUE: argparse claims
# `--grid -1x4` as an option of its own and reports a missing argument before
# parse_grid ever sees it. Both spellings are refused and neither writes a PDF;
# only the message differs, so both are asserted below.
MALFORMED = ["3 x 4", "3,4", "eight", "0x4", "3x0"]
MALFORMED_NEEDING_EQUALS = ["-1x4", "-2x-4"]


@pytest.mark.parametrize("value", UNSUPPORTED)
def test_an_unsupported_grid_is_refused_and_lists_the_supported_set(tmp_path, value):
    """FR-003: a well-formed grid nobody can cut to says which ones are cuttable."""
    target = tmp_path / "never.pdf"
    result = run("build", *CARDS, "--grid", value, "-o", str(target))
    assert result.returncode != 0
    assert "2x4 (A7)" in result.stderr and "4x4 (A8)" in result.stderr, result.stderr
    assert value in result.stderr, result.stderr
    assert not target.exists(), "a refused build writes no PDF"


@pytest.mark.parametrize("value", MALFORMED)
def test_a_malformed_grid_is_refused_end_to_end(tmp_path, value):
    """T009's unit rejections, through the real command line."""
    target = tmp_path / "never.pdf"
    result = run("build", *CARDS, "--grid", value, "-o", str(target))
    assert result.returncode != 0
    assert value in result.stderr, result.stderr
    assert not target.exists(), "a refused build writes no PDF"


@pytest.mark.parametrize("value", MALFORMED_NEEDING_EQUALS)
def test_a_negative_grid_is_refused_in_both_spellings(tmp_path, value):
    """The dash-leading half of T009, which argparse gets to first."""
    target = tmp_path / "never.pdf"

    equals = run("build", *CARDS, f"--grid={value}", "-o", str(target))
    assert equals.returncode != 0
    assert value in equals.stderr, equals.stderr
    assert not target.exists(), "a refused build writes no PDF"

    separate = run("build", *CARDS, "--grid", value, "-o", str(target))
    assert separate.returncode != 0, "argparse must not let a dash-leading value through"
    assert "--grid" in separate.stderr, separate.stderr
    assert not target.exists(), "a refused build writes no PDF"


def test_a_refused_build_leaves_an_existing_pdf_untouched(tmp_path):
    """FR-022: the grid is judged before the output path is opened."""
    target = tmp_path / "cards.pdf"
    assert run("build", *CARDS, "-o", str(target)).returncode == 0
    before = target.read_bytes()
    assert before.startswith(b"%PDF-")

    for value in ("2x6", "3 x 4"):
        result = run("build", *CARDS, "--grid", value, "-o", str(target))
        assert result.returncode != 0, f"--grid {value} should be refused"
        assert target.read_bytes() == before, (
            f"--grid {value} rewrote or truncated the PDF that was already there"
        )


# --- the sheet turns and the card scales (BUG-007) -------------------------


def pdf_page_size_mm(path):
    """The first MediaBox, in mm, as the PDF itself states it."""
    box = re.search(
        rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]", path.read_bytes()
    )
    assert box, "no MediaBox in the PDF"
    pts = [float(box.group(i)) for i in range(1, 5)]
    return (round((pts[2] - pts[0]) * 25.4 / 72, 2), round((pts[3] - pts[1]) * 25.4 / 72, 2))


def test_a7_still_prints_on_a_portrait_sheet(tmp_path):
    """SC-002: the default grid must not move. Asserted before the A8 case."""
    target = tmp_path / "a7.pdf"
    assert run("build", *CARDS, "-o", str(target), "--margin", "0").returncode == 0
    assert pdf_page_size_mm(target) == (210.0, 297.0)


def test_a8_prints_a_landscape_card_on_a_landscape_sheet(tmp_path):
    """FR-024/SC-010: 74.25 x 52.5 mm, wider than tall — not 52.5 x 74.25."""
    target = tmp_path / "a8.pdf"
    result = run("build", *CARDS, "-o", str(target), "--grid", "a8", "--margin", "0")
    assert result.returncode == 0, result.stderr
    assert pdf_page_size_mm(target) == (297.0, 210.0), "the sheet turns for a8"

    sheet_w, sheet_h = pdf_page_size_mm(target)
    cw, ch = sheet_w / 4, sheet_h / 4
    assert (round(cw, 2), round(ch, 2)) == (74.25, 52.5)
    assert cw > ch, f"a flashcard is landscape; this one is {cw} x {ch}"


def test_an_a7_legal_deck_reprints_at_a8_without_a_warning(tmp_path):
    """SC-011: this is what "half the sheets for the same deck" requires.

    A deck sitting on A7's own warning thresholds — 398-character back, 116-
    character front — must build at a8 with nothing reported. Under the
    portrait card it could not: A8 held roughly 160 characters.
    """
    back = (
        "The tidal streams turn about an hour after high and low water, not at the "
        "turn itself, so a passage planned on the height alone runs against the "
        "stream for its first hour. Plan on the stream atlas rather than the tide "
        "table, and add an hour of slack either side of the turn. Spring streams "
        "run at twice the neap rate through the Ovray narrows, where the channel "
        "is at its tightest on the ebb."
    )
    front = (
        "Why does planning a passage on the tide table alone leave you punching "
        "the stream for the first hour after the turn?"
    )
    assert 390 <= len(back) <= 400, len(back)
    assert 110 <= len(front) <= 120, len(front)

    deck = tmp_path / "limits.yaml"
    deck.write_text(
        "topic: 'Tides'\nlanguage: english\ngrid: a7\ncards:\n"
        f"  - subtopic: 'Streams'\n    front: '{front}'\n    back: '{back}'\n"
        "    source: 'Field notes 2'\n",
        encoding="utf-8",
    )
    result = run("build", str(deck), "-o", str(tmp_path / "limits.pdf"), "--grid", "a8")
    assert result.returncode == 0, result.stderr
    assert "WARNING" not in result.stderr, (
        f"an A7-legal card must survive a8 unchanged: {result.stderr}"
    )


# --- the print order (feat/simplex-print-order) ----------------------------


def face_marks_per_page(path):
    """Which face each page carries: a set of "1/2" / "2/2" per page.

    Every card footer prints `<id> · 1/2` on the front and `· 2/2` on the back
    (templates/card.typ), so the face is in the text layer and does not have to
    be inferred from the geometry. A front page is one whose every mark reads
    1/2.
    """
    return [{w for _, _, w in words if re.fullmatch(r"[12]/2", w)} for words in bbox_pages(path)]


def test_simplex_puts_every_front_before_any_back(tmp_path):
    """SC-001, read off the artifact rather than inferred.

    29 cards at 8 up is 4 sheets. Simplex means pages 1-4 are the four fronts
    and pages 5-8 the four backs — not front, back, front, back.
    """
    target = tmp_path / "simplex.pdf"
    result = run("build", *CARDS, "-o", str(target), "--sides", "simplex")
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == 8

    marks = face_marks_per_page(target)
    assert marks[:4] == [{"1/2"}] * 4, f"pages 1-4 must be fronts only: {marks}"
    assert marks[4:] == [{"2/2"}] * 4, f"pages 5-8 must be backs only: {marks}"


def test_simplex_keeps_every_back_behind_its_own_front(tmp_path):
    """SC-002/FR-003: sheet n's back is page N+n, still column-mirrored.

    Turning a printed stack over on the long edge is the same flip a duplex
    printer makes, so the mirroring that lines duplex up lines simplex up too.
    """
    target = tmp_path / "mirror.pdf"
    assert run("build", *CARDS, "-o", str(target), "--sides", "simplex").returncode == 0
    pages = card_grid_per_page(target)
    sheets = len(pages) // 2
    assert sheets == 4, f"expected 4 sheets, got {len(pages)} pages"
    for n in range(sheets):
        front, back = pages[n], pages[sheets + n]
        assert front, f"no ids read off front page {n}"
        assert back == [list(reversed(row)) for row in front], (
            f"sheet {n}: the back on page {sheets + n} is not mirrored behind its front"
        )


def test_simplex_groups_the_faces_at_the_denser_grid_too(tmp_path):
    """The split is by sheet, so it follows the grid — 16 up gives 2 sheets."""
    target = tmp_path / "a8.pdf"
    result = run("build", *CARDS, "-o", str(target), "--sides", "simplex", "--grid", "a8")
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == 4
    assert face_marks_per_page(target) == [{"1/2"}, {"1/2"}, {"2/2"}, {"2/2"}]

    pages = card_grid_per_page(target)
    for n in range(2):
        front, back = pages[n], pages[2 + n]
        assert all(len(row) <= 4 for row in front), f"a row holds more than 4 cards: {front}"
        assert back == [list(reversed(row)) for row in front], (
            f"sheet {n}: a8 backs are not mirrored across four columns"
        )


@pytest.mark.parametrize("grid", ["a7", "a8"])
def test_the_print_order_never_changes_the_page_count(tmp_path, grid):
    """FR-004: the same sheets either way, so 2 x ceil(cards / per sheet)."""
    duplex = tmp_path / f"duplex-{grid}.pdf"
    simplex = tmp_path / f"simplex-{grid}.pdf"
    assert run("build", *CARDS, "-o", str(duplex), "--grid", grid).returncode == 0
    assert (
        run("build", *CARDS, "-o", str(simplex), "--grid", grid, "--sides", "simplex").returncode
        == 0
    )
    assert pdf_pages(duplex) == pdf_pages(simplex)


def test_a_single_sheet_deck_looks_the_same_in_both_orders(tmp_path):
    """At one sheet the two orders are the same sequence, front then back.

    Worth pinning: it is the deck someone tries the flag on first, and a build
    that reordered anything here would be reordering a two-page document.
    """
    one_deck = str(DEMO / "cards" / "tides.yaml")  # 8 cards, exactly one a7 sheet
    duplex, simplex = tmp_path / "one-d.pdf", tmp_path / "one-s.pdf"
    assert run("build", one_deck, "-o", str(duplex)).returncode == 0
    assert run("build", one_deck, "-o", str(simplex), "--sides", "simplex").returncode == 0
    assert pdf_pages(duplex) == pdf_pages(simplex) == 2
    assert face_marks_per_page(simplex) == [{"1/2"}, {"2/2"}]
    assert card_grid_per_page(duplex) == card_grid_per_page(simplex)


def test_an_unknown_print_order_is_refused(tmp_path):
    """FR-005: a usage error, before any card file is read, naming both values."""
    target = tmp_path / "never.pdf"
    for value in ("both", "single", "flip", ""):
        result = run("build", *CARDS, "-o", str(target), "--sides", value)
        assert result.returncode == 2, f"{value!r} should be a usage error: {result.stderr}"
        assert not target.exists(), f"{value!r}: no PDF may be written on a refusal"
        assert "duplex" in result.stderr and "simplex" in result.stderr, result.stderr


def test_check_takes_the_print_order_flag_too(tmp_path):
    """FR-007: both subcommands accept it, and it changes nothing about check."""
    plain = run("check", *CARDS)
    with_flag = run("check", *CARDS, "--sides", "simplex")
    assert with_flag.returncode == 0, with_flag.stderr
    assert f"{DEMO_CARD_COUNT} cards valid" in with_flag.stdout
    assert with_flag.stdout == plain.stdout, "the flag must not change what check reports"


def test_the_simplex_build_says_which_pages_to_print(tmp_path):
    """SC-004: the ranges are computed from the sheets, and add up to the count."""
    result = run("build", *CARDS, "-o", str(tmp_path / "s.pdf"), "--sides", "simplex")
    assert result.returncode == 0, result.stderr
    assert "8 pages, simplex" in result.stdout, result.stdout
    assert "pages 1-4" in result.stdout and "pages 5-8" in result.stdout, result.stdout


def test_the_duplex_build_still_says_flip_on_long_edge(tmp_path):
    """FR-008: the default path's wording is what existing projects rely on."""
    result = run("build", *CARDS, "-o", str(tmp_path / "d.pdf"))
    assert result.returncode == 0, result.stderr
    assert "8 pages, duplex, flip on long edge" in result.stdout, result.stdout
