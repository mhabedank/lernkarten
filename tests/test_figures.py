"""Tests for scripts/figures.py — getting a picture out of a source.

Three jobs a prompt cannot do: rasterising a figure off a PDF page, downloading
one from a URL, and applying the slug rule that check_project.py later
validates. The PDF half needs pypdfium2, which is optional at runtime, so the
degraded path is tested as carefully as the working one — it is the one a user
offline will actually take.
"""

import base64
import http.server
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "tests" / "fixtures" / "demo-project"
HANDBOOK = DEMO / "raw" / "handbook" / "kestrel-handbook.pdf"
sys.path.insert(0, str(ROOT / "scripts"))

import figures  # noqa: E402

pytestmark = pytest.mark.skipif(not HANDBOOK.exists(), reason="run scripts/make_testdata.py first")

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00"
    b"\x00IEND\xaeB`\x82"
)


# A real AVIF, written by Pillow rather than pasted in as base64: a
# hand-assembled one had a valid `ftypavif` container and undecodable pixels,
# which would have let the test below pass for the wrong reason — refused
# because corrupt, not because the engine cannot read AVIF.
def avif_bytes():
    """A genuine AVIF, or None where this Pillow cannot write one."""
    from io import BytesIO

    from PIL import Image

    buffer = BytesIO()
    try:
        Image.new("RGB", (64, 48), (91, 127, 181)).save(buffer, format="AVIF")
    except Exception:  # noqa: BLE001 — an optional codec, not a failure
        return None
    return buffer.getvalue()


AVIF = avif_bytes()


def project(tmp_path):
    (tmp_path / "figures").mkdir(exist_ok=True)
    return tmp_path


# --- extract ---------------------------------------------------------------


def manifest(tmp_path, *extra):
    out = figures.main(
        ["extract", str(HANDBOOK), "--project", str(project(tmp_path)), "--source-id", "handbook"]
        + list(extra)
    )
    assert out == 0
    return json.loads((tmp_path / ".figures-staging" / "handbook" / "manifest.json").read_text())


def test_extract_reports_a_manifest(tmp_path):
    """The figure on page 3 is offered, with where it sat and how big it is."""
    pytest.importorskip("pypdfium2")
    found = manifest(tmp_path)
    chart = [c for c in found["candidates"] if c["width"] > 500]
    assert len(chart) == 1, found["candidates"]
    assert chart[0]["at"] == "page 3"
    assert Path(chart[0]["file"]).exists()


def test_a_picture_repeated_on_every_page_is_offered_once(tmp_path):
    """A logo in the running header is furniture, not a figure.

    Offered once and annotated with how many pages it appeared on, so the model
    can tell a repeated mark from a figure that happens to be small.
    """
    pytest.importorskip("pypdfium2")
    found = manifest(tmp_path)
    marks = [c for c in found["candidates"] if c["width"] < 500]
    assert len(marks) == 1, f"the header mark was offered {len(marks)} times"
    assert marks[0]["repeated_on"] == 4


def test_extract_without_pypdfium2_exits_three(tmp_path, capsys):
    """The degrade contract: exit 3, one line, no traceback (FR-018).

    A user with no PDF renderer still gets every transcription; what they lose
    is the figures, and the summary has to say so by name.
    """
    figures.PDFIUM_UNAVAILABLE = True
    try:
        code = figures.main(
            ["extract", str(HANDBOOK), "--project", str(project(tmp_path)), "--source-id", "h"]
        )
    finally:
        figures.PDFIUM_UNAVAILABLE = False
    assert code == 3
    stderr = capsys.readouterr().err
    assert "kestrel-handbook.pdf" in stderr, "the message has to name the document"
    assert "Traceback" not in stderr
    assert len(stderr.strip().splitlines()) == 1, stderr


# --- fetch -----------------------------------------------------------------


class Server(http.server.BaseHTTPRequestHandler):
    """A server that imitates the web, not our own code.

    The fixture this replaces answered every request with a PNG, at a URL ending
    in `.png`, with no bot protection — so BUG-008's two defects could not appear
    in it. Both were live in production for a release. What a fixture cannot
    express, a test cannot catch, and a green suite says nothing about it.

    The routes below are the shapes that actually broke:

        /chart.png              an ordinary picture
        /docsz/AD_4nXfNOMoq     image/png at a path with no extension at all,
                                which is what a CDN serves for anything pasted
                                out of Google Docs — 181 of 851 URLs
        /guarded.png            403 unless the request says who it is
        /notreally.png          text/html behind a picture's name
        /diagram.avif           a real image the engine cannot print
        /moved.png              a redirect, to prove the header survives one
    """

    redirect_to = None

    ROUTES = {
        "/chart.png": ("image/png", None),
        "/docsz/AD_4nXfNOMoq": ("image/png", None),
        "/notreally.png": ("text/html", b"<html><body>404, but with style</body></html>"),
        "/diagram.avif": ("image/avif", None),
    }

    def _send(self, content_type, body):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 — http.server's spelling
        if self.redirect_to:
            self.send_response(302)
            self.send_header("Location", self.redirect_to)
            self.end_headers()
            return

        # Bot protection, as Cloudflare does it: the empty case is what gets
        # blocked, not any particular client.
        agent = self.headers.get("User-Agent", "")
        if self.path.startswith("/guarded") and (not agent or agent.startswith("Python-urllib")):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden")
            return

        content_type, body = self.ROUTES.get(self.path, ("image/png", None))
        if body is None:
            body = AVIF if content_type == "image/avif" else PNG
        self._send(content_type, body)

    def log_message(self, *args):
        pass


@pytest.fixture
def serving():
    """Hands back a URL builder for the running server."""
    servers = []

    def make(path="/chart.png", redirect_to=None, same_host_path=None):
        handler = type("H", (Server,), {"redirect_to": redirect_to})
        httpd = http.server.HTTPServer(("127.0.0.1", 0), handler)
        base = f"http://127.0.0.1:{httpd.server_port}"
        if same_host_path:
            # Redirect within one server, or SameHostOnly refuses it for the
            # wrong reason and the test proves nothing about the header.
            handler.redirect_to = base + same_host_path
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        servers.append(httpd)
        return f"{base}{path}"

    yield make
    for httpd in servers:
        httpd.shutdown()


def test_fetch_uses_the_standard_library(tmp_path, serving):
    """urllib, so no dependency is added for something already in the box."""
    url = serving()
    assert (
        figures.main(["fetch", url, "--project", str(project(tmp_path)), "--source-id", "web"]) == 0
    )
    staged = list((tmp_path / ".figures-staging" / "web").glob("*.png"))
    assert len(staged) == 1 and staged[0].read_bytes() == PNG


def test_fetch_refuses_a_redirect_off_the_source_host(tmp_path, serving, capsys):
    """A source is a place the user chose. A redirect is not that choice."""
    url = serving(redirect_to="http://example.invalid/elsewhere.png")
    code = figures.main(["fetch", url, "--project", str(project(tmp_path)), "--source-id", "web"])
    assert code != 0
    assert "example.invalid" in capsys.readouterr().err


# --- BUG-008: fetch has to reach the web, not just our own fixture ----------


def staged_files(tmp_path, source_id="web"):
    folder = tmp_path / ".figures-staging" / source_id
    return sorted(folder.iterdir()) if folder.is_dir() else []


def fetch(tmp_path, url, source_id="web"):
    return figures.main(
        ["fetch", url, "--project", str(project(tmp_path)), "--source-id", source_id]
    )


def test_fetch_identifies_itself(tmp_path, serving):
    """Cloudflare blocks the *empty* case, not any particular client.

    An honest product token is the fix; a browser string would be pretending to
    be someone else, which FR-016 forbids and FR-026 says so explicitly.
    """
    assert fetch(tmp_path, serving("/guarded.png")) == 0
    assert len(staged_files(tmp_path)) == 1


def test_the_user_agent_names_the_tool_and_not_a_browser(tmp_path, serving):
    seen = {}
    original = figures.urllib.request.OpenerDirector.open

    def spy(self, request, *args, **kwargs):
        seen["agent"] = dict(self.addheaders).get("User-Agent", "")
        return original(self, request, *args, **kwargs)

    figures.urllib.request.OpenerDirector.open = spy
    try:
        assert fetch(tmp_path, serving()) == 0
    finally:
        figures.urllib.request.OpenerDirector.open = original
    agent = seen["agent"]
    assert "lernkarten" in agent, agent
    assert not any(b in agent for b in ("Mozilla", "Chrome", "Safari", "AppleWebKit")), agent


def test_the_user_agent_survives_a_redirect(tmp_path, serving):
    """Set on the *opener*, not the request, or the redirect drops it.

    The redirect lands on a path that 403s an anonymous request, so this fails
    if the header is attached to the first request only — which is the shape of
    the mistake worth guarding against.
    """
    url = serving("/moved.png", same_host_path="/guarded.png")
    assert fetch(tmp_path, url) == 0
    assert len(staged_files(tmp_path)) == 1


def test_an_extensionless_url_is_fetched_and_named_from_the_response(tmp_path, serving):
    """181 of 851 real URLs. A CDN path carries nothing to check."""
    assert fetch(tmp_path, serving("/docsz/AD_4nXfNOMoq")) == 0
    staged = staged_files(tmp_path)
    assert len(staged) == 1
    assert staged[0].suffix == ".png", f"named {staged[0].name}, and place needs an extension"
    assert staged[0].read_bytes() == PNG


def test_a_png_url_serving_html_is_refused_before_staging(tmp_path, serving, capsys):
    """The honesty sniffing buys: caught here, not at typesetting."""
    assert fetch(tmp_path, serving("/notreally.png")) != 0
    assert staged_files(tmp_path) == [], "nothing may be staged"
    assert "html" in capsys.readouterr().err.lower()


def test_a_url_with_no_filename_says_so(tmp_path, serving, capsys):
    """Not 'this is not an image' — the truth is 'this URL names no file'."""
    assert fetch(tmp_path, serving("/notreally.png")) != 0
    message = capsys.readouterr().err
    assert "not a picture this engine reads" not in message, (
        "the old message blamed the format for something else entirely"
    )


@pytest.mark.skipif(AVIF is None, reason="this Pillow cannot write AVIF")
def test_avif_is_fetched_but_refused_as_a_card_picture(tmp_path, serving, capsys):
    """Downloadable, not printable. Two different questions (FR-028).

    Verified against the pinned engine: typst 0.15.1 gives `error: unknown image
    format` for a genuine AVIF, so widening IMAGE_FORMATS would move a clear
    message to an engine error at build time.
    """
    assert fetch(tmp_path, serving("/diagram.avif")) == 0, "it is a real image; download it"
    staged = staged_files(tmp_path)
    assert len(staged) == 1 and staged[0].suffix == ".avif"

    assert place(tmp_path, str(staged[0]), "driver-tree") != 0
    message = capsys.readouterr().err
    assert "avif" in message.lower()
    assert "convert" in message.lower(), "say what to do, not just what is wrong"


# --- place -----------------------------------------------------------------


def staged(tmp_path, name="p3-1.png", data=PNG):
    folder = tmp_path / ".figures-staging" / "handbook"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(data)
    return str(path)


def place(tmp_path, source, slug, *extra):
    return figures.main(
        [
            "place",
            source,
            "--project",
            str(project(tmp_path)),
            "--source-id",
            "handbook",
            "--slug",
            slug,
            *extra,
        ]
    )


def test_place_puts_the_picture_under_its_source(tmp_path):
    assert place(tmp_path, staged(tmp_path), "tide-curve") == 0
    assert (tmp_path / "figures" / "handbook" / "tide-curve.png").read_bytes() == PNG


def test_place_refuses_a_slug_that_is_not_kebab_case(tmp_path, capsys):
    assert place(tmp_path, staged(tmp_path), "Tide Curve") != 0
    assert "kebab-case" in capsys.readouterr().err


def test_the_same_bytes_placed_twice_are_one_file(tmp_path):
    """Idempotence: a second /ingest must not grow the figure store."""
    assert place(tmp_path, staged(tmp_path), "tide-curve") == 0
    assert place(tmp_path, staged(tmp_path, "p3-1-again.png"), "tide-curve") == 0
    assert len(list((tmp_path / "figures" / "handbook").iterdir())) == 1


def test_place_never_overwrites_a_different_picture(tmp_path, capsys):
    assert place(tmp_path, staged(tmp_path), "tide-curve") == 0
    other = staged(tmp_path, "p4-1.png", PNG + b"\x00")
    assert place(tmp_path, other, "tide-curve") != 0
    assert "already" in capsys.readouterr().err
    assert place(tmp_path, other, "tide-curve", "--force") == 0


def test_place_leaves_the_original_alone(tmp_path):
    """A copy, never a move: the source is not ours to reorganise (FR-010)."""
    source = staged(tmp_path)
    before = Path(source).read_bytes(), Path(source).stat().st_mtime
    assert place(tmp_path, source, "tide-curve") == 0
    assert (Path(source).read_bytes(), Path(source).stat().st_mtime) == before


# --- the command line ------------------------------------------------------


def test_the_module_runs_as_a_command():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "figures.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    for verb in ("extract", "fetch", "place"):
        assert verb in result.stdout


def test_pages_narrows_what_is_looked_at(tmp_path):
    """`sources.yaml` already spells a slice; extract honours the same one.

    The figure sits on page 3, so asking for pages 1-2 must not find it — a
    source that ingests two pages of a long book should not have figures pulled
    off the rest of it.
    """
    pytest.importorskip("pypdfium2")
    found = manifest(tmp_path, "--pages", "1-2")
    assert not [c for c in found["candidates"] if c["width"] > 500], found["candidates"]
    assert [c for c in found["candidates"] if c["width"] < 500], "the header mark is on page 1"


@pytest.mark.parametrize("spec", ["nonsense", "0-2", "4-2"])
def test_a_bad_page_range_is_refused_by_name(tmp_path, spec, capsys):
    pytest.importorskip("pypdfium2")
    code = figures.main(
        [
            "extract",
            str(HANDBOOK),
            "--project",
            str(project(tmp_path)),
            "--source-id",
            "handbook",
            "--pages",
            spec,
        ]
    )
    assert code == 1
    assert spec in capsys.readouterr().err
