---
description: "Task list for Leitner compartments"
---

# Tasks: Leitner compartments

**Input**: Design documents from `/specs/008-leitner-compartments/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [contracts/](./contracts/)

**Regenerated 2026-09-07** after the cross-model review returned NOT READY ([reviews/2026-09-07-not-ready.md](./reviews/2026-09-07-not-ready.md)). The previous list described dividers as grid cells, and four of its 🔴 tasks could not have failed *on their assertion*.

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every behaviour's test is committed **failing on its assertion** before its implementation task starts.

> **The ordering rule this list is built around.** A subprocess that exits 2 with
> `unrecognized arguments: --dividers` is **not red** — it is the ImportError
> class the constitution names explicitly. So the CLI surface is built first, and
> its red test asserts the **message**: `--dividers 5` must say *"takes 3 or 4"*,
> which fails today because argparse says something else. Only once the flag
> parses can a behaviour test fail for the right reason — the flag is accepted,
> does nothing yet, and the page count is 4 where 6 was asserted.
>
> **The same rule at module level.** A red unit test that raises `ImportError`
> or `AttributeError` is the identical failure, so **every implementation task
> for a new module or function begins by committing a stub** — the file, the
> name, the signature, returning nothing useful. Then the test fails on its
> assertion.

**Organization**: grouped by user story so each can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1…US4
- Always name the exact file path
- 🔴 a test that must be **red on its assertion** before the next task begins
- 🛡 a **regression guard**: correct before any code and never red. Labelled, not disguised as 🔴

## Path Conventions

Single flat module — no `src/`. Test placement follows `docs/testing.md`: `tests/test_build_pdf.py` is unit, **no typesetter**; `tests/test_e2e.py` drives `bin/lernkarten` as a subprocess and takes the PDF apart; `tests/test_check_docs.py` covers the docs gate; `tests/test_check_project.py` covers what the model-driven steps write into a *user's* project.

---

## Phase 1: Setup

<!-- parallel-group: 1 (max 3 concurrent) -->

- [x] T001 [P] Install dev tooling: `python3 -m pip install --user -r requirements-dev.txt` — pytest, ruff, pillow, **pypdfium2 5.13.0** (already pinned; T006 needs it)
- [x] T002 [P] Install git hooks: `scripts/install-hooks.sh`
- [x] T003 [P] Build binary test material: `python3 scripts/make_testdata.py`

<!-- sequential -->

- [x] T004 Confirm the engine with `bin/lernkarten engine --check`, then export `LERNKARTEN_E2E=1`

---

## Phase 2: Prerequisite — crop marks at A8 *(separate branch, separate PR)*

`templates/cards.typ:54,59` hardcode `297mm`/`210mm` instead of `sheet-h`/`sheet-w`. At `--grid a8` the sheet is landscape, so the bottom crop marks land at y ≈ −241 pt (off the paper) and the right-edge marks at x = 581.1 pt (mid-sheet). Verified against a real PDF — [research.md R3](./research.md).

**Not part of `feat/leitner-compartments`.** Everything after Phase 2 assumes it merged.

<!-- sequential -->

- [x] T005 Create branch `fix/cropmarks-sheet-axis` off current `main`
- [x] T006 🔴 Add a case in `tests/test_e2e.py` that builds at `--grid a8`, **renders page 1 with `pypdfium2` at scale ≥ 6** and asserts a non-paper pixel appears in the crop-mark arm zone at all four edges. *(Scale matters: a 0.3 pt `guide` line at `scale=2` blends to ~81 away from `#8c8779`, past `page_holds`'s tolerance of 40 — `test_e2e.py:1080`.)*. Red today: the bottom and right zones are blank. *(Rendering beats inflating the content stream — `pypdfium2==5.13.0` is already in `requirements-dev.txt` and `scripts/figures.py` shows the idiom.)*
- [x] T007 Replace the literals in `templates/cards.typ:54` (`297mm` → `sheet-h`) and `:59` (`210mm` → `sheet-w`); T006 goes green
- [x] T008 🛡 Extend the same test so the A7 (2 × 4) case is asserted unchanged — guards against the fix regressing the default grid
- [x] T009 Open, merge and rebase: PR for `fix/cropmarks-sheet-axis`, then rebase `feat/leitner-compartments` on it

---

## Phase 3: Foundational *(blocking)*

<!-- sequential -->

- [x] T010 🔴 Add `tests/test_leitner.py` asserting the interval sets are **not** truncations of one another — `INTERVALS[3] == ("daily", "every 3 days", "every 2 weeks")`, `INTERVALS[4] == ("daily", "every 2 days", "weekly", "every 2 weeks")` — and that `RULES` yields `new + wrong cards` first and `right -> retire` last at both counts (FR-017a, FR-017b)
- [x] T011 Create `scripts/leitner.py` as a **leaf** (stub first, so T010 fails on its assertion rather than on import), importing nothing local: `INTERVALS`, `RULES`, `COLOURS`, and `GROWTH_MM = 1.5`, `BAND_MM = 4.0`, `BLEED_MM = 3.0`, `GAP_MM = 8.0` and `LAYOUT = {3: (3,), 4: (2, 2)}` — a layout **table**, not a per-row maximum: three fit one row, four cannot (`4 × 71.75 = 287.00` is the whole A8 print width) — with the Principle V docstring ([research.md R2, R6](./research.md))
- [x] T012 🛡 Add a case in `tests/test_build_pdf.py` asserting the `scripts/` import graph is acyclic — a **guard**: the graph is acyclic today and `leitner` exists from T011, so it is green from the start and says so and `leitner` imports no local module — **derived from the real imports, not from `constitution.md:256-266`, which omits `cardid` and `figures`** ([research.md R2](./research.md))
- [x] T013 Correct `.specify/memory/constitution.md`: bring the import graph into line with the repository (it omits `cardid` and `figures`), per Principle VI's own rule that a stale rule is removed rather than worked around; and extend Principle XI's prompt-change recipe so a rule about what a skill *says to the user* names `check_docs.py`, which owns `skills/*/SKILL.md`, alongside `check_project.py` for what a skill *writes into a project* — making T055 a rule rather than an exception

<!-- sequential -->

- [x] T014 🔴 Add cases in `tests/test_build_pdf.py` for a pure `divider_block(card_count, count, grid, margin)`: it returns a page index and one `(x, y)` per divider; the arrangement matches `LAYOUT` exactly (three in one row, four as two rows of two); **every gap is ≥ 8 mm cut line to cut line, and every outer cut line is ≥ 8 mm from the paper edge at every margin**; the block is always placeable; **and the threshold both ways** — `divider_block(4, 4, a8, 5)` returns page 0 (the block shares) while `divider_block(5, 4, a8, 5)` returns page 1 (5 cards is two rows) (FR-004, [research.md R6](./research.md))
- [x] T015 Implement `divider_block()` in `scripts/build_pdf.py` — stub with the signature first, so T014 is red on its assertion
- [x] T016 🔴 Add cases in `tests/test_build_pdf.py` for `divider_record(number, of, x, y, grid, margin)`: it returns `w = card_w`, `h = card_h + 1.5` **at every margin including 0**, plus `band`, `bleed`, `x`, `y` in mm — so `templates/divider.typ` reads numbers and defines none — and carries no `id`, no `language` and no side-marker field (FR-003, FR-005, FR-006a, FR-008, SC-002, SC-003a)
- [x] T017 🛡 Add a case in `tests/test_build_pdf.py` pinning the record key set `payload()` produces for a card (`build_pdf.py:379-395, 459-464`) against a literal tuple, so `kind` cannot appear on a card record. A **guard**, not a red test: it is correct today, and writing `kind` unconditionally just to watch it fail would be a fudge. `cards.json` itself lives in a `TemporaryDirectory` and is unreachable from an e2e test (data-model §1, SC-005)
- [x] T018 Implement `divider_record()` (stub with the signature first, so T016 is red on its assertion) and add the `kind` discriminator (`card` | `divider` | `blank`, **absent meaning `card`**) plus `x`/`y` to the `cards.json` writer in `scripts/build_pdf.py`

<!-- sequential -->

- [x] T019 🔴 Add cases in `tests/test_build_pdf.py` feeding a hand-built record list containing one divider through each of the six card-assuming call sites and asserting none raises: `advise_about_ids` (`build_pdf.py:408`, `c["id"]`), `main_language` (`:423`), `payload` (`:461`, `LANGUAGES[c["language"]]`), `offending_card` (`:538`), the page count (`:713`) and the closing `languages` set (`:714`) ([research.md R7](./research.md))
- [x] T020 Split the authored **card list** from the padded **record list** in `scripts/build_pdf.py`: the six sites above take cards; only the `cards.json` writer and `pages()` take records
- [x] T021 🔴 Add a case in `tests/test_e2e.py` asserting a rendered divider carries its numeral, interval, rule and colour from `scripts/leitner.py`, and bears no card id, no `TOPIC / SUBTOPIC` and neither encoding of a card's side; and that numeral `n` on the back page sits at the mirrored `x` (`sheet_w − x − w`) of numeral `n` on the front — without which the back of divider 1 lands where the front of divider 2 is, and a single piece of paper reads `1` on one side and `2` on the other while FR-005's identical-faces test stays green (FR-002, FR-006a, FR-004a, SC-002b, SC-008a, SC-008b)
- [x] T022 Create `templates/divider.typ` — border band in the divider's colour, oversized numeral, `compartment n / of`, interval, rule line — and dispatch on `kind` in `templates/cards.typ`, placing a divider at its `x`/`y` on a front page and at `sheet_w − x − w` on a back page (FR-004a)

<!-- sequential -->

- [x] T023 🔴 Add a case in `tests/test_e2e.py` rendering with `pypdfium2` and asserting **the divider's own colour** reaches all four cut edges on both faces with the back displaced 2 mm in each direction — not merely that some colour is present, which is what the grid layout would have allowed (FR-006, SC-003)
- [x] T024 🔴 Add a case in `tests/test_e2e.py` asserting the numeral and interval are set in `ink`, **not** in the band colour — the assertable half of "legible with the colour removed". Whether it *reads* well on a photocopy goes to the manual list (FR-007, Principle XVI)
- [x] T025 🔴 Add cases in `tests/test_e2e.py` asserting the block carries **its own cut marks**, at the divider's cut lines and not the grid's, that the band does not bury them, and that **the grid's marks are absent on a divider-only page** — with the block centred at A8 the grid column at x = 76.75 mm falls 4 mm *inside* divider 1, so a user cutting to the crop marks would slice it (FR-006b)
- [x] T026 Implement the block's cut marks in `templates/cards.typ`, and suppress the grid's marks for any cut line that bounds no card on that page — `sheet()` already knows which slice it is drawing. Draw them so a `#141414` band cannot hide them — after the cells, knocked out, or with the bleed held clear of the arm zone

---

## Phase 4: User Story 1 — dividers come out of the same print run (P1) 🎯 MVP

**Independent test**: `./bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml --grid a8 --dividers 4 -o /tmp/leitner.pdf` → 6 pages against 4 without the flag.

**The CLI surface comes first**, so every behaviour test that follows can fail on its assertion rather than on an unknown flag.

<!-- sequential -->

- [x] T027 🔴 [US1] Add cases in `tests/test_e2e.py` asserting the **messages**: `--dividers 5` says it takes 3 or 4; `--dividers 4 --grid a7` names A8 per FR-009; both exit non-zero and write no PDF. Red on the message assertion today, because argparse says `unrecognized arguments` (FR-001, FR-009, SC-009)
- [x] T028 [US1] Add `--dividers` and `--box` to `bin/lernkarten` and `scripts/build_pdf.py` with their validation and refusals. The flags parse; they do nothing yet
- [x] T029 [US1] Add a `demo_copy` fixture to `tests/test_e2e.py` copying the demo project into `tmp_path`, and use it for every task below that passes `--dividers`. `run()` uses `cwd=ROOT` with absolute paths into `tests/fixtures/demo-project/`, so a write-back would otherwise land **in the fixture** and make every absent-file assertion order-dependent
- [x] T030 🔴 [US1] Add cases in `tests/test_e2e.py` covering **both branches from one corpus**: the 31-card demo deck at `--grid a8 --dividers 4` produces **6 pages** against 4 without the flag (the block opens a page, SC-001); and `--topic Signals` — 7 cards, two rows at 16-up (`test_e2e.py:813`) — gives **2 pages with `--dividers 3`** (the block shares the sheet) against **4 with `--dividers 4`** (it does not fit). Red on the counts: the flag parses but renders nothing
- [x] T031 [US1] Wire `--dividers` through `divider_block()` into the record list so T030 goes green

<!-- parallel-group: 2 (max 2 concurrent) — two different files -->

- [x] T032 [P] [US1] 🔴 Add a case in `tests/test_e2e.py` asserting cards and dividers are reported as **separate** counts, that the sheet advisory says *which* of the two placement cases the run is in, and the existing `"<n> cards valid"` still sees 31 (FR-012a, SC-004, SC-007)
- [x] T033 [P] [US1] 🔴 Add a case in `tests/test_build_pdf.py` asserting `advisories(...)` returns independent, cumulative strings in a stable order with none suppressing another, and that they go to **stderr** like every existing NOTE/WARNING (`build_pdf.py:412-416, 599-603`) while only the summary stays on stdout (FR-012, FR-012b, FR-012c)
- [x] T034 [P] [US1] 🔴 Add a case in `tests/test_e2e.py` for `--dividers`/`--box` at `--margin 0`: the divider is 74.25 × 54 mm, and `docs/design.md` already records that a `--margin 0` A8 deck does not fit the 73 × 52 mm box, so the run says so (SC-002a)

<!-- sequential -->

- [x] T035 [US1] Implement the advisory lines and the separate counts in `scripts/build_pdf.py`; T032 and T033 go green

**Checkpoint**: independently shippable. `--dividers 4` works; nothing else changed.

---

## Phase 5: User Story 2 — asked once, then never again (P2)

<!-- sequential -->

- [x] T036 🔴 [US2] Add `tests/test_settings.py`: absent, **empty** and `compartments: none` are three distinct states — absent and empty advise, `none` is silent (data-model §2)
- [x] T037 🔴 [US2] Extend it: an **unknown key** warns naming file, key and known keys and the run **continues** (FR-016a); an **invalid value on a known key** raises naming the accepted values (FR-016b); a malformed file reports the line number
- [x] T038 🔴 [US2] Extend it: `lernkarten.yaml` is resolved from the **project root derived from the card files**, not the cwd — a settings file in the cwd must not be picked up (FR-021)
- [x] T039 [US2] Create `scripts/settings.py` over `scripts/yamlio.py` (**not a leaf** — it sits above the format reader), resolving `flag → file → default` **in the shape #67 specifies for the project scope, so #67 stays additive** (FR-019), with the Principle V docstring
- [x] T040 🔴 [US2] Add a case in `tests/test_repo_hygiene.py` asserting `lernkarten.yaml` is gitignored and can never be committed (Principle VII)
- [x] T041 [US2] Add `lernkarten.yaml` to `.gitignore`; the task above goes green

<!-- sequential -->

- [x] T042 🔴 [US2] Add cases in `tests/test_e2e.py`: `lernkarten setup --project <dir> --compartments 4 --dividers-printed no --box-printed no` writes the three keys **into that directory** — run with `cwd=tmp_path`, because `run()` otherwise writes `ROOT/lernkarten.yaml`, which `lernkarten check cards/example.yaml` (a gate) would then read; **without a terminal — including a pipe —** `setup` refuses and names those three flags (FR-013, FR-014b, SC-006)
- [x] T043 [US2] Add the `setup` subcommand to `bin/lernkarten`
- [x] T044 🔴 [US2] Add a case in `tests/test_e2e.py`: a project with no `lernkarten.yaml` builds unchanged and emits the unanswered-setup advisory **exactly once** on stderr, prefixed `NOTE:` and naming `lernkarten setup` — the prefix is load-bearing, because every e2e run over the demo project will emit this line and `test_e2e.py:73`/`:723` assert `"WARNING" not in result.stderr` (FR-014, SC-006a)
- [x] T045 🔴 [US2] Add a case in `tests/test_e2e.py`: `--dividers 4` renders dividers even when `dividers_printed: true` (FR-015); and a **file-driven** count at `--grid a7` builds normally, skips and says so once, where the **flag** still refuses (FR-015a)
- [x] T046 🔴 [US2] Add cases in `tests/test_e2e.py` **against the `demo_copy` fixture**: a successful build that renders dividers sets `dividers_printed: true` and one that writes the box sets `box_printed: true`; but write-back **never creates** the file, **never fires on `lernkarten check`**, and never touches a file whose `compartments` is absent (FR-020)
- [x] T047 [US2] Wire settings resolution and write-back into `scripts/build_pdf.py`; T044–T046 go green
- [x] T048 🛡 [US2] Add a case in `tests/test_e2e.py` asserting that with no settings file the `cards.json` is byte-identical and the PDF matches on page count, page size and placement, at **both grids**, **both `--sides`** and at `--margin 0`. **Not a byte comparison of the PDF** — the engine stamps a `CreationDate` ([research.md R8](./research.md)) (SC-005)

---

## Phase 6: User Story 3 — the box (P2)

<!-- sequential -->

- [x] T049 🔴 [US3] Add a case in `tests/test_e2e.py`: `--box` writes `box.pdf` **beside the `-o` target** (so `tmp_path/box.pdf` under a temporary output), byte-identical to `assets/card-box.pdf`, leaving the card PDF untouched, and the run states 160–250 gsm applies to the box alone (FR-010, FR-011, SC-007)
- [x] T050 [US3] Implement `--box` in `scripts/build_pdf.py` as a `shutil.copyfile` — never a merge, so no PDF library is needed

---

## Phase 7: User Story 4 — the method page (P3)

<!-- sequential -->

- [x] T051 🔴 [US4] Add a case in `tests/test_check_docs.py` asserting `scripts/check_docs.py` fails when `docs/leitner.html` omits an interval string from `scripts/leitner.py`, **and** when it carries an interval-shaped string the module does not define (FR-017, SC-008). *Not `tests/test_check_project.py` — that gate validates a user's project, not this repository's docs.*
- [x] T052 🔴 [US4] Add a case in `tests/test_landing_page.py` asserting `docs/index.html` links `docs/leitner.html`, in the style of `test_the_landing_page_offers_the_box_beside_the_cutting` (`:458`); **and** that every href inside `docs/leitner.html` resolves and the page is one self-contained file, in the style of `test_the_page_stays_one_self_contained_file` (`:408`). `check_docs.py`'s `check_links` scans markdown only, so an HTML link is invisible to it (US4 scenario 1)
- [x] T053 [US4] Author `docs/leitner.html` by hand in the idiom of `docs/index.html` — self-contained, no JS runtime — using `design/guide.html` as a visual template only and honouring `design/README.md`'s superseded list
- [x] T054 [US4] Add the interval cross-check to `scripts/check_docs.py`, importing `scripts/leitner.py`; link the page from `docs/index.html`; T051 and T052 go green

---

## Phase 8: Polish & cross-cutting

<!-- sequential -->

- [x] T055 🔴 Add a check in `scripts/check_docs.py` plus a failing case in `tests/test_check_docs.py` asserting `skills/print/SKILL.md` names `lernkarten setup`. *The constitution's XI recipe says `check_project.py`, but that is written for what a skill **writes into a user's project**, which this change does not touch; `check_docs.py:77-119` already owns `skills/*/SKILL.md`*
- [x] T056 Update `skills/print/SKILL.md` to relay the build's advisory and offer `lernkarten setup`, never inventing answers and never writing the file (FR-014a)

<!-- parallel-group: 3 (max 3 concurrent) — four disjoint files, run three at a time -->

- [x] T057 [P] Add the divider section to `docs/design.md`: geometry, the colour band, why a divider may carry more ink than a card — an **addition for a new artifact**, explicitly not a loosening for cards (FR-018, Principle XVI)
- [x] T058 [P] Add the **four** manual items to `docs/testing.md` by name: the divider slides into the 52 mm opening; 1.5 mm visible from above; the band survives a hand-fed simplex run; **an A8 duplex run, with divider `n`'s back behind divider `n`'s front** (FR-004a is verified against code, not paper); **`lernkarten setup` asked interactively** — pytest has no terminal
- [x] T059 [P] Rewrite the geometry section of `specs/008-leitner-compartments/design/README.md`: it still says "bottom row, growing down", still describes the `--margin 0` fallback and still claims the dividers "cost no extra sheet". **This is the file T053 and T022 send the implementer to read** (closes CHK040)
- [x] T060 [P] Update `CLAUDE.md` and `README.md` where they describe what `lernkarten build` produces

<!-- sequential -->

- [x] T061 Run the four gates: `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`
- [x] T062 Run the three pre-PR commands once: `python3 scripts/make_testdata.py`, `LERNKARTEN_E2E=1 pytest tests/test_e2e.py`, `python3 scripts/check_project.py tests/fixtures/demo-project --strict`
- [x] T063 Walk [quickstart.md](./quickstart.md), then work `checklists/print.md`'s 29 open review questions as the PR self-review

---

## What changed from the first task list

| Review finding | Was | Now |
|---|---|---|
| 4 — 🔴 tasks failing for the wrong reason | e2e tests ran `--dividers` before argparse knew it, exiting 2 | T027 asserts the **message** and is red today; every later e2e test runs after T028 |
| 4 — duplicate implementation | T024 wired the flag, T026 "added the parsing" | one task, T028 |
| 4 — an assertion that could never be red | asserted `check_project.py` never counts a divider, which it structurally cannot see | replaced by T019: the six call sites that *do* see one |
| 4 — guards disguised as 🔴 | two of them | marked 🛡; T017 relabelled 🛡 rather than dressed up as a red test |
| 9 — same-file parallel group | both tasks edited `test_e2e.py` | group 2 is now three different files |
| 12 — no HTML link check | nothing | T052, via `tests/test_landing_page.py` |
| 13 — hidden work | one task "wire `--dividers`" | T019/T020 name all six call sites by line |
| 14 — wrong gate | a skill check in `check_project.py` | T055, in `check_docs.py` |
| 15 — test placement | exit codes in the unit module | all subprocess assertions in `test_e2e.py` |
| 16 — brittle red test | parse the inflated content stream | T006 renders with `pypdfium2`, already pinned |
| — geometry | `divider_slot()` returning a grid index | `divider_block()` returning positions in mm |
| — | *(none)* | T013 corrects the constitution's stale import graph; T025/T026 add the block's own cut marks |

## Dependencies

```
Phase 1 Setup → Phase 2 Prerequisite (separate branch, must merge) → Phase 3 Foundational
  → Phase 4 US1 (P1) → Phase 5 US2 (P2) → Phase 6 US3 (P2) → Phase 7 US4 (P3) → Phase 8
```

US3 needs T028's flag parsing, not only Phase 3. US4 needs only `scripts/leitner.py` from Phase 3.

## Parallel opportunities

| Group | Tasks | Why they are safe together |
|---|---|---|
| 1 | T001 · T002 · T003 | environment only |
| 2 | T032 · T033 | `test_e2e.py` and `test_build_pdf.py`. T034 also edits `test_e2e.py`, so it runs after, not beside |
| 3 | T057 · T058 · T060 | `docs/design.md`, `docs/testing.md`, `design/README.md`, `CLAUDE.md`+`README.md` — disjoint |

Everything else is sequential, most of it necessarily: a 🔴 task and the task that greens it cannot run concurrently without destroying the ordering Principle XI exists to enforce.

## Implementation strategy

**MVP = Phases 1 → 2 → 3 → 4.** Phases 5–7 remove friction and explain; Phase 8 documents and gates.

**Two commits per behaviour**: the 🔴 test seen failing *on its assertion*, then the implementation. `git log` should show a red commit for every behaviour here.

## Completed 2026-09-07

All 63 tasks are done. US1 shipped in #86 as part of v0.8.0; US2, US3, US4 and
the polish followed on `feat/leitner-settings`.

Two tasks were completed differently from the way they are written above, and
both are recorded rather than quietly reinterpreted:

- **T019** implements `divider_record()` but *not* the `kind` discriminator with
  `blank` padding. A divider never occupies a grid slot, so nothing needs padding
  to push it into one; `cards.json` stays a plain list without dividers and
  becomes `{cards, dividers}` with them. Simpler than planned, and it keeps the
  byte-identity SC-005 asks for.
- **T055** puts the skill check in `scripts/check_docs.py`, not
  `scripts/check_project.py` as constitution XI's recipe says. That recipe is
  written for what a skill *writes into a user's project*; `skills/*/SKILL.md`
  belongs to this repository. Issue #89 proposes amending the wording so this is
  a rule rather than an exception.

Issues #88 and #89 were filed for the two observations the reviews turned up
that are outside this feature.

## Format validation

63 tasks. Every one carries a checkbox, a sequential `T0nn` id and an exact file path or command. `[P]` appears only where files are disjoint. `[US1]`–`[US4]` appear on story-phase tasks only. 🔴 and 🛡 are distinguished, so no guard is mistaken for a test that was seen failing.
