# Implementation Readiness Checklist: Configurable press-sheet grid

**Purpose**: Validate that the requirements for this feature are complete, unambiguous and measurable enough to implement without guessing — walked by the reviewer before implementation starts, and again before merge
**Created**: 2026-08-19
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [research.md](../research.md) · [contracts/cards-yaml-grid.md](../contracts/cards-yaml-grid.md)

**Scope note**: this checklist tests the *requirements*, not the code — whether each risk area is pinned down in writing. Whether the implementation then behaves is Phase 9 (Verify) and the gates in [quickstart.md](../quickstart.md) §8. The one exception is the manual print gate, which no automated phase can reach; it has its own section at the end.

**Companion**: [requirements.md](./requirements.md) covers general specification quality (16/16). This file covers the twelve failure modes specific to *this* feature.

## The silent overflow trap (highest risk)

- [ ] CHK001 Is it stated that **both** the compile invocation and the `typst query <overflow>` invocation must receive the grid, rather than just "the build uses the grid"? [Clarity, Spec §FR-010]
- [ ] CHK002 Are all five threading sites enumerated somewhere an implementer will see them — `typeset()`, `overflowing()`, `offending_card()`, `report_failure()`, the page count? [Completeness, research.md §R6]
- [ ] CHK003 Is the *asymmetry* of the failure documented — that a missed grid in `overflowing()` leaves the PDF correct and every warning wrong, so no existing test fails? [Clarity, research.md §R6]
- [ ] CHK004 Is it recorded that the `overflowing.yaml` A8 test does **not** catch this alone, because that card overflows at both grids and is reported either way? [Ambiguity, Spec §SC-005]
- [ ] CHK005 Is the assertion that actually catches it — no demo card warns at A8 — marked as non-redundant so it cannot be dropped during review as duplicative? [Completeness, plan.md test #10]
- [ ] CHK006 Is the structural mitigation (one shared helper building the `--input` list, so the two call sites cannot drift again) stated as a requirement, or only as advice? [Clarity, data-model.md]

## Backwards compatibility

- [ ] CHK007 Is "absent `grid:` key means A7" stated as a hard requirement rather than a default that could be revisited? [Clarity, Spec §FR-012]
- [ ] CHK008 Is the no-flag-no-key case specified as producing output identical to the pre-feature build, and is "identical" defined (page count, card size, layout — or literally bytes)? [Measurability, Spec §SC-002]
- [ ] CHK009 Are the requirements clear that no existing card file needs migrating, and is that traceable to the optional-key decision? [Consistency, contracts/cards-yaml-grid.md]
- [ ] CHK010 Is there a requirement covering what happens if the supported set is ever narrowed and a deck on disk names a now-unsupported grid? [Edge Case, Spec §Edge Cases]

## Resolution precedence and conflict

- [ ] CHK011 Is the three-source precedence (flag → deck key → default) stated unambiguously, including that the flag wins even when the deck disagrees? [Clarity, Spec §FR-013]
- [ ] CHK012 Is the conflict case specified to name **both** files **and** both values, rather than just failing? [Completeness, Spec §FR-014]
- [ ] CHK013 Is the rationale for erroring rather than picking a winner recorded, so a reviewer does not "simplify" it to majority-wins? [Consistency, data-model.md]
- [ ] CHK014 Are requirements defined for the case where decks conflict **and** `--grid` is given — is it specified that the flag resolves it silently? [Coverage, Spec §US2 scenario 5]
- [ ] CHK015 Is it specified whether `grid:` is a top-level key only, and what happens if it appears on an individual card? [Gap, contracts/cards-yaml-grid.md]

## Refusal semantics

- [ ] CHK016 Are the two rejection classes distinguished in the requirements — malformed values versus well-formed-but-unsupported ones? [Clarity, Spec §FR-003, §FR-005]
- [ ] CHK017 Is it specified that the unsupported-grid message lists the supported set *with* A-series names, not just the raw grids? [Completeness, Spec §FR-003]
- [ ] CHK018 Is "no PDF is written or overwritten" stated for **every** failing path, including a pre-existing output file at the target path? [Coverage, Spec §FR-005]
- [ ] CHK019 Is case-insensitivity of grid values specified explicitly (is `A8` accepted, is `3X4` malformed or merely unsupported)? [Ambiguity, contracts/cards-yaml-grid.md]
- [ ] CHK020 Are the boundary values enumerated — `0x4`, `3x0`, negative — with the expected outcome for each? [Edge Case, Spec §US4 scenario 2]

## Acceptance criteria quality

- [ ] CHK021 Can each of SC-001 through SC-009 be objectively verified without judgement, except SC-007 which is explicitly manual? [Measurability, Spec §Success Criteria]
- [ ] CHK022 Is SC-005 stated as a fixed expectation (no demo card overflows at either grid) rather than a golden value someone must re-measure? [Measurability, Spec §SC-005]
- [ ] CHK023 Are the exact A-series dimensions at `--margin 0` specified numerically (105 × 74.25, 52.5 × 74.25) rather than as "DIN A7/A8"? [Clarity, Spec §SC-003]
- [ ] CHK024 Is the paper-saving claim quantified against a named corpus (29 demo cards, 8 → 4 pages) rather than stated as "half"? [Measurability, Spec §SC-001]

## Grid-aware card-style limits

- [ ] CHK025 Are the measured hard limits recorded with their provenance, so the numbers are traceable rather than folklore? [Traceability, research.md §R3]
- [ ] CHK026 Is it specified that `MAX_FRONT` and `MAX_BACK` become grid-dependent, and are the proposed A8 values (60, 160) marked as a tunable judgement within a measured range rather than as fixed requirements? [Clarity, research.md §R3]
- [ ] CHK027 Is the derivation of the A8 thresholds stated (they preserve "~2 lines / ~6 lines" at 46 % field width), so a future change can re-derive rather than guess? [Clarity, research.md §R3]
- [ ] CHK028 Is it specified that the A7 thresholds must not shift, so this feature does not silently re-tune existing behaviour? [Consistency, Spec §SC-002]

## Head-band label budget

- [ ] CHK029 Is the label budget specified per grid with its measurement basis (~53 chars A7, ~22 A8, uppercase, Jost 500 at 6 pt with 0.1 em tracking)? [Measurability, research.md §R4]
- [ ] CHK030 Is the pre-existing A7 clipping (11 of 38 shipped cards, today, in `main`) recorded as a known defect this feature surfaces but does not fix? [Completeness, Spec §Assumptions]
- [ ] CHK031 Is the decision *not* to redesign the head band stated explicitly, so a reviewer can tell a deliberate omission from an oversight? [Clarity, research.md §R4]
- [ ] CHK032 Are `head-h` (8.6 mm) and `foot-h` (6.2 mm) named as values this feature must leave untouched? [Consistency, data-model.md]
- [ ] CHK033 Is the new label check specified as a **warning** rather than an error, given that 29 % of shipped cards would trip it immediately? [Clarity, Gap]

## Test-first adequacy (constitution XI, non-waivable)

- [ ] CHK034 Does every one of the 17 planned assertions describe a state in which it can actually go **red** on the assertion, rather than erroring on a missing import? [Measurability, plan.md §Test plan]
- [ ] CHK035 Is it specified that the model-driven half's only acceptable red artifact is a `check_project.py` check plus a failing case in `tests/test_check_project.py`? [Clarity, Spec §US2 Independent Test]
- [ ] CHK036 Does each of FR-001..FR-020 map to at least one planned assertion, and is any FR with no assertion identified as such rather than silently unverified? [Coverage, Traceability]
- [ ] CHK037 Are the two new demo fixtures specified precisely enough to write — one deck declaring `grid:`, and a second declaring a *different* one? [Completeness, research.md §R5]

## Consistency across artifacts

- [ ] CHK038 Do spec.md, plan.md, contracts/cards-yaml-grid.md and quickstart.md agree on the supported set, the aliases, the default and the precedence rule? [Consistency]
- [ ] CHK039 Are the documents that must stop asserting one card size all enumerated — `docs/design.md`, `docs/testing.md`, `skills/print/SKILL.md`, `CLAUDE.md`, `cards/example.yaml`? [Completeness, Spec §FR-017..FR-020]
- [ ] CHK040 Is the constitution amendment (principles XVI and XVII, which both quote A7 as *the* card size) identified as in-scope for this PR? [Conflict, plan.md §Constitution Check]
- [ ] CHK041 Is it stated that the amendment changes only the quoted dimension and leaves every rule those principles state intact? [Clarity, plan.md §Complexity Tracking]

## Dependencies and assumptions

- [ ] CHK042 Is the "no new dependency" claim justified against constitution III, given that grid parsing is hand-rolled? [Assumption, plan.md §Reuse check]
- [ ] CHK043 Is the `scale = 1.0` invariant stated as non-negotiable and tied to the 11 pt floor, rather than as a current implementation detail? [Clarity, Spec §Assumptions]
- [ ] CHK044 Is "one PDF is one grid" recorded as a scope boundary rather than a limitation to be lifted later? [Clarity, Spec §Assumptions]
- [ ] CHK045 Is the A4-only assumption stated, so nobody reads `--grid` as the start of general paper-size support? [Clarity, Spec §Assumptions]

## The manual print gate (SC-007 — blocks the merge)

*The only section here that checks an outcome rather than a requirement, because no automated phase can reach it. Procedure is [quickstart.md](../quickstart.md) §9.*

- [ ] CHK046 Is the gate specified with pass conditions a person can apply without judgement calls — registration, cut size, box fit, label legibility? [Measurability, Spec §SC-007]
- [ ] CHK047 Is the trap recorded — that all 38 shipped cards exceed the A8 label budget, so **a short-label card must be printed alongside** or the legibility check is vacuous? [Coverage, quickstart.md §9]
- [ ] CHK048 Is it stated that a PDF viewer screenshot does not satisfy this gate? [Clarity, quickstart.md §9]
- [ ] CHK049 — **A8 sheet printed duplex on real card stock; every back sits behind its front**
- [ ] CHK050 — **Cut on the crop marks yields 50 × 71.75 mm cards, nothing clipped that should not be**
- [ ] CHK051 — **A cut card drops into a DIN A8 Lernbox**
- [ ] CHK052 — **A label within the ~22-character budget is complete and legible at 6 pt**
- [ ] CHK053 — **An over-budget label clips cleanly at the band edge without disturbing the layout**
- [ ] CHK054 — **Outcome recorded in the PR description**

## Notes

- Check items off as completed: `[x]`
- CHK001–CHK048 are requirements-quality questions: walk them **before** implementation. A "no" means the spec needs a sentence, not that code needs writing.
- CHK049–CHK054 are physical outcomes: they can only be walked **after** a build exists, and they block the merge.
- Traceability: 48 of 54 items carry a spec/plan/research reference or an explicit marker (89 %). The six without are CHK049–CHK054, the physical print outcomes — they trace to SC-007 as a group rather than individually.
- Highest-risk cluster is CHK001–CHK006. If only one section is walked carefully, walk that one — it is the only failure mode that is both silent and undetectable by the existing suite.
