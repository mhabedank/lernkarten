# Feature Specification: Three landing page fixes

**Feature Branch**: `fix/landing-page`

**Created**: 2026-08-19

**Status**: Draft

**Input**: GitHub issues [#27](https://github.com/mhabedank/lernkarten/issues/27),
[#28](https://github.com/mhabedank/lernkarten/issues/28) and
[#29](https://github.com/mhabedank/lernkarten/issues/29) — three reported bugs
on the landing page, `docs/index.html`.

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: none of them. `docs/index.html` is a project
surface, not a pipeline step — it is the page a newcomer reads before they run
anything. Nothing under `skills/`, `scripts/`, `bin/` or `templates/` changes,
and no artifact a user has on disk changes.

**Implementation half**:

- [ ] **Model-driven**
- [x] **Deterministic** — one versioned file, `docs/index.html`, whose contents
      are assertable from pytest exactly as
      `tests/test_repo_hygiene.py::test_the_repo_does_not_still_promise_five_commands`
      already asserts them today.
- [ ] **Both**

The seam is unusual and worth naming: the file is HTML and CSS, so what a test
can reach is its *source text and structure*, never its rendered geometry. Every
requirement below is therefore split deliberately — a structural claim that a
test asserts, and, where the bug is about how the page looks, a named entry on
the manual checklist in `docs/testing.md`. Constitution XI allows exactly this
split for layout work and requires the assertable half to come first.

**Who runs into this**: a newcomer reading the landing page — someone who has
not installed anything yet. Two of the three bugs (#27, #28) are only visible to
that person, never to a contributor running the test suite.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every nav link is reachable on a phone (Priority: P1)

A newcomer opens the landing page on a phone and wants to install the plugin.
The nav bar shows `how it works`, `the card`, `printing`, `install`. Today the
row overflows the bar horizontally, the scrollbar is deliberately suppressed
(`.nav__links` carries `overflow-x: auto` with `scrollbar-width: none` and a
`::-webkit-scrollbar { display: none }` rule, `docs/index.html:99-105`), and
`install` — the one link that matters most — is the one that falls off the right
edge. There is no arrow, no fade, no bar: nothing tells the reader that more
links exist.

The sideways scroll was chosen on purpose, and the comment at
`docs/index.html:96-97` states why: a wrapped row makes the sticky bar two lines
tall on a phone and eats the top of every section. That reasoning still holds,
so the fix must not simply hand the row to `flex-wrap` — that reintroduces the
problem this was solving.

**Why this priority**: it is the only one of the three bugs that hides
functionality. A reader who cannot reach `install` cannot install.

**Independent Test**: shipping this alone leaves a page whose navigation works
at every width. Structurally: assert that below the mobile breakpoint the link
row is not an overflow container and that a labelled control exists to reveal
it. Visually: the manual checklist entry below.

**Acceptance Scenarios**:

1. **Given** `docs/index.html` at a viewport of 360 px, **When** the page
   loads, **Then** the link row is not rendered as a horizontally scrolling
   strip — no `overflow-x: auto` applies to it at that width.
2. **Given** the same viewport, **When** the reader looks at the bar, **Then** a
   control with a text-bearing accessible name is present that reveals the four
   links, and the four links are reachable through it.
3. **Given** a viewport above the breakpoint, **When** the page loads, **Then**
   the bar is unchanged from today: wordmark, four inline links, github block,
   one line tall.
4. **Given** the reveal control is open on a phone, **When** the reader taps a
   link, **Then** they arrive at the target section. (The bar is
   `position: sticky`; whether the panel closes behind them is a design
   decision for the plan, not a correctness one.)
5. **Given** a browser with JavaScript disabled, **When** the page loads at
   360 px, **Then** the four links are still reachable.

---

### User Story 2 - The band note stops inflating the section heading (Priority: P2)

A reader arrives at section `01 the pipeline`. The heading sits in a row far
taller than it needs and reads as floating in empty vertical space.

`.band` is `display: flex` with `align-items: stretch`
(`docs/index.html:74`), so the tallest child sets the row height. The `h2` needs
roughly 74 px — `clamp(26px, 4vw, 38px)` at `line-height: 1` plus `18px 28px`
of padding. The note beside it (`docs/index.html:81`, `420`) is 400 px wide,
14 px text at `line-height: 1.6`, three to four lines, `18px 24px` of padding —
roughly 103 px. The note wins and drags the heading row with it.

**Scope, precisely**: `.band` already wraps at `max-width: 1080px`
(`docs/index.html:291-296`), where `.band__note` goes to `width: 100%`, drops
its left border and takes a top border instead. Below 1080 px the note is
therefore *already* a full-width block under the heading row and the bug does
not occur. **This bug is visible only above 1080 px.**

**All three bands are affected, not just the pipeline one.** The note box is
400 px wide with 24 px of side padding, leaving a 352 px measure; at 14 px with
`line-height: 1.6` a line is 22.4 px and holds roughly 50 characters, and the
box adds 36 px of vertical padding. The heading is `clamp(26px, 4vw, 38px)` at
`line-height: 1` plus the same 36 px — 74 px, constant above roughly 950 px of
viewport. That gives:

| Note | Chars | Lines | Height | Over the heading |
|---|---|---|---|---|
| pipeline (`docs/index.html:420`) | 196 | 4 | ~126 px | +52 px |
| printing (`docs/index.html:590`) | 113 | 3 | ~103 px | +29 px |
| install (`docs/index.html:669`) | 57 | 2 | ~81 px | +7 px |

Even the shortest note — *"Two lines in Claude Code. That is the whole
installation."* — exceeds the heading, because one line would need 50 characters
or fewer and it has 57. So this is not a defect of one long note. It is the
construction: `align-items: stretch` couples a height the heading sets to a
content whose length varies freely, and every instance of that coupling is
already over.

**Two fixes that were considered and rejected**, recorded so they are not
re-proposed:

- *Shrink the note's type.* Fitting 196 characters into the 38 px of text height
  the heading leaves needs roughly 9 px. The floor is 15 px on screen
  (constitution XVI). The note is already at 14 px, which is itself below that
  floor and is tracked separately as issue #30 — the correct direction for the
  type size is up, which makes the row taller, not shorter.
- *Shorten the note's text.* It moves the threshold without removing it: the
  pipeline note would have to drop from 196 characters to about 50 to fit one
  line, and the next person to edit the copy reintroduces the bug. Feature 001
  lengthened this note from 157 to 196 characters and made the symptom worse,
  but the 157-character version on `main` was already three lines and already
  over the heading.

**Why this priority**: it is a pure layout defect on the first content section
of the page — high visibility, no functional loss.

**Independent Test**: shipping this alone leaves a page whose section headings
sit in rows sized by the heading. Structurally: assert no `band__note` is left
as a flex child of a `band`. Visually: the manual checklist entry below.

**Acceptance Scenarios**:

1. **Given** `docs/index.html` above 1080 px, **When** section `01` renders,
   **Then** the heading row's height is set by the heading, not by the note.
2. **Given** the same section, **When** the note renders, **Then** it sits
   below the band and above the step strip.
3. **Given** the printing and install sections, **When** they render above
   1080 px, **Then** their headings sit in rows of the same height as section
   `01`'s — all three bands are one height, because none of them is stretched
   by a note any more.
4. **Given** a viewport below 1080 px, **When** any of the three sections
   renders, **Then** the reading order is unchanged from today — number,
   heading, note, content — and the rules between them still meet, with no
   doubled or missing border where the note now sits.
5. **Given** the `install` section, whose band carries the inverted colour
   treatment (`docs/index.html:255-257`, `296`), **When** it renders, **Then**
   its note keeps that treatment: `--sand` on `--ink`, with the rule above it
   in `--sand` rather than the default.
6. **Given** the `02 one card, one idea` band, which holds a `.toggle` button
   rather than a note (`docs/index.html:502`), **When** it renders, **Then** it
   is unaffected — the button is `flex: none` and short, and this story does not
   touch it.

---

### User Story 3 - "show the back" turns the card over (Priority: P3)

A reader reaches section `02 one card, one idea` and clicks **show the back**.
The button label changes to "show the front" — and nothing else happens. Both
cards stay on screen the whole time, so the control reads as broken.

The script at `docs/index.html:719-736` is correct and does run; the changing
label proves it. It sets `back.hidden = true`, and the CSS silently defeats it:
`.card` declares `display: flex` (`docs/index.html:146`), and any author
`display` declaration outranks the user-agent rule `[hidden] { display: none }`.
There is no `[hidden]` rule anywhere in the file.

Why the button itself hides correctly without JS, and the cards do not: `.toggle`
(`docs/index.html:283-288`) never sets `display`, so the user-agent rule still
reaches it. Only `.card` overrides it. The no-JS fallback — both sides side by
side, no button — works today for that reason and must keep working.

**Scope decision, already taken**: repair only. The issue raises a second,
separate concern — that even once the toggle works it does not explain itself,
because the button sits in the band far from the cards and neither card is
labelled *front* or *back*. Relabelling the cards, moving the button, and
dropping the toggle in favour of showing both sides are all **out of scope**
here and stay open on issue #28.

**Why this priority**: the smallest of the three, and the one the plan is most
likely to get right in a single line. It ranks last only because the other two
are seen by more readers.

**Independent Test**: shipping this alone leaves a page whose one interactive
control works. Structurally: assert a rule exists that makes the `hidden`
attribute effective against `.card`.

**Acceptance Scenarios**:

1. **Given** the page with JavaScript enabled, **When** it loads, **Then**
   exactly one card is visible and the button reads "show the back".
2. **Given** that state, **When** the reader clicks the button, **Then** the
   visible card is replaced by the other one and the label reads "show the
   front".
3. **Given** JavaScript is disabled, **When** the page loads, **Then** both
   cards are visible and the button is not — unchanged from today.
4. **Given** any future element that is given the `hidden` attribute, **When**
   it renders, **Then** the attribute takes effect regardless of what `display`
   its class sets.

### Edge Cases

Most of the recurring list does not apply — nothing here touches Python, the
typesetter, card text or a file on a user's disk. What does apply:

- **JavaScript disabled**: covered above, and it is the reason the `[hidden]`
  fix has to be checked against the no-JS path rather than only the JS one.
- **Encoding and file names**: `docs/index.html` is one self-contained UTF-8
  file and stays one file. No asset is added.
- **Idempotence**: the page is static; there is nothing to re-run.
- **Minimum type size**: 15 px on screen is a hard floor (constitution XVI). A
  burger panel is a new surface that must respect it, and the existing note at
  14 px is *not* reading text under that rule — it is a secondary annotation in
  `--muted`, unchanged by this feature.
- **Non-Latin text**: not applicable; no card text is involved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The landing page MUST NOT rely on a horizontally scrolling
  container to reach any navigation link at any viewport width.
- **FR-002**: Below the mobile breakpoint the landing page MUST provide a
  control that reveals the navigation links, and that control MUST carry a
  text-bearing accessible name. An icon alone does not satisfy this —
  constitution XVI forbids letting a visual carry meaning on its own.
- **FR-003**: The navigation MUST remain reachable without JavaScript at every
  viewport width.
- **FR-004**: The sticky navigation bar MUST remain one line tall at every
  viewport width, in its resting state. This is the constraint the current
  sideways scroll exists to satisfy (`docs/index.html:96-97`) and it survives
  the fix.
- **FR-005**: Above the mobile breakpoint the navigation MUST be visually
  unchanged from today.
- **FR-006**: The heading row of a section band MUST take its height from the
  heading, not from the note beside it.
- **FR-007**: Every section note MUST render below its band and above that
  section's content, at every viewport width. This applies to all three —
  pipeline, printing and install — not only the one reported.
- **FR-008**: No band MUST be left able to reach the failure again: after the
  change, a longer note MUST NOT be able to grow its section's heading row.
  This is what distinguishes the fix from shortening the copy.
- **FR-009**: The rules framing a relocated note MUST remain single — no
  doubled border where the band's bottom rule meets the note, and none missing.
- **FR-010**: The `install` section's note MUST keep its inverted colour
  treatment after the change: `--sand` on `--ink`, with the rule above it in
  `--sand`.
- **FR-011**: Note type size MUST stay at its current 14 px. Raising it to the
  15 px floor is issue #30's decision, not this feature's, and changing it here
  would confound the visual review of the move.
- **FR-012**: The stylesheet MUST make the `hidden` attribute effective against
  every element on the page, including those whose class sets `display`.
- **FR-013**: The card toggle MUST show exactly one card at a time when
  JavaScript is enabled, and both cards with no button when it is not.
- **FR-014**: `docs/index.html` MUST remain one self-contained file, with no
  new script block and no new external asset. If script is unavoidable for
  FR-002, it MUST extend the single existing block.
- **FR-015**: Every change MUST hold to the design rules — flat colour and type
  only, no gradients, no shadows, no rounded corners, reading text never below
  15 px, colour never carrying meaning alone.

### Format Contracts *(mandatory — state "none" if untouched)*

**No format change.** None of the five file formats is touched: this feature
does not read or write `goal.md`, `sources.yaml`, `knowledge/`, `catalog/` or
`cards/`.

**Backwards compatibility**: nothing to break. No project on disk is affected;
`docs/index.html` is published to GitHub Pages and has no consumers other than
a browser.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: the landing page (`docs/index.html`) only. Not
  the card, not the press sheet, not the mark, not the readme graphics.
- **Black-only laser print still readable**: N/A for the page itself, but
  FR-002 carries the same principle onto the screen — the reveal control is
  named in words, not by an icon alone.
- **Minimum type size respected**: yes — 15 px on screen for reading text; the
  burger panel's links are `label`-class uppercase like the existing nav links
  and inherit that treatment.
- **Brand PNGs need re-rendering**: no. `assets/brand/*.typ` is untouched, and
  so is `pipeline.png` — the step strip's contents do not change, only what
  sits above it.
- **Duplex alignment unaffected**: yes, nothing printed changes.

`docs/design.md` has been read (constitution XVI). Two of its statements bind
this feature directly: the landing page is built from *flat colour and type
only*, and it is *one self-contained file*. A third is worth naming because it
is nearby and must not be disturbed: the step strip's column measure is set by
the longest command, `/learning-goal`, which is why the command is set at 16 px
and the caption at 15 px. Moving the note above that strip must not touch the
strip's own geometry.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. The change
  is CSS and markup in an existing file.
- **New runtime dependency**: none.
- **New dev dependency**: none expected. If the structural assertions need to
  parse HTML rather than match text, the standard library's `html.parser`
  covers it — `test_repo_hygiene.py` already reads this file as plain text, so
  text-level assertions have precedent in the suite.
- **New external binary**: none.
- **Anything this makes redundant**: the `::-webkit-scrollbar` suppression rule
  at `docs/index.html:103` and `scrollbar-width: none`, if the mobile fix
  removes the overflow container that made them necessary. The plan should
  delete what is left dead rather than leave it.
- **Engine version change**: no.
- **Platforms verified**: platform-independent — this is a browser surface. What
  does need naming is *browser* coverage: the fix must work in current Firefox,
  Safari and Chromium, which is what the `scrollbar-width` / `::-webkit-`
  pairing in the current code was already accounting for.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At 360 px width, all four navigation links are reachable without
  horizontal scrolling, and the navigation bar occupies one line at rest.
- **SC-002**: With JavaScript disabled at 360 px, all four navigation links are
  still reachable.
- **SC-003**: Above 1080 px, the heading rows of `01 the pipeline`, the printing
  section and the install section are all the same height, and none is taller
  than its heading needs — no note sets a heading row's height any more.
- **SC-004**: Reading order in every section band is unchanged at every width:
  number, heading, note, content.
- **SC-005**: Clicking "show the back" leaves exactly one card visible; clicking
  again leaves exactly the other one visible.
- **SC-006**: With JavaScript disabled, both cards are visible and no toggle
  button is.
- **SC-007**: `docs/index.html` is still one file with exactly one `<script>`
  block and no external asset reference beyond what it has today.
- **SC-008**: The three landing-page assertions fail on the parent commit and
  pass on the merge commit — the red-then-green evidence constitution XI
  requires.
- **SC-009**: The four gates are green: `ruff check . && ruff format --check .`,
  `pytest`, `lernkarten check cards/example.yaml`,
  `python3 scripts/check_docs.py`.

## Resolved Questions

- **Q1 — does the note move out of every band, or only the pipeline band?**
  **Answered: every band.** The question was opened on the assumption that only
  the pipeline note out-measures its heading, which would have made the choice a
  trade between minimal change and design consistency. Measuring all three
  showed the assumption was wrong — printing exceeds the heading by 29 px and
  install by 7 px, so the same defect is present in all three, and moving one
  would leave two of them broken as well as leaving two band structures on one
  page. The measurements are in User Story 2.

## Assumptions

- **The base is `main`** — since 2026-08-19, when feature 001 landed there as
  [PR #32](https://github.com/mhabedank/lernkarten/pull/32). This branch was
  originally cut from `feat/goal-driven-catalog` and stacked on it, because
  issue #29 quotes the note "Seven steps, two of them optional. …" and derives
  its height from those three-to-four lines — text that existed only on the
  feature branch while `main` still carried the shorter note and the `five
  commands` heading. That stacking is now moot: the branch has been rebased onto
  `main`, which carries the same tree, and the pull request targets `main`.
  (#27 and #28 always reproduced on both.)
- **The mobile breakpoint for the nav fix is the existing 760 px**
  (`docs/index.html:316`), not a new one. The plan may move it with a reason.
- **The band breakpoint stays 1080 px** (`docs/index.html:291`). US2 changes
  what sits inside the band, not when it wraps.
- **The visual half of each bug is verified by eye, and named for it.** No test
  in this repo can measure a rendered row height or prove a link is discoverable.
  Constitution XI's layout carve-out applies, which means each of the three gets
  a named entry on the manual checklist in `docs/testing.md` — not left implicit.
- **No new test corpus.** `tests/fixtures/demo-project` is untouched; the
  assertions read `docs/index.html` from the repo root, as
  `test_repo_hygiene.py` already does.
- **Issue #26 is not part of this feature.** "README buries the landing page" is
  a documentation change with no overlap in the file.
- **Issue #30 is not part of this feature.** Filed while specifying this one:
  four places on the page set running prose below the 15 px screen floor that
  `docs/design.md` and constitution XVI state — `.band__note` at 14 px
  (`:83`), `.anatomy__item p` at 14 px (`:209`), `.print__cut p` at 13 px
  (`:240`) and an inline 14 px at `:581`. It is a decision about whether the
  page or the rule is wrong, it changes band heights again, and FR-011 holds
  this feature's note size at 14 px so the two do not confound each other's
  visual review.
- **The line counts in User Story 2 are derived, not rendered.** They come from
  the box measure, the declared `line-height` and an average character width of
  half the font size — enough to show all three notes exceed the heading and
  that a type-size fix is impossible by an order of magnitude, but the plan
  should confirm the exact heights in a browser before the visual review signs
  off.
