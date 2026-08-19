# Pre-Implementation Review

**Feature**: Configurable press-sheet grid (`feat/card-grid`, specs/003-card-grid)
**Date**: 2026-08-20
**Review model**: Fable 5 · **Generating model**: Opus 5
**Artifacts reviewed**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/cards-yaml-grid.md, quickstart.md, both checklists, constitution.md — verified against templates/cards.typ, templates/card.typ, scripts/build_pdf.py, scripts/check_project.py, tests/test_e2e.py, tests/test_check_project.py, .github/workflows/ci.yml, the demo corpus, and the cached Typst 0.15.1 engine (measurements re-run, not taken on trust)

## Summary

| Dimension | Verdict | Issues |
|-----------|---------|--------|
| Spec-Plan Alignment | WARN | Plan and spec agree but share one inverted premise (SC-005); "exactly DIN A8" glosses ISO 216 rounding |
| Plan-Tasks Completeness | WARN | Untasked breakages: `test_check_project.py`'s `== 6`, `--grid` in the help-text test, stale header comments |
| Dependency Ordering | **FAIL** | Phase 3 implements before the US1/US3 red tests exist; T032's fixture placement invalidates the baseline |
| Parallelization Correctness | PASS | All three `[P]` groups genuinely disjoint, max-3 respected |
| Feasibility & Risk | **FAIL** | The mitigation for the feature's own named highest risk is provably non-detecting; two `--strict` CI collisions |
| Standards Compliance | WARN | Constitution XI met on paper but broken by task ordering; XVI/XVII amendment handling exemplary |
| Implementation Readiness | WARN | Unusually specific, but T028/T030/T032 contain factually wrong instructions; mixed `grid:` semantics unspecified |

**Overall**: **NOT READY**

## Critical findings

### C1 — The FR-010 trap detection is inverted (confirmed empirically, twice)

Plan test #10, SC-005, US3 scenario 5, research R6, quickstart §5, CHK004/CHK005 and tasks T028/T030 all claim "no demo card warns at A8" catches a grid that reaches the compile call but not the overflow query. **It cannot.** If `overflowing()` misses the grid the query runs at the template default (2 × 4) — and the demo cards do not overflow at A7 *either*. Measured at both geometries: **both return `[]`**. Under the exact bug being guarded against, T027 passes *and* T028 passes. T030's sabotage step would end in confusion, not confirmation.

An assertion of **absence** cannot catch this. Only an assertion of **presence** can, via a card that fits A7 and overflows A8.

**Verified fix**: a ~297-character back gives `[]` at 2 × 4 and `['mid-1']` at 4 × 4. Add it to `broken/`, assert the WARNING fires at `--grid a8` and not at the default, and retarget T030's sabotage at that test. Keep T028 as a regression guard — just stop calling it the trap-catcher.

### C2 — The `grid: a8` fixture lands in a globbed directory

T032 puts `tides-a8.yaml` in `tests/fixtures/demo-project/cards/`, which `CARDS` globs (test_e2e.py:24). Every no-flag `run("build", *CARDS)` then either conflicts and exits 1, or silently builds the whole corpus at A8. Either breaks T019, `test_build_writes_a_pdf_with_one_sheet_per_eight_cards` (test_e2e.py:79) and the `== 6` file-count assertion (test_check_project.py:330, untouched by T034). Quickstart is internally inconsistent on exactly this: §1 expects 8 pages from the unflagged glob, §7 expects A8 from the same glob.

Two fixes: **specify the mixed absent+declared case** (FR-014 covers only decks that both *declare*; one declared deck among silent ones is unwritten, and is the most likely real situation), and **move the declaring fixture out of the globbed directory**. T033's conflict deck in `broken/` is placed correctly.

### C3 — Two designed-in `--strict` collisions will turn CI red

CI runs `check_project.py tests/fixtures/demo-project --strict` (ci.yml:120), and `--strict` exits non-zero on **any** warning (check_project.py:696-697).

- **FR-015a / T043–T044**: the "deck does not record its size" warning fires on all six grid-less demo decks. FR-015a's "every existing project stays green" is false under `--strict` — which is how this repo checks its own demo project, and how gate T064 repeats it.
- **FR-023 / T042**: the A7 label-budget warning fires on 11 demo cards (3 in `palirroia-el.yaml`, 2 in `priliv-ru.yaml`, 6 in `tides.yaml`). Downgrading to a warning protects the non-strict gates only.

Resolve before implementing: scope the checks, give the demo decks explicit `grid:` keys, shorten the demo labels, or accept and document a `--strict` break. Any is defensible; silence is not.

### C4 — Red/green ordering violates constitution XI

Phase 3 (T013–T016) fully implements the flag, threading and template parameterisation *before* the US1 reds (T017–T021) and US3 reds (T027–T028) exist. T029 admits it: "If T013 and T014 were done properly they already do [pass]". A 🔴 task that cannot fail when scheduled is not test-first. CHK034 asks exactly this and, walked honestly, fails for assertions 8–10 and 13–14.

Fix by reordering: write the e2e reds before T014–T016, or shrink Phase 3 to the pure functions (T008–T012) and move threading into US1's green step.

## Warnings

1. **"Exactly DIN A8" overstates ISO 216.** Official A8 is 52 × 74 mm (the series rounds down); 52.5 × 74.25 is the unrounded ideal, 0.5 mm oversize. The 4×4-over-3×4 decision survives — 3×4's 70 × 74.25 fits nothing — but SC-003's "fit boxes sold for those sizes" is least true in the one case SC-003 tests.
2. **An input-side sixth change**: `load_cards()` (build_pdf.py:87-129) discards top-level keys, so FR-014's per-file error needs it extended. Implied by T040, never named. Also untasked: `--grid` in `test_the_build_help_documents_the_options` (test_e2e.py:266), and stale header comments in `cards.typ` and `build_pdf.py`'s docstring that T015's "must not be touched" would freeze in place.
3. **FR-015a needs new warning semantics** — today warnings always print and `--strict` only changes the exit code; a warning that *appears* only under `--strict` is a third category.
4. **Spec numbers go stale** when T032/T034 grow the corpus — SC-001 and the "29 cards" references.
5. **T054 leaves the example's `grid:` value unspecified** — declared `a8` silently switches every default example build; commented out exercises nothing.

## Observations

1. **The central claim is true**: `cards.typ` derives everything from the two constants — `cw`, `ch`, `per-page`, both crop-mark loops, the mirroring (0↔1 at A7, 0↔3/1↔2 at A8, exactly as US1 scenario 4 states), pagination. Nothing else is hardcoded to 2, 4 or 8 except comments.
2. **Every measured number survived independent re-measurement**: 38 shipped cards, max front 66 / back 154; 11 of 38 labels over 53 chars, all 38 over 22, shortest 29; label geometry 91.4/41.4 mm, usable 84.6/34.6; writing areas 4786/2218 mm² (46 %); 8/4 pages; zero overflow at both grids. The measurements are impeccable — only the *inference* drawn from R2 for FR-010 detection is wrong.
3. **Backwards compatibility is genuinely guaranteed by the design**, and repeated builds are byte-identical, so the T004/T019 baseline is sound once C2 stops invalidating it.
4. `offending_card()`/`report_failure()` threading has no red assertion — acceptable (a markup failure is grid-independent), worth a line in T014.
5. **Scope**: upper edge of one PR but defensibly coherent. If split, the seam is the format contract: PR1 = US1 + US3 + US4 (the plan's own MVP), PR2 = the `grid:` key, the checks and `/cards`. Notably **all three unresolved design collisions live entirely in PR2's territory**.
6. The checklists are high quality — CHK034 catches C4, CHK005 is where C1 got institutionalised. Both unchecked; walking them honestly would have caught half this review.

## Recommended Actions

- [ ] Add the discriminating overflow fixture (fits A7, overflows A8 — ~300-char back verified), assert the WARNING at `--grid a8`, retarget T030's sabotage, and correct SC-005 / US3-5 / plan test #10 / R6 / quickstart §5 / CHK004-005 / T028
- [ ] Specify the mixed absent+declared `grid:` semantics; move the `grid: a8` fixture out of `demo-project/cards/`; reconcile quickstart §1 vs §7; extend T034 to cover the `== 6` assertion
- [ ] Decide how FR-015a and the label-budget warning coexist with the `--strict` CI gate before T042/T044 are written
- [ ] Reorder so every 🔴 task can actually fail
- [ ] Reword the "exactly DIN A8" claims for ISO 216 rounding
- [ ] Add tasks for: `--grid` in the help-text test, `load_cards` surfacing per-file grids, stale header comments; pin down T054's example value


---

# Re-review — 2026-08-20

**Overall**: **READY WITH WARNINGS** (was NOT READY)

All four criticals verified **genuinely resolved**, each traced to the source files it depends on rather than taken from the artifacts' own account of themselves. None was cosmetic.

| Dimension | Verdict | Change |
|-----------|---------|--------|
| Spec-Plan Alignment | WARN → **PASS** | plan.md and data-model.md residue swept after this re-review |
| Plan-Tasks Completeness | **PASS** | every previously untasked breakage now has a task |
| Dependency Ordering | **PASS** | Phase 3 is pure functions; US1 reds precede implementation |
| Parallelization Correctness | **PASS** | groups disjoint, max-3 respected |
| Feasibility & Risk | **PASS** | trap-catcher is now an assertion of presence with a verified fixture and a sabotage proof; both `--strict` collisions dissolve when traced through ci.yml |
| Standards Compliance | WARN | five 🔴 labels are guards that cannot fail when scheduled — now stated openly in tasks.md |
| Implementation Readiness | WARN → **PASS** | T036/T042 card count reconciled; T038 mechanism corrected; quickstart §9 fixed |

**Task numbering verified mechanically**: 79 definition lines, T001–T079, strictly sequential, zero duplicates, zero gaps, zero dangling references, 23 🔴 tasks. The collision from the first renumbering attempt is gone.

## Issues raised by the re-review, and their disposition

| # | Issue | Fixed |
|---|---|---|
| 1 | **T036 said "short deck" but T042 asserted 4/8 pages — which requires 25–32 cards.** At n ≤ 8 the two grids are indistinguishable by page count, so a literal reading produced a fixture on which the red test could never go green | ✅ fixture pinned to **12 cards**; counts corrected to 2 pages at A8, 4 at A7, with the constraint stated |
| 2 | `SKIP` in `scripts/demo.py:33` is dead code — T038's stated mechanism was fictional (the real protection is `demo.copy()`'s allowlist) | ✅ T038 rewritten to name the real mechanism |
| 3 | quickstart §9's gate build omitted the short-label deck its own prose requires | ✅ command now matches T072 |
| 4 | CHK034 said "17 planned assertions" (now 23); CHK036 bounded traceability at FR-001..FR-020, letting the review-era FRs escape | ✅ both rebounded |
| 5 | **plan.md was never amended** — still carried the inverted C1 claim, sited fixtures in `cards/`, and said a dedicated fixture directory was rejected | ✅ test table gains a trap-catcher row, reasoning corrected, Project Structure and Complexity Tracking updated |
| 6 | spec US3 scenario 6's tail contradicted its own opening; data-model.md still named `overflowing.yaml` as the trap-catcher | ✅ both swept |
| 7 | Five 🔴 tasks (T016, T031, T032, T052, T053) cannot fail when scheduled — guards, not tests | ✅ stated openly in the Phase 4 header; T030 remains the one load-bearing red, proved by T034 |

Grep confirms no surviving instance of the inverted claim in any artifact.
