"""Resolves links that point at the repository rather than at a page.

The five migrated documents were written to be read on GitHub, so they link
`../templates/card.typ`, `../assets/fonts/` and `../README.md#install`. Sphinx
cannot resolve any of those to a document, and under `-W` each one is a build
failure.

The obvious repair — rewriting them to absolute URLs in the source — is wrong,
and quietly so. `scripts/check_docs.py` resolves every relative link against
the file system and skips anything starting with `http`, so rewriting would
hand each link to Sphinx and take it out of the dead-link gate at the same
time. The links would render and rot.

So the sources keep the paths they have and the resolution happens here, at
build time. Both checks stay honest: the gate resolves the path on disk, the
site resolves it for the web.

Two hooks, because two different things go wrong:

* a `SphinxPostTransform` at priority 5, ahead of MyST's own resolver at 9.
  The obvious `missing-reference` event never fires — MyST warns instead of
  emitting it — so this has to run before that resolver rather than after it.
* a `doctree-read` handler at priority 100, ahead of Sphinx's
  `DownloadFileCollector` at 500. A link from a page here to a file that
  exists on disk becomes a *download*: Sphinx copies the file under
  `_downloads/<hash>/` and marks the link `download`. For the method page that
  is a second copy at a second URL that the browser saves instead of opening.
  Rewriting the node before the collector sees it makes `_downloads/`
  disappear entirely.
"""

from pathlib import Path

from docutils import nodes
from sphinx import addnodes
from sphinx.transforms.post_transforms import SphinxPostTransform

REPO = "https://github.com/mhabedank/lernkarten"
ROOT = Path(__file__).resolve().parent.parent.parent

# A repository file that is also a page of this site: link the page, not GitHub.
PAGES = {
    "docs/workflow.md": "user/workflow",
    "docs/design.md": "contributing/design",
    "docs/testing.md": "contributing/testing",
    "CONTRIBUTING.md": "contributing/guide",
}

# A repository file the site serves at its root, beside the documentation tree.
# The value is relative to the site root; the depth prefix is added per page.
SERVED = {
    "docs/index.html": "index.html",
    "docs/leitner.html": "leitner.html",
    "assets/card-box.pdf": "card-box.pdf",
}


def split_anchor(target):
    """`a/b.md#section` -> `("a/b.md", "#section")`."""
    path, _, anchor = target.partition("#")
    return path, f"#{anchor}" if anchor else ""


def repo_path(source, target):
    """`target` as a repository-relative path, resolved from the file it was written in.

    From the *source* file, never the including page. A migrated document is
    pulled in with `{include}`, and its links are relative to where it lives
    on disk — `docs/design.md` writes `../CONTRIBUTING.md` while
    `CONTRIBUTING.md` writes `docs/design.md`, and resolving either against
    the page that included it gets both wrong.
    """
    if not source:
        return None
    try:
        resolved = (Path(source).parent / target).resolve()
        return resolved.relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return None


def site_root_prefix(docname):
    """`../` repeated far enough to climb out of the documentation tree.

    The site publishes the documentation under `/docs/`, so a page at
    `contributing/design` is two levels below the site root. Computed from the
    document's own depth rather than hard-coded, so a third level costs
    nothing (C2).
    """
    return "../" * (docname.count("/") + 1)


def resolve(name, anchor, docname):
    """The resolution order of contracts/docsite-layout.md § 6.

    Returns a URI, or None to leave the node alone so MyST warns and the build
    fails — a link to something that genuinely does not exist stays an error.
    """
    if name in PAGES:
        return None  # handled by the caller, which builds a real cross-reference
    if name in SERVED:
        return site_root_prefix(docname) + SERVED[name] + anchor
    absolute = ROOT / name
    if absolute.is_dir():
        return f"{REPO}/tree/main/{name}{anchor}"
    if absolute.is_file():
        return f"{REPO}/blob/main/{name}{anchor}"
    return None


class RepositoryLinks(SphinxPostTransform):
    """Rewrites unresolved MyST references that point into the repository."""

    default_priority = 5  # ahead of MystReferenceResolver at 9

    def run(self, **kwargs):
        for node in list(self.document.findall(addnodes.pending_xref)):
            if node.get("reftype") not in ("myst", "doc"):
                continue
            target = node.get("reftarget", "")
            if target.startswith(("http://", "https://", "//", "mailto:")):
                continue

            path, anchor = split_anchor(target)
            name = repo_path(node.source, path)

            # MyST strips a `.md` suffix before handing the target over, so a
            # link to a repository Markdown file arrives as `docs/design`,
            # which matches no file and no page. Putting the suffix back is
            # what makes the spelling the gate requires — the extension has to
            # be in the source, or `check_links` cannot resolve it — the same
            # spelling the site renders. Measured, not assumed: the node
            # carries `reftype="myst"` and an already-absolute, already-stripped
            # target.
            if name is not None and name not in PAGES and not (ROOT / name).exists():
                name = f"{name}.md" if (ROOT / f"{name}.md").exists() else name

            if name is None:
                continue

            if name in PAGES:
                self.link_to_page(node, PAGES[name], anchor)
                continue

            uri = resolve(name, anchor, self.env.docname)
            if uri is not None:
                self.replace_with_uri(node, uri)

    def link_to_page(self, node, docname, anchor):
        """An internal link to another page of this site, anchor preserved."""
        uri = self.app.builder.get_relative_uri(self.env.docname, docname) + anchor
        self.replace_with_uri(node, uri)

    def replace_with_uri(self, node, uri):
        reference = nodes.reference("", "", internal=False, refuri=uri)
        reference.extend(node.children or [nodes.Text(uri)])
        node.replace_self(reference)


def rewrite_downloads(app, doctree):
    """Turns a `download_reference` back into an ordinary link.

    Runs before Sphinx's `DownloadFileCollector`, which is connected to the
    same event at the default priority of 500. By the time that collector sees
    a node it has already decided to copy the file; rewriting first means the
    copy never happens and no `_downloads/` directory appears at all.

    The asymmetry that makes this necessary is worth naming, because 014 will
    meet it: a link written in a page *here* to a file that exists on disk
    becomes a download, while the same link inside an `{include}`d document
    does not, because MyST resolves that one against the including page where
    it does not exist. Nothing warns either way.
    """
    docname = app.env.docname
    for node in list(doctree.findall(addnodes.download_reference)):
        path, anchor = split_anchor(node.get("reftarget", ""))
        name = repo_path(node.source, path)
        if name is None:
            continue
        uri = resolve(name, anchor, docname)
        if uri is None:
            continue
        reference = nodes.reference("", "", internal=False, refuri=uri)
        reference.extend(node.children or [nodes.Text(uri)])
        node.replace_self(reference)


def setup(app):
    app.add_post_transform(RepositoryLinks)
    app.connect("doctree-read", rewrite_downloads, priority=100)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
