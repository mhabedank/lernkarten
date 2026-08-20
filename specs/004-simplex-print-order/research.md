# Phase 0 Research: Simplex print order

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-08-20

The spec left no `[NEEDS CLARIFICATION]` markers, so this phase is not about
resolving unknowns in the requirement. It is about the four questions the plan
template asks of every feature here — is there a library, does Typst support
it, does the fixture suffice, what does the degraded path look like — plus the
one question this feature turns on: **where in the pipeline is a page order
decided, and can it be read back out of the finished PDF?**

---

## Decision 1 — The order is produced, not repaired

**Decision**: emit the pages in the requested order from `templates/cards.typ`,
driven by one more `sys.inputs` value. Do not touch the PDF after the engine
writes it.

**Rationale**: the pages do not need reordering; they need producing in a
different order. `cards.typ` already computes which cards go on which sheet and
already takes seven parameters (`margin`, `logo`, `columns`, `rows`, `sheet-w`,
`sheet-h`, `scale`). The page sequence is one line of that same computation. A
post-processing step would spend a dependency to undo work the generator was
about to do correctly.

The dependency question is not close. `pypdf`, `pikepdf` and `fitz` all reorder
pages in a few lines, and all three would be **runtime** dependencies — the
build path, not the test path. Constitution II allows dependencies, but the
project has no mechanism to deliver a runtime dependency to a plugin user
today, so a runtime dependency cannot ship at all. That alone ends it, before
the vetting table is reached.

**Alternatives considered**:

| Alternative | Why not |
|---|---|
| `pypdf` / `pikepdf` / `fitz` reorder after the build | Runtime dependency, undeliverable today (constitution II). Also slower and a second place page order lives |
| Two engine invocations — one for fronts, one for backs, concatenated | Needs the concatenation anyway, so it inherits the same problem, and doubles the typesetting cost |
| A second Typst template, `cards-simplex.typ` | Two copies of the sheet layout that must not drift. The thing that differs is four lines of pagination |
| Hand-write PDF page-tree surgery | Hand-rolling what a library does — the exact thing constitution III forbids. Rejected on principle, not on difficulty |

---

## Decision 2 — One list of faces, walked once

**Decision**: replace the `front / pagebreak / back` loop with a face sequence
computed up front, then a single loop that places a `pagebreak()` before every
face but the first.

**Rationale**: the naive change is to add an `if` around the existing loop body,
which gives two pagination code paths and two places for the last-page
`pagebreak()` bug to live. Computing the sequence first collapses both orders
into data:

```typst
#let sheets = range(0, calc.ceil(cards.len() / per-page))
#let order = if sides == "simplex" {
  sheets.map(i => (i, false)) + sheets.map(i => (i, true))
} else {
  sheets.map(i => ((i, false), (i, true))).fold((), (a, p) => a + p)
}
```

Two properties fall out rather than being maintained:

- **`mirror` is the same boolean as "this is a back page".** The existing
  `sheet()` already takes `mirror` as its third argument and the caller already
  passes `false` for fronts and `true` for backs. Making it one value means no
  ordering can desynchronise the mirroring from the face, which is FR-003 held
  by construction rather than by a test — though it is tested anyway
  (assertions 11 and 12).
- **Page count is `2 × sheets.len()` in both branches**, so `pages()` in
  `build_pdf.py` needs no change and the rule
  `2 × ⌈cards ÷ (columns × rows)⌉` is not implemented twice. FR-004.

**Typst notes**, both verified against the primitives already in the file:

- `.flatten()` must **not** be used for the duplex branch. It flattens deeply
  and would turn `((0, false), (0, true))` into `(0, false, 0, true)`,
  destroying the pairs. `.fold((), (a, p) => a + p)` concatenates one level.
- `sides` arrives as `sys.inputs.at("sides", default: "duplex")`, matching how
  every other parameter arrives. An absent input means today's behaviour, so an
  engine call that forgets to pass it cannot silently change a build — which
  matters because three call sites build engine arguments.
- No new Typst feature is used, so `scripts/engine.py` keeps its version and
  all six platform checksums (constitution XV).

**Alternative considered**: `range(0, 2 * n).map(k => (calc.quo(k, 2), calc.rem(k, 2) == 1))`
for the duplex branch. Correct and shorter, but it encodes "front, back, front,
back" as arithmetic on a page index, which is exactly the thing a reader has to
decode. The `map`/`fold` version says what it means.

---

## Decision 3 — The order is readable from the PDF, exactly

**Decision**: assert the page order against the finished PDF's text layer, not
against a mock or a byte comparison.

**Rationale**: this was the open risk when planning started — a page-order
feature whose acceptance criteria cannot be checked automatically would be
verified by eye, which is how the last two stale claims shipped. It turns out
the PDF already carries everything needed, in two independent forms:

1. **Which face a page is.** `templates/card.typ:96` prints
   `card.id + " · " + (if back { "2/2" } else { "1/2" })` in every card's
   footer. So a page is a front page exactly when every face mark on it reads
   `1/2`. That is the literal form of SC-001 — "the first half contains only
   fronts" — with no inference from geometry.
2. **Which sheet a page is.** The same footer carries the card id, and
   `card_grid_per_page()` in `tests/test_e2e.py` already reads the ids with
   their coordinates via `pdftotext -bbox-layout`, recovering the grid row by
   row. Comparing page `N + i` to page `i` gives SC-002 — every back sheet
   behind its own front — at any grid.

Byte comparison is not available and is not needed: the engine stamps a
`CreationDate`, so two builds of identical input already differ.
`test_the_a_series_alias_is_the_same_grid` already made this call and compares
layout instead.

**Consequence for the tests**: `card_grid_per_page` and the new
`face_marks_per_page` both need "words with coordinates, per page". Extract
`bbox_pages(path)` — the `pdftotext -bbox-layout` call plus its two skip
guards — and build both readers on it. Copying the guards would be
hand-rolling inside the test suite, and the two existing tests that assert the
guard *skips* (`test_a_pdftotext_without_bbox_support_skips_instead_of_blaming_the_pdf`,
`test_a_pdftotext_that_returns_bbox_xml_without_pages_also_skips`) keep working
against the extracted function.

---

## Decision 4 — The fixture already suffices

**Decision**: no new test material. `tests/fixtures/demo-project` is enough.

**Rationale**: 29 demo cards give 4 sheets at `a7` (8 pages) and 2 at `a8`
(4 pages), so both grids exercise a genuinely multi-sheet order — the case
where duplex and simplex differ. A `--topic` filter cuts a single-sheet deck
out of the same corpus for the degenerate case, where the two orders coincide
and the closing line must still say `page 1` rather than `pages 1-1`.

Constitution VIII and `docs/testing.md` both say a new failure mode belongs in
the demo project rather than in a fixture of its own; here not even that is
needed, because the failure mode is about *page sequence*, which any deck of
more than one sheet exhibits.

---

## Decision 5 — Degraded paths

| Missing | Behaviour | Where it comes from |
|---|---|---|
| No typesetting engine | The build fails before the flag is consulted, exactly as today | `engine.find()` runs before `typeset()` |
| No `pdftotext` | The new order tests skip; the build is unaffected | The guard already in `card_grid_per_page`, moved into `bbox_pages` |
| A non-poppler `pdftotext` (GitHub windows-latest) | Skip, naming the tool — not a failure blamed on the PDF | The second existing guard, same function |
| `sides` input not passed to the engine | Duplex, i.e. today's output | `sys.inputs.at("sides", default: "duplex")` |
| An old PDF built before this feature | Unaffected — nothing on disk records a print order | FR-012: the order is a property of the run |

---

## Decision 6 — The gate for the prompt half

**Decision**: the red artifact for the `skills/print/SKILL.md` change is a new
`check_print_order()` in `scripts/check_docs.py`, not a check in
`scripts/check_project.py`.

**Rationale**: constitution XI says a prompt change is verified through a
`check_project.py` check, because a prompt is normally verified by the shape of
the file it writes. This prompt writes no file — it runs a command and then
speaks. What can go stale is its *claim*: `skills/print/SKILL.md:65` currently
tells the model to state "duplex, flip on long edge" as the instruction, full
stop, which becomes false the moment a second order exists.

`check_docs.py` already reads `skills/*/SKILL.md` as one of its inputs
(`markdown_files()`), and already carries the precedent for this exact class of
staleness: `check_sheet_capacity` exists because a hand-written grep for the
`--grid` sweep missed "A4, 8 cards per page" in the `/print` description and
"puts 8 cards on an A4 page" in the README, and both shipped in v0.4.0. The new
check is the same shape, in the same file, for the same reason, and it fails on
the repository as it stands today — which is what makes it a red artifact
rather than a formality.

**Known limitation, accepted**: prose matching can false-positive on future
writing that mentions duplex in passing. Its neighbour has the same property
and has caused no trouble since v0.4.0; the cost of a false positive is naming
the mode in the sentence, which is what the gate is asking for anyway.

**Alternative considered**: no gate, and a careful sweep. Rejected on evidence —
that is precisely what shipped the two stale claims the neighbouring gate now
prevents.
