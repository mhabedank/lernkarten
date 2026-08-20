# Feature Specification: Simplex print order — all fronts, then all backs

**Feature Branch**: `feat/simplex-print-order`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "It should be possible to print on simplex printers. currenlty the pdfs are optimized for dubley, every second page is a backside. but witth a simplex printer that is not the richt solution. the right solution would be to print all fronts and then all backs."

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/print`, and the build machinery under it
(`scripts/build_pdf.py`, `templates/cards.typ`).

**Implementation half**:

- [ ] **Model-driven** — a prompt change under `skills/<name>/SKILL.md`.
- [ ] **Deterministic** — Python under `scripts/` or `bin/lernkarten`, and/or Typst under `templates/`.
- [x] **Both** — the seam is the **build command line**, not a file format. The
  deterministic half gains one print-time option and emits the pages in a
  different order; the model-driven half (`skills/print/SKILL.md`) learns when
  to pass it and what to tell the user afterwards. No artifact under
  `cards/`, `catalog/`, `knowledge/` or `sources.yaml` changes shape, so the
  five file formats of constitution I are untouched.

**Who runs into this**: the user driving Claude in their own project — anyone
whose printer cannot print both sides of a sheet in one pass. A contributor
runs into it only through the docs gate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A PDF a one-sided printer can actually use (Priority: P1)

A user has a printer that prints one side at a time. Today `lernkarten build`
interleaves the sheet faces — page 1 front, page 2 the backs of those same
cards, page 3 the next front — which is right for a duplex printer and useless
for theirs: sending the whole file to a simplex printer produces twice as many
sheets, each printed on one side, and no card at all.

They run:

```bash
lernkarten build cards/*.yaml --sides simplex
```

and get a PDF whose **first half is every front sheet and second half is every
back sheet, in the same sheet order**. They print the first half, put the
printed stack back in the paper tray, and print the second half onto the
reverse.

**Why this priority**: without it the tool does not work at all for this class
of printer. Everything else in this feature is guidance around it.

**Independent Test**: build the demo deck twice — once with the flag, once
without — and compare the page order. Extracted text of the simplex PDF must
show every front before any back; the duplex PDF must alternate. Both must have
the same page count.

**Acceptance Scenarios**:

1. **Given** the demo project's 29 cards, which fill 4 sheets at `a7`,
   **When** the user runs `lernkarten build ... --sides simplex`, **Then** the
   PDF has 8 pages: pages 1–4 carry only card fronts, pages 5–8 only card
   backs, and page 4 + n carries the backs of the cards on page n.
2. **Given** the same card files, **When** the user runs `lernkarten build`
   with no `--sides` flag, **Then** the output is exactly what this version
   produced before the feature existed — fronts and backs on consecutive pages
   — and every existing end-to-end expectation still holds.
3. **Given** a deck small enough for one sheet, **When** built with
   `--sides simplex`, **Then** the PDF has 2 pages and its page order is
   identical to the duplex build (one front sheet, one back sheet) — the two
   orders coincide at a single sheet, and the build still reports the simplex
   instructions.
4. **Given** `--sides simplex` together with `--grid a8`, **When** the user
   builds, **Then** the split is by sheet at that grid (16 cards per sheet) and
   the backs keep the same column mirroring the duplex build uses.
5. **Given** a value the flag does not accept (`--sides both`), **When** the
   user builds, **Then** the command exits 2 with a usage error naming the
   accepted values, before any card file is read — the same way a bad `--grid`
   is handled.
6. **Given** `--sides simplex --check`, **When** the user runs it, **Then**
   validation behaves exactly as `--check` does today, writes no PDF, and the
   flag changes nothing about which cards are reported.

---

### User Story 2 - The build says how to print it (Priority: P2)

The two-pass procedure is not obvious, and getting it wrong wastes a stack of
paper. Today the build's closing line ends with `(8 pages, duplex, flip on long
edge)`. In simplex mode that sentence is wrong, and a bare page count is not
enough: the user needs the two page ranges and the re-feed step.

**Why this priority**: the PDF is useless without knowing how to feed it, but
the PDF has to exist first. Independently testable and independently valuable.

**Independent Test**: run the build with and without the flag and assert on the
closing line — it names the mode, and in simplex mode it names both page ranges
computed from the actual sheet count.

**Acceptance Scenarios**:

1. **Given** the 4-sheet demo deck, **When** built with `--sides simplex`,
   **Then** the closing line reports 8 pages, states that pages 1–4 are the
   fronts and pages 5–8 the backs, and says the stack is re-fed and printed at
   100 % scale.
2. **Given** the same deck built without the flag, **When** it finishes,
   **Then** the closing line still says `duplex, flip on long edge` — the
   wording existing tests assert on does not move.

---

### User Story 3 - `/print` offers it when the printer needs it (Priority: P3)

A user tells Claude "my printer only does one side". The `/print` skill passes
`--sides simplex` and, when it hands the PDF over, states the two-pass
instructions instead of the duplex ones. A user who says nothing about their
printer gets today's duplex build and today's instructions.

**Why this priority**: the flag is usable by hand without it; this makes it
discoverable through the pipeline the project is actually built around.

**Independent Test**: the docs gate. A documentation or skill line that states
the printing instruction as an unconditional fact ("duplex, flip on long edge"
as *the* way to print) is wrong once a second mode exists — exactly as
"8 cards per page" became wrong once `--grid` existed. `scripts/check_docs.py`
fails on such a line until it is qualified by the mode it belongs to.

**Acceptance Scenarios**:

1. **Given** the repo as it stands today, **When** the new docs gate runs,
   **Then** it fails, naming every line that states duplex as the only
   printing instruction (`README.md`, `docs/workflow.md`,
   `skills/print/SKILL.md`, `docs/index.html` is out of the gate's scope but in
   the sweep).
2. **Given** those lines rewritten to name the mode they describe, **When**
   `python3 scripts/check_docs.py` runs, **Then** it exits 0.
3. **Given** `skills/print/SKILL.md`, **When** a user's message says their
   printer prints one side only, **Then** the skill's documented behaviour is
   to pass `--sides simplex` and to report the two page ranges the build
   printed.

---

### Edge Cases

- **Missing optional tooling**: unchanged — this feature adds no tool. Without
  a typesetting engine the build fails exactly as it does today, before the
  flag matters.
- **Fresh install on each platform**: page order is decided in Python and
  Typst; nothing platform-specific. Verified on macOS and Linux in CI, Windows
  by hand.
- **Python floor**: 3.12, no new dependency.
- **Encoding and file names**: untouched.
- **Non-Latin card text**: untouched — the same cards are rendered, in a
  different page order.
- **Idempotence**: two builds with the same flag give the same page order;
  dropping the flag returns the duplex order with no leftover state.
- **Text that does not fit**: the overflow warning is computed per card and is
  independent of page order — the same cards warn in both modes.
- **A card language nothing can hyphenate**: untouched.
- **A simplex PDF sent to a duplex printer**: the faces land on the wrong
  sheets. The build cannot detect this; the closing line and the docs are the
  only defence, which is why User Story 2 is P2 and not optional.
- **A printer that stacks face-up**: the second pass then needs the back range
  printed in reverse page order. Every common print dialog (Preview, Acrobat,
  CUPS, Windows) offers "reverse order", so this is documented rather than
  built — see Assumptions.
- **A partly filled last sheet**: the last front page and the last back page
  hold the same number of cards, so the two halves are always equal in length
  and the page count stays even. No blank padding page is introduced.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `lernkarten build` command MUST accept a print-order option
  with two values — duplex (interleaved, today's behaviour) and simplex (all
  fronts, then all backs) — defaulting to duplex.
- **FR-002**: In simplex mode the command MUST emit, for a deck occupying N
  sheets, exactly 2 × N pages: pages 1…N the front of sheets 1…N in order, and
  pages N+1…2N the back of sheets 1…N in the same order.
- **FR-003**: The command MUST apply the identical column mirroring to back
  pages in both modes, so a back sits behind its front after the stack is
  turned about the long edge, at every supported grid.
- **FR-004**: The command MUST leave the page *count* unchanged between modes
  for the same cards and grid, so `2 × ⌈cards ÷ (columns × rows)⌉` remains the
  page-count rule the docs and the skill state.
- **FR-005**: The command MUST reject an unrecognised print-order value as a
  usage error, exiting 2 and naming the accepted values, before reading card
  files — matching how an unrecognised `--grid` is handled.
- **FR-006**: The command's closing line MUST name the print order it produced.
  In simplex mode it MUST state both page ranges (fronts and backs) computed
  from the actual sheet count and the re-feed step; in duplex mode it MUST keep
  today's wording.
- **FR-007**: The command MUST accept the option together with `--check`,
  `--grid`, `--margin`, `--topic`, `--subtopic`, `--language` and `--no-logo`
  without changing what any of those do.
- **FR-008**: Without the option, the command MUST produce the same page order
  as before this feature — no existing project changes behaviour, and no card
  file needs editing.
- **FR-009**: The `print` skill MUST pass the simplex value when the user says
  their printer prints one side only, and MUST otherwise pass nothing.
- **FR-010**: The `print` skill MUST state the printing instructions that match
  the mode it built: the two-pass ranges and re-feed for simplex, duplex/flip
  on long edge for duplex. The cutting instructions are identical in both.
- **FR-011**: `scripts/check_docs.py` MUST fail on any tracked markdown or
  skill line that presents a duplex printing instruction as the only way to
  print, unqualified by the mode — the same shape of gate as
  `check_sheet_capacity`, and for the same reason (a hand grep already let two
  stale claims ship once).
- **FR-012**: The print order MUST be a property of the print run, not of a
  deck: no key is added to `cards/*.yaml`, and no card file can declare it.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | none — the print order is a run-time choice, never a deck key (FR-012) | — |

**Backwards compatibility**: complete. Every existing project builds the same
PDF from the same command; the new option is opt-in and the default path is
byte-for-byte the old one. Nothing to migrate.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: none of the card, the press sheet layout, the
  mark or the README graphics. Only the *order of pages* in the output PDF, and
  the printing instructions in `README.md`, `docs/workflow.md`,
  `docs/design.md`, `docs/testing.md`, `docs/index.html` and
  `skills/print/SKILL.md`.
- **Black-only laser print still readable**: N/A — nothing visible changes.
- **Minimum type size respected**: N/A.
- **Brand PNGs need re-rendering**: no.
- **Duplex alignment unaffected**: yes. The default path is unchanged, and the
  simplex path reuses the same mirrored back sheets — it only moves them within
  the document. `docs/testing.md` gains a second physical check (two-pass
  simplex) beside the existing duplex one, because page order is the one thing
  no automated test can prove on paper.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. Page order
  is decided where the pages are generated; no PDF post-processing library is
  needed, and reaching for one would add a runtime dependency the project
  cannot ship today.
- **New runtime dependency**: none.
- **New dev dependency**: none. The end-to-end assertions read the PDF the same
  way `tests/test_e2e.py` already does.
- **New external binary**: none.
- **Anything this makes redundant**: none.
- **Engine version change**: no.
- **Platforms verified**: macOS and Linux in CI; Windows by hand. The physical
  two-pass print is a manual check on one printer, recorded in
  `docs/testing.md`.

### Key Entities *(include if the feature involves data)*

- **Sheet**: one physical piece of paper carrying up to `columns × rows` cards.
  It has exactly two faces — a front page and a back page. A build produces
  N sheets; the print order decides only *where in the document* those 2 × N
  faces appear.
- **Print order**: how the 2 × N faces are sequenced. *Duplex* = front, back,
  front, back … (the printer turns the sheet). *Simplex* = all N fronts, then
  all N backs (the user turns the stack).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any deck and any supported grid, the simplex build and the
  duplex build have the same page count, and the simplex build's first half
  contains only fronts while its second half contains only backs — verified
  automatically over at least one multi-sheet deck at each grid.
- **SC-002**: The card printed at position p of front page n is the card whose
  back is printed at the mirrored position of page N + n, for every card in a
  multi-sheet deck — checked automatically, not by eye.
- **SC-003**: Running the build with no new flag produces the same page order,
  page count and closing line as the release before this feature, and the whole
  existing end-to-end suite passes without any assertion being rewritten.
- **SC-004**: The build's closing line in simplex mode names two page ranges
  that add up to the reported page count — checked at a one-sheet deck (topic
  filter), the 2-sheet `--grid a8` build and the 4-sheet `a7` build of the demo
  project.
- **SC-005**: A physical two-pass print of the demo deck on a one-sided printer
  at 100 % scale puts every back exactly behind its front — recorded as a check
  in `docs/testing.md` beside the existing duplex one.
- **SC-006**: `python3 scripts/check_docs.py` fails on the repository as it
  stands today (naming at least the three known unqualified duplex claims) and
  exits 0 once every printing instruction names the mode it belongs to.
- **SC-007**: A user who has never printed with this tool can go from
  `lernkarten build --sides simplex` to a stack of correct cards using only the
  build's closing line and `README.md`, without opening the source.

## Assumptions

- **The option is a command-line flag on `build`, spelled `--sides` with the
  values `duplex` (default) and `simplex`.** The exact spelling is a naming
  choice open to the plan; what the spec fixes is that it is one print-run
  option with a duplex default, not a deck key (FR-012) and not a separate
  subcommand.
- **One PDF, not two.** The user asked for "all fronts and then all backs",
  which is one document read in two passes. Two files (`…-fronts.pdf`,
  `…-backs.pdf`) would add an output-naming contract and a second `-o`
  question for no gain, since either way the user starts two print jobs.
- **The stack is turned about the long edge between passes**, the same axis a
  duplex printer uses with "flip on long edge". That is what makes the existing
  column mirroring correct in both modes, and it is what the instructions tell
  the user to do.
- **Printers that stack face-up are handled by the print dialog**, not by the
  build: the user prints the back range in reverse order using the option every
  common dialog already has. A `--reverse-backs` build flag is deliberately out
  of scope; if the manual check (SC-005) shows the dialog route is not enough,
  it becomes its own feature.
- **The page-count rule stays `2 × ⌈cards ÷ (columns × rows)⌉`** in both modes,
  so the skill's existing "the page count must be even" check and the docs
  around it need no arithmetic change.
- **The demo project already carries enough material**: its 29 cards fill 4
  sheets at `a7` and 2 at `a8`, and a topic filter cuts a single-sheet deck out
  of it, so this feature needs no new fixture — only new assertions.
- **`docs/index.html` is prose the docs gate does not read.** It states the
  duplex instruction today and has to be updated by hand in the same change;
  the gate covers the markdown and the skills.
