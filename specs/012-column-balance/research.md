# Phase 0 Research: The landing page's two-column sections carry their weight

**Feature**: 012-column-balance | **Date**: 2026-09-08

The usual first question — *is there a library for this?* — does not arise. This
feature moves three blocks in one static HTML file and writes one rule. No
dependency is added, removed or considered, so constitution II, III and IV are
answered by "no dependency change" and the rest of this document is about the
page.

---

## R1 — How does a block leave a column and become full width?

**Decision**: copy US2 of feature 002 exactly. A block that leaves a column
becomes a **sibling of the container it left**, with a top rule and no side
rules.

**Rationale**: the pattern is already in the file and already tested. The three
`band__note` paragraphs were children of their `.band`, inflating the heading
row; US2 made each one an immediate next sibling of its band, full width, with
`border-bottom: var(--rule)` and no `border-left`. Assertions A4, A5 and A6
guard that shape today (`test_no_band_note_is_a_child_of_its_band`,
`test_every_band_note_follows_its_band`, `test_the_band_note_carries_no_left_border`).

`.print__box` is the same shape of problem — a self-contained block sitting in a
column it does not belong to — so it gets the same shape of answer, and its
assertion can be written in the idiom of A4.

**The rule direction flips.** A `band__note` follows its band and takes a
`border-bottom`; `.print__box` follows the two columns and takes a
`border-top`, which it already declares. `#print` carries
`border-bottom: var(--rule)` inline, so the box needs no bottom rule of its own
— one added would double it. This is FR-006 and it is the detail most likely to
be got wrong.

**Alternatives considered**:

- *Leave the box in the column and shorten its copy.* Rejected: it is the same
  "shorten the text until the layout works" move FR-008 of feature 002 rejected
  for the bands. The imbalance would return with the next paragraph.
- *Make `.print__rules` scroll.* Rejected out of hand — feature 002 removed the
  page's only scrolling container because it hid content, and A1 forbids it
  returning to the nav. Reintroducing the idea elsewhere would be perverse.

---

## R2 — Where does the cutting diagram go, and what does it cost?

**Decision**: `.print__cut` becomes the third child of `.print__sheets`, which
is already `display: flex; flex-wrap: wrap; gap: 32px`. The two sheet mock-ups
take the first row; the diagram wraps onto the second.

**Rationale**: it is a drawing of a sheet with cut lines on it. It belongs with
the two drawings of sheets, not stranded beneath 400 px of prose about printer
settings. Measured, this is also what closes the gap: the sheets column goes
from 327 px of content in 1176 px to 547 px in 627 px.

**What has to change with it**: `.print__cut` currently declares
`flex: 1; justify-content: center` — both written for its old life as the
filler at the bottom of a text column, and both wrong inside a wrapping row of
pictures. Its 24 px / 28 px padding also duplicates the 40 px the sheets column
already applies. These are edits to the rule, not new rules.

**Alternatives considered**:

- *Move the diagram out full-width too, beside the box.* Measured: leaves the
  sheets column at 433 px against 327 px of content, 24 % dead. Better than
  today, worse than this, and it separates the diagram from rule 3, which is the
  text that introduces it.
- *Centre the sheets vertically and leave everything else.* Measured: 765 px
  column, 327 px content, dead space merely redistributed to 219 px above and
  219 px below. It converts a hole into two margins without adding anything to
  look at. Rejected as cosmetic.

---

## R3 — What can be asserted, given the module never renders the page?

**Decision**: assert the **structure that produces the proportion**, in four
places, and say in the test why structure is the level.

| Assertion | What it pins |
|---|---|
| `.print__box` is not a descendant of `.print__rules` | US2's move, R1 |
| `.print__cut` is a descendant of `.print__sheets` | R2 |
| No element inside `.anatomy__cards` carries `hidden`, and the page declares no `.toggle` | both cards visible, FR-001/FR-002 |
| The page holds **at most one** `<script>` and the same single external sub-resource | FR-011 |

**Rationale**: `tests/test_landing_page.py` opens with the reason — *"It reads
the file; it never renders it. So it can assert that a selector exists … and it
can assert none of the geometry those things produce."* A proportion is
geometry. What is assertable is the arrangement that causes it, which is the
same trade FR-008 of feature 002 made for the bands: it did not assert a heading
row's height, it asserted that no note is a child of a band.

CI has no browser leg, and feature 002's T039 records the decision that it will
not grow one for this page. An assertion needing a browser would be a gate that
never runs.

**Alternatives considered**:

- *Add a headless browser to CI and assert the pixels.* Rejected. It is the only
  way to check the proportion directly, and it costs a browser download on every
  leg of a six-job matrix to defend one static page. The by-hand row plus the
  structural assertions cover it at a fraction of the cost. Recorded here so the
  next person does not have to re-reason it.
- *Assert a character count on the columns' text.* Rejected: a proxy that
  correlates with the problem without measuring it, and one that would fire on
  an innocent copy edit while missing a 300 px image.

---

## R4 — What does the design rule say, and where does it live?

**Decision**: a new subsection in `docs/design.md` § *The screen surfaces*,
with a bullet in constitution XVI pointing at it — the same shape the 15 px type
floor has, where the rule lives in `design.md` and XVI carries a one-line
statement of it.

**The rule, in substance**: a two-column section is proportioned by its heavier
column, so a new block joins the column whose *kind* it is — pictures with
pictures, prose with prose. A block that belongs to neither kind, or that would
make one column outgrow the other by more than about half, becomes a full-width
block beneath both, the way the section notes did.

**Rationale**: the gap this feature exists to close is not that two sections are
lopsided; it is that **nothing in the repository has an opinion about
proportion**. Every landing-page gate checks type size, structure, rules or
copy. Three features in a row added correct, well-scoped content to one column
and no one was told. A rule a contributor reads before adding a block is the
only thing that reaches the case the assertions cannot: a block that is *added*
rather than moved.

**Why "about half" and not a number**: the assertions are structural, so a
numeric threshold could not be enforced anyway, and a false precision in
`design.md` invites arguing about the number instead of looking at the page. The
rule names the direction and the remedy; the by-hand row does the looking.

---

## R5 — What else does the toggle take with it?

**Decision**: three CSS rules go with the button, and the file already says so.

The `@media (max-width: 1080px)` block carries this comment:

> *The toggle goes full width, so the band has to wrap in the same breath — a
> 100 % item in a non-wrapping row just pushes the page sideways. **Only section
> 02 still has a child that needs this; the notes left the band.***

The toggle **is** that child. With it gone, `.band { flex-wrap: wrap }` and
`.band h2 { flex-basis: calc(100% - 72px) }` have nothing left to serve, and
`.toggle` has no element — both its base rule and its 1080 px override.

**Rationale**: this is not opportunistic tidying. The previous feature wrote
down the condition under which these rules become dead, and this feature meets
it. Leaving them is leaving a trap: the next reader sees `.band { flex-wrap:
wrap }` and reasonably concludes bands are expected to wrap.

**What does *not* go**: the `[hidden]` reset (FR-012). It was added against a
class of bug — an author `display` outranking the user-agent rule — not against
the toggle, and the comment at `docs/index.html:44` records the reasoning.
Deleting it with its one caller would re-arm the class silently, and
`test_the_hidden_attribute_outranks_any_display_a_class_sets` would go red for
the wrong reason.

**Alternatives considered**: keeping `.toggle` in the stylesheet against a future
control. Rejected — dead CSS in a single self-contained file is exactly what the
A8 assertion's design rule exists to prevent, and reviving it later is two lines.

---

## R6 — Does anything below 1080 px break?

**Decision**: no, but two of the three moves have to be checked there, not
assumed.

- **`.print__box` full width** is a no-op below the breakpoint: `.print` already
  wraps and `.print__rules` already goes to `width: 100%`, so the box was
  full-width there already. Moving it up one level changes its order slightly —
  it now follows both columns rather than trailing the rules — which is the
  order FR-007 asks for anyway.
- **`.print__cut` in the sheets column** inherits `.print__sheets { min-width: 0;
  padding: 28px 20px }` from the 760 px block, which is what stops that column
  holding the page open at 320 px. The diagram's SVG is a fixed 200 × 150, well
  inside that.
- **Both cards in section 02** is the *existing* no-JS rendering, so it is
  already the layout the ≤1080 px and ≤760 px blocks were written against.
  `.anatomy__cards` is `flex-wrap: wrap`, so the second card wraps below the
  first on a narrow screen exactly as it does today with JavaScript off.

**Rationale for checking anyway**: FR-007 is the requirement most likely to be
satisfied by accident and then broken by the *next* change, and the narrow
widths are where feature 002's `.print__sheets { min-width: 0 }` had to be added
after the fact.
