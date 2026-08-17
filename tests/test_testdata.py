"""The raw material: what scripts/make_testdata.py builds, and whether it is
really the thing /ingest has to cope with.

A PDF that claims to be a scan is only useful as test data if no text can be
pulled out of it, and an infographic only if it is pixels. That is what this
module checks — the generator, and then the artifacts themselves.
"""

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "tests" / "fixtures" / "demo-project"
RAW = DEMO / "raw"
sys.path.insert(0, str(ROOT / "scripts"))

import make_testdata  # noqa: E402
import minyaml  # noqa: E402
import zotero_ingest  # noqa: E402

HANDBOOK = RAW / "handbook" / "kestrel-handbook.pdf"
SCAN = RAW / "handbook" / "tide-tables-scan.pdf"
ALMANAC = RAW / "handbook" / "tide-almanac.pdf"
DAMAGED = RAW / "handbook" / "damaged.pdf"
LATIN1 = RAW / "field-notes" / "harbour-log.txt"
CHART = RAW / "images" / "tide-chart.png"
PHOTO = RAW / "images" / "harbour-noticeboard.jpg"
DOCX = RAW / "office" / "mail-boat-timetable.docx"

# What the ingest skill says it can read. One file of each has to exist, or the
# fixture stops being a test of the folder walk.
SUPPORTED = {".pdf", ".md", ".txt", ".html", ".docx", ".png"}


@pytest.fixture(scope="session", autouse=True)
def testdata():
    """Builds the binary test data once; skips if that is impossible here."""
    try:
        make_testdata.build()
    except make_testdata.BuildError as e:
        pytest.skip(f"cannot build the test data: {e}")


def pdf_text(path):
    """The text layer of a PDF, or None when no extractor is installed."""
    if shutil.which("pdftotext") is None:
        return None
    # Both sides of the encoding stated outright — see scripts/zotero_ingest.py.
    result = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", "-layout", str(path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout if result.returncode == 0 else ""


def png_size(path):
    """(width, height) from the PNG header — no image library needed."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    assert data[12:16] == b"IHDR"
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


# --- the generator --------------------------------------------------------


def test_it_builds_everything_it_promises():
    for target, _, _ in make_testdata.JOBS:
        if target in make_testdata.OPTIONAL and not make_testdata.jpeg_available():
            continue
        assert target.exists(), f"{target.relative_to(ROOT)} was not built"
        assert target.stat().st_size > 500, f"{target.name} is suspiciously small"


def test_a_second_run_builds_nothing():
    assert make_testdata.build() == [], "the generator is not idempotent"


def test_check_agrees_that_nothing_is_stale():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "make_testdata.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "up to date" in result.stdout


def test_a_deleted_artifact_comes_back(tmp_path):
    victim = DOCX
    backup = tmp_path / victim.name
    shutil.copy(victim, backup)
    victim.unlink()
    try:
        assert victim in make_testdata.build()
        assert victim.exists()
    finally:
        if not victim.exists():
            shutil.copy(backup, victim)


# --- the PDF with a text layer --------------------------------------------


def test_the_handbook_is_a_multi_page_pdf():
    data = HANDBOOK.read_bytes()
    assert data.startswith(b"%PDF-")
    assert b"/Count 4" in data, "the 'pages' option needs a PDF with several pages"


def test_the_handbook_has_a_text_layer():
    text = pdf_text(HANDBOOK)
    if text is None:
        pytest.skip("pdftotext is not installed")
    assert len(text) > 1500, "an ordinary PDF has to yield its text"
    for expected in ("Kestrel", "rule of twelfths", "Torvig Harbour"):
        assert expected in text


def test_the_almanac_is_long_enough_to_need_chunking():
    """Over ~40 pages the ingest is told to prefer pdftotext and read in chunks."""
    data = ALMANAC.read_bytes()
    pages = max(int(c) for c in re.findall(rb"/Count\s+(\d+)", data))
    assert pages > 40, f"{pages} pages is not long enough to test the long-document path"


def test_the_almanac_still_yields_its_text():
    text = pdf_text(ALMANAC)
    if text is None:
        pytest.skip("pdftotext is not installed")
    assert "Week 60" in text, "the last page has to be readable too"


# --- the file that cannot be read at all ----------------------------------


def test_the_damaged_pdf_looks_like_a_pdf_and_is_not_one():
    data = DAMAGED.read_bytes()
    assert data.startswith(b"%PDF-"), "it has to get past a file-type check first"
    assert b"%%EOF" not in data, "a truncated file has no trailer"


def test_nothing_can_be_extracted_from_the_damaged_pdf():
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is not installed")
    text, pending = zotero_ingest.extract(DAMAGED)
    assert text is None and pending, "a broken file is not silently ingested as empty"


# --- text that is not UTF-8 -----------------------------------------------


def test_the_harbour_log_is_not_utf_8():
    raw = LATIN1.read_bytes()
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")
    assert "Stärke" in raw.decode("cp1252"), "the umlauts are the point of the file"


# --- the scan, which is the whole point of having one ---------------------


def test_the_scan_is_two_pages_of_pixels():
    data = SCAN.read_bytes()
    assert data.startswith(b"%PDF-")
    assert b"/Count 2" in data
    assert b"/Image" in data, "a scan is images, not glyphs"


def test_nothing_can_be_extracted_from_the_scan():
    text = pdf_text(SCAN)
    if text is None:
        pytest.skip("pdftotext is not installed")
    assert len(text.strip()) < 200, (
        "the scan must not have a text layer — otherwise it tests nothing"
    )


def test_the_ingest_treats_the_scan_as_pending_and_the_handbook_as_text():
    """The branch zotero_ingest keys on: extractable or a job for the Read tool."""
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is not installed")
    text, pending = zotero_ingest.extract(HANDBOOK)
    assert text and not pending
    text, pending = zotero_ingest.extract(SCAN)
    assert pending and text is None


# --- the image and the office document ------------------------------------


def test_the_infographic_is_a_real_image():
    width, height = png_size(CHART)
    assert width > 800 and height > 400, f"{width}x{height} is too small to read"
    assert CHART.stat().st_size > 20_000


def test_the_photo_is_a_real_jpeg():
    data = PHOTO.read_bytes()
    assert data[:2] == b"\xff\xd8", "not a JPEG (no SOI marker)"
    assert data[-2:] == b"\xff\xd9", "the JPEG was not written completely"
    assert len(data) > 20_000


def test_the_jpeg_needs_nothing_the_machine_happens_to_have(tmp_path, monkeypatch):
    """Pillow is declared, so this no longer depends on finding sips or magick.

    It used to be whichever of sips, magick or convert existed — which meant the
    JPEG was built on macOS, sometimes on Linux and never on Windows, so the one
    fixture covering a photographed notice quietly did not exist on most CI legs.
    """
    monkeypatch.setenv("PATH", str(tmp_path))
    assert shutil.which("sips") is None and shutil.which("magick") is None, (
        "the point of this test is that no system converter is reachable"
    )
    binary, _ = make_testdata.engine.find(fetch_if_missing=False)
    target = tmp_path / "photo.jpg"
    make_testdata.build_jpeg(binary, DEMO / "generators" / "noticeboard.typ", target)
    data = target.read_bytes()
    assert data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9", "not a complete JPEG"


def test_the_docx_is_a_readable_word_file():
    with zipfile.ZipFile(DOCX) as z:
        assert "word/document.xml" in z.namelist()
        assert "[Content_Types].xml" in z.namelist()
        text = z.read("word/document.xml").decode("utf-8")
    assert "Mail boat timetable" in text
    assert "Ovray Cove" in text


# --- the folder a user would point /sources at ----------------------------


def test_every_file_type_the_ingest_claims_to_read_is_there():
    present = {p.suffix.lower() for p in RAW.rglob("*") if p.is_file()}
    assert present >= SUPPORTED, f"no test file for {sorted(SUPPORTED - present)}"


def test_the_field_notes_hold_the_awkward_cases():
    notes = RAW / "field-notes"
    assert (notes / "appendix" / "wind-log.txt").exists(), "no file in a subfolder"
    assert (notes / "empty.md").exists() and (notes / "empty.md").stat().st_size == 0
    non_ascii = [p for p in notes.iterdir() if not p.name.isascii()]
    assert non_ascii, "no file name with an umlaut — slug building is never tested"


def test_the_web_source_is_a_small_site_with_links():
    pages = sorted(p.name for p in (RAW / "web").glob("*.html"))
    assert pages == ["index.html", "members.html", "signals.html", "tides.html"]
    index = (RAW / "web" / "index.html").read_text(encoding="utf-8")
    assert 'href="tides.html"' in index and 'href="signals.html"' in index
    assert "cookie-banner" in index, "boilerplate is there on purpose, to be dropped"


def test_the_ingest_skill_reads_the_image_formats_the_fixture_offers():
    """A folder of photos has to be ingested without the user writing a pattern."""
    skill = (ROOT / "skills" / "ingest" / "SKILL.md").read_text(encoding="utf-8")
    default = skill.split("collect files recursively by `pattern` (default:", 1)[1]
    default = default.split(")", 1)[0]
    for extension in (".png", ".jpg"):
        assert f"*{extension}" in default, (
            f"{extension} is not in the default folder pattern — such a folder ingests as empty"
        )


def test_every_local_source_in_the_register_exists():
    data = minyaml.load((DEMO / "sources.yaml").read_text(encoding="utf-8"))
    for entry in data["sources"]:
        if entry["type"] in ("folder", "pdf"):
            assert (DEMO / entry["path"]).exists(), f"{entry['id']}: {entry['path']} is missing"
