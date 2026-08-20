"""Guards the structure of the landing page, `docs/index.html`.

Separate from `test_repo_hygiene.py` on purpose. That module guards what a
release must and must not ship — no user content, no committed binaries, and
what the versioned documentation says. Its landing-page checks ("still promises
five commands", and that the README points a reader at the live page) belong
there because they guard a release from shipping a stale promise or burying the
page entirely. The assertions here are about how the page is *built*, which is
a different question.

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
    "area",
    "base",
    "br",
    "circle",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "path",
    "polygon",
    "rect",
    "source",
    "track",
    "wbr",
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

    Every rule the page defines lives here. It does link one external stylesheet
    — the Google Fonts one, which delivers faces and no rules — and A8 is what
    keeps that list from growing.
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


def next_element_sibling(node):
    """The element that follows this one under the same parent, or None."""
    siblings = node.parent.children
    index = siblings.index(node)
    return siblings[index + 1] if index + 1 < len(siblings) else None


# ---------------------------------------------------------------------------
# US2 — the band note stops inflating the section heading (issue #29)
#
# `.band` is a flex row with align-items: stretch, so its tallest child sets the
# row height. All three notes are taller than their heading — by 52, 29 and 7 px
# — so the defect is the coupling, not the length of any one note. Moving the
# note out is what removes the coupling; shortening copy would only move the
# threshold. None of those heights is reachable from here, so what follows
# asserts the structure that makes them impossible, and the manual checklist
# carries the geometry.
# ---------------------------------------------------------------------------


def test_no_band_note_is_a_child_of_its_band():
    """A4 — nothing but the number and the heading sizes the heading row."""
    trapped = [note for note in find(tree(), "p", "band__note") if note.parent.has_class("band")]
    assert not trapped, (
        f"{len(trapped)} note(s) still sit inside a .band, where a long one stretches "
        "the heading row it shares"
    )


def test_every_band_note_follows_its_band():
    """A5 — the reading order stays number, heading, note, content."""
    notes = find(tree(), "p", "band__note")
    assert len(notes) == 3, (
        f"expected three band notes (pipeline, printing, install), found {len(notes)}"
    )
    for note in notes:
        previous = [
            sibling
            for sibling in note.parent.children
            if sibling.tag == "div" and sibling.has_class("band")
        ]
        assert previous, f"{note!r} has no .band sibling to follow"
        assert next_element_sibling(previous[0]) is note, (
            "a note must come directly after its band — anything between them "
            "reorders what the reader meets"
        )


def test_the_band_note_carries_no_left_border():
    """A6 — the note is a block under the band, not a column beside it.

    Matched as a substring, deliberately: `.install .band__note` carries
    `border-left-color`, and an exact property match would walk past it and leave
    the inverted install band half-converted.
    """
    stale = [body for body in rules_for(".band__note") if "border-left" in body]
    assert not stale, f"the note still carries a left border: {stale}"

    inside_1080 = rules_for(".band__note", css=media_block("1080px"))
    assert not inside_1080, (
        "the 1080px block still restyles the note's borders; those rules existed "
        f"only to fake the block layout on narrow screens: {inside_1080}"
    )


# ---------------------------------------------------------------------------
# US3 — the hidden attribute takes effect (issue #28)
#
# The script that turns the card over is correct and does run; the changing
# button label proves it. `.card` declares display: flex, which ties with
# [hidden] at specificity (0,1,0) and wins on source order, so the user-agent
# rule never applies and both cards stay on screen. !important is the fix rather
# than a smell here: `hidden` states that an element is not relevant, which is
# not a style preference to be outranked.
# ---------------------------------------------------------------------------


def test_the_hidden_attribute_outranks_any_display_a_class_sets():
    """A7 — one rule, so the next element given `hidden` cannot fail the same way."""
    rules = rules_for("[hidden]")
    assert rules, (
        "the page has no [hidden] rule at all, so the browser default is left to "
        "lose to any class that declares display — which .card does"
    )
    # Matched on the property, not the substring: `var(--display)` is the font
    # custom property and appears in half the rules on this page.
    effective = [body for body in rules if re.search(r"\bdisplay\s*:\s*none\s*!important", body)]
    assert effective, (
        "a [hidden] rule without !important is a no-op here: [hidden] and .card "
        f"both weigh (0,1,0) and .card is declared later, so it wins. Found: {rules}"
    )


# ---------------------------------------------------------------------------
# Cross-cutting — the page stays what docs/design.md says it is
# ---------------------------------------------------------------------------

# What the page loads from elsewhere today. FR-014 forbids *new* entries, not
# these: the fonts are how the three faces reach a reader, and dropping them is
# a separate decision. The canonical link and og:image are metadata rather than
# sub-resources, and the icon is a data: URI, so none of the three appear here.
EXTERNAL_SUBRESOURCES = {"https://fonts.googleapis.com/css2"}


# ---------------------------------------------------------------------------
# BUG-006 — reading text keeps the 15 px floor (issue #30)
#
# A9 is the one assertion in this module that is not half of a pair. A font size
# is a declaration in the stylesheet, not a rendered dimension, so the assertion
# reaches the whole requirement and no manual row stands behind it.
#
# The exemption is stated as a rule rather than as a list of selectors, and that
# is the point: `docs/design.md` gives Jost labels and IBM Plex Mono literals
# their own rows, and its floor sentence says *reading text*. So a small size is
# allowed exactly where the rule that sets it also names one of those faces. A
# list of selector names would go stale and would become somewhere to put the
# next violation; this cannot, because adding a rule that sets 13 px of Archivo
# fails it whatever the selector is called.
# ---------------------------------------------------------------------------

SCREEN_FLOOR = 15  # px — docs/design.md, constitution XVI
FONT_SIZE_PX = re.compile(r"font-size:\s*([\d.]+)px")
OTHER_FACE = re.compile(r"font-family:\s*var\(--(display|mono)\)")
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def test_reading_text_is_never_below_the_screen_floor():
    """A9 — no Archivo running prose under 15 px, in the stylesheet or inline.

    Red on six declarations before the fix: `.band__note` (14), `.anatomy__item p`
    (14), `.rule-item p` (13.5), `.print__cut p` (13), `.principle p` (14.5) and
    an inline `style` on the "One file per topic" paragraph (14). Issue #30 named
    four of the six; the other two were found by asking the question of the whole
    stylesheet instead of of a list.
    """
    offenders = []
    for selector, body in _innermost_rules(stylesheet()):
        if OTHER_FACE.search(body):
            continue  # a Jost label or a Plex Mono literal — not reading text
        for size in FONT_SIZE_PX.findall(body):
            if float(size) < SCREEN_FLOOR:
                offenders.append(f"{CSS_COMMENT.sub('', selector).strip()} -> {size}px")

    for style in re.findall(r'style="([^"]*)"', page_source()):
        for size in FONT_SIZE_PX.findall(style.replace(" ", "").replace(":", ": ")):
            if float(size) < SCREEN_FLOOR:
                offenders.append(f"inline style -> {size}px")

    assert not offenders, (
        "reading text below the 15 px screen floor that docs/design.md and "
        f"constitution XVI state: {offenders}"
    )


def test_the_page_stays_one_self_contained_file():
    """A8 — a regression guard, green from the start.

    Unlike the seven assertions above this one was never red, and it could not
    be without breaking the page on purpose. It is here because "one
    self-contained file with almost no script" is a design rule
    (`docs/design.md`, *The screen surfaces*) that no other check defends.
    """
    source = page_source()

    scripts = re.findall(r"<script\b[^>]*>", source)
    assert len(scripts) == 1, (
        f"expected exactly one <script> block, found {len(scripts)}: {scripts}"
    )
    assert "src=" not in scripts[0], f"the script must stay inline: {scripts[0]}"

    loaded = {
        url.split("?")[0]
        for url in re.findall(r'<link[^>]+rel="stylesheet"[^>]*href="([^"]+)"', source)
        + re.findall(r'<link[^>]+href="([^"]+)"[^>]*rel="stylesheet"', source)
        + re.findall(r'<img[^>]+src="([^"]+)"', source)
        if url.startswith("http")
    }
    assert loaded == EXTERNAL_SUBRESOURCES, (
        f"the page's external sub-resources changed: {loaded ^ EXTERNAL_SUBRESOURCES}"
    )
