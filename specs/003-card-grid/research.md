# Phase 0 Research: Configurable press-sheet grid

**Feature**: `feat/card-grid` | **Date**: 2026-08-19 | **Spec**: [spec.md](./spec.md)

Everything below was **measured against the real engine** (Typst 0.15.1, cached
locally) by patching `columns`/`rows` in a copy of `templates/cards.typ` and
running the same `typst query <overflow>` the build runs. Nothing here is an
estimate unless it says so.

Two of the four findings **contradict assumptions written into spec.md**. Those
corrections are called out and must be applied to the spec.

---

## R1. Is a library needed for any of this? (Constitution III)

**Decision**: no library. Hand-roll the grid parsing.

**Rationale**: the whole parsing job is `"4x4".split("x")` into two ints, plus a
four-entry alias dict. Constitution III's own text names the legitimate
exception — "the need is a three-line slice of a library that would drag in
thirty packages" — and this is smaller than that. There is no category of
library for "parse two integers separated by an x".

**Alternatives considered**: none seriously. `argparse` type functions cover the
validation, and `argparse` is standard library and already in use.

**Consequence**: no new runtime dependency, no new dev dependency, no vetting
table needed under constitution IV.

---

## R2. Does the demo corpus overflow at A8?

**Decision**: **no — zero of the 29 demo cards overflow at A8.**

**This contradicts spec.md.** The spec's Assumptions say "Some demo cards are
expected to overflow at A8, since they were written for A7 and A8 has 46 % of
the writing area", and User Story 3 scenario 5 and SC-005 are written around
measuring that set. Measured, the set is empty.

| Grid | Demo cards (29) | Pages | Overflow reported |
|---|---|---|---|
| A7 (2 × 4) | 29 | 8 | none |
| A8 (4 × 4) | 29 | 4 | none |

`tests/fixtures/demo-project/broken/overflowing.yaml` reports `overflowing-2` at
**both** grids, so the detection mechanism itself works at A8 — the demo cards
simply fit. Their median back is 85 characters and their longest is 154; the A8
hard limit is 185 (see R3).

**Action required on the spec**:

- Delete the Assumption that some demo cards will overflow at A8.
- User Story 3 scenario 5 and SC-005 can be stated as the plain, stronger fact:
  *no demo card overflows at either grid, and `overflowing-2` is reported at
  both.* That is a better test than "matches the measured truth" because it is
  a fixed expectation rather than a golden value someone must re-measure.

**Rationale for why this is good news**: it means the paper saving is free for
the shipped corpus — the deck genuinely fits at half the area. It also removes
the "measure then encode a golden set" step the plan was going to need.

---

## R3. What is the real text capacity at each grid?

> **Retired 2026-08-20 — [BUG-007](./bugs/BUG-007.md).** Everything below was
> measured against a **portrait** A8 card, 52.5 × 74.25 mm. The corrected card
> is landscape and rendered at a uniform scale, so the two grids are
> proportionally identical. Re-measured through the real command, a back first
> overflows at **500 characters at A7 and 520 at the scaled A8** — the denser
> grid holds marginally *more*, because the scale takes the tighter of the two
> ratios and leaves about 3 % of width slack. The per-grid thresholds this
> section justified are gone (FR-027); `MAX_FRONT = 120` and `MAX_BACK = 400`
> now apply at both. Kept for the record.


**Decision**: measured by bisection on a single probe card, at the default 5 mm
margin.

| Field | A7 hard limit | A8 hard limit | A8 as % of A7 |
|---|---|---|---|
| `front` | 291 chars | 145 chars | 50 % |
| `back` | 455 chars | 185 chars | 41 % |

"Hard limit" = the character count at which the `<overflow>` marker first fires.

The existing warning thresholds in `scripts/check_project.py` sit below those:
`MAX_FRONT = 120` (41 % of the A7 hard limit) and `MAX_BACK = 400` (88 %). The
comment above them reads "Front at most ~2 lines, back at most ~6 — the card is
only 100 x 72 mm", so they encode *line counts*, not a fraction of the limit.

**Recommended A8 thresholds**, scaling by the 46 % field-width ratio so they
keep meaning "~2 lines" and "~6 lines":

| Constant | A7 (today) | A8 (proposed) |
|---|---|---|
| `MAX_FRONT` | 120 | **60** |
| `MAX_BACK` | 400 | **160** |

**Rationale**: at A8 the field is 43.2 mm wide against 93.2 mm, so a line holds
46 % as much. 120 × 0.46 ≈ 55 and 400 × 0.46 ≈ 185. 185 is *exactly* the A8 hard
limit, which would leave no room for the note rules or the source line, so the
back threshold is pulled back to 160. 60 for the front keeps a little headroom
over 55 while staying far below the 145 hard limit.

**Alternatives considered**: keeping one pair of thresholds for both grids —
rejected, because at A8 a 400-character back is more than twice the hard limit
and the warning would fire only after the card had already overflowed, which
makes it useless. Making the thresholds a pure fraction of the measured hard
limit — rejected, because the existing constants encode line counts and changing
their meaning would silently re-tune the A7 behaviour this feature must not
touch.

**Note**: these two values are a judgement call within a measured range. The
implementer may tune them; what is not negotiable is that they become
grid-dependent.

---

## R4. The head band clips, and it already clips today

> **Retired 2026-08-20 — [BUG-007](./bugs/BUG-007.md), and wrong on its own
> terms.** Two errors. The measurements are against the portrait card, whose
> label box was 41.4 mm; the corrected card scales, so the box is
> proportionally the same at both grids and there is no A8-specific budget.
> And the premise is false: the band **wraps** its label rather than losing the
> tail. Rendered at A7, a 55-character label is one line, 75 is two, 170 is
> three, and text is first lost at 221 characters where a fourth line is cut
> top and bottom. So loss begins near **200** characters, not 53, and the "11
> of 38 cards clip silently" claim below is not happening — those labels wrap
> and read fine. A label check may still be worth having for crowding, but it
> belongs to the card design at every size (constitution XVI), not to this
> feature. Kept for the record.


**Decision**: this is the real constraint on A8, and it is **pre-existing, not
introduced by this feature**.

The topic/subtopic label sits in a box of `cw − head-h` with `inset: (x: pad-x)`
and `clip: true`. Measured usable width and the uppercase-character budget at
Jost 500, 6 pt, 0.1 em tracking:

| Grid | Label box | Usable | Budget |
|---|---|---|---|
| A7 (2 × 4) | 91.4 mm | 84.6 mm | **~53 characters** |
| A8 (4 × 4) | 41.4 mm | 34.6 mm | **~22 characters** |

Measured against the 38 cards actually shipped in this repo (29 demo + 9 example):

| | Cards whose `TOPIC / SUBTOPIC` label exceeds the budget |
|---|---|
| At A7 — **today, already happening** | **11 of 38 (29 %)** |
| At A8 | **38 of 38 (100 %)** |

The shortest label in the corpus is 29 characters, which is already over the A8
budget of 22. The demo topics are long by design — `Kestrel Islands: Tides` is a
22-character topic before a subtopic is appended.

**This contradicts spec.md.** SC-007 requires that on a printed A8 sheet "the
head-band topic label is legible and not clipped on the demo topics". That is
**unachievable**: every demo label clips at A8, and a third of them already clip
at A7 on today's shipped cards.

**Action required on the spec**: restate SC-007. The honest gate is that a label
*within budget* is legible and complete, and that an over-budget label clips
cleanly at the band edge without disturbing the layout — not that the demo
corpus is clip-free, which it has never been.

**Decision on what to do about it in this feature**:

1. **Do not redesign the head band.** That is a card-design change under
   constitution XVI and it is a bigger question than this feature — the ticket
   itself says "the band design itself is up for discussion" at 16-up. It should
   be its own spec.
2. **Do add a grid-aware label-length check** to `scripts/check_project.py`,
   beside the existing `MAX_FRONT`/`MAX_BACK` warnings. This turns a silent
   truncation into a named warning, and — importantly — it is exactly the red
   artifact constitution XI demands for the `/cards` prompt change, which
   otherwise has nothing testable.
3. **Document the budget** in `CLAUDE.md` and `skills/cards/SKILL.md` so `/cards`
   writes short topic names for A8 decks. A real deck with topic `Statistics`
   and subtopic `Bayes` gives an 18-character label and fits A8 comfortably; the
   demo corpus is an unusually hostile case, not a typical one.
4. **Raise the pre-existing A7 clipping separately.** 11 shipped cards silently
   losing their label tail today is a real defect, but it is not this feature's
   to fix and folding it in would blur the change.

**Alternatives considered**: shrinking the label font at A8 — rejected, the type
floor in `docs/design.md` binds reading text and a 6 pt letterspaced label is
already at the small end. Wrapping the label to two lines — rejected, it would
change `head-h` and therefore the card design, which is item 1 above. Abbreviating
the topic automatically — rejected, silently rewriting the user's words is worse
than clipping them, and the check in item 2 makes the problem visible instead.

---

## R5. Does the demo project already carry the material this feature needs?

**Decision**: mostly, but two fixtures must be added.

Present and sufficient: 29 cards over six files including German, Greek and
Russian (so non-Latin label and hyphenation behaviour at A8 is covered), and
`broken/overflowing.yaml` for the overflow path.

**Missing, and needed** — per `CLAUDE.md`, a new failure mode belongs in the demo
project rather than a fixture of its own:

- a card file carrying `grid: a8`, to exercise the deck-declared default and the
  `--grid` override (FR-012, FR-013);
- a **second** card file declaring a *different* grid, so the conflict error
  (FR-014) has something to fire on. One file cannot conflict with itself.

Both are ordinary text and commit cleanly. Neither is a binary, so constitution
VIII is untouched.

---

## R6. Where does the grid have to reach?

**Decision**: five call sites, and missing any one of them is a silent bug.

`scripts/build_pdf.py` builds the `--input` list in two places, and three
functions call through to them:

| Site | Why it needs the grid |
|---|---|
| `typeset()` | the compile call — draws the PDF |
| `overflowing()` | the `typst query <overflow>` call — **decides which cards are reported** |
| `offending_card()` | calls `typeset()` per card to name a build failure |
| `report_failure()` | calls `offending_card()` |
| the page report | `CARDS_PER_PAGE = 8` stops being a constant |

**The trap**: `typeset()` and `overflowing()` each build their own `--input`
list. If the grid reaches the first but not the second, the build typesets A8
while checking overflow against A7 geometry. Every warning would be wrong, and
**no existing test would fail** — the PDF would be correct and the warnings
silently bogus. This is FR-010 and it is the single most important correctness
risk in the feature.

**Mitigation — corrected after cross-model review.** The original mitigation
here was wrong, and the correction matters more than the original finding.

This document first claimed that "no demo card warns at A8" catches the bug. It
does not. If `overflowing()` misses the grid, the query runs at the template
default of 2 x 4 — and the demo cards do not overflow at A7 *either* (R2). So the
query returns an empty set under **both** the correct and the buggy path, and an
assertion of *absence* cannot tell them apart. Re-measured against the engine to
confirm: `[]` at 2 x 4 and `[]` at 4 x 4.

Catching it requires an assertion of **presence**, via a card that fits A7 and
overflows A8. Measured: a ~300-character back gives `[]` at 2 x 4 and
`['mid-1']` at 4 x 4. That card becomes
`tests/fixtures/demo-project/broken/overflows-only-at-a8.yaml`, and the test
asserts it is reported at `--grid a8` and not at the default.

Beyond the test, the two `--input` lists should be built by one shared helper so
they cannot diverge again — that is the structural half of the fix, and it is
what makes the defect unlikely rather than merely detectable.

---

## R7. Constitution principles that state the card size as a fixed fact

**Decision**: this feature requires a constitution amendment, and that must be
planned, not discovered at review.

Two principles assert A7 as *the* card size:

- **XVI (Design rules)**: "The card is 105 × 74.25 mm landscape (A7), three bands
  that never move."
- **XVII (Card style)**: "Front at most ~2 lines, back at most ~6".

Both become one of two cases. Per the constitution's own Governance section,
"Amendments go through a pull request like anything else", so the amendment
rides in this PR alongside the `docs/design.md` and `CLAUDE.md` changes that FR-017
and FR-019 already require.

This is bookkeeping rather than a change of intent: the *rules* those principles
state — bands that never move, type never shrunk to fit, a card that does not fit
is reported — all survive intact. Only the single quoted dimension becomes two.
