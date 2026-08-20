# Specification Quality Checklist: Configurable press-sheet grid

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-19
**Updated**: 2026-08-19 (after `/speckit-clarify`)
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

**16/16 items passing** (was 15/16). The one previously-unchecked item —
"No [NEEDS CLARIFICATION] markers remain" — now passes: all three markers were
resolved in the clarification session of 2026-08-19 and the count is zero.

### What the clarification changed

Four questions were asked and answered. The first reversed the ticket's central
recommendation:

| # | Question | Answer |
|---|---|---|
| 1 | Which grids should `--grid` accept? | `2x4` (A7) + `4x4` (A8) — the only grids on A4 producing a card with a purchasable box. **`3x4`, the ticket's suggestion, is dropped.** |
| 2 | How does the target size reach `/cards`? | An optional `grid:` key in `cards/*.yaml`. The model-driven half is **in scope**. |
| 3 | Is the real-printer check a release gate? | Yes — A8 must be printed duplex and cut before merge. |
| 4 | What naming vocabulary? | `--grid COLSxROWS` canonical, `a7`/`a8` accepted as aliases. |

Consequences for the spec: the running example moved from 3×4 to A8 throughout;
the paper saving went from 25 % to **50 %**; requirements grew from 15 to 20 as
the format contract came into scope; and success criteria grew from 7 to 9, one
of which (SC-007) is a hard release gate that cannot be automated.

### Research finding that drove the reversal

Standard flashcard sizes are the ISO A-series, and A4 halves into them, so only
four grids land on a standard size at all. `2x4` is exactly **A7** — the current
card, which `docs/design.md` already documents as such — and `4x4` is exactly
**A8**, the next standard size down, with widely-sold Lernboxen for both. The
ticket's `3x4` (70 × 74.25 mm) matches nothing purchasable. Sources are cited in
the spec's Clarifications section.

### Note on "no implementation details"

This item stays checked despite the spec naming files such as
`scripts/build_pdf.py` and `templates/cards.typ`. That is required by *this
project's* spec template, whose mandatory "Format Contracts" and "Scope in the
Pipeline" sections ask which files carry each of the five formats. It is
structural bookkeeping demanded by the template, not implementation leaking in.

### Carried forward from Phase 1

Issue #23 says "the 31 demo cards"; the demo project holds **29**
(`DEMO_CARD_COUNT = 29`, `tests/test_e2e.py:25`), the figure having come from two
stale comments in that file at lines 78 and 230. Page counts are unaffected at
every grid considered, so the ticket's measurements stand. Recorded in the spec's
Assumptions; the stale comments are worth fixing while this feature is in the file.

### Status

**Ready for `/speckit-plan`.** No blocking ambiguity remains. Two items the plan
must carry rather than rediscover:

1. **SC-007 is a release gate that blocks on hardware.** The plan needs to place
   the physical print check explicitly, not leave it implied.
2. **The A8 overflow set was measured in Phase 0, and it is empty.** All 29 demo
   cards fit at A8 despite the 46 % writing area — the corpus is short (longest
   back 154 characters against an A8 hard limit of 185). The assertion is
   therefore a fixed expectation — *no demo card overflows at either grid* — not
   a golden value anyone must re-measure. `overflowing-2` is still reported at
   both grids, so detection itself works.
