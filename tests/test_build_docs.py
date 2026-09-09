"""The documentation build: the real command, a real Sphinx run, real output.

Everything here runs `scripts/build_docs.py` as a subprocess, the way a
contributor and the `docs-build` CI job do. What the other modules assert about
sources, this asserts about what the build makes of them.

Sphinx is needed for all of it, and it is not in `requirements-dev.txt` — a
contributor running the four gates installs pytest and ruff and nothing else.
So this module **skips** when the documentation requirements are absent, the
way `tests/test_e2e.py` skips without a typesetting engine. That is deliberate
(FR-023, SC-006) and it has a consequence worth stating: writing an assertion
here before running `pip install -r requirements-docs.txt` shows it *skipped*,
never red, and a skip is not the red constitution XI asks for.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUILD_DOCS = ROOT / "scripts" / "build_docs.py"

pytest.importorskip(
    "sphinx",
    reason="the documentation toolchain is absent — pip install -r requirements-docs.txt",
)


def build(*args, source=None, site=None):
    """Runs the build the way a contributor does. Never raises.

    `sys.executable`, never the string `python3`: the Windows leg of the
    `docs-build` job is the only place these assertions execute rather than
    skip, and `python3` is not what that runner resolves. A hard-coded
    `python3` would fail every one of them for a reason that has nothing to do
    with the documentation.
    """
    argv = [sys.executable, str(BUILD_DOCS), *args]
    if source is not None:
        argv += ["--source", str(source)]
    if site is not None:
        argv += ["--site", str(site)]
    return subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)


def toctree(site):
    """What the root document pulls in, read from the build environment.

    Not from the rendered sidebar: that is the theme's presentation of this
    same data, so asserting against it would tie the check to a theme version
    and break on an upgrade that changed nothing about the documentation.
    """
    import pickle

    with open(site / "docs" / ".doctrees" / "environment.pickle", "rb") as handle:
        env = pickle.load(handle)
    return env.toctree_includes


def reachable_documents(site):
    """Every document reachable from the root through nested toctrees."""
    includes = toctree(site)
    seen, frontier = set(), ["index"]
    while frontier:
        docname = frontier.pop()
        if docname in seen:
            continue
        seen.add(docname)
        frontier += includes.get(docname, [])
    return seen


def test_the_build_exits_zero_and_writes_an_index(tmp_path):
    """One command, no arguments, and a site that opens.

    FR-019 asks for a command a contributor can run without remembering
    anything. `--site` exists so a test does not write into the working tree;
    that it has a default is what makes the no-argument form the real command.
    """
    result = build(site=tmp_path)

    assert result.returncode == 0, (
        f"the build exited {result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    index = tmp_path / "docs" / "index.html"
    assert index.exists(), (
        f"no {index.relative_to(tmp_path)} in the assembled site. The documentation is "
        f"published at /docs/, so that file is the page the landing page's `docs/` link "
        f"opens. The site holds {sorted(p.name for p in tmp_path.rglob('*'))[:20]}"
    )


def hrefs(site, document):
    """Every `href` on a built page, in source order."""
    import re

    html = (site / "docs" / document).read_text(encoding="utf-8")
    return re.findall(r'href="([^"]+)"', html)


def test_every_repository_link_resolves(tmp_path):
    """The four branches of the transform, one representative each.

    No source file is edited to make this pass. That is the whole design: the
    five migrated documents keep the relative paths they have on disk, so
    `check_docs.check_links` goes on resolving them against the file system,
    and the build rewrites them for the web. Retargeting them by hand would
    make each one dead in the checkout and turn gate #4 red — the repair that
    looks obvious and is wrong.
    """
    result = build(site=tmp_path)
    assert result.returncode == 0, f"the build failed:\n{result.stdout}\n{result.stderr}"

    design = hrefs(tmp_path, "contributing/design.html")
    joined = " ".join(design)

    # A page of this site: an internal cross-reference, anchor preserved.
    assert any(h.endswith("design.html#the-box") or "#the-box" in h for h in design), (
        f"`design.md#the-box` did not become an internal reference with its anchor. "
        f"The page links {design[:15]}"
    )
    # Served at the site root, depth-aware — two levels up from docs/contributing/.
    assert "../../index.html" in design, (
        f"`index.html` did not become `../../index.html`. From a page two levels inside "
        f"the documentation tree, one `../` reaches the wrong place (C2). Links: {design[:15]}"
    )
    assert "../../card-box.pdf" in design, (
        "`../assets/card-box.pdf` did not become `../../card-box.pdf`. It is a published "
        "download at the site root, not a repository file to send a reader to GitHub for"
    )
    # A repository file that is not a page: a GitHub blob URL.
    assert "blob/main/templates/card.typ" in joined, (
        f"`../templates/card.typ` did not become a GitHub blob URL. Links: {design[:15]}"
    )
    # A directory: a tree URL, not a blob URL.
    assert "tree/main/assets/fonts" in joined, (
        "`../assets/fonts/` did not become a GitHub tree URL — a directory is not a blob"
    )

    # The anchor survives the rewrite to an absolute URL.
    workflow = " ".join(hrefs(tmp_path, "user/workflow.html"))
    assert "blob/main/README.md#install" in workflow, (
        "`../README.md#install` lost its anchor on the way to GitHub, so the link lands "
        "at the top of the README instead of at the install section"
    )


def test_the_method_page_is_never_duplicated(tmp_path):
    """One page, one URL — and the natural way to write it gives two.

    A link from a page here to a file that exists on disk is read as a
    *download*: Sphinx copies the file under `_downloads/<hash>/` and marks
    the link `download`, so a reader who clicks it gets a saved file instead
    of the page, at an address nothing else links. The method page would then
    exist twice — once at the site root, where the landing page and the README
    point, and once inside the documentation tree.

    Nothing warns about it. The build is perfectly happy, which is why this
    needs an assertion rather than an eye.

    Asserted on the output rather than on the exit code, on purpose. `-W
    --keep-going` writes the site and *then* reports, so the artifacts exist
    either way, and this assertion is about what was written rather than about
    whether some unrelated page had a bad link. Row 5 owns the exit code;
    coupling every later row to it makes each one fail for the previous one's
    reason.
    """
    build(site=tmp_path)

    downloads = list((tmp_path / "docs").rglob("_downloads"))
    assert not downloads, (
        f"the build wrote {[str(d) for d in downloads]}. A `_downloads/` directory here "
        f"means a link that should open a page is saving a copy of it instead"
    )

    # By content, not by name: `docs/user/leitner.html` is the signpost page
    # that introduces the method, which is a different document that happens
    # to share a basename. What must not exist is a second copy of the method
    # page itself.
    original = (ROOT / "docs" / "leitner.html").read_bytes()
    copies = sorted(
        p.relative_to(tmp_path).as_posix()
        for p in (tmp_path / "docs").rglob("*.html")
        if p.read_bytes() == original
    )
    assert not copies, (
        f"the documentation tree holds a copy of the method page at {copies}. It is served "
        f"at the site root, where docs/index.html and README.md both link it; a second copy "
        f"is a second URL for one page"
    )


def docsite_copy(tmp_path):
    """A throwaway copy of `docsite/` to write probe pages into.

    Never the checked-in tree. An interrupted run would leave a probe page
    behind that fails the next build, fails gate #4 — `check_docs.check_links`
    reads `docsite/**/*.md` and a probe's dead link is exactly what it reports
    — and trips the no-stray-copies guard. Whoever hit it next would be
    debugging a failure that has nothing to do with their change.

    It copies more than `docsite/`, and it has to. Every migrated page is one
    `{include}` reaching two levels up, so a bare `copytree` of `docsite/`
    alone leaves those targets missing: the pages build empty, lose the H1
    they take their title from, and every toctree entry warns instead. The
    failure looks like a broken toctree and is really a broken fixture. So the
    copy reconstructs the part of the repository the includes reach.
    """
    import shutil

    shutil.copytree(ROOT / "docsite", tmp_path / "docsite")
    shutil.copytree(ROOT / "docs", tmp_path / "docs")
    shutil.copytree(ROOT / "assets", tmp_path / "assets")
    shutil.copy2(ROOT / "CONTRIBUTING.md", tmp_path / "CONTRIBUTING.md")
    return tmp_path / "docsite"


def test_a_missing_reference_fails_the_build(tmp_path):
    """A reference to something that does not exist stops the build.

    This is the drift protection the whole feature is for. A dead link that
    merely warns is a dead link that ships — which is how this repository
    ended up with a landing page whose only outbound link 404'd for a release.
    The message has to name both ends, because "one warning" in a build of
    forty pages is not a bug report.

    The last assertion checks that the probe's *own* error disappears with the
    probe, rather than that the build then passes. Those are the same thing
    only once the site builds clean, and it does not between enabling `-W` and
    landing the link transform: the twenty-seven unresolved repository links
    are still open in that window, deliberately. Asserting a clean build here
    would make this test a hostage of another phase and would tempt whoever
    hit it into hand-editing a source link — which is exactly the repair that
    puts a dead path into `check_docs.check_links` and turns gate #4 red.
    """
    source = docsite_copy(tmp_path)
    probe = source / "user" / "probe.md"
    probe.write_text(
        ":orphan:\n\n# Probe\n\n[a page that does not exist](nowhere.md)\n",
        encoding="utf-8",
    )

    result = build(source=source, site=tmp_path / "site")
    assert result.returncode != 0, (
        "the build exited 0 with an unresolved reference in it. Warnings that do not "
        f"fail are warnings nobody reads.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    output = result.stdout + result.stderr
    assert "probe" in output and "nowhere" in output, (
        f"the failure names neither the document nor the target it could not resolve, so "
        f"it cannot be acted on:\n{output}"
    )

    probe.unlink()
    after = build(source=source, site=tmp_path / "site2")
    remaining = after.stdout + after.stderr
    assert "probe" not in remaining and "nowhere" not in remaining, (
        f"the probe's failure survives the probe's deletion, so the assertions above were "
        f"reading something else:\n{remaining}"
    )


def test_a_docsite_page_may_link_a_repository_file(tmp_path):
    """The spelling the gate requires is also the spelling that renders.

    `check_docs.check_links` resolves a relative target against the file
    system, so a page here has to write `../docs/design.md` with its
    extension or the gate cannot see it. MyST reads that same target the other
    way: it strips the `.md`, looks for a *document* of that name, finds none,
    warns, and renders the text with no link at all — so the spelling that
    keeps the gate honest is the one that silently produces no link.

    The probe sits at the root of the copy because that is the depth this
    spelling is correct at; from a page in `user/` the same link needs another
    `../`. The branch under test does not depend on depth, but a probe written
    at the wrong one fails on the path and looks like the bug reappearing.
    """
    source = docsite_copy(tmp_path)
    probe = source / "probe.md"
    probe.write_text(
        ":orphan:\n\n# Probe\n\n[design.md](../docs/design.md)\n",
        encoding="utf-8",
    )

    build(source=source, site=tmp_path / "site")
    html = (tmp_path / "site" / "docs" / "probe.html").read_text(encoding="utf-8")

    assert 'href="contributing/design.html"' in html, (
        f"`[design.md](../docs/design.md)` did not become a link to the page this site "
        f"publishes for that file. MyST strips the extension and resolves a docname; "
        f"unhandled, the text renders unlinked. The page contains:\n{html[-800:]}"
    )


def test_the_images_are_rendered_not_linked(tmp_path):
    """The two figures appear as pictures, not as links to GitHub.

    `docs/workflow.md` and `docs/design.md` both render an image from
    `../assets/`. Pulled in with `{include}`, those paths resolve against the
    *including* page unless the include says otherwise — so without
    `:relative-images:` the pipeline diagram and the example cards are simply
    missing, and the transform would be within its rights to turn them into
    repository URLs, which is a link where a picture belongs.
    """
    build(site=tmp_path)

    for document, name in [
        ("user/workflow.html", "pipeline"),
        ("contributing/design.html", "example-cards"),
    ]:
        html = (tmp_path / "docs" / document).read_text(encoding="utf-8")
        assert f"_images/{name}" in html or f'src="../_images/{name}' in html, (
            f"{document} does not show {name}.png from the built `_images/`. Either the "
            f"include did not resolve the path, or the figure became a link"
        )
        assert f"blob/main/assets/{name}" not in html, (
            f"{document} links {name}.png on GitHub instead of showing it. A figure that "
            f"is a link is a figure the reader does not see"
        )


def test_every_migrated_document_is_in_the_toctree(tmp_path):
    """All five documents are reachable, in two separate areas.

    The complaint this feature answers is that the project's documentation was
    split between the website and the repository for no reason a newcomer
    could see. A document that builds but hangs off no toctree is that split
    again, one level in: published, and reachable only by guessing its URL.

    The two areas are asserted separately because "all five are somewhere" is
    satisfied by a flat list, and a flat list is what puts a contributor's
    testing checklist next to a reader's first steps.
    """
    result = build(site=tmp_path)
    assert result.returncode == 0, f"the build failed:\n{result.stdout}\n{result.stderr}"

    found = reachable_documents(tmp_path)
    expected = {
        "user/workflow",
        "user/leitner",
        "contributing/design",
        "contributing/testing",
        "contributing/guide",
    }
    assert expected <= found, (
        f"these documents are not reachable from the root toctree: "
        f"{sorted(expected - found)}. The build found {sorted(found)}"
    )

    branches = toctree(tmp_path).get("index", [])
    assert "user/index" in branches and "contributing/index" in branches, (
        f"the root does not carry a user branch and a contributing branch as separate "
        f"top-level entries. It carries {branches}"
    )
