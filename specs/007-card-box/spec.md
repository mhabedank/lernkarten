# Feature Specification: Ship the card box as a download

**Feature Branch**: `feat/card-box`

**Created**: 2026-09-01 · **Revised**: 2026-09-01 (scope cut, see *History*)

**Status**: Draft

**Input**: GitHub issue #45 — "Nothing holds the cards once they are cut: no printable box template".

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/print`, and the landing page beside it.

The box already exists. It was designed, printed, folded and used, and it sits at
`assets/card-box.pdf`. The only thing wrong with it is that **nobody else can get
it**: it is untracked, `.gitignore` refuses it, and no page links it. This feature
publishes it. It does not rebuild it.

**Implementation half**:

- [x] **Model-driven** — one advisory sentence in `skills/print/SKILL.md`.
- [x] **Deterministic** — one `.gitignore` line, one link in `docs/index.html`,
      a `docs/design.md` section, and tests.
- [ ] **Both** *(in the sense of a seam)* — there is no seam; see Format Contracts.

**Who runs into this**: the user. They print, cut, and now have somewhere to put
the cards. Contributors do nothing with this artifact except not break the link.

## History

The first version of this spec required a Typst source (`templates/box.typ`), a
render script, byte-reproducible regeneration, and a geometry contract deriving
the box from the card size. **That scope was cut on 2026-09-01** as unnecessary
complexity: the box is finished, it does not need to change, and a project that
prints one A4 sheet does not need a build pipeline to produce it.

What that decision costs is written down in *Accepted Trade-offs* rather than
left to be rediscovered.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download the box (Priority: P1)

A user has printed and cut an A8 deck. They open the landing page, see the box
offered next to the printing step, click it, print it on card stock at 100 %,
cut, fold, glue, and put their cards in it.

**Why this priority**: it is the entire feature.

**Independent Test**: the file is tracked by git and reachable from
`docs/index.html`.

**Acceptance Scenarios**:

1. **Given** the repository as committed, **When** `git ls-files` is read,
   **Then** `assets/card-box.pdf` is in it. *(Red today: `.gitignore` line 43 is
   `*.pdf`, so the file cannot be committed at all.)*
2. **Given** `docs/index.html`, **When** it is parsed, **Then** it links
   `assets/card-box.pdf`, and the page is still one self-contained file with an
   unchanged set of external sub-resources.
3. **Given** the committed PDF, **When** its page geometry is read, **Then** it
   is one page, portrait, and A4 to within printing tolerance — so a user prints
   it without choosing a page range or an orientation. The exact millimetres are
   209.97 × 296.97; see SC-002.

---

### User Story 2 - Know before you print whether it fits your deck (Priority: P1)

The box takes an A8 card at the default margin. A user with the **default A7
deck** must learn that before they spend card stock and an hour on it.

**Why this priority**: equal first, and the one genuine risk this feature adds.
Publishing a box to everyone while it fits only the non-default grid is worse
than not publishing it, unless the constraint is stated where the download is.

**Independent Test**: the text sits next to the link, in the page source.

**Acceptance Scenarios**:

1. **Given** the landing page, **When** the box download is read, **Then** the
   text beside it names the grid it fits — `--grid a8` — and that it is for a
   deck printed at the default margin.
2. **Given** `docs/design.md`, **When** its box section is read, **Then** it
   states the same constraint and the card size in millimetres.

### Edge Cases

- **A user with an A7 deck** — the default. Mitigated only by the text beside the
  download (Story 2). The sheet itself cannot be corrected; see *Accepted
  Trade-offs*.
- **A user printing "fit to page"** — the sheet already carries a scale-check bar
  reading `check scale 50 mm · print at 100 %`, so this is handled by the
  artifact and needs nothing from this feature.
- **A deck printed at `--margin 0`** — its A8 cards are 74.25 mm wide against a
  73 mm opening and will not fit. Stated with the grid constraint.
- **Missing optional tooling, platforms, Python floor, encodings, idempotence** —
  not applicable. This feature adds no code path.

## Requirements *(mandatory)*

- **FR-001**: `.gitignore` MUST allow `assets/card-box.pdf` to be committed, by an
  explicit negation of the `*.pdf` rule in the shape of the existing
  `!cards/example.yaml` carve-out. The rule that keeps build leftovers out MUST
  otherwise stay intact.
- **FR-002**: `assets/card-box.pdf` MUST be tracked by git.
- **FR-003**: `docs/index.html` MUST link it from the section about printing, and
  MUST remain one self-contained file with an unchanged set of external
  sub-resources.
- **FR-004**: The text beside that link MUST name the deck the box fits — the
  **A8 grid at the default margin** — because the sheet does not say it and
  cannot be changed.
- **FR-005**: `docs/design.md` MUST gain a section describing the box: what it is,
  the card size and inner dimensions, the paper weight, and the grid constraint.
  Constitution XVI makes that document govern everything visible, and this is now
  a shipped visible artifact.
- **FR-006**: `README.md` MUST name the box where it describes what the project
  produces.
- **FR-007**: `skills/print/SKILL.md` MUST mention the box where it tells the user
  what to do with the cut cards. *(Run output — manual checklist, per XI.)*
- **FR-008**: The two places that justify the two grids as "a card you can buy a
  box for" — `scripts/build_pdf.py` and `docs/design.md`, *The press sheet* —
  MUST be corrected. One of those boxes is now one you print.

- **FR-009**: `.specify/memory/constitution.md` **Principle VIII** MUST be amended
  so its stated exception covers this artifact. VIII today reads: *"The one
  deliberate exception is the brand PNGs under `assets/`, which are committed
  because nobody should have to run a renderer to read the README."* The box
  earns an exception for a related reason — nobody should have to run a renderer
  to print a box either. The amendment MUST keep the rule itself intact:
  generated test material stays generated, and the exception stays a short,
  **named** list rather than becoming a general permission.
  - Without this, the repository carries a principle and a file that contradict
    each other, and every future review re-discovers it.
  - **The amendment MUST NOT claim this is the same case as the brand PNGs.** It
    is not, in the part that matters: the PNGs have Typst sources at
    `assets/brand/*.typ` and a render script, so they are committed for
    *convenience* and remain regenerable and reviewable as text. The box has no
    source at all. The PNG exception trades regeneration effort; this one gives
    up regenerability. Saying "the same logic" would misrepresent the precedent,
    and that misrepresentation is what the next source-less binary would cite.
  - The amendment MUST also acknowledge that **Principle IX** ("sources of truth,
    never generated artifacts") now has a standing counterexample, rather than
    leaving a reader to find it.
- **FR-009a**: The same amendment MUST name the **committed fonts**
  (`assets/fonts/*.ttf`, four files) in Principle VIII's exception list. They are
  committed binaries that the list does not mention, so the repository already
  contradicts VIII today — FR-009's own rationale applies to them verbatim, and
  fixing one contradiction while walking past the other would ship the claim
  "a short named list" as false.

**Explicitly out of scope**: a Typst source, a render script, regenerating the
PDF, deriving the box from the card size, an A7 box, and any change to the
artifact itself.

### Format Contracts *(mandatory)*

**No format change.** `sources.yaml`, `knowledge/**` frontmatter,
`catalog/topics.md` and the `cards/*.yaml` schema are untouched. Every project on
disk builds exactly as before. There is no seam between the halves.

### Print & Design Impact *(mandatory)*

- **Visible surfaces touched**: the landing page (one link and its caption), the
  README, `docs/design.md`. **The box artifact itself is not touched.**
- **Black-only laser print still readable**: yes — verified by inspection of the
  existing sheet, which distinguishes cut (solid), fold (dashed) and glue (tinted
  area plus the printed word), and carries a printed legend naming all three. No
  channel depends on colour, so constitution XVI already holds.
- **Minimum type size respected**: on the landing page, yes. On the sheet, as
  built.
- **Brand PNGs need re-rendering**: no.
- **Duplex alignment unaffected**: yes — nothing shared with the press sheet.

### Dependency & Portability Impact *(mandatory)*

- **Hand-rolling anything a library does?** No — no code is written.
- **New runtime dependency**: none. **New dev dependency**: none. **New external
  binary**: none. **Engine version change**: no.
- **Anything made redundant**: none.
- **Platforms verified**: not applicable — no executable path is added.

## Accepted Trade-offs

These follow from cutting the build pipeline. They are decisions, not oversights.

1. **The committed PDF has no source in this repository, permanently.** This is
   the real cost of the scope cut, and it is **settled rather than merely noted**:
   FR-009 amends constitution VIII so its stated exception covers the box, on the
   same logic that already covers the brand PNGs. The repository ends up with a
   rule it obeys, instead of a rule it contradicts.

   What stays true regardless: if the box ever needs to change, it changes in a
   design tool outside this repository, and no test can tell whether the result
   still matches what the docs claim about it.
2. **The sheet's own footer says `a4 landscape`, and the page is A4 portrait.**
   Measured: `/MediaBox 0 0 595.2 841.8`, no `/Rotate`. Without a source this
   cannot be corrected. The documentation beside the download says portrait, and
   is right.
3. **The sheet says `cards 70 × 49 mm`, a nominal.** The real A8 card at the
   default margin is 71.75 × 50 mm. Documentation carries the real figure.
4. **The box serves the A8 grid only, while A7 is the default.** Mitigated by
   FR-004 and FR-005, not by a second box.
5. **If the card geometry ever changes, the box silently becomes wrong.** Issue
   #45 warned about exactly this coupling and asked for a parameterised template
   to prevent it. Cutting that scope accepts the risk. Whoever changes `--grid`
   or the card size needs to know this file exists — which is what the
   `docs/design.md` section is for.

## Success Criteria *(mandatory)*

- **SC-001**: `git ls-files` includes `assets/card-box.pdf` — it is in the
  repository, not in one working copy.
- **SC-002**: The committed PDF is exactly 1 page, portrait, and A4 **within
  printing tolerance** — its MediaBox is `595.2 × 841.8 pt` (209.97 × 296.97 mm),
  a Quartz approximation of A4 rather than the exact 595.276 × 841.89 pt. Any
  assertion must allow that, or it can never pass.
- **SC-003**: A reader on the landing page reaches the download in one click from
  the section about printing.
- **SC-004**: The grid constraint is readable next to the download, without
  following a link.
- **SC-005**: No file in the repository still claims a deck's box is one you buy.
- **SC-006**: The four quality gates stay green, and each assertable requirement
  above has a test that failed on its assertion before the change.

## Assumptions

- The artifact at `assets/card-box.pdf` is correct and final. It was folded and
  used; this feature takes that as proven and does not re-test the geometry.
- A user has a printer that handles 160–250 gsm card stock, and scissors and glue.
- GitHub Pages does **not** serve the repository — the workflow assembles a `_site`
  holding `docs/index.html` and nothing else, so the PDF has to be copied into it
  explicitly (FR-003). An earlier draft of this spec assumed the opposite; it was
  wrong, and following it would have shipped a 404 as the feature's deliverable.
