# Cross-Model Pre-Implementation Review — second pass

**Feature**: Leitner compartments · **Date**: 2026-09-07
**Review model**: Fable 5.1 · read-only, nothing modified
**Prior report**: [2026-09-07-not-ready.md](./2026-09-07-not-ready.md)

## Verdict

| Dimension | Verdict | Reason |
|---|---|---|
| Spec-plan alignment | WARN | FR-004 contradicts itself ("at most two per row" vs "three fit one row of three"); the plan encodes the wrong half as `PER_ROW = 2` |
| Plan-tasks completeness | WARN | no task mirrors a divider's `x` on the back page; no task walks the links inside `docs/leitner.html`; no task corrects `design/README.md`; plan still routes US4 through `check_project.py` |
| Dependency ordering | WARN | seven unit-level red tasks call names that do not exist yet (ImportError class); T033 is red across the US1 checkpoint |
| Parallelization correctness | PASS | groups 1–3 verified disjoint by file |
| Feasibility & risk | **FAIL** | an unmirrored divider on the back page yields a card reading "1" on one side and "2" on the other, and nothing would see it; FR-020's write-back lands in `tests/fixtures/demo-project/` |
| Standards compliance | WARN | Principle XI fixed for subprocesses only; T017 is a deliberate wrong-implementation fudge; T012 is a guard marked red |
| Implementation readiness | WARN | the divider record builder is still unnamed; how `divider.typ` gets its geometry is still unspecified; `setup` has no write directory; `--box`'s output path is ambiguous |

**Overall: NOT READY — narrowly.** The redesign itself is sound; what remains is artifact-level, not another rework.

## Recomputed rather than taken on trust

- **Print width**: 4 × 71.75 = **287.00** ✓ — four dividers with any gap (311 mm) overflow even the paper. 3 × 71.75 + 16 = 231.25 ✓. Two per row 151.5 ✓. Two rows 111 ✓.
- **Is 8 mm enough?** Neighbour's bleed nearest edge at `cut + 5 + δ ≥ cut + 3`; worst cut at `cut + 1`. Own bleed on the displaced face reaches `cut + 3 + δ ≥ cut + 1`. **Sufficient, 2 mm headroom. Finding 1 of the first pass is genuinely resolved.**
- **The "free card rows needed" table is wrong; its conclusions are right.** 2.2 and 1.1 divide block height by 50 with **no gaps**. With 8 mm above and 8 mm to the paper edge: (8+111+8−5)/50 = **2.44** and (8+51.5+8−5)/50 = **1.25**. Both still round to the same "shares when" column, so SC-001 holds — but the spec repeats 2.2 in four places as if it were the criterion.
- **SC-001**: 31 cards + 1 blank + 4 dividers = 36 records → `pages(36)` = 6 ✓ against 4.
- **`--margin 0` outer bleed**: cut line ≥ 8 mm from the paper edge, bleed to 5 mm. **On the paper** — deleting the fallback did not push ink off the sheet.
- **R7's six line numbers** — 408, 423, 461, 538, 713, 714 — all verified.
- **`sheets` from `cards.len()`** survives padding; `typeset()` globs `TEMPLATES/*.typ`, so `divider.typ` needs no wiring.
- **T027 and T029 are genuinely red** on their assertions.
- **pypdfium2 5.13.0** present; `page_holds()` already exists at `test_e2e.py:1080`.

## Remediation audit

| First-pass finding | Landed? | Note |
|---|---|---|
| 1 adjacent dividers overpaint | **YES** | free placement removes the shared cut line; 8 mm verified |
| 2 SC-005 unachievable | PARTIAL | re-baselined honestly, but `cards.json` lives in a `TemporaryDirectory` and is deleted — an e2e test cannot read it (new finding 7) |
| 3 bleed buries crop marks | **YES** | FR-006b + T025/T026 |
| 4 five red tasks | PARTIAL | subprocess half fixed; unit half not (new finding 4) |
| 5 `compartments: 4` at A7 | **YES** | FR-015a, SC-009, T043 |
| 6 setup flags unnamed | **YES** | but where `setup` *writes* is unspecified (new finding 9) |
| 7 `dividers_printed` never flips | **YES**, and it bites | new finding 3 |
| 8 lookup root | **YES** for `build`, not for `setup` |
| 9 parallel same-file | **YES** | three files verified |
| 10 margins in (0, 4.5) | **YES** (dissolved) |
| 11 how `divider.typ` gets geometry | **NO** | still open — new finding 5 |
| 12 HTML link check | PARTIAL | nothing checks links *inside* `leitner.html` (new finding 10) |
| 13 hidden work in wiring | **YES** | six sites named, lines correct |
| 14 skill check wrong gate | **YES** | T053 |
| 15 test placement | **YES** |
| 16 content-stream parsing | **YES** | pypdfium2 |
| 17 "two questions" | **YES** | no occurrence left |
| constitution graph stale | **YES** | T013 |
| `settings` "LEAF over yamlio" | **YES** |
| US2-6 warning vs quickstart error | **YES** |

## New findings

### 1. HIGH — A free-placed divider's `x` must be mirrored on the back page

`templates/cards.typ:65-72` · `spec.md:203` · `tasks.md` T022 · `data-model.md:25`

`sheet()` mirrors a card by recomputing its **column** (`column = columns - 1 - column`). A divider is no longer a column — it is an `(x, y)` in mm. T022 says "placing a divider at its `x`/`y` rather than in a grid cell", so with the block centred, **divider 1's back prints where divider 2's front is**. After the flip one piece of paper reads "1" on one side and "2" on the other.

FR-005 ("a divider has no wrong way round") becomes physically false while its test — both faces render from one definition — stays **green**. T023 samples colour at the edges and would pass too: same size, same band, wrong numeral.

`spec.md:203`'s *Duplex alignment* paragraph argues that "the 1.5 mm of growth does not need a mirrored counterpart" — reasoning inherited from the downward-growth design, about a quantity that no longer exists — and says nothing about `x`.

**Change**: on a back page a divider is placed at `sheet_w − x − w`; `y` unchanged. Say so in FR-004/FR-005 and in T022. Fold into T021 an assertion that numeral `n` on the back sits at the mirrored `x` of numeral `n` on the front. Add an A8 duplex run to T056's physical list.

### 2. HIGH — FR-004 contradicts itself and the plan encodes the wrong half

`spec.md:144` · `plan.md:252` (`PER_ROW = 2`) · `tasks.md` T011, T014 · `research.md:263-265`

FR-004 says "**at most two per row** … Three dividers fit one row of three." T014 asserts *both*. With `PER_ROW = 2` three dividers take two rows and the R6 table's 1.1 rows is wrong for three; with three per row `PER_ROW = 2` is false.

**Change**: replace `PER_ROW` with `LAYOUT = {3: (3,), 4: (2, 2)}`. Reword FR-004 as "three in one row; four as two rows of two — four in one row is impossible because 4 × 71.75 = 287.00 is the whole print width". T014 asserts the layout table, not a per-row maximum.

### 3. HIGH — FR-020's write-back is under-specified, and one case corrupts the test corpus

`spec.md:180` · `contracts/cli.md:90-93` · `tasks.md` T044, T045 · `tests/test_e2e.py:46-50`

- **Absent file**: does a flag-driven `--dividers 4` create one? With what `compartments`? A file with `dividers_printed: true` and no `compartments` is a **fourth state** the three-state table does not have.
- **`--check`**: `lernkarten check --dividers 4` test-typesets the dividers. That "renders" them. If check writes back, the `/print` skill's check-then-build sequence marks them printed before the real build, which then skips them.
- **The e2e corpus**: `run()` uses `cwd=ROOT` with absolute paths into `tests/fixtures/demo-project/cards/`, so `project_root()` is the demo project. Every test passing `--dividers` would write `tests/fixtures/demo-project/lernkarten.yaml`. Gitignored, so hygiene stays green — but every "absent file" assertion becomes **order-dependent** and the file persists across runs.

**Change**: write back only into an **existing** file whose `compartments` is 3 or 4; never create one; never on `--check`. Settings-exercising tasks copy the demo project to `tmp_path` (`one_figure_card()` at `test_e2e.py:1067` is the pattern).

### 4. MEDIUM — Principle XI is fixed for subprocesses, not for modules

`tasks.md` T010, T014, T032, T035–T037 · `constitution.md:366-369`

T010 imports `scripts/leitner.py` before T011 creates it (ImportError); T014 calls `divider_block()` before T015 (AttributeError); T035–T037 import `settings` before T038. Verbatim the class the constitution refuses.

**T017 is a fudge**: writing wrong code on purpose to watch a test fail is not test-first. It and T012 are guards.

**Change**: add to the ordering rule — *the implementation task for a new module or function begins with a stub carrying the name and signature, so the red test fails on its assertion rather than on import*. Mark T012 and T017 🛡.

### 5. MEDIUM — T016 asserts on a record builder that is never named

`tasks.md` T016 · `data-model.md:17-25` · `plan.md:243-244`

The record lists `kind number of interval rule colour x y` — no width, height, band or bleed. Plan says `divider.typ` "receives" the constants; R2 rejects `sys.inputs`; `divider_block()` returns only `(x, y)`. First-pass finding 11 asked how, and it is still unanswered.

**Change**: the record carries `w`, `h`, `band`, `bleed` in mm; data-model §1 lists them; T016 names the builder.

### 6. MEDIUM — "8 mm of clear paper" is not what FR-004 derives

`spec.md:59, 144, 228` vs `:141`/`:132` · `tasks.md` T014

8 mm is derived as 3 + 3 + 2 — a **cut-line-to-cut-line** distance of which only 2 mm is white. US1-4, SC-002 and T014 say "8 mm of **clear paper**", which would need 14 mm cut-to-cut. Also FR-003 says the block keeps clear of the *print area* while the `--margin 0` case says 8 mm from the *paper edge* — 3 mm apart at the default margin.

**Change**: "8 mm between adjacent cut lines, of which the middle 2 mm is unprinted"; "every outer cut line at least 8 mm from the paper edge, at every margin". Correct the R6 table to include the gaps.

### 7. MEDIUM — SC-005's comparable half is unreachable from T046

`tasks.md` T046, T017 · `build_pdf.py:703-711`

`cards.json` is written into a `TemporaryDirectory` and deleted before the subprocess exits, so an e2e test cannot read it — and "the pre-feature one" names no artifact in the repo.

**Change**: T017 becomes a unit guard in `test_build_pdf.py` on the pinned key set (`build_pdf.py:379-395, 459-464`); T046's baseline is the literals the existing e2e tests already pin.

### 8. MEDIUM — Old-geometry text outside anything marked superseded

- `design/README.md:61-69, 79-80, 28-32` — "bottom row, growing down", the `--margin 0` fallback, "cost no extra sheet". **This is the file T051/T022 send the implementer to read.** CHK040 is open for exactly this; no task closes it.
- `spec.md:57` — "the fourth cell of that row is empty"; there is no fourth cell in a row of three.
- `plan.md:195-196` — the R1 summary still says "the bleed forces FR-004 to be tightened".
- `plan.md:130, 145, 169-172, 184` — `check_project.py` for dividers and for US4's red assertion; the skill check "in `check_project.py`".
- `tasks.md` T055 — "the bleed's outermost 1.5 mm sits inside the non-printable zone"; under the block it ends 5 mm from the edge.

### 9. MEDIUM — `setup` has no stated write directory

FR-021 derives the lookup root from the card files; `setup` takes none. The contract's bare `lernkarten setup` writes to the cwd — a different rule from the read. And `run()` uses `cwd=ROOT`, so T040 writes `ROOT/lernkarten.yaml` while `lernkarten check cards/example.yaml` — a gate — then reads it.

**Change**: `setup --project <dir>`, cwd as default (precedent: `scripts/figures.py --project`); T040 runs with `cwd=tmp_path`.

### 10. MEDIUM — US4-1 is half-tasked

"every link resolves" and "one self-contained file" have no task; T050 covers index → leitner only. `tests/test_landing_page.py:408` is the pattern.

### 11–17 (LOW)

11. T033 is red in Phase 4 and green in Phase 5, across the "independently shippable" checkpoint. Move it before T039.
12. The pixel tests need a render scale: a 0.3 pt `guide` line at `scale=2` blends to ≈ 81 away from `#8c8779`, above `page_holds`'s tolerance of 40. Render at scale ≥ 6 for the mark tests.
13. `--box` output path ambiguous — literal `output/box.pdf`, or beside the `-o` target? T047 with `tmp_path` needs the answer.
14. At `--margin 0` the A8 card is 74.25 × 52.5 and `docs/design.md:224-226` already says that deck does not fit the box; the divider is then 74.25 × 54. SC-002 celebrates full size without saying it does not slide in.
15. Advisory stream: `contracts/cli.md:43-46` says stdout; every existing NOTE/WARNING in `build_pdf.py:412-416, 599-603` goes to stderr.
16. T024 ("legible with the colour channel removed") is a looks-right test. The assertable part is "the numeral and interval are set in `ink`, not the band colour".
17. T053 departs from Principle XI's letter. Since T013 amends the constitution anyway, amend XI's recipe there so the departure is a rule rather than an exception.

## Observation, outside this feature's scope

`docs/design.md:194-198` and `build_pdf.py:217-218` say "flip on long edge" for both grids, and `cards.typ` mirrors **columns** for both. On the **landscape** A8 sheet the long edge is horizontal; a long-edge flip mirrors rows, and column mirroring corresponds to a **short**-edge flip. If that is right, A8 duplex has been mis-instructed since `feat/card-grid`, and `spec.md:203`'s "verified rather than assumed" was verified against the code, not against paper. Not asserted as a defect of this feature — but T056's physical list should include an A8 duplex run.

## Where I found nothing wrong

The core redesign holds. R6's arithmetic is correct where stated as numbers; 8 mm is sufficient with 2 mm headroom; SC-001's page count is right under the new padding; `cards.typ`'s sheet/page derivation survives blanks and dividers unchanged; R7's six call sites are the real six; T027 and T029 are genuinely red on their assertions. FR-014b, FR-015a, FR-021, T013, T019/T020, T050, T053 and the pypdfium2 route landed as claimed. The parallel groups are disjoint. `.gitignore`'s no-slash semantics do what T039 needs without a fixture negation.
