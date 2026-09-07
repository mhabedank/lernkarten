# Phase 0 Research: Leitner compartments

Three unknowns went into the first pass. Two were named by the spec as
plan-level decisions; the third was found while reading the code the feature
has to change, and it reorders the work.

**Revised 2026-09-07** after the cross-model review returned NOT READY
([reviews/2026-09-07-not-ready.md](./reviews/2026-09-07-not-ready.md)). R1's
*derivation* survived the review's own recomputation; its *premise* did not, and
the fix moved dividers out of the card grid entirely. R6–R8 are new and come
from the review.

---

## R1 — How wide is the colour band?

**Decision**: the band is **4 mm wide** measured inward from the nominal cut
line, and it **bleeds 3 mm outward** past it. Both scale with `card_scale`, so
the divider keeps its proportions at any grid the way every other part of the
card does.

**Rationale**: FR-006 fixes the property, not the number — colour must still
reach every cut edge when the back face is displaced by 2 mm. Turning that into
a width needs the second error term the spec did not name: the cut itself.

Let the band run from the cut line inward by `W` and outward by `B`. Let `δ` be
the front-to-back registration error (spec: up to 2 mm under hand-fed simplex)
and `e` the cut error against the nominal line (±1 mm is what a ruler and a
craft knife achieve; a guillotine does better).

On the displaced face the band covers `[cut − B + δ, cut + W + δ]`. The actual
cut lands at `cut + e`. For it to fall inside the band for every combination:

```
worst case  e = +1, δ = −2   ⇒   +1 ≤ W − 2   ⇒   W ≥ 3
worst case  e = −1, δ = +2   ⇒   −1 ≥ −B + 2  ⇒   B ≥ 3
```

So 3 mm is the floor on both, and 4 mm inward is the first round number above
it — one millimetre of headroom for a worse-than-assumed registration, at a
cost of 1 mm of the 50 mm card face. The bleed stays at its floor of 3 mm; the
gap between two dividers is then `2 × 3` plus 2 mm of cut tolerance, which is
where the **8 mm minimum gap** in FR-004 comes from.

*(The review recomputed this independently and confirmed both the algebra and
the choice of worst cases. It also noted the consequence: on the worst edge of
the displaced face the visible band is `4 − 2 − 1 = 1 mm`. That is thin but it
is colour, which is all FR-006 asks for.)*

**Alternatives considered**:

- *A hairline rule at the edge.* Fails the arithmetic outright: any `W` below
  3 mm leaves white on one edge of one face at the stated tolerances.
- *A fixed 5 mm.* Buys nothing the fourth millimetre does not, and eats more of
  a face that also has to carry a numeral, an interval and a rule line.
- *Deriving W from `margin`.* Tempting, because the bleed is already bounded by
  the margin — but it would make the ink area of a divider depend on a flag
  about the user's printer, which is the coupling `build_pdf.py:53-59` already
  argues against for `sides`.

### ~~The bleed forces FR-004 to be tightened~~ — superseded, and why

**Superseded on 2026-09-07.** What follows was the first pass's reasoning. It is
kept because the *problem* it identified is real and the replacement has to
solve it too — but the mechanism it chose was wrong, and the review found out
why before any code was written.

The error was one of scope. This section worried about the bleed landing on a
**card** and tightened FR-004 to keep cards away. It never asked what happens
between **two dividers**, and in a 4-column grid four dividers share three
vertical cut lines *with each other*. Both neighbours bleed 3 mm across every one
of them, and `templates/cards.typ:67-72` paints in enumeration order, so divider
1 would carry a 3 mm yellow strip on its right edge, 2 a blue one, 3 a black one.
**No band geometry fixes it: two colours cannot both bleed past one line.**

The resolution is to stop treating a divider as a grid cell at all — see R6.
With free placement nothing is ever adjacent to a divider, so FR-006 regains an
unconditional guarantee and a test can assert *the divider's own* colour rather
than merely that some colour is present. The `--margin 0` fallback disappears
with it: the bleed now lives in the block's own gaps, not in the page margin.

<details><summary>The superseded reasoning, verbatim</summary>

#### The bleed forces FR-004 to be tightened

A 3 mm bleed runs outward on **all four** edges, and FR-004 only guarantees that
the divider's own row is card-free. The row *above* it may hold cards: at 16 up,
a sheet carrying 12 cards has rows 1–3 full and row 4 empty, so a divider in
row 4 would bleed 3 mm of red onto the bottom edge of the card directly above
it — on a real card, after cutting, unrecoverable.

Skipping the upward bleed does not save it. The top edge is the one the user
actually looks at, because the cards stand on their long edge and the box is
looked into from above; with no bleed there, a back face displaced 2 mm downward
leaves 2 mm of white along exactly that edge.

**Decision**: FR-004 is tightened to *"the divider's row **and the row above it**
hold no cards"*. Cards fill top-down, so this costs nothing whenever a sheet is
at most half full — the case that motivated putting dividers in the card PDF at
all — and it changes nothing for the demo project, which pays for a fresh sheet
either way. It is a change to an acceptance criterion and is flagged as such
rather than absorbed silently.

**Alternatives considered**: *dividers always take a sheet of their own* — makes
the rule trivially safe and trivially testable, but throws away the paper saving
outright; *bleed sideways and down only* — leaves the most visible edge as the
one without tolerance.

</details>

---

## R2 — Where does the single source for the interval strings live?

**Decision**: a new leaf module **`scripts/leitner.py`**, holding the interval
sets and the rule lines as plain data and importing nothing local.
`build_pdf.py` imports it and writes the strings into `cards.json`;
`check_docs.py` imports it and asserts `docs/leitner.html` carries exactly those
strings.

```
deps, engine, leitner      ← leaves, import nothing local
yamlio                     → deps
cardid                     → yamlio
figures                    → deps
settings                   → yamlio          (new)
build_pdf                  → cardid, engine, yamlio, leitner, settings
check_project              → build_pdf, cardid, yamlio
check_docs                 → yamlio, leitner
```

**The constitution's copy of this graph is stale.** `constitution.md:256-266`
omits `cardid` and `figures`, both of which exist and are imported today —
verified by reading the import statements, not the document. Principle VI's own
governance rule says a rule that no longer traces to the codebase "is stale and
should be removed, not worked around", so **T012 asserts the real graph** and the
constitution's table is corrected as a separate docs change. Writing the test
against the documented graph would make it pass while the repository disagrees
with it, which is the failure mode the principle exists to prevent.

**Rationale against Principle VI**: `leitner` is a new leaf, so it adds two
edges and no cycle. `settings` is *not* a leaf — it sits one level above
`yamlio`, and calling it one (as the first plan did) was a contradiction in
terms. The graph's rule — "whatever sits at the bottom must stay a
leaf" — is satisfied by construction, because a table of strings has nothing to
import.

**Rationale against Principle XI**: this is what makes FR-017 assertable at all.
The check is bidirectional and both halves can be seen failing before the code
exists: every string in `leitner.INTERVALS` appears in `docs/leitner.html`, and
the page contains no interval-shaped string that is not in the module. A page
that drifts fails `check_docs.py`, which is already one of the four gates.

Passing the strings through `cards.json` rather than through `sys.inputs` also
avoids touching `templates/cards.typ`'s input contract: a divider entry simply
carries its own text, the way a card entry carries `front` and `back`.

**Alternatives considered**:

- *A shared data file (YAML/JSON) read by both.* Equivalent in effect and one
  more file to keep in sync with nothing enforcing it — and it would need
  `yamlio`, making `leitner` a non-leaf for no gain.
- *Constants in `build_pdf.py`, imported by `check_docs.py`.* No cycle either
  (`check_project` already imports `build_pdf`), but it drags `engine` into the
  docs gate's import path, which today runs without ever touching the engine.
- *Passing the strings as `sys.inputs` to Typst.* Widens the template's input
  contract for data that is per-divider, not per-run.

---

## R3 — The crop marks are wrong at A8 *(found, not asked)*

**This is a shipped defect, it is not caused by this feature, and this feature
cannot be built correctly on top of it.**

`templates/cards.typ:48-61` writes the sheet size into the crop-mark loops as
literals:

```typst
place(dx: x, dy: 297mm - margin, line(end: (0mm, arm), stroke: stroke))   // line 54
place(dx: 210mm - margin, dy: y, line(end: (arm, 0mm), stroke: stroke))   // line 59
```

`297mm` and `210mm` are A4 **portrait**. But the same file computes the page
from `sheet-w` / `sheet-h`, which `scripts/build_pdf.py` sets to a **landscape**
A4 for the 4 × 4 grid — because a flashcard is landscape and every A-series
halving flips the orientation. At `--grid a8` the page is 297 mm wide and
210 mm tall, and the two literals are then simply the wrong axis.

**Verified, not inferred.** `lernkarten build cards/example.yaml --grid a8`
was run and the crop-mark segments recovered from the PDF content stream
through their transformation matrices:

| | measured | expected |
|---|---|---|
| vertical marks, x | 14.2 · 217.6 · 420.9 · 624.3 · 827.7 pt ✓ | the same |
| vertical marks, y | 581.1 pt and **−240.9 pt** | 581.1 and 14.2 |
| horizontal marks, x | 5.7 pt and **581.1 pt** | 5.7 and 827.7 |

Page box is 841.89 × 595.28 pt. So on every A8 sheet:

- the five **bottom** crop marks are drawn at y ≈ −241 pt — off the paper, lost;
- the five **right-edge** marks are drawn at x = 581.1 pt, a ghost column
  standing in the middle of an 841.9 pt-wide sheet instead of at its edge.

No test covers crop marks at all, which is why it survived #23 and #003.

**Why it blocks this feature.** The divider grows 1.5 mm downwards, so its cut
line is *below* the bottom card row's — the bottom crop mark is precisely the
line the user cuts to, and at A8 it does not exist. Building the divider first
would mean shipping a card that can only be cut accurately by measuring.

**Decision**: fix it **first**, in its own change, test-first — replace the two
literals with `sheet-h` and `sheet-w`, and add the assertion that was missing.
It is independently valuable (every A8 print today is affected), it is a
one-line-per-axis fix, and it is a `fix/` not a `feat/`. #84 raises the stakes
further by making A8 the default grid.

**Alternatives considered**:

- *Fold it into this branch.* It would work, but it buries a user-facing bug
  fix inside a feature PR and delays it behind four more phases of work.
- *Work around it in the divider template.* Draws correct marks for dividers
  while cards keep the broken ones on the same sheet. Rejected: two rules for
  one sheet, and the bug stays.

---

## R4 — Does the demo project already carry the material?

**Decision**: yes; no fixture is added.

31 cards at `--grid a8` (16 up) fill sheet 1 and leave 15 on sheet 2 — rows 1–3
full, three cards in row 4. Under R6 that leaves far less than the 2.44 free rows
a two-row block needs, so it is exactly the "dividers open a further page" case,
and it makes SC-001's page count (6 with dividers, 4 without) a real assertion
rather than a contrived one.

The complementary case — a sheet with enough free height for the block — is
reachable from the same corpus by building a subset of the deck, so it needs no
new cards either (Principle XI: extend the demo project, never start a second
corpus).

---

## R5 — Is anything here a job for a library?

**Decision**: no dependency is added, and nothing is hand-rolled that a library
does.

- **Rendering the divider** is Typst, the engine this project already pins.
- **Reading and writing `lernkarten.yaml`** is `scripts/yamlio.py` over PyYAML —
  already the project's only runtime dependency.
- **`output/box.pdf`** is `shutil.copyfile`. This is the whole reason the spec
  refuses to merge the box into the card PDF: merging would need a PDF library,
  and a file copy needs nothing. Constitution III asks whether a library should
  do the job; here the standard library already does it in one call.

---

## R6 — Where the divider block goes *(new, 2026-09-07)*

**Decision**: dividers leave the card grid. They are free-placed as one block,
**full card width, laid out by `LAYOUT = {3: (3,), 4: (2, 2)}`, minimum 8 mm
cut-line-to-cut-line gap** on every side,
positioned in the free area below the cards where the block fits and on a
further page where it does not.

**Rationale**: R1's superseded section shows why they cannot stay in the grid —
adjacent cells share a cut line and two colours cannot both bleed across it. Once
they are free-placed, nothing is ever adjacent, and three requirements that only
existed to work around the grid disappear: the "row above must be card-free"
tightening, the `--margin 0` fallback, and the downward-only growth direction.

**The arithmetic**, at A8 — print area 287 × 200 mm, divider 71.75 × 51.5 mm,
gap 8 mm (3 mm bleed each side plus 2 mm of cut tolerance):

| | Block size | Height incl. gaps | Free card rows needed | Shares a sheet when |
|---|---|---|---|---|
| 3 dividers, one row of 3 | 231.25 × 51.5 mm | 8 + 51.5 + 8 − 5 = 62.5 mm | **1.25** | the last sheet uses ≤ 2 rows |
| 4 dividers, two rows of 2 | 151.5 × 111 mm | 8 + 111 + 8 − 5 = 122 mm | **2.44** | the last sheet uses ≤ 1 row |

*(Corrected in the second review pass: the first version divided the bare block
height by 50 and ignored the 8 mm above it and the 8 mm to the paper edge below.
The "shares when" column was right either way, but 1.1 and 2.2 were quoted in
four places as if they were the criterion.)*

**Four dividers cannot share one row.** `4 × 71.75 = 287.00 mm` is *exactly* the
print width, so any gap at all overflows it. That single number is what forces
the two-row arrangement, and it is why the block shares a sheet less often than
the first design promised.

The demo project (31 cards → three-and-a-bit rows on sheet 2) opens a further
page either way, so SC-001 stays at 6 pages against 4 — recomputed independently
by the review.

**Alternatives considered**: *narrower dividers (~68 mm) so four fit one row* —
halves the free height needed and would share a sheet far more often, but a
divider 4 mm narrower than the cards sits recessed in the box, and spanning it
like a card is what makes the coloured top edge readable at a glance;
*a blank grid cell between dividers* — only two fit per row and only a bottom row
can grow, so half the dividers would lose the 1.5 mm ridge.

## R7 — The build has six places that assume every record is a card *(new)*

**Decision**: keep the authored **card list** and the padded **record list**
separate all the way to the engine. `pages()` and the `cards.json` writer take
records; everything that reads a card's fields takes cards.

**Verified by reading, not assumed** — every one of these breaks on a divider:

| `scripts/build_pdf.py` | What it does | How it breaks |
|---|---|---|
| `:408` `advise_about_ids` | `c["id"]` | `KeyError` — a divider has no id (FR-008) |
| `:423` `main_language` | `Counter(c["language"] …)` | `KeyError` |
| `:461` `payload` | `LANGUAGES[c["language"]]` | `KeyError` |
| `:538` `offending_card` | typesets each record *as a card* | renders a divider through `card.typ` |
| `:713` `page_count = pages(len(cards), grid)` | counts the list | wrong once the list is padded |
| `:714` `{c["language"] for c in cards}` | the closing line | `KeyError` |

This is the difference between a feature that works and one that fails with the
`KeyError`-class errors Principle XI explicitly refuses to accept as "red". The
tasks name all six.

## R8 — SC-005 cannot mean "byte-identical" *(new)*

**Decision**: the guarantee is **`cards.json` byte-identical** plus **PDF
page count, page size and card placement unchanged**, baselined against `main`
*after* the crop-mark prerequisite.

**Rationale**: `tests/test_e2e.py` already records that the engine stamps a
`CreationDate`, so two builds of identical input differ in bytes **today**. The
build passes no `--creation-timestamp` and sets no `SOURCE_DATE_EPOCH`; without
one of those, no byte comparison of any PDF is possible at all. The first pass
asserted byte-identity across five configurations without checking whether
byte-identity was achievable.

Two further reasons the old wording could not hold: the prerequisite
**deliberately changes** the A8 bytes by moving the crop marks, so "the previous
release" is the wrong baseline; and the quickstart proposed obtaining the
reference with `git stash`, which pytest cannot do.

`cards.json` *is* comparable today, and the absent-means-`card` rule for `kind`
is what makes it so. That is the load-bearing half of the guarantee and it stays.

**Alternatives considered**: *make the build reproducible first* (pass
`--creation-timestamp` from `SOURCE_DATE_EPOCH`) — genuinely worth doing and it
would make byte-identity real, but it is a second independent change to the build
and belongs in its own PR, like the crop marks.
