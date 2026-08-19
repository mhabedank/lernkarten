"""Guards the structure of the landing page, `docs/index.html`.

Separate from `test_repo_hygiene.py` on purpose. That module guards what the
repository must not contain — user content, committed binaries — and its one
landing-page check ("still promises five commands") belongs there because it
guards a release from shipping a stale promise. The assertions here are about
how the page is *built*, which is a different question.

What this module can and cannot reach is the shape of everything below. It reads
the file; it never renders it. So it can assert that a selector exists, that an
element is or is not a child of another, that a media query declares something —
and it can assert none of the geometry those things produce. A heading row that
is 126 px tall when it should be 74 px is invisible from here.

That is why every requirement this module covers is half of a pair. The other
half is a numbered row on the manual checklist in `docs/testing.md`, which is
what constitution XI asks for when the assertable part of a layout change cannot
carry the whole requirement.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "index.html"

# Elements that never have a closing tag. The page carries SVG, where most
# shapes arrive self-closing and reach us through handle_startendtag instead,
# but `path` and friends are listed anyway: a hand-written `<path>` without the
# slash would otherwise swallow the rest of the document into its subtree.
VOID = {
    "area", "base", "br", "circle", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "path", "polygon", "rect", "source", "track", "wbr",
}


class Node:
    """One element, with the parent link that makes the containment questions answerable."""

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []
        self.text = ""

    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    def has_class(self, name):
        return name in self.classes

    def descendants(self):
        for child in self.children:
            yield child
            yield from child.descendants()

    def __repr__(self):
        cls = " ".join(sorted(self.classes))
        return f"<{self.tag}{' class=' + cls if cls else ''}>"


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", [], None)
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self._stack[-1])
        self._stack[-1].children.append(node)
        if tag not in VOID:
            self._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, attrs, self._stack[-1])
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data):
        self._stack[-1].text += data


def page_source():
    """The landing page, verbatim."""
    return PAGE.read_text(encoding="utf-8")


def tree():
    """The page as a node tree — for questions about containment and order."""
    parser = _Tree()
    parser.feed(page_source())
    return parser.root


def find(root, tag=None, cls=None):
    """Every descendant matching a tag, a class, or both."""
    return [
        node
        for node in root.descendants()
        if (tag is None or node.tag == tag) and (cls is None or node.has_class(cls))
    ]


def one(root, tag=None, cls=None):
    """The single matching descendant. Raises if there is not exactly one."""
    found = find(root, tag=tag, cls=cls)
    assert len(found) == 1, f"expected exactly one {tag or ''}.{cls or ''}, found {len(found)}"
    return found[0]


def stylesheet():
    """The contents of every <style> block, concatenated.

    The page has no external stylesheet — A8 is what keeps that true — so this is
    the whole of the CSS.
    """
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", page_source(), re.S))


def _innermost_rules(css):
    """(selector, body) for every rule with no nested braces.

    An @media wrapper never matches: its body contains braces, so only the rules
    inside it do. That is exactly what is wanted — a selector is found whether or
    not it sits in a media query, and `media_block()` narrows when it matters.
    """
    return [
        (selector.strip(), body.strip())
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
    ]


def rules_for(fragment, css=None):
    """The bodies of every rule whose selector mentions `fragment`."""
    return [
        body
        for selector, body in _innermost_rules(stylesheet() if css is None else css)
        if fragment in selector
    ]


def media_block(query):
    """The text inside the @media block whose header mentions `query`.

    Brace-matched rather than regexed, because the block contains nested rules.
    """
    css = stylesheet()
    start = css.find("@media")
    while start != -1:
        header_end = css.index("{", start)
        if query in css[start:header_end]:
            depth, index = 0, header_end
            while index < len(css):
                if css[index] == "{":
                    depth += 1
                elif css[index] == "}":
                    depth -= 1
                    if depth == 0:
                        return css[header_end + 1 : index]
                index += 1
        start = css.find("@media", start + 1)
    raise AssertionError(f"no @media block matching {query!r}")


def ancestors(node):
    """Every ancestor of a node, innermost first."""
    chain, current = [], node.parent
    while current is not None:
        chain.append(current)
        current = current.parent
    return chain


NAV_LINKS = ("#how", "#cards", "#print", "#install")


# ---------------------------------------------------------------------------
# US1 — the navigation is reachable on a phone (issue #27)
#
# A1 is symptom-shaped: it asserts the overflow container is gone, which is the
# defect the reader met. A2 and A3 are not — they assert the shape of the chosen
# fix, because "the links are discoverable" cannot be reached without rendering
# the page. They are proxies, and a different but equally good navigation would
# fail them. The manual checklist carries the claim they stand in for.
# ---------------------------------------------------------------------------


def test_nav_links_are_not_an_overflow_container():
    """A1 — no sideways scroll hides a link the reader is given no hint about."""
    offenders = [body for body in rules_for(".nav__links") if "overflow-x" in body]
    assert not offenders, (
        "the nav link row still scrolls sideways, and its scrollbar is suppressed, "
        f"so a link can exist that nobody can see: {offenders}"
    )


def test_nav_offers_a_disclosure_control_that_says_what_it_is():
    """A2 — the control carries a word, not only a glyph (constitution XVI)."""
    nav = one(tree(), "nav")
    menus = find(nav, "details")
    assert len(menus) == 1, f"expected exactly one <details> in the nav, found {len(menus)}"
    summaries = find(menus[0], "summary")
    assert len(summaries) == 1, f"expected exactly one <summary>, found {len(summaries)}"
    assert summaries[0].text.strip(), (
        "the disclosure control has no text: an icon alone makes the meaning depend "
        "on a visual, which docs/design.md forbids"
    )


def test_the_four_nav_links_sit_inside_the_disclosure_and_the_rest_does_not():
    """A3 — the links move into the panel; the wordmark and github stay in the bar."""
    nav = one(tree(), "nav")
    menu = one(nav, "details")
    inside = {
        anchor.attrs.get("href")
        for anchor in find(menu, "a")
        if anchor.attrs.get("href") in NAV_LINKS
    }
    assert inside == set(NAV_LINKS), f"these links are not in the panel: {set(NAV_LINKS) - inside}"

    # FR-004: the bar stays one line, which it cannot if these move in with them.
    for cls in ("nav__home", "nav__gh"):
        element = one(nav, cls=cls)
        assert menu not in ancestors(element), f".{cls} must stay in the bar, not in the panel"
