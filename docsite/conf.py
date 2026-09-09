"""Sphinx configuration for the documentation site.

Written by hand rather than generated. `sphinx-quickstart`'s output does not
pass `ruff check` at this repository's settings — no `exclude` is declared in
`pyproject.toml`, so this file is inside the first pre-PR gate from its first
commit.

Built by `python3 scripts/build_docs.py`, which publishes the result at
`/docs/` beside the hand-written landing page at the site root.
"""

import sys
from pathlib import Path

# Relative to this file, so a copied tree builds unchanged — which is what
# lets a test build a throwaway copy instead of writing into the working tree.
sys.path.insert(0, str(Path(__file__).parent / "_ext"))

project = "lernkarten"
author = "Martin Habedank"
copyright = "2026, Martin Habedank"

extensions = ["myst_parser", "repolinks"]

# The pages are Markdown, and the five migrated documents stay Markdown — they
# are pulled in with `{include}` rather than converted, so `docs/workflow.md`
# remains the file a contributor edits and the file check_docs.py gates.
source_suffix = {".md": "markdown"}

# Depth 3, which is exactly what the cross-document anchors need:
# docs/testing.md links `design.md#the-box` and
# `workflow.md#when-something-goes-wrong`. Without this MyST generates no
# anchor for either and both links become build failures under -W.
myst_heading_anchors = 3

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

# Deliberately NOT set: `html_baseurl`.
#
# The site is published under a sub-path (`/docs/`) and must also work when the
# build output is opened straight off the filesystem, so every internal link
# has to stay document-relative. Sphinx's HTML builder does that by default —
# which means this requirement is satisfied by the *absence* of a line, and
# would be silently lost by an innocent-looking addition. A sitemap, an Open
# Graph tag or a canonical URL all want `html_baseurl`; if one of them is ever
# needed, check what it does to the emitted hrefs first.

exclude_patterns = ["_build", "_ext", "Thumbs.db", ".DS_Store"]
