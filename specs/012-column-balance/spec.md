# Feature Specification: The landing page's two-column sections carry their weight

**Feature Branch**: `design/column-balance`

**Created**: 2026-09-08

**Status**: Draft

**Input**: GitHub issue [#104](https://github.com/mhabedank/lernkarten/issues/104),
split out of [BUG-011](../002-landing-page-fixes/bugs/BUG-011.md) S2 and S3. Revives
the undecided half of [#28](https://github.com/mhabedank/lernkarten/issues/28).

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: none of them. `docs/index.html` is a project
surface, not a pipeline step — it is the page a newcomer reads before running
anything. Nothing under `skills/`, `scripts/`, `bin/` or `templates/` changes,
and no artifact a user has on disk changes.

**Implementation half**:

- [ ] **Model-driven**
- [x] **Deterministic** — markup and CSS in `docs/index.html`, one assertion
      module in `tests/test_landing_page.py`, one rule in `docs/design.md`.
- [ ] **Both**

**Who runs into this**: both. A reader meets two sections with a hole in them;
a contributor meets a page where nothing stops the next feature reopening it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Section 02 shows the card it is talking about (Priority: P1)

A reader scrolls to `02 one card, one idea`. The right-hand column explains four
parts of a card — the header band, the field, the footer band, the note space.
The left-hand column shows **one** card and then 335 px of nothing.

The four explanations name things that appear on *both* sides of a card. The
header band differs front to back; the mark is hollow on one and solid on the
other; the note space only exists on the back. A reader looking at one side
cannot check three of the four claims against what they see.

Both cards come back — one above the other, which is how 269 px twice plus the
26 px gap comes to the 644 px the prose beside it sets — and the toggle goes. That is the no-JS
fallback the page already had, which the script's own comment calls "the same
information, one scroll longer" — and the measurement says it is not even longer:
two cards are what the column was proportioned around.

**Why this priority**: it is the section that teaches the format the whole
project is about, and it is the one whose gap was *introduced* by a fix rather
than accreted.

**Independent Test**: shipping this alone leaves a section whose picture matches
its prose. Structurally: assert that nothing in the card column carries `hidden`
on load and that the page declares no toggle control.

**Acceptance Scenarios**:

1. **Given** the page is opened with JavaScript enabled, **When** section 02 is
   reached, **Then** both the front and the back card are visible, and no
   control offers to turn one into the other.
2. **Given** the page is opened with JavaScript disabled, **When** section 02 is
   reached, **Then** it looks exactly as it does with JavaScript enabled.
3. **Given** the four `anatomy__item` explanations, **When** a reader checks any
   one against the cards beside it, **Then** the thing it names is on screen —
   including the three that differ front to back.

### User Story 2 - Section 03 puts the pictures with the pictures (Priority: P2)

A reader scrolls to `03 print it, cut it`. The right-hand column runs three
printing rules, then a cutting diagram, then the whole card-box block — 1174 px
of it. The left-hand column shows two sheet mock-ups, 327 px, and then 809 px of
empty ground.

Two moves fix it, and both improve the reading order rather than merely closing
a hole:

- The **cutting diagram** joins the sheets in the left column. It is a picture of
  a sheet; it belongs with the pictures of sheets, not stranded under the text.
- The **card box** leaves the rules column for a full-width block beneath both
  columns. It is a different subject — what you keep the cards in, not how you
  print them — and it is the same move US2 already made for the section notes.

**Why this priority**: the bigger hole (65 % against 46 %) but the less
important section, and it costs no decision — nothing is removed, only moved.

**Independent Test**: shipping this alone leaves a printing section with no hole
in it. Structurally: assert `.print__box` is not a descendant of `.print__rules`
and the cutting diagram is a descendant of the sheets column.

**Acceptance Scenarios**:

1. **Given** the printing section above 1080 px, **When** it is read top to
   bottom, **Then** the order is: the two sheets and the cutting diagram on the
   left, the three numbered rules on the right, the card box across the full
   width beneath both.
2. **Given** the card box block, **When** it is moved, **Then** its download
   link, its sizing caption and its Leitner paragraph move with it as one unit,
   and the relative `card-box.pdf` href is unchanged.
3. **Given** any viewport from 320 px up, **When** the section is narrowed,
   **Then** no column is left holding the page open and the reading order is
   unchanged.

### User Story 3 - The next feature cannot reopen the hole (Priority: P3)

A contributor adds a paragraph to the printing section, the way three features
did between v0.5 and v0.9. Nothing today measures one column against the other,
so the page silently tips again.

`docs/design.md` gains a rule about two-column sections, constitution XVI points
at it, and `tests/test_landing_page.py` asserts the *structure* that keeps the
proportion — not a rendered measurement, which it cannot see and CI cannot run.

**Why this priority**: it is what makes this a fix rather than a tidy-up, but it
protects work the first two stories have to do first.

**Independent Test**: revert either story's markup move and the new assertion
goes red.

**Acceptance Scenarios**:

1. **Given** the rule in `docs/design.md`, **When** a contributor reads it before
   changing the page, **Then** it tells them which column a new block joins and
   what to do when one side outgrows the other.
2. **Given** a change that puts the card box back inside the rules column,
   **When** the suite runs, **Then** it fails and names the section.

### Edge Cases

Most of the recurring list does not apply — this feature touches no pipeline
step, no card, no dependency and no engine. What does apply:

- **Fresh install on each platform**: not affected. The page is one static file
  with no build step; the assertions are pure Python over its text.
- **Below the 1080 px breakpoint**, both sections already collapse to one
  column. Every move here must leave that collapse intact — a block moved out
  of a column must not become a second column on a phone.
- **JavaScript disabled** stops being an edge case for section 02: with the
  toggle gone, there is one rendering rather than two, which is the point.
- **The page keeps no script at all.** `docs/index.html` becomes a file with
  zero `<script>` blocks. That is a *stronger* form of the design rule the
  current assertion defends, and it has to be restated rather than deleted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Section 02 MUST show both card faces at every viewport width, with
  no control that hides either.
- **FR-002**: The page MUST NOT ship a card toggle. The button, its `aria-controls`
  wiring, its label-swapping script and the `hidden` attribute it toggled all go
  — a control removed from the markup but left in the script is the failure mode
  this replaces.
- **FR-003**: `.print__box` MUST NOT be a descendant of `.print__rules`. It MUST
  render as a full-width block below both columns of the printing section, at
  every viewport width.
- **FR-004**: The cutting diagram MUST render in the same column as the sheet
  mock-ups.
- **FR-005**: Moving a block MUST NOT change its content, its links or its
  reading order relative to the text that introduces it. The `card-box.pdf` href
  stays relative and stays correct on the deployed site.
- **FR-006**: The rules framing every moved block MUST remain single — no
  doubled 4 px rule where a moved block meets its neighbour, and none missing.
  This is FR-009 of feature 002, which the same class of move needed then.
- **FR-007**: Below the 1080 px breakpoint both sections MUST still collapse to
  a single column, and a block moved out of a column MUST NOT reappear as a
  second column.
- **FR-008**: `docs/design.md` MUST state a rule for the page's two-column
  sections: which column a new block joins, and what happens when one side
  outgrows the other. Constitution XVI MUST point at it, the way it already
  points at the type floor.
- **FR-009**: The rule MUST be defended by an assertion over the page's
  *structure*, not over rendered geometry. `tests/test_landing_page.py` reads
  the file and never lays it out, and CI has no browser leg — feature 002's
  T039 records that it will not grow one. An assertion that needs a browser is
  not a gate in this repository.
- **FR-010**: ~~`docs/index.html` MUST remain one self-contained file with
  exactly one `<script>` block.~~ **Superseded by FR-011.**
- **FR-011**: *(supersedes FR-010, and SC-007 and FR-014 of feature 002)*
  `docs/index.html` MUST remain one self-contained file with **at most one**
  `<script>` block and no external sub-resource beyond the one font stylesheet
  it loads today. With the toggle gone the count is zero, and zero satisfies the
  design rule the old wording was defending — "one self-contained file with
  almost no script" — more completely than one did. The assertion must not be
  weakened to "any number": a page that grows a second script has left the rule
  whether or not the first one was removed.
- **FR-012**: The `[hidden]` reset in the stylesheet MUST stay, and MUST be
  documented as a reset rather than as the toggle's fix. Feature 002 added it
  because an author `display` outranks the user-agent rule and the whole class
  of bug can recur on the next element given `hidden`. Deleting it with its one
  caller would re-arm that class silently. FR-012 of feature 002 survives this
  feature intact.

### Format Contracts *(mandatory — state "none" if untouched)*

**No format change.** No artifact a user has on disk is read or written by this
feature. `sources.yaml`, `knowledge/`, `catalog/topics.md` and `cards/*.yaml`
are all untouched.

**Backwards compatibility**: not applicable — nothing on disk changes, and the
landing page is served, not consumed by a tool.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: the landing page only. Not the card, not the
  press sheet, not the mark, not the README graphics.
- **Black-only laser print still readable**: N/A for a web page, but the rule it
  stands for is respected — nothing here makes colour carry meaning. Removing
  the toggle removes a control, not a signal: the front/back distinction is
  already tripled (colour, shape, position) on the cards themselves.
- **Minimum type size respected**: yes. No type size changes; the 15 px floor
  and SC-010 of feature 002 are untouched.
- **Brand PNGs need re-rendering**: no. `scripts/render_brand.py` draws the card,
  the banner, the pipeline strip and the social card — none of them appears in
  either section being changed.
- **Duplex alignment unaffected**: yes — no press-sheet code is touched. The
  *pictures* of sheets move; the sheets themselves do not.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. The change
  is markup, CSS and one assertion using the module's existing HTML parser and
  CSS helpers.
- **New runtime dependency**: none.
- **New dev dependency**: none.
- **New external binary**: none. A browser was used to *measure* the problem
  and will be used to check the result by hand, but nothing in the repository
  gains a dependency on one — that is exactly what FR-009 is about.
- **Anything this makes redundant**: the toggle button, its script and the
  `EXTERNAL_SUBRESOURCES` expectation of exactly one script block. Named here so
  they are deleted rather than left orphaned.
- **Engine version change**: no.
- **Platforms verified**: the assertions are text over a file and run everywhere
  CI runs — Ubuntu and Windows, Python 3.12 and 3.13. The by-hand rows are
  macOS here, in the three engines feature 002 established.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In section 02, the visible content of the card column fills its
  cell to within the cell's own padding. Measured today: 269 px of content in a
  644 px cell, 335 px dead (46 %). Target: 564 px in 644 px, 0 % dead.
- **SC-002**: In section 03, **both** columns end together — the sheets column
  and the rules column. Measured before: the sheets column held 327 px in
  1176 px, 769 px dead (65 %). After: both columns close at 433 px.
  **Corrected during implementation.** This criterion first read *"the visible
  content of the sheets column fills its column"* and predicted 547 px in
  627 px from a prototype. Written that way it was satisfiable by moving the
  hole rather than closing it, and that is exactly what happened: sending the
  cutting diagram to the picture column but letting it wrap *below* the two
  sheets filled the left column to 595 px and left 161 px under the three rules
  on the right. The one-sided measurement reported 0 % and the section still had
  a hole in it. A criterion about a two-column section has to name both columns.
- **SC-003**: Section 02 holds at 1120, 1280, 1440 and 1800 px. Section 03 holds
  from 1280 px up; between 1080 px and about 1180 px the cutting diagram wraps
  below the sheets and roughly 160 px is left under the rules column.
  **That fallback is accepted, not overlooked**: closing it would mean squeezing
  the diagram's caption below its minimum width, and the layout never shrinks
  reading text to fit (constitution XVI). It is a fifth of the 769 px it
  replaced and within the tolerance the new design rule states.
- **SC-004**: `docs/index.html` contains zero `<script>` blocks and the same
  single external sub-resource it has today.
- **SC-005**: With JavaScript disabled, both sections render identically to the
  JavaScript-enabled rendering — byte-for-byte the same DOM, because no script
  runs in either case.
- **SC-006**: Reverting either markup move turns the suite red, and the failure
  names the section.
- **SC-007**: Below 1080 px both sections are a single column, and the reading
  order within each is unchanged from today.
- **SC-008**: The new assertions fail on the parent commit and pass on the merge
  commit — the red-then-green evidence constitution XI requires.
- **SC-009**: The four gates are green: `ruff check . && ruff format --check .`,
  `pytest`, `lernkarten check cards/example.yaml`,
  `python3 scripts/check_docs.py`.

## Assumptions

- **The user has taken the toggle decision.** Removing it rather than centring
  the single card was chosen deliberately, against the measured alternative
  (centring leaves the same 46 % dead, symmetrically). This closes the *"Second,
  separate concern"* of issue #28, which was closed undecided when the toggle
  was merely made to work.
- **Two cards are the right amount of content for that column**, not a
  coincidence. 2 × 269 px plus the 26 px gap plus 80 px of padding is 644 px,
  which is what the four prose blocks beside it set. The column is being
  restored to its own proportion rather than padded to a new one.
- **The measurements are reproducible.** They were taken in headless Chrome
  against visible ink — the `.sheet` boxes are stretched by `align-items:
  stretch` and are not ink, which is why a naive descendant walk reports the
  printing column as full. Anyone re-measuring must exclude them.
- **No new test material is needed.** The landing page is its own fixture; the
  demo project under `tests/fixtures/` is not involved.
- **The `hidden` reset stays** even with nothing using it (FR-012), so the
  existing assertion that defends it keeps passing unchanged.
