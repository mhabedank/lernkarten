---
description: "Task list for the stable card id (issue #59)"
---

# Tasks: A short, stable card id

**Input**: Design documents from `/specs/005-card-id/`

**Prerequisites**: [plan.md](./plan.md) (20 red-first assertions), [spec.md](./spec.md) (22 FRs, 9 SCs, 5 stories), [contracts/cards-yaml.md](./contracts/cards-yaml.md), [data-model.md](./data-model.md), [research.md](./research.md)

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every story opens with a test task, committed *failing on its assertion* before the implementation task starts.

**Branch**: `feat/card-id` — already created and checked out. Do not create or switch.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel — **different files only**. Two tasks touching the same file are never both `[P]`, even when they look independent.
- **[Story]**: US1–US5 from spec.md
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## The ImportError trap — read before starting Phase 3

`scripts/cardid.py` does not exist yet, so every test against it would fail with
`ImportError`, and **the constitution does not accept that as red** (XI: "make it
fail on the assertion"). T004 therefore creates the module as a **skeleton of
stubs** before any test is written. Stubs are not implementation — they exist so
that a red test is red for the reason the story cares about.

---

## Phase 1: Setup

**Purpose**: get the environment able to verify the work.

<!-- parallel-group: 1 (max 3 concurrent) -->

- [x] T001 [P] Install dev tooling: `python3 -m pip install --user -r requirements-dev.txt` (pytest, ruff, pillow, pyyaml)
- [x] T002 [P] Install git hooks: `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [x] T003 [P] Confirm the engine: `bin/lernkarten engine --check` — Typst 0.15.1, pinned. No version change in this feature, so no checksum bump.

**Checkpoint**: `pytest` runs green on `main`'s behaviour before anything changes.

---

## Phase 2: Dependencies

**⚠️ SKIPPED — [plan.md](./plan.md) says "No dependency change".**

Recorded rather than deleted, because the alternative was considered and
rejected on its merits: `ruamel.yaml` was evaluated for the YAML round-trip and
rejected because it *reserialises*, so it cannot promise the byte-identity
FR-006a requires. PyYAML's `compose()` — already a runtime dependency
(`pyyaml==6.0.3` in `scripts/deps.py`) — supplies exact line/column marks, which
makes the write a text splice instead. Full argument in
[research.md § R-1](./research.md).

**Nothing to do here. Do not invent work.**

---

## Phase 3: Format contract & id primitives (BLOCKING)

**Purpose**: the `cards/*.yaml` schema is the entire interface between the two
halves (constitution I). Settle it, and the primitives every story needs, before
either half is written.

The contract itself is already written:
[contracts/cards-yaml.md](./contracts/cards-yaml.md).

<!-- sequential -->

- [x] T004 Create `scripts/cardid.py` as a **stub skeleton** — module docstring (what it is for, and why it is not in `yamlio.py`), `ALPHABET = ""`, and `generate`, `normalise`, `validate`, `cards_in`, `insert_ids`, `remove_ids`, `backfill`, `reassign` all present and returning `None`. Imports only `yamlio` and stdlib `secrets`/`re`. **This is scaffolding, not implementation** — it exists so every 🔴 below fails on its assertion rather than on `ImportError`.
- [x] T004a Add `"id"` to `COMMANDS` in **`bin/lernkarten` and `scripts/lernkarten`** (byte-identical mirrors — one task, both files) dispatching to a `cardid.main()` **stub** that parses nothing and exits 0. **Scaffolding, not implementation** — the same reason as T004: without it, T035a below would fail with "unknown command", which is the CLI's equivalent of an ImportError and does not count as red (constitution XI). Confirm `diff bin/lernkarten scripts/lernkarten` is empty.
- [x] T004b Add a `compose(text)` **stub** to `scripts/yamlio.py` returning `None`, routed through the existing `_load_pyyaml()` bootstrap — **not** a bare `import yaml`. Scaffolding, so T004c fails on its assertion rather than on `AttributeError`. *(Cross-model review F3: `yamlio`'s public surface is only `YamlError`, `load`, `main`, so `cardid` could not reach `compose()` without either bypassing the dependency bootstrap or calling a private function. A bare `import yaml` would crash `scripts/check_project.py` — a constitution XII gate — on a machine that has never run `deps.activate()`.)*
- [x] T004c 🔴 Add to `tests/test_yamlio.py`: `yamlio.compose(src)` returns a node tree whose card nodes carry `start_mark` line and column; and it works when `yaml` has not already been imported, proving it goes through the bootstrap. **Fails on the assertion** (constitution II, VI)
- [x] T004d 🟢 Implement `compose()` in `scripts/yamlio.py` — one call through `_load_pyyaml()`, wrapping `yaml.YAMLError` in `YamlError` exactly as `load()` does. Make T004c pass. `yamlio` stays a leaf.
- [x] T005 🔴 Add to `tests/test_cardid.py`: `validate("A45DK") is None`; `validate("A45DI")` names `I`; `validate("A45D")` names the length; `validate(12345)` names the type; `normalise("a45dk") == "A45DK"`; `normalise("A45DO") == "A45D0"`; 10 000 generated ids all length 5, all in-alphabet, all distinct. **Run it — must fail on the assertions** (plan assertions 1–3; FR-003, FR-004, FR-009, SC-001)
- [x] T006 🟢 Implement in `scripts/cardid.py`: `ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"`, `normalise()` (upper-case, then `I`→`1`, `L`→`1`, `O`→`0`; `U` is **not** folded), `validate()`, and `generate(taken)` using `secrets.choice` with redraw-on-clash. Make T005 pass.
- [x] T007 🔴 Add to `tests/test_cardid.py`: `generate` gives up after a bounded number of redraws, raising an error that names the id count and the bound, and writes nothing. **Fails on the assertion** (plan assertion 11b; FR-003b)
- [x] T008 🟢 Add the redraw bound and the exhaustion error to `generate()` in `scripts/cardid.py`. Make T007 pass.
- [x] T009 🔴 Add to `tests/test_cardid.py`: `remove_ids(insert_ids(src)) == src` **byte-for-byte** on LF input, on CRLF input, and on input with umlauts; `insert_ids` twice equals once; a pre-existing id is byte-identical after `insert_ids`. **Define the inputs as string constants inside the test module** — comments, single-quoted Typst markup, umlauts, and an LF and a CRLF variant. **Do not read `cards/example.yaml` or any file under `tests/fixtures/demo-project/cards/`**: T014 and T015 add ids to every one of them, after which `insert_ids` would insert nothing and this assertion would silently decay to `src == src` — passing forever while testing nothing. This is the feature's central byte-fidelity guarantee, so its input must be one no later task can neuter. **Fails on the assertions** (plan assertions 4–6; FR-006a, SC-006)
- [x] T010 🟢 Implement `cards_in()` (via **`yamlio.compose()`** from T004d — never a bare `import yaml`, never scanning text), `insert_ids()` (splice `id:` as each card's first key, moving the `- ` dash onto the new line, preserving the line ending) and `remove_ids()` (the exact inverse) in `scripts/cardid.py`. Make T009 pass.

- [x] T009a 🔴 Add to `tests/test_cardid.py`: `insert_ids` **refuses** a deck whose cards it cannot splice safely, naming the file and card and writing nothing — (a) a **flow-style** card (`- {front: 'a', back: 'b'}`), where the first key's mark sits inside the brace so the `- ` prefix assumption breaks; (b) an **aliased** card (`- *c` twice), where both cards are the *same* node with identical marks and would be spliced twice at one position. **Fails on the assertion** *(cross-model review F2, reproduced: dash-detached keys, block scalars and quoted first keys were also probed and are safe — only these two break.)*
- [x] T010a 🟢 Implement the guard in `scripts/cardid.py`: detect flow-style and aliased card nodes before splicing and refuse the file; after splicing, **re-parse the result and compare it to the original data** before writing, so an unforeseen shape fails loudly instead of corrupting a user's deck. Make T009a pass.

**Checkpoint**: the id primitives are green and the round-trip is proven
byte-exact. `scripts/cardid.py` is a leaf — confirm nothing imports *into* it
except stdlib and `yamlio` (constitution VI).

---

## Phase 4: User Story 2 - Existing decks keep working untouched (Priority: P1)

**Goal**: a deck with no `id:` anywhere still builds, to the same page count.

**Independent Test**: `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/noids.pdf` — exit 0, page count `2 × ⌈29 ÷ 8⌉`.

**Why first**: this is the smallest change that touches `build_pdf.py`, and it is
the guarantee every other story could break. Landing the empty-string fallback
*before* fixtures carry ids removes the ordering hazard entirely — the demo decks
keep building at every point in the sequence.

<!-- sequential -->

- [x] T011 🔴 [US2] Add to `tests/test_build_pdf.py`: `load_cards` on a deck with **no** `id:` returns `""` for every card's `id` — never a missing key, never `stem-N`; a deck where *some* cards have ids returns those ids and `""` for the rest. **Fails on the assertion** (plan assertions 10, 11; FR-005, US2, SC-003)
- [x] T012 🟢 [US2] In `scripts/build_pdf.py` `load_cards` (~line 303), replace `"id": f"{path.stem}-{i}"` with the card's own `id`, defaulting to `""` — this is what makes **FR-001** true (the id is no longer derived from position or file name). Make T011 pass. **Do not touch `enumerate(...)`** — it runs before the `--subtopic` filter and that is what keeps ids filter-stable.
- [x] T013 [US2] Run `pytest` in full and fix any existing test that asserted on the old `stem-N` id shape. Record in the PR description which assertions changed and why.

**Checkpoint**: the demo decks build unchanged with no ids present. The
backwards-compatibility guarantee holds **before** anything else moves.

---

## Phase 5: User Story 1 - The id is stable (Priority: P1) 🎯 MVP

**Goal**: a card's id survives inserting, deleting, renaming, editing and filtering — and `/cards` assigns one on write.

**Independent Test**: note card 3's id in a deck; insert a card before it, delete one before it, rename the file, edit its text, build with `--subtopic`; the id is unchanged in all five.

### Test material first

<!-- parallel-group: 2 (max 3 concurrent) -->

- [x] T014 [P] [US1] Add `id:` as the first key of every card in `tests/fixtures/demo-project/cards/*.yaml` (6 decks, 29 cards) — 5-character Crockford Base32, unique across the whole demo project. Invent them; never derive from position. **Note**: T009's round-trip test must not read these files — see the warning in T009.
- [x] T015 [P] [US1] Add `id:` as the first key of every card in `cards/example.yaml`, keeping all 11 comments and the single-quoted Typst markup byte-identical. This file is the versioned schema reference. **Note**: T009's round-trip test must not read this file — see the warning in T009.
- [x] T016 [P] [US1] Add a fixture deck under `tests/fixtures/demo-project/cards/` (or extend one) that carries a **mix** of carded and uncarded entries, so the partial case has material.

### 🔴 Red

<!-- sequential -->

- [x] T017 🔴 [US1] Add to `tests/test_build_pdf.py`: a card's id is byte-identical after each of the five operations — insert-before, delete-before, file rename, text edit, `--subtopic` build. **Fails on the assertion** (plan assertion 9; SC-002). This is the assertion the whole feature exists to make true.
- [x] T018 🔴 [US1] Add a check to `scripts/check_project.py` reporting a card deck whose cards carry no ids, **plus** a case in `tests/test_check_project.py` that fails against what the **current** `skills/cards/SKILL.md` produces. **This is the only artifact that makes a prompt change verifiable** (constitution XI, plan assertion 15; FR-002). If no failing check can be written, stop and go back to the spec.

### 🟢 Green

<!-- sequential -->

- [x] T019 🟢 [US1] Make T017 pass — should already hold once T012 landed; if it does not, the id is still positional somewhere and that is the bug.
- [x] T020 🟢 [US1] Update `skills/cards/SKILL.md`: assign a fresh 5-character Crockford Base32 id to every card written, **never** alter an id already present, and place `id:` first on each card. Update its "Card schema" block. Keep the frontmatter valid (`name` == folder). Make T018 pass.

**Checkpoint**: ids are stable under all five operations, and `/cards` assigns
them. `python3 scripts/check_project.py tests/fixtures/demo-project --strict`
passes.

---

## Phase 6: User Story 3 - The id is legible on the printed card (Priority: P1)

**Goal**: the id renders at 8 pt (up from 4.6 pt), fits the `cw / 3` cap, and a card with no id renders the side marker alone.

**Independent Test**: measure the rendered `<id> · 1/2` through the pinned engine — 52.80 pt against a 94.49 pt cap.

> Visible surface. **Read [`docs/design.md`](../../docs/design.md) first** (constitution XVI).

<!-- sequential -->

- [x] T021 🔴 [US3] Add to `tests/test_build_pdf.py`: a card whose id is `""` renders the side marker **alone** — `1/2` / `2/2`, with no id text and no `·` separator — and the footer stays well-formed. **Fails on the assertion** (plan assertion 11a; FR-005). Unit level, **not** e2e: this is a P1 guarantee and must not skip silently without an engine.
- [x] T022 🔴 [US3] Add to `tests/test_e2e.py`: the rendered id measures **8 pt** and its block width is strictly less than `cw / 3`. Measured, not eyeballed. **Fails on the assertion** (plan assertion 17; FR-010, FR-011, SC-005). Opt-in via `LERNKARTEN_E2E=1`.
- [x] T023 🟢 [US3] Edit `templates/card.typ` `footer()`: id `size: 4.6pt * scale` → `8pt * scale`; when the id is empty, render only the side marker with no separator. Leave `foot-h`, the band geometry and the `id-w` cap formula alone. Make T021 and T022 pass.
- [x] T024 [US3] Verify by eye at both grids: `bin/lernkarten build cards/example.yaml -o output/cards.pdf` and `--grid a8`. The id must not overpower the 5 pt wordmark (FR-011a) — that constraint, not the clip cap, is what bounds the size.

**Checkpoint**: the id is readable at desk distance and the band still reads as
quiet. No brand PNG re-render — the mark and wordmark are untouched.

---

## Phase 7: User Story 5 - A broken id is reported, not printed (Priority: P2)

**Goal**: duplicate, wrong-length, out-of-alphabet and non-string ids are reported with both offenders named — and **nothing is written**.

**Independent Test**: `bin/lernkarten check` on the broken fixtures — non-zero exit, and every input file byte-identical afterwards.

### Test material first

<!-- parallel-group: 3 (max 3 concurrent) -->

- [x] T025 [P] [US5] Add `tests/fixtures/demo-project/broken/duplicate-id.yaml` — two cards sharing one id. Text only, no generator, no binaries.
- [x] T026 [P] [US5] Add `tests/fixtures/demo-project/broken/bad-alphabet-id.yaml` (an `I`, `L`, `O` or `U`) and `tests/fixtures/demo-project/broken/wrong-length-id.yaml` (4 and 6 characters).
- [x] T027 [P] [US5] Add `tests/fixtures/demo-project/broken/non-string-id.yaml` — `id:` empty, `id: 12345`, `id: [a]`.

<!-- sequential -->

- [x] T028 [US5] Add one row per new fixture to the table in `tests/fixtures/demo-project/broken/README.md`, naming the expected reaction.

### 🔴 Red

- [x] T029 🔴 [US5] Add to `tests/test_check_project.py`: duplicate reported naming **both** cards (file and card, not just the id); out-of-alphabet naming the offending character; wrong length naming the length found; non-string naming the type. Duplicate detection operates on the **normalised** id, so `a45dk` and `A45DK` collide. **Fails on the assertions** (plan assertions 12, 13; FR-008, FR-009, SC-004)
- [x] T030 🔴 [US5] Add to `tests/test_check_project.py`: hash every input file before and after a check run over the broken fixtures — **byte-identical**. **Fails on the assertion** (plan assertion 14; FR-013a, SC-009). The checker is a CI gate; a gate that rewrites the tree is not a gate.

- [x] T029a 🔴 [US5] Add to `tests/test_e2e.py`: **`bin/lernkarten check`** on the duplicate-id fixture exits non-zero and names both cards. **This is the assertion SC-004 actually makes, and nothing else covers it**: `bin/lernkarten` maps `check` to `build_pdf.main()` with `--check` and **never invokes `check_project.py`**, so validation added only to `check_project.py` would leave SC-004, US5 and this phase's own independent test undelivered while the task list read as complete. **Fails on the assertion** *(cross-model review F1, verified against `bin/lernkarten`.)*

### 🟢 Green

- [x] T031 🟢 [US5] Implement the four validations in `scripts/check_project.py` `check_cards()`, using `cardid.validate()` and `cardid.normalise()`. Make T029 and T030 pass. **Add no write path to this module.**
- [x] T031a 🟢 [US5] Make T029a pass by appending id-validation errors to the `errors` list returned by `load_cards` in `scripts/build_pdf.py` (~line 271–312), the same channel the existing schema errors use — `main()` already prints them and exits non-zero under `--check` (~line 535–540). One insertion point serves both `lernkarten check` and `check_project.py`; do **not** duplicate the rules in two places. Still no write path.
- [x] T032 🟢 [US5] Add the missing-id advisory: `lernkarten check` on a deck with no ids exits **0** and prints **one** line per run naming the backfill path — not one line per card (FR-005, US2 scenario 2).

**Checkpoint**: broken ids are caught and named; the checker provably writes nothing.

---

## Phase 8: User Story 4 - Backfill ids into a hand-written deck (Priority: P2)

**Goal**: `lernkarten id --backfill` assigns ids to cards lacking one, all-or-nothing, preserving the file.

**Independent Test**: backfill `cards/example.yaml` twice — the first run adds one `id:` line per card and touches nothing else; the second changes nothing.

### 🔴 Red

<!-- sequential -->

- [x] T033 🔴 [US4] Add to `tests/test_cardid.py`: (a) `backfill` over a set where one file is unparseable or unwritable leaves **every** file unmodified; (b) `backfill` completes with **no typesetting engine present and no network** — patch `engine` and any socket access to raise, and assert it still succeeds. **Fails on the assertions** (plan assertion 7; FR-007, **FR-012**). (b) matters because backfill is the one writing path a user runs on a fresh checkout, before an engine is ever fetched.
- [x] T034 🔴 [US4] Add to `tests/test_cardid.py`: two decks sharing an id — the card later **by command-line order** is reassigned, the earlier keeps its id, and the record carries both ids; swapping the two file arguments reassigns the other card. **Fails on the assertion** (plan assertion 8; FR-013b, SC-008)
- [x] T035 🔴 [US4] Add to `tests/test_cardid.py`: a replacement id that itself clashes is redrawn — one pass over the combined set leaves **zero** duplicates. **Fails on the assertion** (plan assertion 11c; FR-013d)

- [x] T035a 🔴 [US4] Add to `tests/test_e2e.py`: `bin/lernkarten id --backfill` as a subprocess assigns ids to a deck that lacks them and leaves its comments intact. **Fails on the assertion, not on "unknown command"** — T004a already registered the subcommand as a no-op stub, so the failure is "no ids were written", which is the point (plan assertion 16; US4). Opt-in via `LERNKARTEN_E2E=1`.

### 🟢 Green

- [x] T036 🟢 [US4] Implement `backfill(paths)` in `scripts/cardid.py` (**FR-006** — the backfill path itself) — read every file first, build the project id set, splice, then write; on any failure write nothing at all. Make T033 pass.
- [x] T037 🟢 [US4] Implement `reassign(paths)` in `scripts/cardid.py` — automatic reassignment on collision (**FR-013**), first-occurrence-wins by argument order then card order, replacement ids checked against the whole combined set and redrawn via `generate()` (**FR-003a**). Make T034 and T035 pass.
- [x] T038 🟢 [US4] Emit the reassignment report: name the card, the old id and the new one, **and state the consequence** — the old id no longer resolves in past conversations and any revision history against it is orphaned (FR-013c).
- [x] T039 🟢 [US4] Replace T004a's stub with the real dispatch in **`bin/lernkarten` and `scripts/lernkarten`** — argument parsing and the flag surface defined in [contracts/cards-yaml.md](./contracts/cards-yaml.md) § The `id` subcommand, called after `deps.activate()`. Make T035a pass. Confirm `diff bin/lernkarten scripts/lernkarten` is empty afterwards.

**Checkpoint**: backfill and reassignment work through the real command, and a
failed run leaves the tree untouched.

---

## Phase 9: Docs & Cross-Cutting

<!-- parallel-group: 4 (max 3 concurrent) -->

- [x] T041 [P] Update the `cards/*.yaml` schema block in `CLAUDE.md` to document `id` — 5 characters, Crockford Base32, unique per project, assigned by `/cards`, optional for backwards compatibility.
- [x] T042 [P] Record the id at **8 pt** in `docs/design.md`. **Do not edit the sentence "it does not bind a letterspaced label at 11 px or a card id at 8.5 px"** — that exemption is what makes 8 pt legal, and the spec now requires it be left intact.
- [x] T043 [P] Name the two Principle XI manual-checklist items in `docs/testing.md`: **SC-007** (read an id off paper, use it in a session, confirm it still resolves after an edit) and the **wording** of the missing-id advisory line. Add the four new broken fixtures to its fixture table.

<!-- sequential -->

- [x] T044 Correct the stale dependency claim in `CLAUDE.md`: it says a runtime dependency "cannot ship today", which is wrong on **both** halves — `pyyaml==6.0.3` already ships via `scripts/deps.py`, and `bin/lernkarten` already calls `deps.activate()` before doing work. (Found in [research.md § C-2](./research.md).)
- [x] T045 Update `DEMO_CARD_COUNT` in `tests/test_e2e.py` if T016 changed the demo card count from 29.
- [x] T046 Confirm every relative markdown link resolves — `scripts/check_docs.py` fails on a dead one. Add any new expected file to `REQUIRED_FILES`.
- [x] T047 Refactor pass over `scripts/cardid.py` — now that it is green, clean it up. The third step of red-green-refactor is not optional either.

---

## Phase 10: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

<!-- sequential -->

- [x] T048 `ruff check . && ruff format --check .`
- [x] T049 `pytest`
- [x] T050 `bin/lernkarten check cards/example.yaml`
- [x] T051 `python3 scripts/check_docs.py`
- [x] T052 `LERNKARTEN_E2E=1 pytest tests/test_e2e.py -v` — the engine-dependent assertions (T022, T029a, T035a) skip silently without this, so run it once
- [x] T053 `python3 scripts/check_project.py tests/fixtures/demo-project --strict`
- [x] T054 `bin/lernkarten build cards/*.yaml --margin 0 --no-logo -o output/borderless.pdf` and `--grid a8` — the id must fit at both grids
- [x] T055 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries (constitution VII, VIII)
- [x] T056 Confirm scope was not widened: **no `--card` flag anywhere**, no global registry, no meaning encoded in the id, no `@version` suffix (FR-014)
- [ ] T057 Push `feat/card-id` and open a pull request. Note in the description that `cards/example.yaml` and the demo fixtures changed, and why (constitution VII needs an explicit note).

---

## Phase 11: By Hand

**Purpose**: what no script can judge. Full checklist in `docs/testing.md`.

- [ ] T058 `python3 scripts/demo.py ~/lernkarten-demo --raw`, then drive `/cards` in a real Claude session and confirm it writes ids
- [ ] T059 Print duplex, flip on long edge, 100 % scale — each back exactly behind its front, and the id identical on both faces
- [ ] T060 **SC-007**: read an id off a printed card, use it in a Claude session to identify that card, edit the card, confirm the id still resolves
- [ ] T061 Photocopy test — the id still reads in black only at 8 pt
- [ ] T062 A Greek or Cyrillic deck still shows letters, and its ids are ordinary Latin/digits

---

## Dependencies & Execution Order

### Phase order

- **Setup (1)**: no dependencies
- **Dependencies (2)**: skipped — no dependency change
- **Format contract & primitives (3)**: **blocks everything**
- **US2 (4)**: needs Phase 3. Deliberately before US1 — it removes the ordering hazard, because the empty-string fallback lands before any fixture carries an id, so the demo decks build at every point.
- **US1 (5)**: needs Phase 4
- **US3 (6)**: needs Phase 5 (fixtures must carry ids before rendering can be measured)
- **US5 (7)**: needs Phase 3; independent of US3
- **US4 (8)**: needs Phase 3 and Phase 7's normalisation
- **Docs (9)**: after the behaviour settles
- **Gates (10)**, **By hand (11)**: last

### Story priority vs. execution order

All three P1 stories (US1, US2, US3) land before the two P2 stories. Within the
P1 group the order is US2 → US1 → US3, driven by dependency rather than priority:
the compatibility fallback must exist before fixtures change, and fixtures must
carry ids before the rendering can be measured.

### Within a story

1. Test material, so a test can fail for the right reason
2. 🔴 tests, seen failing **on their assertions** — commit here
3. 🟢 deterministic half, then model-driven half
4. Layout, if anything visible changes
5. Refactor

**Never move an implementation task above its test.** That is the one rule here
with no exception (constitution XI).

### Parallel groups

| Group | Tasks | Why they are safe together |
|---|---|---|
| 1 | T001, T002, T003 | independent shell commands |
| 2 | T014, T015, T016 | three different card files |
| 3 | T025, T026, T027 | three different new fixture files |
| 4 | T041, T042, T043 | `CLAUDE.md`, `docs/design.md`, `docs/testing.md` — three different docs |

### Explicitly NOT parallel

- **🔴 and 🟢 for the same behaviour.** Ever.
- **`tests/test_cardid.py`** — T005, T007, T009, T033, T034, T035 all write the same file. Sequential, despite looking independent.
- **`tests/test_check_project.py`** — T018, T029, T030 share a file.
- **`scripts/cardid.py`** — T006, T008, T010, T036, T037, T038, T047 share a file.
- **`scripts/check_project.py`** — touched by T018, T031, T032; serialize.
- **`bin/lernkarten` and `scripts/lernkarten`** — byte-identical mirrors, so T039 is one task editing both.
- **T041 and T044** both edit `CLAUDE.md` — T044 is outside group 4 for exactly this reason.

---

## Notes

- **Test-first, always.** A test written after the code tells you what the code does; only a test seen failing tells you it does what was asked.
- **T004 is the ImportError guard.** Without the stub skeleton, every Phase 3 test would fail on import and prove nothing.
- **No dependency lands here.** If one seems necessary, that is a plan change, not a task — go back to [plan.md](./plan.md) § Dependency Decisions.
- Never `git add -f` anything under `knowledge/`, `catalog/`, `cards/` (except `example.yaml`), `output/`, or `sources.yaml`.
- Never commit a binary. All four new fixtures are text.
- Extend the demo project; do not start a second fixture corpus.
- Commit after each task or logical group, and **always at a 🔴 checkpoint** — the failing commit is the evidence that test-first was honoured.
