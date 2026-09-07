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


def test_the_desktop_bar_carries_its_height_down_to_the_link_row():
    """A10 — the stretch chain `.nav` → `.nav__links` survives the `<details>` wrapper.

    `.nav` is `align-items: stretch`, and before the disclosure existed
    `.nav__links` was a direct flex child carrying `flex: 1`. That is where the
    vertical centring came from: a full-height box for `align-items: center` to
    centre in. Wrapping the row in `<details class="nav__menu">` moved `flex: 1`
    to the wrapper, and a `<details>` is a block container — so the stretched
    height stopped there and the links fell to the top of the bar (BUG-011).

    This asserts the chain, not a pixel. The module never renders the page, and
    FR-018 forbids the alternative anyway: a height or a padding on `.nav__links`
    re-breaks the moment the bar's own height changes. Each link in the chain has
    to be a flex container for the stretch to reach the row.
    """

    # Exact selectors, not `rules_for`'s substring match: a rule for something
    # *inside* `.nav__menu` would satisfy a fragment search while leaving the
    # wrapper itself a block, which is the defect rather than the fix.
    def exact(css):
        # Comments first: `_innermost_rules` does not know about them, so a rule
        # with an explanation above it arrives with the whole comment glued to
        # the front of its selector and matches nothing.
        css = CSS_COMMENT.sub("", css)
        return {selector.strip(): body.replace(" ", "") for selector, body in _innermost_rules(css)}

    # `display: flex` only. `flex: 1` is a flex *item* property — it says how the
    # box behaves in its own parent, nothing about what it does to its children,
    # and accepting it here would pass the exact defect BUG-011 is.
    def is_flex_container(body):
        return "display:flex" in body or "display:inline-flex" in body

    # `.nav__menu` is checked outside any media query, because the wrapper holds
    # two things that both need the bar's height: the link row above the
    # breakpoint, and the `menu` control below it. Scoping this to the desktop
    # block is what left the control hanging from the ceiling on a phone.
    unscoped = exact(re.sub(r"@media[^{]*\{.*?\n  \}", "", stylesheet(), flags=re.S))
    assert is_flex_container(unscoped.get(".nav__menu", "")), (
        ".nav__menu is not a flex container at every width, so the bar's height "
        "stops at the wrapper. Above the breakpoint that drops the link row to the "
        "top edge; below it, the `menu` control (FR-005, FR-018). "
        f"Rule found: {unscoped.get('.nav__menu', '')!r}"
    )

    desktop = exact(media_block("min-width: 761px"))
    assert is_flex_container(desktop.get(".nav__menu::details-content", "")), (
        "::details-content is not a flex container above the breakpoint, so the "
        "height stops one box short of the link row and the links hang from the top "
        "edge instead of sitting on the bar's centre line (FR-005, FR-018). "
        f"Rule found: {desktop.get('.nav__menu::details-content', '')!r}"
    )

    # FR-018: the chain, never a hard-coded size on the row itself.
    banned = ("height", "padding-block", "padding-top", "line-height")
    for body in rules_for(".nav__links"):
        for declaration in banned:
            assert f"{declaration}:" not in body.replace(" ", ""), (
                f".nav__links declares {declaration}, which fakes the centring at one "
                "bar height and breaks at the next. Carry the stretch through the "
                f"wrapper instead (FR-018). Rule: {body}"
            )


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
# Feature 012 — the two-column sections carry their weight.
#
# These four assert *arrangement*, never proportion. A column that is half empty
# is geometry, and this module never lays the page out. What it can reach is the
# arrangement that causes the proportion — the same trade FR-008 of feature 002
# made for the bands, where the fix was not asserting a heading row's height but
# asserting that no note is a child of a band.
# ---------------------------------------------------------------------------


def test_both_card_faces_stand_and_no_control_hides_one():
    """A11 — section 02 shows the card it is talking about (FR-001, FR-002).

    Asserts absence twice, and the two halves are not the same kind of claim:

    - **The toggle half is red today** and is what this feature turns green.
    - **The `hidden` half is green today** and is a regression guard, like A8.
      It cannot be red, because no card carries `hidden` in the *markup* — the
      deleted script applied it at runtime, and this module never runs one. What
      it guards is the next contributor writing the attribute into the source by
      hand.

    Saying which is which matters: a suite where every assertion is presented as
    red evidence, and one of them never could be, is a suite that has stopped
    meaning what constitution XI asks it to mean.

    The two halves are still written together because either alone passes a
    half-done removal: delete the button while something still sets `hidden` and
    one card is gone with no way back; delete the script while the button stays
    and the page carries a dead control. The runtime route is closed by A14,
    which drops the script count to zero — with no script on the page, `hidden`
    can only arrive the way this assertion checks.
    """
    cards = one(tree(), cls="anatomy__cards")
    hidden = [
        node.tag for node in find(cards) if "hidden" in node.attrs
    ]
    assert not hidden, (
        f"these elements in the card column carry `hidden`: {hidden}. Both faces "
        "have to stand — the explanations beside them name parts that differ "
        "between front and back"
    )

    toggles = find(tree(), cls="toggle")
    assert not toggles, (
        f"the page still declares {len(toggles)} toggle control(s). The button and "
        "the script that drove it go together; one without the other is either a "
        "dead control or a hidden card"
    )


def test_the_card_box_is_not_buried_in_the_printing_rules():
    """A12 — the box leaves the column it did not belong to (FR-003).

    Written in the idiom of `test_no_band_note_is_a_child_of_its_band` and
    `test_every_band_note_follows_its_band`, because it is the same move: a
    self-contained block sitting inside a container it out-measures, lifted to a
    full-width sibling. US2 of feature 002 did it for the section notes; this
    does it for the card box, which had grown to 410 px inside a 420 px column.
    """
    columns = one(tree(), cls="print")  # the two-column flex row
    rules = one(columns, cls="print__rules")
    boxes = find(tree(), cls="print__box")
    assert boxes, "the printing section no longer has a card box block at all"
    for box in boxes:
        assert rules not in ancestors(box), (
            "the card box is still inside .print__rules. It is a different subject "
            "from the three printing rules — what you keep the cards in, not how "
            "you print them — and it is what tipped that column to 3.6x the one "
            "beside it"
        )

    assert next_element_sibling(columns) is boxes[0], (
        "the card box must follow .print as its next sibling, so it spans the "
        "full width beneath both columns rather than trailing one of them"
    )


def test_the_cutting_diagram_sits_with_the_sheets_it_draws():
    """A13 — pictures with pictures (FR-004).

    The diagram is a drawing of a sheet with cut lines on it. It belongs beside
    the two drawings of sheets, not stranded under 400 px of prose about printer
    settings — and moving it is what takes the sheets column from 327 px of
    content in a 1176 px column to 547 px in 627 px.
    """
    sheets = one(tree(), cls="print__sheets")
    cuts = find(tree(), cls="print__cut")
    assert cuts, "the cutting diagram is gone from the page entirely"
    for cut in cuts:
        assert sheets in ancestors(cut), (
            "the cutting diagram is not in the sheets column. It is the third "
            "picture in a section whose other two pictures are there"
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
    """A8, restated as A14 by feature 012 — a regression guard, green from the start.

    Unlike the seven assertions above this one was never red, and it could not
    be without breaking the page on purpose. It is here because "one
    self-contained file with almost no script" is a design rule
    (`docs/design.md`, *The screen surfaces*) that no other check defends.

    **It counted *exactly* one script until feature 012 removed the card
    toggle**, which was the only one. That count would have failed for the worst
    possible reason: a passing test going red because the code got better. It
    now reads *at most* one, which supersedes SC-007 and FR-014 of feature 002.

    Not "any number". Zero satisfies the design rule more completely than one
    did; two does not satisfy it at all, and a page that grows a second script
    has left the rule whether or not the first one was ever removed. The ceiling
    is the whole point of the assertion — dropping it to keep the test passing
    would throw away the guard along with the count.
    """
    source = page_source()

    scripts = re.findall(r"<script\b[^>]*>", source)
    assert len(scripts) <= 1, (
        f"expected at most one <script> block, found {len(scripts)}: {scripts}. "
        "The page is one self-contained file with almost no behaviour; a second "
        "script leaves that rule regardless of what the first one does"
    )
    assert all("src=" not in tag for tag in scripts), (
        f"any script must stay inline: {scripts}"
    )

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


# ---------------------------------------------------------------------------
# The card box download (feature 007).
#
# The site is *assembled*, not served from the repository: pages.yml copies
# docs/index.html into _site and nothing else. So a link to the box is only half
# the requirement — the other half lives in the workflow, and it is asserted as
# text because CI never executes it. A YAML error here merges green and surfaces
# as a failed deploy on main.
# ---------------------------------------------------------------------------

WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
BOX_PDF = "card-box.pdf"


def print_section():
    """The `print it, cut it` section — where a reader is told to cut."""
    source = page_source()
    match = re.search(r'<section id="print".*?</section>', source, re.DOTALL)
    assert match, 'docs/index.html has no <section id="print"> — this test\'s anchor moved'
    return match.group(0)


def test_the_landing_page_offers_the_box_beside_the_cutting():
    """The download belongs where the reader has just been told to cut."""
    assert f'href="{BOX_PDF}"' in print_section(), (
        f"the print section does not link {BOX_PDF} — the box is unreachable, which "
        "is the whole gap issue #45 opened"
    )


def test_the_pages_workflow_publishes_the_box():
    """`href="card-box.pdf"` is a 404 unless the workflow puts it there.

    The site is one assembled file. Without the copy the deployed link is
    broken, and nothing else in this suite would notice: opened from the
    filesystem the page is fine, and CI never runs the workflow.
    """
    workflow = WORKFLOW.read_text(encoding="utf-8")
    copied = re.search(r"^\s*cp\s+\S*assets/card-box\.pdf\s+\S*_site/", workflow, re.MULTILINE)
    assert copied, "pages.yml does not copy the box into _site — the download would 404"
    triggers = re.search(r"paths:\n(.*?)\n\s*\w+:", workflow, re.DOTALL)
    assert triggers and "assets/card-box.pdf" in triggers.group(1), (
        "pages.yml does not trigger on assets/card-box.pdf — replacing the box "
        "would never redeploy the site"
    )


def landing_page_relative_refs():
    """Every path the landing page points at inside its own site.

    Absolute URLs are somebody else's problem, and a bare `#anchor` never
    leaves the page. What is left is exactly the set that has to exist in
    `_site`, because a relative link resolves against the deployed site and
    nothing else.
    """
    refs = set(re.findall(r'(?:href|src)="([^"]+)"', page_source()))
    return sorted(
        ref
        for ref in refs
        if not ref.startswith(("http://", "https://", "//", "#", "mailto:", "data:"))
    )


def test_the_pages_workflow_assembles_every_relative_link():
    """A relative link to a path the workflow never copies is a live 404.

    `test_the_pages_workflow_publishes_the_box` asserts this for one file. It
    was written for the box and it only ever knew about the box, so when the
    method page arrived with `href="leitner.html"` nothing objected — the page
    is fine opened off the filesystem, the link is in the HTML, the suite is
    green, and the deployed link 404s. The workflow's own header comment warns
    about exactly this. This test closes it for good by deriving the list from
    the page instead of naming files: the next relative link anyone adds is
    covered the moment they add it.
    """
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for ref in landing_page_relative_refs():
        copied = re.search(rf"^\s*cp\s+\S*{re.escape(ref)}\s+\S*_site/", workflow, re.MULTILINE)
        assert copied, (
            f"docs/index.html links {ref!r}, but pages.yml never copies it into "
            f"_site — the deployed link is a 404 that looks fine locally"
        )


def box_block():
    """The download block itself, not the section around it.

    Scoping matters: the print section already says `a8` and `--margin 0` for
    unrelated reasons, so asserting against the whole section passes before the
    caption is written and proves nothing.
    """
    match = re.search(r'<div class="print__box">.*?</div>\s*</div>', print_section(), re.DOTALL)
    assert match, 'docs/index.html has no <div class="print__box"> holding the download'
    return match.group(0)


def prose():
    """The page as a reader meets it: tags stripped, attribute text kept.

    `aria-label` carries a claim too — the cutting diagram describes itself to a
    screen reader in words, and those words were as wrong as the picture.
    """
    text = page_source()
    labels = " ".join(re.findall(r'aria-label="([^"]*)"', text))
    return re.sub(r"<[^>]+>", " ", text) + " " + labels


def test_the_page_does_not_give_the_a7_sheet_as_what_you_get(tmp_path=None):
    """The landing page owns its own copy of this claim (FR-011, FR-012).

    `check_docs.py` gates markdown, `scripts/*.py` and `templates/*.typ`; it
    does not read HTML and should not become the second thing that parses this
    file. So the four sites BUG-010 found here are asserted where the rest of
    the page's claims already live.
    """
    text = prose()
    assert "105 × 74.25" not in text, (
        "the page still gives the A7 card as what a default build produces — "
        "at the default a8 grid, --margin 0 cuts to 74.25 × 52.5 mm"
    )
    assert "100 × 71.75" not in text, (
        "the page still gives the A7 card as the default-margin card — "
        "at the default a8 grid it is 71.75 × 50 mm"
    )
    assert "8 cards / A4 page" not in text, (
        "the hero band still opens with the A7 sheet capacity; the default is 16 up"
    )
    assert "full A7" not in text, (
        "the page still says borderless printing gives an A7 card; at the default grid it gives A8"
    )


def test_the_cutting_diagram_shows_the_default_sheet():
    """One vertical cut and three across is the 2x4 sheet, which is no longer it.

    The picture and the sentence beside it are one claim, and the SVG is the
    half a reader believes: three interior verticals and three horizontals at
    4x4, against one and three at 2x4.
    """
    text = prose()
    assert "one vertical cut down the middle" not in text.lower(), (
        "the page still describes the 2x4 cut; at the default a8 grid it is "
        "three vertical cuts and three horizontal"
    )
    cut_svg = one(one(tree(), cls="print__cut"), "svg")
    verticals = [n for n in find(cut_svg, "line") if n.attrs.get("x1") == n.attrs.get("x2")]
    assert len(verticals) == 3, (
        f"the cutting diagram draws {len(verticals)} interior vertical cuts; "
        "the default 4x4 sheet needs three"
    )


def test_the_box_download_says_which_deck_it_fits():
    """An A7 reader has to stop *before* spending an hour on a box.

    The sheet itself cannot say this — it has no source in this repository, and
    it prints `cards 70 x 49 mm`, a nominal that is not the real card. So the
    only place the constraint can live is beside the link.
    """
    block = box_block().lower()
    assert "a8" in block, (
        "the box download does not name the a8 grid — an A7 deck is 100 mm wide "
        "against a 73 mm opening, and a deck can still pin a7"
    )
    assert "margin" in block, (
        "the box download does not mention the margin — a deck printed at "
        "--margin 0 has 74.25 mm cards and does not fit either"
    )


# --- the method page (US4) --------------------------------------------------


def test_the_landing_page_points_at_the_method():
    """US4 scenario 1. `check_docs.check_links` reads markdown only, so an
    HTML-to-HTML link is invisible to it — this is where it gets checked."""
    assert 'href="leitner.html"' in page_source(), "the landing page does not link the method page"


def test_the_method_page_is_one_self_contained_file():
    """The rule docs/design.md states for every screen surface here."""
    page = (ROOT / "docs" / "leitner.html").read_text(encoding="utf-8")
    assert "<script" not in page, "the method page must carry no script at all"
    assert "http://" not in page, "no plain-http asset"
    for external in re.findall(r'<(?:link|img|script)\b[^>]*\bsrc="([^"]+)"', page):
        assert not external.startswith("http"), f"remote asset: {external}"


def test_every_link_on_the_method_page_resolves():
    """US4 scenario 1: 'every link in it resolves'."""
    page = (ROOT / "docs" / "leitner.html").read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"]+)"', page):
        if href.startswith(("http", "#", "mailto:")):
            continue
        target = (ROOT / "docs" / href).resolve()
        assert target.exists(), f"dead link on the method page: {href}"
