"""The two source types that need something to talk to: web and zotero.

Both are served locally here — a static site out of raw/web, and the fake
Zotero library out of tests/fixtures/zotero. Nothing in this module touches
the network, and nothing needs Zotero installed.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "tests" / "fixtures" / "demo-project"
WEB = DEMO / "raw" / "web"
ZOTERO = ROOT / "tests" / "fixtures" / "zotero"
INGEST = ROOT / "scripts" / "zotero_ingest.py"
sys.path.insert(0, str(ROOT / "scripts"))

import make_testdata  # noqa: E402
import zotero_stub  # noqa: E402

HREF = re.compile(r'href="([^"]+)"')


def serve(server):
    """Runs a server in the background and shuts it down afterwards."""
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, r.read().decode("utf-8")


# --- a web source ---------------------------------------------------------


class GuardedHandler(SimpleHTTPRequestHandler):
    """Serves the demo site, but refuses one path the way bot protection does."""

    FORBIDDEN = "/pilot-roster.html"

    def do_GET(self):  # noqa: N802 — the base class spells it this way
        if self.path == self.FORBIDDEN:
            self.send_error(403, "Forbidden")
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        pass


@pytest.fixture(scope="module")
def site():
    """The demo site on a free port — what a `type: web` source points at."""
    handler = partial(GuardedHandler, directory=str(WEB))
    yield from serve(ThreadingHTTPServer(("127.0.0.1", 0), handler))


def test_the_entry_page_answers(site):
    status, body = get(f"{site}/index.html")
    assert status == 200
    assert "Harbour office Torvig" in body
    assert "deep-water pier" in body


def test_the_entry_page_links_to_the_subpages_a_depth_one_ingest_would_follow(site):
    _, body = get(f"{site}/index.html")
    local = {h for h in HREF.findall(body) if not h.startswith(("http", "/"))}
    assert {"tides.html", "signals.html", "members.html"} <= local


def test_every_local_link_resolves(site):
    _, body = get(f"{site}/index.html")
    for href in HREF.findall(body):
        if href.startswith(("http://", "https://", "/")):
            continue
        status, _ = get(f"{site}/{href}")
        assert status == 200, f"{href} is a dead link in the fixture"


def test_the_subpages_carry_the_content_the_cards_are_made_of(site):
    _, tides = get(f"{site}/tides.html")
    assert "rule of twelfths" in tides and "3.4 m" in tides
    _, signals = get(f"{site}/signals.html")
    assert "harbour closed" in signals and "Half mast" in signals


def test_the_page_behind_the_login_gives_nothing_away(site):
    """`login: true` in the register — an ingest must not invent what is inside."""
    _, body = get(f"{site}/members.html")
    assert 'type="password"' in body and "Sign in" in body
    assert "<table" not in body, (
        "everything of substance has to stay behind the form — there is nothing to ingest"
    )


def test_the_entry_page_carries_boilerplate_to_be_dropped(site):
    _, body = get(f"{site}/index.html")
    assert "cookie" in body.lower() and "<nav>" in body


def test_a_page_that_refuses_the_fetch_is_a_403(site):
    """What bot protection looks like: the skill falls back to the browser here."""
    with pytest.raises(urllib.error.HTTPError) as e:
        get(f"{site}{GuardedHandler.FORBIDDEN}")
    assert e.value.code == 403


def test_a_page_that_is_not_there_is_a_404(site):
    with pytest.raises(urllib.error.HTTPError) as e:
        get(f"{site}/does-not-exist.html")
    assert e.value.code == 404


# --- a zotero source ------------------------------------------------------


@pytest.fixture(scope="module")
def library():
    """The fake Zotero library, on a free port, with its storage built."""
    try:
        make_testdata.build()
    except make_testdata.BuildError as e:
        pytest.skip(f"cannot build the attachments: {e}")
    yield from serve(zotero_stub.serve(port=0, quiet=True))


def ingest(library, project, *args, path=None):
    """Runs zotero_ingest.py against the stub, writing into `project`."""
    env = dict(
        os.environ,
        ZOTERO_API=f"{library}/api/users/0",
        ZOTERO_STORAGE=str(ZOTERO / "storage"),
    )
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        [sys.executable, str(INGEST), "--project", str(project), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def documents(project, source_id="kestrel-zotero"):
    folder = Path(project) / "knowledge" / source_id
    return {p.stem: p.read_text(encoding="utf-8") for p in folder.glob("*.md")}


def test_the_stub_answers_like_the_local_api(library):
    _, body = get(f"{library}/api/users/0/collections?limit=100&start=0")
    collections = {c["data"]["name"] for c in json.loads(body)}
    assert {"Kestrel Islands", "Mainland"} <= collections


def test_it_writes_one_document_per_item_with_a_pdf(library, tmp_path):
    result = ingest(
        library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands"
    )
    assert result.returncode == 0, result.stderr
    files = documents(tmp_path)
    assert set(files) == {
        "currents-in-the-ashwind-sea-a-first-survey",
        "tide-tables-of-the-kestrel-islands-scanned",
        "signal-code-of-the-kestrel-islands-offprint",
        "fog-over-the-kestrel-deep",
    }
    assert "3 new, 1 awaiting the Read tool" in result.stdout


def test_the_metadata_of_an_item_lands_in_the_frontmatter(library, tmp_path):
    ingest(library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands")
    paper = documents(tmp_path)["currents-in-the-ashwind-sea-a-first-survey"]
    assert 'authors: "Marek Ovray, Sanne Torvig"' in paper
    assert 'year: "2019"' in paper
    assert 'collections: "Kestrel Islands"' in paper
    assert "zotero_key: ITEM01" in paper
    assert "source: kestrel-zotero" in paper
    assert "Journal of Invented Oceanography" in paper, "the text itself is missing"


def test_a_scanned_attachment_is_left_for_the_read_tool(library, tmp_path):
    if shutil.which("pdftotext") is None:
        pytest.skip("without pdftotext everything is pending, which proves nothing")
    ingest(library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands")
    scan = documents(tmp_path)["tide-tables-of-the-kestrel-islands-scanned"]
    assert "pending:" in scan, "a scan has no text layer — it has to be flagged"
    assert "read this PDF with the Read tool" in scan


def test_an_item_without_a_pdf_is_counted_but_not_written(library, tmp_path):
    result = ingest(
        library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands"
    )
    assert "2 without a PDF" in result.stdout, result.stdout
    assert not any("bird" in name for name in documents(tmp_path))


def test_a_second_run_skips_what_is_already_there(library, tmp_path):
    ingest(library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands")
    again = ingest(
        library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands"
    )
    assert "0 new" in again.stdout and "4 skipped" in again.stdout, again.stdout


def test_the_collection_filter_leaves_the_other_collection_alone(library, tmp_path):
    ingest(library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands")
    assert not any("ferry" in name for name in documents(tmp_path))

    whole = tmp_path / "whole"
    ingest(library, whole, "--source-id", "kestrel-zotero")
    assert any("ferry" in name for name in documents(whole)), (
        "without --collection the whole library is fetched"
    )


def test_an_unknown_collection_names_the_ones_that_exist(library, tmp_path):
    result = ingest(library, tmp_path, "--source-id", "x", "--collection", "Atlantis")
    assert result.returncode != 0
    assert "not found" in result.stderr and "Kestrel Islands" in result.stderr


def test_an_unreachable_library_says_so(tmp_path):
    result = ingest("http://127.0.0.1:1", tmp_path, "--source-id", "x")
    assert result.returncode != 0
    assert "Zotero API unreachable" in result.stderr


def test_without_an_extractor_everything_waits_for_the_read_tool(library, tmp_path):
    """No pdftotext on the machine: the metadata is written, the text is not."""
    empty = tmp_path / "no-tools"
    empty.mkdir()
    result = ingest(
        library,
        tmp_path,
        "--source-id",
        "kestrel-zotero",
        "--collection",
        "Kestrel Islands",
        path=str(empty),
    )
    assert result.returncode == 0, result.stderr
    assert "0 new, 4 awaiting the Read tool" in result.stdout
    assert all("pending:" in text for text in documents(tmp_path).values())


def test_an_attachment_filed_by_absolute_path_is_found(library, tmp_path):
    """Not every attachment is a `storage:` one — some carry a full path."""
    ingest(library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands")
    files = documents(tmp_path)
    assert "fog-over-the-kestrel-deep" in files
    assert "zotero_key: ITEM08" in files["fog-over-the-kestrel-deep"]


def test_a_note_under_an_item_is_not_mistaken_for_a_document(library, tmp_path):
    """The paper has a note attached as well — one document has to come out."""
    ingest(library, tmp_path, "--source-id", "kestrel-zotero", "--collection", "Kestrel Islands")
    papers = [name for name in documents(tmp_path) if name.startswith("currents-in-the-ashwind")]
    assert len(papers) == 1


def test_it_writes_into_the_project_and_not_into_the_repo(library, tmp_path):
    before = sorted(p.name for p in (ROOT / "knowledge").iterdir())
    result = ingest(library, tmp_path, "--source-id", "kestrel-zotero")
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "knowledge" / "kestrel-zotero").is_dir()
    assert sorted(p.name for p in (ROOT / "knowledge").iterdir()) == before, (
        "the ingest wrote into the plugin folder instead of the user's project"
    )
