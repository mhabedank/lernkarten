# Cross-Model Pre-Implementation Review — third pass (current)

**Feature**: Leitner compartments · **Date**: 2026-09-07
**Review model**: Fable 5.1 · read-only
**Prior passes**: [pass 1](./reviews/2026-09-07-not-ready.md) (NOT READY, 6 HIGH) · [pass 2](./reviews/2026-09-07-second-pass.md) (NOT READY narrowly, 3 HIGH)

## Overall: READY WITH WARNINGS

> *"Three passes have taken this from a geometry that could not work to a task list
> whose every red test is red for its stated reason. […] Write the code; fix
> findings 1–6 in the tasks they touch; let the final sweep handle the drift."*

**Repository state verified**: none of `scripts/leitner.py`, `scripts/settings.py`, `templates/divider.typ`, `docs/leitner.html`, `tests/test_leitner.py`, `tests/test_settings.py` exists; `lernkarten.yaml` is not in `.gitignore`; `skills/print/SKILL.md` does not mention `lernkarten setup`; `docs/index.html` does not link `leitner.html`. **So every red task that claims to be red today is red today.**

| Dimension | Verdict |
|---|---|
| Spec-plan alignment | WARN |
| Plan-tasks completeness | WARN |
| Dependency ordering | **PASS** |
| Parallelization correctness | WARN |
| Feasibility & risk | **PASS** |
| Standards compliance | WARN |
| Implementation readiness | **PASS** with notes |

## Recomputed rather than taken on trust

**FR-004a's formula is correct at any margin and any alignment.** The existing grid mirror is `column = columns − 1 − column` placed at `margin + column·cw`. For a card in column `c`: `sheet_w − x − cw = margin + (columns − 1 − c)·cw` — *exactly* the existing rule. The grid mirror **is** the reflection about the sheet's centre line, and because the print area is inset by the same margin on both sides, the two centres coincide.

Worked, A8, margin 5, block of two centred (block left 72.75):

| | front `x` | back `x = 297 − x − 71.75` |
|---|---|---|
| divider 1 | 72.75 | 152.50 |
| divider 2 | 152.50 | 72.75 |

They swap, and both stay ≥ 8 mm from either paper edge. Left-aligned instead (block left 8): front 8 / 87.75 → back 217.25 / 137.5, right edge at 289. **The formula holds without centring.**

**SC-001**: 31 cards → sheet 2 uses 4 rows → no share → pad 1 blank → 32 → append 4 → 36 → `pages(36) = 6` ✓

**The share case can never overflow a page slice.** Four dividers share only when the last sheet holds ≤ 1 row (≤ 4 cards): 4 + 4 = 8 ≤ 16. Three share when ≤ 2 rows (≤ 8 cards): 8 + 3 = 11 ≤ 16.

**R6's mm criterion**: rows end at y = 55/105/155/205. Four dividers after 1 row: 55 + 8 + 111 + 8 = 182 ≤ 210 ✓; after 2 rows: 224 ✗. Three after 2 rows: 172.5 ✓; after 3: 222.5 ✗.

## Findings to fix before the tasks they touch

### 1. MEDIUM — the grid's crop marks contradict the block's cut lines

`templates/cards.typ:48-61, :66` · FR-006b · T026/T027

`sheet()` draws the grid's crop marks on **every** page unconditionally, implying edge-to-edge cuts at grid columns (x = 5, 76.75, 148.5, 220.25, 292) and rows. With the block centred, divider 1 spans 72.75–144.5 and divider 2 spans 152.5–224.25: **the grid column at 76.75 runs 4 mm inside divider 1, and the one at 220.25 4 mm inside divider 2.** On a shared sheet the grid rows run through them too.

A user who does what `docs/testing.md` says — cut along the crop marks — with a guillotine **slices every divider**. FR-006b addresses the band *burying* the block's marks; it says nothing about the sheet's marks *lying* about the block.

**Fix**: on a page holding the block, grid marks are drawn only for cut lines that bound a card — none at all on a divider-only page. `sheet()` already has the slice to decide from.

### 2. MEDIUM — parallel group 2 has pass 1's same-file conflict again

T033 and T035 both edit `tests/test_e2e.py`; the table names `test_repo_hygiene.py`, which is T041, in Phase 5. The renumbering pulled T035 in without re-checking files.

### 3. MEDIUM — FR-016 contradicts SC-005

FR-016 still says "MUST produce **byte-identical** output" — a requirement its own success criterion says cannot be met while the engine stamps a `CreationDate`.

### 4. MEDIUM — the advisory stream is stated two ways, and will trip existing tests

FR-012c says stderr; `contracts/cli.md:43-46` says stdout. And after the advisory lands, **every e2e run over the demo project emits the unanswered-setup line on stderr** — while two existing tests assert `"WARNING" not in result.stderr`. The prefix must be pinned to `NOTE:` (what `advise_about_ids` already uses at `build_pdf.py:413`).

### 5. MEDIUM — the "block shares the last sheet" branch has no test at all

T014 names no threshold case; T031 covers add-a-page only. Half of FR-012 and the whole free-area rule are untested. `--topic Signals` is 7 cards (`test_e2e.py:813`) = two rows at 16-up, so `--dividers 3` shares and `--dividers 4` opens a page — **one deck, both branches, both advisories.**

### 6. MEDIUM — data-model lags tasks, and `divider_record()` has no implementation task

The record table lists seven fields; T017 requires `w h band bleed` too, and the validation line "all seven" is wrong by four. No task says "implement `divider_record()`".

### 7–10 (LOW)

7. T016 asserts a back-page position in `test_build_pdf.py`, but the only implementation is in `cards.typ` — there is no Python callee, so it can be neither red nor green. Fold into T022.
8. T012 is a guard still labelled red — green from the start, since T011 precedes it.
9. **SC-002a is right to advise rather than refuse**, but the asymmetry with FR-009 is unargued: an A7 card is 27 mm over the opening; a margin-0 A8 divider is 1.25 mm over, and the *cards* it accompanies are already 1.25 mm over and are not refused. Write that sentence, and promote SC-002a to an FR — it carries behaviour, and success criteria should not be the only home of a requirement.
10. Drift: 2.2/1.1 still quoted in five places; `plan.md:278` "at most two per row"; `quickstart.md:74` "clear paper"; `contracts/cli.md:72` bare `setup`; `:90-93` write-back without FR-020's limits; the checklist's "41 items" (there are 55).

## Where the reviewer found nothing wrong

Every cross-reference in `tasks.md` resolves to the task it means, and no task cites a number that no longer exists — verified after two renumberings. The 64-count is right. FR-003, FR-004, FR-004a, FR-006, FR-006b, FR-010, FR-012c, FR-020, FR-021, SC-002 and SC-002b do not contradict one another. FR-020's three limits close every case pass 2 raised — so thoroughly that `demo_copy` is belt-and-braces rather than necessary. The stub-first clause genuinely closes the ImportError class. T028 is red on its message today. The record-list arithmetic works for both branches. The feature is implementable from spec + plan + tasks + data-model.

## Is a fourth round worth it?

**No.** *"What this pass found is (a) one print-workflow hazard visible only by overlaying two sets of coordinates, and (b) artifacts drifting from each other after two renumberings. Category (a) is now exhausted — I overlaid every cut line against every mark and there is nothing else. Category (b) will not converge under review: each remediation pass edits four files and the fifth drifts. The remaining risk is in things a fourth pass cannot see — whether `divider.typ`'s text fits, whether the block's marks read well beside the band, whether the `NOTE:` line is phrased so a user acts on it — and those are found by building it."*
