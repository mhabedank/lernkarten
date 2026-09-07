"""End-to-end tests: the real command, the real typesetter, a real PDF.

Everything here runs `bin/lernkarten` as a subprocess over the demo project in
tests/fixtures/demo-project — the same way a user or CI would. What the other
test modules do with functions, this does with exit codes and files.

The typesetter is needed for all of it. If this machine has none, the module
skips instead of downloading 30 MB behind your back; set LERNKARTEN_E2E=1 (as
CI does) to let the first test fetch it.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "bin" / "lernkarten"
DEMO = ROOT / "tests" / "fixtures" / "demo-project"
CARDS = sorted(str(p) for p in (DEMO / "cards").glob("*.yaml"))
DEMO_CARD_COUNT = 32

# How many cards a press sheet holds, per grid.
A7_UP, A8_UP = 8, 16


def sheet_pages(cards, per_sheet=A7_UP):
    """Pages a deck of `cards` fills: one sheet is two pages, and a part-full
    sheet still prints both of them. 33 cards at 8 up is five sheets, not four
    and a bit — which is the arithmetic every assertion below used to spell out
    as a literal, and the reason the demo deck could not grow by one card."""
    return 2 * -(-cards // per_sheet)


DEMO_A7_PAGES = sheet_pages(DEMO_CARD_COUNT)
DEMO_A8_PAGES = sheet_pages(DEMO_CARD_COUNT, A8_UP)

# A sheet is two pages, so the sheet count is what the simplex order is built on.
DEMO_A7_SHEETS = DEMO_A7_PAGES // 2
DEMO_A8_SHEETS = DEMO_A8_PAGES // 2

# cards/tides.yaml on its own, which is what `--topic Tides` selects.
TIDES_CARD_COUNT = 11

sys.path.insert(0, str(ROOT / "scripts"))

import engine  # noqa: E402
import yamlio  # noqa: E402


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


# --- the arithmetic the assertions below rely on --------------------------


@pytest.mark.parametrize(
    "cards, per_sheet, pages",
    [
        (1, A7_UP, 2),  # one card still costs a whole sheet, front and back
        (8, A7_UP, 2),  # exactly full
        (9, A7_UP, 4),  # one over, and the second sheet is whole
        (32, A7_UP, 8),  # the demo deck today
        (33, A7_UP, 10),  # one more card is two more pages, not none
        (32, A8_UP, 4),  # the same deck, denser grid
        (16, A8_UP, 2),
        (17, A8_UP, 4),
    ],
)
def test_sheet_pages_rounds_a_part_full_sheet_up(cards, per_sheet, pages):
    """The rule the page-count assertions are derived from.

    The 32/33 pair is the one that matters: it is why adding a single card to
    the demo project used to mean hand-editing a dozen assertions.
    """
    assert sheet_pages(cards, per_sheet) == pages


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
    # Both counts follow from DEMO_CARD_COUNT. This comment used to state the
    # deck size itself, and issue #23 inherited a stale '31' from it.
    assert pdf_pages(target) == DEMO_A7_PAGES
    assert f"{DEMO_A7_PAGES} pages, duplex" in result.stdout


def test_check_writes_no_pdf(tmp_path):
    target = tmp_path / "nothing.pdf"
    assert run("check", *CARDS, "-o", str(target)).returncode == 0
    assert not target.exists(), "--check must not write a file"


def test_a_topic_filter_narrows_the_build(tmp_path):
    target = tmp_path / "tides.pdf"
    result = run("build", *CARDS, "--topic", "Tides", "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert f"{TIDES_CARD_COUNT} cards" in result.stdout, result.stdout
    assert pdf_pages(target) == sheet_pages(TIDES_CARD_COUNT)


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
    assert pdf_pages(plain) == pdf_pages(borderless) == DEMO_A7_PAGES
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
        # Four ways a picture can be wrong, and four different messages. One
        # message covering all of them would send the user looking in the wrong
        # place three times out of four. The order they are checked in is why
        # the .tiff — which is also absent — is reported as the wrong format.
        (
            "missing-image.yaml",
            "card M5SS1: back_image 'figures/island-images/gone.png' does not exist",
        ),
        (
            "image-wrong-format.yaml",
            "card FMT01: back_image 'figures/island-images/tide-chart.tiff' "
            "is not an image the engine reads",
        ),
        (
            "image-outside-project.yaml",
            "card ESC01: back_image '../../../elsewhere/chart.png' is outside the project",
        ),
        # The only one Python cannot answer: a real file with an accepted name
        # that is not an image. The engine says so, and offending_card() says
        # which card it belongs to.
        ("unreadable-image.yaml", "Offending card: RDB21"),
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
    assert pdf_pages(target) == sheet_pages(DEMO_CARD_COUNT + 1), (
        "the demo cards plus the one intact card of the broken file"
    )


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


def declared_ids():
    """Every id the demo decks declare, read from the card files themselves.

    The ids used to be `<stem>-<n>`, which a regex could pick out of the page.
    A Crockford id is five characters with no separator, and the header band
    sets the topic in upper case — so `TIDES` would match a naive pattern just
    as well as a real id. Matching against what the decks actually declare is
    both exact and self-maintaining.
    """
    found = set()
    for card_file in CARDS:
        deck = yamlio.load(Path(card_file).read_text(encoding="utf-8"))
        for card in deck.get("cards") or []:
            if isinstance(card, dict) and isinstance(card.get("id"), str):
                found.add(card["id"])
    return found


def card_grid_per_page(path):
    """The card ids laid out as a grid, page by page: [[row], [row], ...]."""
    known = declared_ids()
    pages = []
    for words in bbox_pages(path):
        rows = {}
        for x, y, w in words:
            if w not in known:
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
    """32 demo cards: 2 x ceil(32/16) = 4 pages, against 8 at the default."""
    target = tmp_path / "a8.pdf"
    result = run("build", *CARDS, "-o", str(target), "--grid", "a8")
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == DEMO_A8_PAGES
    assert f"{DEMO_A8_PAGES} pages, duplex" in result.stdout


def test_the_a_series_alias_is_the_same_grid(tmp_path):
    alias = tmp_path / "alias.pdf"
    explicit = tmp_path / "explicit.pdf"
    assert run("build", *CARDS, "-o", str(alias), "--grid", "a8").returncode == 0
    assert run("build", *CARDS, "-o", str(explicit), "--grid", "4x4").returncode == 0
    assert pdf_pages(alias) == pdf_pages(explicit) == DEMO_A8_PAGES
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
    assert pdf_pages(target) == DEMO_A7_PAGES
    assert f"{DEMO_A7_PAGES} pages, duplex" in result.stdout


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
    assert f"{DEMO_CARD_COUNT} cards valid" in result.stdout


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
    assert sizes["a7"] == DEMO_A7_PAGES and sizes["a8"] == DEMO_A8_PAGES


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

    # The fixture states `grid: a7` — since #84 an absent key would mean A8,
    # and this test is about the pair of grids rather than about the default.
    sparse = run("check", fixture)
    assert sparse.returncode == 0, sparse.stderr
    assert "overflows-only-at-a7-2" in sparse.stderr, (
        f"the 507-character back does not fit A7 and must be reported by id: {sparse.stderr}"
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


GUIDE = (140, 135, 121)  # #8c8779, the only colour the crop marks are drawn in


def crop_marks_per_edge(path, index=0, margin=5.0, scale=8):
    """How many guide-coloured pixels sit in each of the four margin strips.

    Rendered at scale 8 on purpose: an arm is a 0.3 pt line, and at the scale=2
    `page_holds` uses it blends towards paper white past that helper's
    tolerance. The strips are held 0.6 mm clear of the print area, because a
    card's own ink lands on the boundary pixel and would otherwise be counted
    as a mark that is not there.
    """
    pdfium = pytest.importorskip("pypdfium2", reason="renders the page to look at it")
    image = pdfium.PdfDocument(str(path))[index].render(scale=scale).to_pil().convert("RGB")
    width, height = image.size
    sheet_w, sheet_h = pdf_page_size_mm(path)
    arm, pad = min(margin * 0.7, 3.0), 0.6
    px, py = width / sheet_w, height / sheet_h

    def guide_pixels(box):
        patch = image.crop(tuple(int(v) for v in box)).getdata()
        return sum(
            1 for p in patch if sum((a - b) ** 2 for a, b in zip(p, GUIDE, strict=True)) <= 60**2
        )

    return {
        "top": guide_pixels((0, (margin - arm) * py, width, (margin - pad) * py)),
        "bottom": guide_pixels(
            (0, (sheet_h - margin + pad) * py, width, (sheet_h - margin + arm) * py)
        ),
        "left": guide_pixels(((margin - arm) * px, 0, (margin - pad) * px, height)),
        "right": guide_pixels(
            ((sheet_w - margin + pad) * px, 0, (sheet_w - margin + arm) * px, height)
        ),
    }


@pytest.mark.parametrize("grid", ["a7", "a8"])
def test_the_crop_marks_reach_all_four_edges_of_the_sheet(tmp_path, grid):
    """The marks are the line a user cuts to, so all four edges must carry them.

    `templates/cards.typ` wrote the sheet size into the crop-mark loops as the
    literals `297mm` and `210mm` — A4 *portrait*. The 4 x 4 grid tiles a
    *landscape* A4, so at `--grid a8` the bottom marks were placed 292 mm down a
    210 mm page, off the paper entirely, and the right-hand marks 205 mm across
    a 297 mm one, a ghost column standing in the middle of the sheet. A7 was
    never affected, which is why it survived unnoticed through two grids.
    """
    target = tmp_path / f"{grid}.pdf"
    result = run("build", *CARDS, "-o", str(target), "--grid", grid)
    assert result.returncode == 0, result.stderr

    marks = crop_marks_per_edge(target)
    missing = sorted(edge for edge, count in marks.items() if count == 0)
    assert not missing, f"no crop marks on the {missing} edge(s) at {grid}: {marks}"


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

    The demo deck at 8 up is DEMO_A7_SHEETS sheets. Simplex means the first
    half of the pages are the fronts and the second half the backs — not
    front, back, front, back.
    """
    target = tmp_path / "simplex.pdf"
    result = run("build", *CARDS, "-o", str(target), "--sides", "simplex")
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == DEMO_A7_PAGES

    marks = face_marks_per_page(target)
    s = DEMO_A7_SHEETS
    assert marks[:s] == [{"1/2"}] * s, f"pages 1-{s} must be fronts only: {marks}"
    assert marks[s:] == [{"2/2"}] * s, f"pages {s + 1}-{2 * s} must be backs only: {marks}"


def test_simplex_keeps_every_back_behind_its_own_front(tmp_path):
    """SC-002/FR-003: sheet n's back is page N+n, still column-mirrored.

    Turning a printed stack over on the long edge is the same flip a duplex
    printer makes, so the mirroring that lines duplex up lines simplex up too.
    """
    target = tmp_path / "mirror.pdf"
    assert run("build", *CARDS, "-o", str(target), "--sides", "simplex").returncode == 0
    pages = card_grid_per_page(target)
    sheets = len(pages) // 2
    assert sheets == DEMO_A7_SHEETS, f"expected {DEMO_A7_SHEETS} sheets, got {len(pages)} pages"
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
    assert pdf_pages(target) == DEMO_A8_PAGES
    s = DEMO_A8_SHEETS
    assert face_marks_per_page(target) == [{"1/2"}] * s + [{"2/2"}] * s

    pages = card_grid_per_page(target)
    for n in range(s):
        front, back = pages[n], pages[s + n]
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
    one_deck = str(DEMO / "cards" / "signals.yaml")  # 7 cards, exactly one a7 sheet
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
    assert f"{DEMO_A7_PAGES} pages, simplex" in result.stdout, result.stdout
    s = DEMO_A7_SHEETS
    assert f"pages 1-{s}" in result.stdout and f"pages {s + 1}-{2 * s}" in result.stdout, (
        result.stdout
    )


def test_the_duplex_build_still_says_flip_on_long_edge(tmp_path):
    """FR-008: the default path's wording is what existing projects rely on."""
    result = run("build", *CARDS, "-o", str(tmp_path / "d.pdf"))
    assert result.returncode == 0, result.stderr
    assert f"{DEMO_A7_PAGES} pages, duplex, flip on long edge" in result.stdout, result.stdout


# --- the id on the printed card (feat/card-id) -------------------------------
#
# The old id was `<stem>-<n>` and the measured example ran 124.62 pt against a
# 94.49 pt box with `clip: true` — so it was cut off on the card, and a user
# could not read it even to type it out. A five-character id fits with room to
# spare, which is what lets it be set larger than the old 4.6 pt.

ID_DECK = """topic: 'Legibility'
language: english
grid: a7
cards:
  - id: A45DK
    subtopic: 'Basics'
    front: 'Front'
    back: 'Back'
"""

NO_ID_DECK = """topic: 'Legibility'
language: english
grid: a7
cards:
  - subtopic: 'Basics'
    front: 'Front'
    back: 'Back'
"""


def _words_on(path):
    return [w for page in bbox_pages(path) for (_x, _y, w) in page]


def test_the_id_is_printed_on_both_faces(tmp_path):
    deck = tmp_path / "deck.yaml"
    deck.write_text(ID_DECK, encoding="utf-8")
    target = tmp_path / "id.pdf"
    assert run("build", str(deck), "-o", str(target)).returncode == 0
    assert _words_on(target).count("A45DK") == 2, "front and back each carry the id"


MEASURE = """#set page(width: 400mm, height: 100mm, margin: 0pt)
#context {
  let cw = 100mm
  let id = text(font: "IBM Plex Mono", size: SIZE, "A45DK · 1/2")
  [#metadata((width: measure(id).width.pt(), cap: (cw / 3).pt()))<measurement>]
}
"""


def measured_id_width(size_pt):
    """The rendered width of the longest id line, through the pinned engine.

    Read back with `typst query` rather than off the page: an SVG or PDF turns
    text into glyph outlines, so the number would not be there to find. This is
    the same mechanism the build already uses to detect an overflowing card.
    """
    binary, _ = engine.find(fetch_if_missing=False)
    with tempfile.TemporaryDirectory() as work:
        source = Path(work) / "m.typ"
        source.write_text(MEASURE.replace("SIZE", f"{size_pt}pt"), encoding="utf-8")
        result = subprocess.run(
            [
                str(binary),
                "query",
                "--ignore-system-fonts",
                "--font-path",
                str(ROOT / "assets" / "fonts"),
                str(source),
                "<measurement>",
                "--field",
                "value",
            ],
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    return payload[0]["width"], payload[0]["cap"]


def test_the_id_fits_the_box_it_is_clipped_to_by_measurement(tmp_path):
    """FR-010/SC-005: measured through the engine, not eyeballed.

    `templates/card.typ` caps the id block at `cw / 3` and sets `clip: true`,
    so an id that is too wide is silently cut rather than reported — which is
    exactly what happened to the old `<stem>-<n>` ids.
    """
    if shutil.which("pdftotext") is None:
        pass  # this one does not need pdftotext, only the engine
    width, cap = measured_id_width(8)
    assert width < cap, f"the id block overruns its clip box: {width} pt against {cap} pt"
    assert width / cap < 0.75, (
        f"{width} pt is {100 * width / cap:.0f} % of the cap — too little headroom "
        "for a denser grid or a longer side marker"
    )


def test_the_template_sets_the_id_at_the_agreed_size():
    """FR-011: 8 pt, up from 4.6 pt.

    Asserted against the template source rather than by comparing two synthetic
    measurements — measuring 8 pt against 4.6 pt only proves that 8 is bigger
    than 4.6, which is true whatever the card is actually set in.
    """
    source = (ROOT / "templates" / "card.typ").read_text(encoding="utf-8")
    sizes = re.findall(r"size:\s*([0-9.]+)pt \* scale,\s*\n\s*fill: muted", source)
    assert sizes == ["8"], f"the id should be set at 8pt * scale, found {sizes}"
    assert "4.6pt" not in source, "the old id size is still in the template"


def test_a_card_without_an_id_prints_the_side_marker_alone(tmp_path):
    """FR-005: no id text and no separator — not a stranded '·'."""
    deck = tmp_path / "plain.yaml"
    deck.write_text(NO_ID_DECK, encoding="utf-8")
    target = tmp_path / "plain.pdf"
    assert run("build", str(deck), "-o", str(target)).returncode == 0

    words = _words_on(target)
    assert "1/2" in words and "2/2" in words, f"the side marker must remain: {words}"
    assert "·" not in words, f"a separator with nothing before it was printed: {words}"


def test_the_separator_is_there_when_there_is_an_id(tmp_path):
    """The other half of the case above, so the guard cannot pass vacuously."""
    deck = tmp_path / "deck.yaml"
    deck.write_text(ID_DECK, encoding="utf-8")
    target = tmp_path / "id.pdf"
    assert run("build", str(deck), "-o", str(target)).returncode == 0
    assert "·" in _words_on(target)


# --- `lernkarten id` through the real command --------------------------------


def test_backfill_through_the_command_assigns_ids_and_keeps_the_comments(tmp_path):
    """US4 end to end. Needs no engine — backfill never renders anything."""
    deck = tmp_path / "deck.yaml"
    deck.write_text(
        "# a comment that has to survive\n"
        "topic: 'Plain'\n"
        "cards:\n"
        "  - subtopic: 'One'\n"
        "    front: 'a'\n"
        "    back: 'b'\n",
        encoding="utf-8",
    )
    before = deck.read_text(encoding="utf-8")

    result = run("id", "--backfill", str(deck))
    assert result.returncode == 0, result.stderr

    after = deck.read_text(encoding="utf-8")
    assert after.count("- id: ") == 1, f"no id was written: {after}"
    assert "# a comment that has to survive" in after
    assert "front: 'a'" in after
    assert after != before


def test_bare_id_without_a_flag_is_refused_with_usage(tmp_path):
    """The contract: one of the two flags is required.

    The destructive act must never be what happens when you type the command
    with no flag and hit return.
    """
    deck = tmp_path / "deck.yaml"
    deck.write_text("topic: 'T'\ncards:\n  - front: 'a'\n    back: 'b'\n", encoding="utf-8")
    result = run("id", str(deck))
    assert result.returncode != 0
    assert "backfill" in (result.stderr + result.stdout).lower()


def test_reassign_through_the_command_reports_what_it_cost(tmp_path):
    """FR-013c: the report has to name the consequence, not just the change."""
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    for path, front in ((a, "a"), (b, "c")):
        path.write_text(
            f"topic: 'T'\ncards:\n  - id: A45DK\n    front: '{front}'\n    back: 'x'\n",
            encoding="utf-8",
        )
    result = run("id", "--reassign", str(a), str(b))
    assert result.returncode == 0, result.stderr

    assert "id: A45DK" in a.read_text(encoding="utf-8"), "the first file keeps its id"
    assert "id: A45DK" not in b.read_text(encoding="utf-8")
    message = result.stderr + result.stdout
    assert "A45DK" in message
    assert "orphan" in message.lower() or "no longer name" in message.lower(), (
        f"the report has to state the cost, not just the substitution: {message}"
    )


# --- pictures on a card (feat/figure-cards) ---------------------------------
#
# The demo figure is a chart whose bars are #5b7fb5, a blue that appears nowhere
# in the card design. So "did the picture print on this face?" becomes a
# question a test can answer: render the page and look for that colour.

CHART_BLUE = (0x5B, 0x7F, 0xB5)

FIGURE_DECK = """topic: 'Tides'
language: english
cards:
  - id: F3M2Q
    subtopic: 'Range'
    front: 'Describe the rule of twelfths'
    back: 'One twelfth, two, three, three, two, one.'
    {face}: 'figures/chart.svg'
    source: 'Tide chart'
"""


def one_figure_card(tmp_path, face):
    """A one-card project, so front and back are page 1 and page 2 exactly."""
    (tmp_path / "cards").mkdir(exist_ok=True)
    (tmp_path / "figures").mkdir(exist_ok=True)
    shutil.copyfile(
        DEMO / "figures" / "island-images" / "tide-chart.svg",
        tmp_path / "figures" / "chart.svg",
    )
    deck = tmp_path / "cards" / "deck.yaml"
    deck.write_text(FIGURE_DECK.format(face=face), encoding="utf-8")
    return str(deck)


def page_holds(path, index, rgb, tolerance=40):
    """Whether page `index` (0-based) of the PDF holds a pixel near `rgb`."""
    pdfium = pytest.importorskip("pypdfium2", reason="renders the page to look at it")
    page = pdfium.PdfDocument(str(path))[index]
    pixels = page.render(scale=2).to_pil().convert("RGB").getdata()

    def near(pixel):
        return sum((a - b) ** 2 for a, b in zip(pixel, rgb, strict=True)) <= tolerance**2

    return any(near(pixel) for pixel in pixels)


@pytest.mark.parametrize(
    ("face", "printed_on", "blank"),
    [("back_image", 1, 0), ("front_image", 0, 1)],
    ids=["back", "front"],
)
def test_a_picture_lands_on_the_face_that_named_it(tmp_path, face, printed_on, blank):
    target = tmp_path / "one.pdf"
    assert run("build", one_figure_card(tmp_path, face), "-o", str(target)).returncode == 0
    assert pdf_pages(target) == 2
    assert page_holds(target, printed_on, CHART_BLUE), f"{face} did not print on its own face"
    assert not page_holds(target, blank, CHART_BLUE), f"{face} printed on the other face too"


def test_a_figure_deck_costs_no_extra_page(tmp_path):
    """32 cards at 8 up is 4 sheets, whether or not two of them carry a picture."""
    target = tmp_path / "figures.pdf"
    result = run("build", *CARDS, "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert pdf_pages(target) == DEMO_A7_PAGES


def test_a_picture_scales_with_the_card_at_a8(tmp_path):
    """A deck legal at a7 stays legal at a8: the picture shrinks with everything else."""
    target = tmp_path / "a8.pdf"
    result = run("build", str(DEMO / "grids" / "tides-a8.yaml"), "-o", str(target))
    assert result.returncode == 0, result.stderr
    assert page_holds(target, 1, CHART_BLUE), "the picture has to survive the denser grid"


def test_a_back_whose_text_and_picture_do_not_fit_is_named(tmp_path):
    """The picture is measured at its minimum, not at the room it is given.

    Without that, an answer long enough to squeeze the diagram to two
    millimetres would report "fits" and print something nobody can read.
    """
    (tmp_path / "cards").mkdir()
    (tmp_path / "figures").mkdir()
    shutil.copyfile(
        DEMO / "figures" / "island-images" / "tide-chart.svg",
        tmp_path / "figures" / "chart.svg",
    )
    deck = tmp_path / "cards" / "deck.yaml"
    deck.write_text(
        "topic: 'Tides'\nlanguage: english\ncards:\n"
        "  - id: F3M2Q\n    subtopic: 'Range'\n    front: 'Describe the rule of twelfths'\n"
        f"    back: '{'The range is spread unevenly over the six hours of the flood. ' * 6}'\n"
        "    back_image: 'figures/chart.svg'\n",
        encoding="utf-8",
    )
    result = run("build", str(deck), "-o", str(tmp_path / "over.pdf"))
    assert result.returncode == 0, "an overlong card still builds"
    assert "F3M2Q" in result.stderr and "does not fit" in result.stderr, result.stderr


# --- the dividers through the real command (feat/leitner-compartments) -------


def test_dividers_refuses_a_count_it_does_not_have(tmp_path):
    """FR-001. Red on the *message*: argparse alone says 'unrecognized arguments'.

    An exit code of 2 is not the assertion. What the user needs is to be told
    which counts exist, so that is what is asserted.
    """
    target = tmp_path / "no.pdf"
    result = run("build", *CARDS, "-o", str(target), "--grid", "a8", "--dividers", "5")
    assert result.returncode != 0
    assert "3 or 4" in result.stderr, result.stderr
    assert not target.exists(), "a refused run writes no PDF"


def test_dividers_as_a_flag_refuses_a_grid_the_box_does_not_fit(tmp_path):
    """FR-009/SC-009: the box is 73 mm inside and an A7 card is 100 mm wide."""
    target = tmp_path / "no.pdf"
    result = run("build", *CARDS, "-o", str(target), "--grid", "a7", "--dividers", "4")
    assert result.returncode != 0
    assert "a8" in result.stderr.lower(), result.stderr
    assert not target.exists()


def test_four_dividers_open_a_further_page_on_the_demo_deck(tmp_path):
    """SC-001: 31 cards fill three-and-a-bit rows of sheet 2.

    Far less than the 2.44 free card rows a two-row block needs, so the block
    cannot share the sheet and opens a further one. Both counts follow from
    DEMO_CARD_COUNT; typing them would be the drift test_repo_hygiene forbids.
    """
    plain, with_dividers = tmp_path / "plain.pdf", tmp_path / "leitner.pdf"
    assert run("build", *CARDS, "-o", str(plain), "--grid", "a8").returncode == 0
    assert pdf_pages(plain) == DEMO_A8_PAGES

    result = run("build", *CARDS, "-o", str(with_dividers), "--grid", "a8", "--dividers", "4")
    assert result.returncode == 0, result.stderr
    assert pdf_pages(with_dividers) == DEMO_A8_PAGES + 2, "one further sheet, so two pages"


def test_three_dividers_share_a_sheet_with_a_short_deck(tmp_path):
    """FR-004/FR-012, the other branch, from the same corpus.

    The Signals topic is two rows at 16 up, which leaves more than the 1.25
    rows a one-row block of three needs — so the block costs no paper at all.
    Compared against the same deck built without dividers, never against a
    typed number: signals.yaml may grow.
    """
    plain, shared = tmp_path / "plain.pdf", tmp_path / "shared.pdf"
    common = ("build", *CARDS, "--grid", "a8", "--topic", "Signals")
    assert run(*common, "-o", str(plain)).returncode == 0
    result = run(*common, "-o", str(shared), "--dividers", "3")
    assert result.returncode == 0, result.stderr
    assert pdf_pages(shared) == pdf_pages(plain), "the block shares the last sheet"


def test_the_run_counts_dividers_apart_from_cards(tmp_path):
    """FR-012a: a divider must never inflate the number the user wrote."""
    result = run("build", *CARDS, "-o", str(tmp_path / "c.pdf"), "--grid", "a8", "--dividers", "4")
    assert result.returncode == 0, result.stderr
    assert f"{DEMO_CARD_COUNT} cards" in result.stdout, result.stdout
    assert "4 dividers" in result.stdout, result.stdout


def test_the_run_says_which_paper_case_it_is_in(tmp_path):
    """FR-012: 'they cost no paper' is true only when the last sheet has room."""
    added = run("build", *CARDS, "-o", str(tmp_path / "a.pdf"), "--grid", "a8", "--dividers", "4")
    shared = run(
        "build",
        *CARDS,
        "-o",
        str(tmp_path / "b.pdf"),
        "--grid",
        "a8",
        "--topic",
        "Signals",
        "--dividers",
        "3",
    )
    assert "further sheet" in added.stderr.lower(), added.stderr
    assert added.stderr.count("NOTE:") >= 1, "advisories carry the NOTE: prefix"
    assert "no extra" in shared.stderr.lower() or "shares" in shared.stderr.lower(), shared.stderr


def test_dividers_do_not_change_a_deck_that_does_not_ask_for_them(tmp_path):
    """SC-005: the feature is invisible until it is asked for."""
    before, after = tmp_path / "one.pdf", tmp_path / "two.pdf"
    assert run("build", *CARDS, "-o", str(before), "--grid", "a8").returncode == 0
    assert run("build", *CARDS, "-o", str(after), "--grid", "a8").returncode == 0
    assert pdf_pages(before) == pdf_pages(after) == DEMO_A8_PAGES
    assert pdf_page_size_mm(before) == pdf_page_size_mm(after)


# --- the settings a user answers once (feat/leitner-settings) ---------------


def scratch_project(tmp_path, settings_text=None):
    """A project directory shaped the way the pipeline writes one."""
    (tmp_path / "cards").mkdir()
    deck = tmp_path / "cards" / "deck.yaml"
    deck.write_text(
        "topic: 'Tides'\nlanguage: english\ngrid: a8\ncards:\n"
        "  - subtopic: 'S'\n    front: 'a'\n    back: 'b'\n",
        encoding="utf-8",
    )
    if settings_text is not None:
        (tmp_path / "lernkarten.yaml").write_text(settings_text, encoding="utf-8")
    return deck


def test_setup_writes_the_three_keys_where_the_build_will_read_them(tmp_path):
    """FR-013/FR-014b/SC-006. The flags are the pytest-reachable path.

    The prompting path needs a terminal, which pytest has not got — it is on
    the manual checklist in docs/testing.md instead.
    """
    scratch_project(tmp_path)
    result = run(
        "setup",
        "--project",
        str(tmp_path),
        "--compartments",
        "4",
        "--dividers-printed",
        "no",
        "--box-printed",
        "no",
    )
    assert result.returncode == 0, result.stderr
    written = (tmp_path / "lernkarten.yaml").read_text(encoding="utf-8")
    assert "compartments: 4" in written
    assert "dividers_printed: false" in written


def test_setup_refuses_a_piped_stdin_rather_than_guessing(tmp_path):
    """FR-014b: a pipe is not a terminal, so there is nobody to ask."""
    scratch_project(tmp_path)
    result = subprocess.run(
        [sys.executable, str(CLI), "setup", "--project", str(tmp_path)],
        input="4\nn\nn\n",
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode != 0
    assert "--compartments" in result.stderr, "the error names the flags that work"
    assert not (tmp_path / "lernkarten.yaml").exists(), "nothing was guessed"


def test_an_unanswered_project_is_told_once_how_to_answer(tmp_path):
    """FR-014: the build is unchanged, and says so on stderr with a NOTE prefix.

    The prefix is load-bearing: two existing cases assert `"WARNING" not in
    result.stderr`, and this line appears on every run of an unanswered project.
    """
    deck = scratch_project(tmp_path)
    result = run("build", str(deck), "-o", str(tmp_path / "out.pdf"))
    assert result.returncode == 0, result.stderr
    assert result.stderr.count("lernkarten setup") == 1, result.stderr
    assert "NOTE:" in result.stderr
    assert "WARNING" not in result.stderr


def test_a_declined_project_is_never_nagged(tmp_path):
    """`compartments: none` is an answer, so the advisory stops."""
    deck = scratch_project(tmp_path, "compartments: none\n")
    result = run("build", str(deck), "-o", str(tmp_path / "out.pdf"))
    assert result.returncode == 0, result.stderr
    assert "lernkarten setup" not in result.stderr, "asked and declined is not unanswered"


def test_the_file_drives_the_dividers_without_a_flag(tmp_path):
    deck = scratch_project(tmp_path, "compartments: 3\n")
    result = run("build", str(deck), "-o", str(tmp_path / "out.pdf"))
    assert result.returncode == 0, result.stderr
    assert "3 dividers" in result.stdout, result.stdout


def test_a_printed_deck_is_not_reprinted_but_a_flag_still_wins(tmp_path):
    """FR-015: an explicit flag is a request just made and beats the file."""
    deck = scratch_project(tmp_path, "compartments: 3\ndividers_printed: true\n")
    quiet = run("build", str(deck), "-o", str(tmp_path / "a.pdf"))
    assert "dividers" not in quiet.stdout, quiet.stdout
    forced = run("build", str(deck), "-o", str(tmp_path / "b.pdf"), "--dividers", "3")
    assert "3 dividers" in forced.stdout, forced.stdout


def test_a_successful_build_records_that_the_dividers_are_printed(tmp_path):
    """FR-020, and the two limits that keep it safe."""
    deck = scratch_project(tmp_path, "compartments: 3\n")
    assert run("build", str(deck), "-o", str(tmp_path / "out.pdf")).returncode == 0
    assert "dividers_printed: true" in (tmp_path / "lernkarten.yaml").read_text(encoding="utf-8")

    # ... but never on `check`, which typesets without anything being printed —
    # and /print runs check before every build.
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    deck2 = scratch_project(fresh, "compartments: 3\n")
    assert run("check", str(deck2)).returncode == 0
    assert "dividers_printed: true" not in (fresh / "lernkarten.yaml").read_text(encoding="utf-8")

    # ... and never into a project that never answered.
    never = tmp_path / "never"
    never.mkdir()
    deck3 = scratch_project(never)
    assert run("build", str(deck3), "-o", str(never / "o.pdf"), "--dividers", "3").returncode == 0
    assert not (never / "lernkarten.yaml").exists(), "write-back never creates the file"


def test_a_file_driven_count_at_a7_skips_instead_of_refusing(tmp_path):
    """FR-015a. A flag is a request just made; a file is an answer from months ago.

    Refusing on the file would make an unrelated A7 build impossible for
    someone who once said "four compartments".
    """
    (tmp_path / "cards").mkdir()
    deck = tmp_path / "cards" / "deck.yaml"
    deck.write_text(
        "topic: 'T'\nlanguage: english\ngrid: a7\ncards:\n  - front: 'a'\n    back: 'b'\n",
        encoding="utf-8",
    )
    (tmp_path / "lernkarten.yaml").write_text("compartments: 4\n", encoding="utf-8")
    result = run("build", str(deck), "-o", str(tmp_path / "out.pdf"))
    assert result.returncode == 0, "a file must not make an A7 build impossible"
    assert "a8" in result.stderr.lower(), result.stderr
    assert "dividers" not in result.stdout, result.stdout


# --- the card box beside the cards (US3) -----------------------------------


def test_box_writes_the_pdf_beside_the_target_and_names_the_stock(tmp_path):
    """FR-010/FR-011/SC-007.

    Beside the `-o` target, not at a fixed `output/box.pdf`: a fixed path would
    put the file somewhere the user did not ask for whenever -o points
    elsewhere. Never merged into the card PDF -- merging would need a PDF
    library, and the two want different paper anyway.
    """
    target = tmp_path / "deck.pdf"
    result = run("build", *CARDS, "-o", str(target), "--grid", "a8", "--box")
    assert result.returncode == 0, result.stderr

    box = tmp_path / "box.pdf"
    assert box.exists(), "no box beside the target"
    assert box.read_bytes() == (ROOT / "assets" / "card-box.pdf").read_bytes()
    assert pdf_pages(target) == DEMO_A8_PAGES, "the card PDF is untouched by --box"

    assert "160" in result.stderr and "250" in result.stderr, result.stderr
    assert "box" in result.stderr.lower()


def test_box_as_a_flag_refuses_a_grid_it_does_not_fit(tmp_path):
    """US3 scenario 3, per FR-009 — the same rule the dividers follow."""
    target = tmp_path / "no.pdf"
    result = run("build", *CARDS, "-o", str(target), "--grid", "a7", "--box")
    assert result.returncode != 0
    assert "a8" in result.stderr.lower(), result.stderr
    assert not (tmp_path / "box.pdf").exists()


def test_a_deck_that_states_no_grid_is_told_once(tmp_path):
    """FR-006/SC-006. The whole safety net of #84 is this one line.

    Someone with a printed A7 deck has to find out that the default moved
    *before* they cut the reprint. Once per run, not once per deck: a project
    with six silent decks is one decision, not six.
    """
    (tmp_path / "cards").mkdir()
    for name in ("a", "b"):
        (tmp_path / "cards" / f"{name}.yaml").write_text(
            f"topic: '{name}'\nlanguage: english\ncards:\n  - front: 'x'\n    back: 'y'\n",
            encoding="utf-8",
        )
    decks = [str(p) for p in sorted((tmp_path / "cards").glob("*.yaml"))]

    result = run("check", *decks)
    assert result.returncode == 0, result.stderr
    said = [line for line in result.stderr.splitlines() if "state no `grid:` key" in line]
    assert len(said) == 1, f"once per run, whatever the number of silent decks: {result.stderr}"
    assert "a8" in said[0].lower(), "it has to name what the default now is"
    assert "grid: a7" in said[0], "and what to write to keep the old size"

    pinned = tmp_path / "cards" / "a.yaml"
    pinned.write_text(
        pinned.read_text(encoding="utf-8").replace(
            "language: english", "language: english\ngrid: a8"
        ),
        encoding="utf-8",
    )
    still = run("check", str(pinned))
    assert "state no `grid:` key" not in still.stderr, "a deck that states its grid is not nagged"


def test_the_suite_is_not_at_the_mercy_of_the_developers_own_machine(tmp_path):
    """FR-009/SC-006. Every command the suite runs must see a known config.

    Without this the tests pass or fail depending on whether whoever runs them
    once typed `lernkarten setup --sides simplex` — and they would pass on CI,
    which has no home directory to speak of, and fail on exactly one laptop.
    """
    assert os.environ.get("XDG_CONFIG_HOME"), (
        "conftest must point XDG_CONFIG_HOME somewhere empty for the whole run"
    )
    home = Path(os.environ["XDG_CONFIG_HOME"]) / "lernkarten" / "settings.yaml"
    assert not home.exists(), f"the suite is reading a real machine file: {home}"

    deck = scratch_project(tmp_path)
    result = run("build", str(deck), "-o", str(tmp_path / "o.pdf"))
    assert result.returncode == 0, result.stderr
    assert "says so" not in result.stderr, "no machine file, so nothing to report"


def test_the_machine_answers_for_every_project_until_a_flag_says_otherwise(tmp_path):
    """SC-002/SC-003. The point of #67: a printer is answered once, not per project.

    Two projects that have never heard of each other, one answer.
    """
    config = Path(os.environ["XDG_CONFIG_HOME"]) / "machine-test"
    env = dict(os.environ, XDG_CONFIG_HOME=str(config))

    def cmd(*args):
        return subprocess.run(
            [sys.executable, str(CLI), *args], capture_output=True, text=True, cwd=ROOT, env=env
        )

    assert cmd("setup", "--sides", "simplex").returncode == 0
    assert (config / "lernkarten" / "settings.yaml").exists()

    for name in ("one", "two"):
        room = tmp_path / name
        room.mkdir()
        deck = scratch_project(room)
        assert not (room / "lernkarten.yaml").exists(), "a machine answer touches no project"

        result = cmd("build", str(deck), "-o", str(room / "out.pdf"))
        assert result.returncode == 0, result.stderr
        assert "simplex" in result.stdout, f"{name}: the machine answer did not reach it"
        assert "says so" in result.stderr, f"{name}: the origin must be named"

        forced = cmd("build", str(deck), "-o", str(room / "flag.pdf"), "--sides", "duplex")
        assert "duplex" in forced.stdout, "a flag beats the machine"


def test_a_setting_written_into_the_wrong_file_is_named_not_obeyed(tmp_path):
    """SC-004, both directions. Two places one value can live is what #67 forbids."""
    deck = scratch_project(tmp_path, "compartments: none\nsides: simplex\n")
    result = run("build", str(deck), "-o", str(tmp_path / "o.pdf"))
    assert result.returncode == 0, result.stderr
    assert "sides" in result.stderr and "machine setting" in result.stderr, result.stderr
    assert "duplex" in result.stdout, "the misplaced key must not take effect"
