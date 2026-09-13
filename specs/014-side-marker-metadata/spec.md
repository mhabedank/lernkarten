# Feature Specification: The side marker leaves the card and becomes document metadata

**Feature Branch**: `design/side-marker-metadata`

**Created**: 2026-09-11

**Status**: Draft

**Input**: User description: "Issue #75"

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/print` and the build machinery beneath it
(`templates/card.typ`, `scripts/build_pdf.py`, the e2e suite, the design docs
and the landing page).

**Implementation half**:

- [ ] **Model-driven**
- [x] **Deterministic** — Typst under `templates/card.typ`, Python under
      `scripts/build_pdf.py` and `scripts/check_docs.py`, assertions under
      `tests/`. No skill prompt changes; no card file is read differently.
- [ ] **Both**

**Who runs into this**: both — the user holds the printed card, the contributor
maintains the print-order guarantee that today reads the marker back out of the
PDF.

## Context

`docs/design.md` states the rule the card is built on: *every colour is doubled
by a shape or a position*. Which face you hold is therefore already encoded
twice, and each encoding is colour-plus-shape, so both survive a mono laser
print:

| Where | Front | Back |
|---|---|---|
| Header right square (`templates/card.typ:75-81`) | red, hollow circle | yellow, solid disc |
| Footer mark box (`templates/card.typ:113-119`) | no fill, ink mark | solid ink, paper mark |

The printed `1/2` / `2/2` in the footer is a **third** encoding of one bit, and
the only one made of text. The two that remain are not redundant with each
other: the header marker reads when you look at a card, the footer box reads
across a stack — which is the job `card.typ` already claims for it ("the one
signal you need when eight cards land face-down").

The marker cannot simply be deleted, because `tests/test_e2e.py` reads it out of
the PDF text layer to decide which face each page carries, and that helper is
the only mechanism verifying the print-order guarantees from #48. This feature
therefore **moves the front/back signal from the card into the document
metadata**: the tests keep their assertion and gain a stronger one, the card
loses the ink.

Settled in the issue thread and explicitly **not** in scope: `LERNKARTEN BY
MHABEDANK` stays on both faces, unchanged. `--no-logo` remains the way to print
without it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The footer band gets quieter (Priority: P1)

A user runs `/print` (or `lernkarten build cards/*.yaml`) and gets the same deck
with one less thing in a band `docs/design.md` calls "meant to be quiet". The
right-hand footer block shows the card id and nothing else; no `·`, no `1/2`, no
`2/2`. Which face they hold is still unmistakable — red hollow circle against
yellow solid disc in the header, hollow against solid mark box in the footer —
and both of those still work on a black-only photocopy.

**Why this priority**: it is the change. Everything else in this spec exists to
let it happen without losing a guarantee.

**Independent Test**: build the demo deck and read the PDF text layer — the
tokens `1/2` and `2/2` do not occur on any page, at either grid, with or without
`--no-logo`, while every card id still occurs twice.

**Acceptance Scenarios**:

1. **Given** the demo project at `tests/fixtures/demo-project`, **When**
   `lernkarten build cards/*.yaml`, **Then** the built PDF's text layer contains
   no token matching `[12]/2` on any page.
2. **Given** the same deck, **When** built at `--grid a8` and at `--grid a7`,
   **Then** each card id still appears exactly twice per card (front and back)
   and the footer band keeps its height at both grids.
3. **Given** a deck whose cards carry ids, **When** built, **Then** the
   right-hand footer block holds the bare id — the `·` separator does not appear
   anywhere on the card.

---

### User Story 2 - The print order stays verifiable (Priority: P1)

A contributor runs `pytest` with `LERNKARTEN_E2E=1`. The print-order guarantees
from #48 — duplex interleaves front, front, back, back per sheet; simplex puts
every front page before any back page — are still asserted per page against a
real build, exactly rather than by inference from geometry, and no longer depend
on `pdftotext` being installed.

**Why this priority**: deleting the marker without this deletes the only check
that the pages come out in the right order. Equal priority to US1 because US1
cannot land without it.

**Independent Test**: on a machine with no `pdftotext` on `PATH`, the print-order
tests run rather than skip, and fail if the page order is perturbed. They ask
`bin/lernkarten` for the face map as a subprocess, exactly as they ask it for a
PDF today.

**Acceptance Scenarios**:

1. **Given** the demo deck, **When** built with `--sides simplex` at `a7`,
   **Then** the face of each card-bearing page is read from the document
   metadata and every front page precedes every back page.
2. **Given** the same deck built with the default `--sides duplex`, **Then** the
   faces per page read front, front, back, back … one pair per sheet.
3. **Given** `pdftotext` is absent, **When** the print-order tests run, **Then**
   they execute and pass — no skip.
4. **Given** a single card whose front and back are laid out identically,
   **When** built, **Then** the two pages are still distinguishable as front and
   back — the signal is exact, not inferred from mirrored geometry.
5. **Given** an ordinary build that does not ask for the face map, **When** it
   finishes, **Then** it has written the PDF and nothing else — the diagnostic
   costs a user who never uses it nothing, not even a file.
6. **Given** a build asked for the map at a path it cannot write, **When** it
   runs, **Then** it fails with an error naming that path rather than building
   on in silence.

---

### User Story 3 - A card with no id leaves no smudge (Priority: P2)

A user with a deck written before ids existed (or built with ids absent) prints
it. The right-hand footer block, which until now would have shown the side
marker alone, is **not there at all**: no box, no vertical rule in front of it.
The footer band keeps its height and its top rule, and the wordmark block takes
the width the id block would have had.

**Why this priority**: it is the edge case that makes the deletion safe.
`card.typ:92-95` avoided a separator with nothing in front of it; removing the
marker without this leaves a rule with nothing behind it — the same smudge, one
step further along.

**Independent Test**: build a deck whose cards carry no `id`, and check that
nothing is printed in the right-hand footer block and that the rule which
delimits it is not drawn.

**Acceptance Scenarios**:

1. **Given** a deck with no `id` on any card, **When** built, **Then** the text
   layer contains neither `·` nor `1/2` nor `2/2`.
2. **Given** the same deck built with `--no-logo`, **When** built, **Then** the
   footer band is empty apart from its top rule, keeps its 6.2 mm height, and
   the build exits 0 with no warning.
3. **Given** a deck in which some cards carry an id and some do not, **When**
   built, **Then** each card is treated on its own — the block and its rule
   appear on the cards that have an id and are absent on the cards that do not.

---

### User Story 4 - No shipped document still claims the printed marker (Priority: P3)

A reader of `docs/design.md`, `docs/workflow.md`, `docs/testing.md` or the
landing page sees a card described as it now prints. The description of the
footer band, the card-anatomy prose and the facsimile cards on the landing page
all drop `1/2` / `2/2`, and a gate in `scripts/check_docs.py` keeps them that
way.

**Why this priority**: valuable but not blocking the other three. It is here as
its own story because a hand-written grep is what let two stale claims ship
once before — the criterion has to be a gate that runs in CI, not a search
somebody remembers to do.

**Independent Test**: `python3 scripts/check_docs.py` exits non-zero on a doc
that reintroduces the printed marker, and exits 0 on the repository as shipped.

**Acceptance Scenarios**:

1. **Given** the repository after this change, **When**
   `python3 scripts/check_docs.py`, **Then** it exits 0.
2. **Given** a doc edited to say the card prints `1/2` or `2/2`, **When** the
   gate runs, **Then** it fails and names the file and line.
3. **Given** the landing page, **When** a visitor reads the card anatomy,
   **Then** the facsimile footer and its explanation match the card the build
   produces.

### Edge Cases

- **Missing optional tooling**: with no `pdftotext`, the print-order tests no
  longer skip — that is the point of US2. With no typesetting engine the e2e
  module skips as it always did.
- **A page that carries only dividers**: `--dividers` may open a sheet beyond
  the last card page. Such a page carries no card face, so the face map reports
  none for it, and the print-order assertions are stated over card-bearing pages
  rather than over all pages.
- **`--no-logo` together with a deck that has no ids**: the footer band is empty.
  It still keeps its height and its top rule — the three bands never move
  (constitution XVI).
- **Mono laser print**: both remaining face signals are colour *and* shape, so
  the card still reads. This is the premise of the whole change.
- **Idempotence**: building twice produces the same PDF; nothing about this
  change is stateful.
- **Both grids**: `a7` and `a8` render the same card at one scale, so the
  narrower id block and the collapsed rule behave identically at both.
- **Already-printed decks**: cards printed before this change carry the marker
  and cards printed after do not. They mix in one box without harm — the header
  and footer markers are what a learner reads, and those are unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `templates/card.typ` MUST NOT print `1/2` or `2/2` on any card
  face, at any grid, with or without `--no-logo`.
- **FR-002**: `templates/card.typ` MUST print the card id alone in the
  right-hand footer block when the card carries one — no separator, no side
  text — at the size and font it uses today (IBM Plex Mono, 8 pt × scale, muted).
- **FR-003**: `templates/card.typ` MUST omit the right-hand footer block **and
  the vertical rule that delimits it** when the card carries no id, and MUST
  give the wordmark block the width thereby freed. The footer band MUST keep its
  height and its top rule in that case.
- **FR-004**: The card document MUST carry, per card face, a queryable label
  naming the card id and which side that face is, so that the front/back
  identity of every page is readable from the document without reading printed
  text and without `pdftotext`.
- **FR-005**: The face signal MUST identify the **page** each face lands on, so
  a reader can state which face each page of a built document carries.
- **FR-006**: `lernkarten build` MUST write the face map when asked for it, and
  only then. The map is a **diagnostic**, off by default: a build that does not
  ask for it writes nothing beyond the PDF it writes today, and the option is
  documented where a contributor looks (`docs/testing.md`, `--help`), not sold
  to users as a feature. It is written by the real command rather than
  reconstructed by the test suite, so the print-order assertions keep driving
  `bin/lernkarten` as a subprocess — which is what `tests/test_e2e.py` exists
  for, and what the #48 guarantee is stated about.
- **FR-006a**: The face map MUST be machine-readable, name the page each face
  lands on, the card id and which side it is, and cover the whole document —
  including pages that carry no card face at all (a divider-only sheet), which
  it reports as carrying none rather than omitting.
- **FR-006b**: A face map that cannot be written — an unwritable path, a
  directory that does not exist — MUST be an error naming the path, not a
  silently skipped diagnostic. The PDF build itself MUST NOT be altered by
  asking for the map: the same bytes come out either way.
- **FR-007**: The e2e print-order assertions MUST be rewritten against the face
  map and MUST keep their present meaning: duplex interleaves front, front,
  back, back per sheet; simplex puts every front page before any back page; at
  both grids; and a back page stays column-mirrored behind its own front.
- **FR-008**: The test that today asserts the marker is printed MUST be replaced
  by one asserting it is **not** printed, and the no-id test MUST assert that
  nothing — neither marker nor separator — is printed in the right-hand block.
- **FR-009**: `scripts/check_docs.py` MUST fail when a shipped document
  (`docs/*.md`, `docs/index.html`, `README.md`, `CLAUDE.md`) describes the card
  as printing `1/2` or `2/2`, naming the file and line. The gate MUST not fire on
  text that exists in order to forbid the claim (this spec, the check itself).
- **FR-010**: The following MUST be updated to describe the card as it now
  prints: `docs/design.md` (the band table's footer row, and the paragraph about
  the id block and the card with no id), `docs/workflow.md` (the card
  description), `docs/testing.md` (the manual footer-band check), and
  `docs/index.html` (the three facsimile `card__id` values and the footer-band
  explanation).
- **FR-011**: The header side marker (red hollow circle / yellow solid disc), the
  footer mark box (hollow / solid) and `LERNKARTEN BY MHABEDANK` on both faces
  MUST be unchanged.
- **FR-012**: No card file is read or written differently: a deck that builds
  today MUST build after this change, with no migration and no new key.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | none | — |

**No format change.** The document handed to the engine
(`workdir/cards.json`) is unchanged; the new label is produced by the template
from data it already has.

**Backwards compatibility**: every project on disk still builds, unchanged, with
no migration. The only difference a user sees is on paper: decks printed before
and after this change differ in the footer band. Both remain usable, and mixing
them in one box is harmless.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: the card (footer band, both faces) and the
  landing page's facsimile cards.
- **Black-only laser print still readable**: yes — the two remaining face
  signals are each colour *and* shape *and* position; removing the text encoding
  removes the only one that was not.
- **Minimum type size respected**: yes — nothing is set smaller; text is
  removed.
- **Brand PNGs need re-rendering**: no — the mark is untouched.
- **Duplex alignment unaffected**: yes — the id block's width is measured from
  the id, which is identical on both faces, so front and back blocks stay the
  same width as each other. A card with no id now has no block on either face.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. The
  metadata-plus-query mechanism already exists in this repo for `<overflow>`.
- **New runtime dependency**: none.
- **New dev dependency**: none. Removing the text-layer dependency means the
  print-order tests stop needing poppler's `pdftotext`.
- **New external binary**: none.
- **Anything this makes redundant**: `face_marks_per_page()` in
  `tests/test_e2e.py`, and the `pdftotext` skip that guarded the print-order
  tests.
- **Engine version change**: no.
- **Platforms verified**: macOS and Linux locally and in CI; Windows through the
  existing CI legs. Nothing here is platform-specific.

### Key Entities

- **Face signal**: the assertion "this page carries the front (or back) of card
  X". Lives in the document metadata after this change, printed text before it.
- **Face map**: face signals for a whole built document, grouped by page — what
  the print-order tests read. Written by `lernkarten build` on request, never by
  default, and never something the printed deck depends on.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The demo deck built at `a7` and `a8`, duplex and simplex, with and
  without `--no-logo`, yields a PDF whose text layer contains zero tokens
  matching `[12]/2` and zero `·` characters, while every card id still appears
  twice per card.
- **SC-002**: The face of every card-bearing page is determined exactly for all
  four grid × print-order combinations, read from a map the real `lernkarten
  build` wrote, on a machine with no `pdftotext` installed, and the print-order
  tests fail if the page sequence is perturbed.
- **SC-002a**: A build that does not ask for the face map writes exactly the
  files it writes today, and a build that does asks produces a byte-identical
  PDF to one that does not.
- **SC-003**: A deck with no ids builds with exit 0, prints nothing in the
  right-hand footer block, and the footer band keeps its 6.2 mm height at both
  grids — verified automatically for the printed text and by one manual row in
  `docs/testing.md` for the band's appearance.
- **SC-004**: All four gates are green — `ruff check . && ruff format --check .`,
  `pytest`, `lernkarten check cards/example.yaml`, `python3
  scripts/check_docs.py` — plus `LERNKARTEN_E2E=1 pytest tests/test_e2e.py`.
- **SC-005**: `scripts/check_docs.py` fails on a doc that reintroduces the
  printed marker, demonstrated by a failing case in `tests/test_check_docs.py`.
- **SC-006**: Page counts, card counts and the mirrored back layout are byte-for-
  byte what they were before the change — this is a subtraction from one band,
  not a re-layout.

## Assumptions

- The user has Python 3.12+ and the pinned typesetting engine (fetched on first
  use, as always).
- The demo project already carries what this needs: decks with ids for the
  print-order tests, and the inline no-id deck the id tests already build in
  `tmp_path`. No new fixture corpus.
- Test-first per constitution XI: the red artifacts are (a) a print-order test
  reading the face map, which cannot pass before the label exists, (b) a text-
  layer test asserting the marker is gone, which fails on today's template, and
  (c) a `tests/test_check_docs.py` case for the new gate.
- `docs/index.html` currently shows `example-3 · 1/2` and `probability-3 · 2/2`
  — ids in the format that `docs/design.md` says was *replaced* by five
  characters of Crockford Base32. Since this change edits exactly those strings,
  the facsimiles get valid five-character ids at the same time rather than being
  left contradicting the design doc. This is the only scope beyond the issue's
  list, and it is one line of HTML per card.
- The comment at `templates/divider.typ:3` ("it has no front and no back, so a
  side marker would be false") is still true and stays; it is checked for
  wording only, not behaviour.
- Already-printed decks are not migrated and cannot be. The issue accepts this
  (reversibility 2 of 12).
- The **spelling** of the diagnostic — a `--…` option on `build`, an environment
  variable, or a sibling subcommand — is a plan decision. The spec fixes only
  its behaviour: opt-in, off by default, written by the real command, machine-
  readable, loud when it cannot be written. The repo has precedent for both
  shapes (`--dividers` for options, `LERNKARTEN_E2E` for a contributor-only
  switch), so the plan weighs them against `--help` noise.

## Out of Scope

- `LERNKARTEN BY MHABEDANK` on the back face — settled in the issue thread: it
  stays on both faces. `--no-logo` remains the way to print without it.
- The header topic/subtopic on the back, both face markers, the note rules and
  the `·` separator's existing no-id handling — examined in the issue and
  deliberately left alone.
- Any change to the card box, the dividers or the press sheet.
