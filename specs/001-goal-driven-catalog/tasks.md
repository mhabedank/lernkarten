---
description: "Task list for the goal-driven catalog"
---

# Tasks: Goal-driven catalog

**Input**: Design documents from `specs/001-goal-driven-catalog/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every story opens with a test task committed *failing on its assertion*. This overrides the generic "tests are optional" default — in this repo a prompt change with no failing `check_project.py` check is not implementable, it is under-specified.

**Organization**: grouped by user story so each can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: independent of its neighbours — no ordering dependency between them.
  Where [P] tasks touch **different files** they may also be fanned out concurrently,
  and those are the ones inside a `<!-- parallel-group: N -->`. Several red-test tasks
  carry [P] while editing the *same* module (`tests/test_check_project.py`): they are
  independent cases, safe to write in any order and to commit together, but they must
  **not** be edited concurrently. Those sit under `<!-- sequential -->`. Fan out on the
  group markers, never on [P] alone
- **[Story]**: US1–US6, mapping to [spec.md](spec.md)
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## A word on "Phase"

Three different numbering schemes overlap in this feature, so bare "Phase 3" is
ambiguous. In **this file** a phase is an execution block, Phase 1–12 below.
[plan.md](plan.md) numbers its own Phase 0 (Research) and Phase 1 (Design), which
are *both* finished before tasks.md Phase 1 starts. The fleet orchestrator has a
third set. Cross-references here always name the file and the title —
"tasks.md Phase 3 (Foundational)".

## Path Conventions

Single flat module, no `src/`. Implementation in `scripts/<module>.py`, prompts in `skills/<name>/SKILL.md`, tests in `tests/test_<module>.py`, test material in `tests/fixtures/demo-project/`.

---

## Phase 1: Setup

<!-- parallel-group: 1 (max 3 concurrent) -->
- [x] T001 [P] `python3 -m pip install -r requirements-dev.txt` — pytest, ruff, pillow, pyyaml
- [x] T002 [P] `scripts/install-hooks.sh` — confirm `core.hooksPath=.githooks` is set
- [x] T003 [P] `python3 scripts/make_testdata.py` — build the binary test material the demo project needs

<!-- sequential -->
- [x] T004 Branch created: `feat/goal-driven-catalog` (constitution XIV) — done in commit `53241d7`
- [x] T005 Confirm baseline green before changing anything: `ruff check . && pytest && python3 scripts/check_docs.py`

**Checkpoint**: the suite passes on an untouched tree, so every red below is caused by this feature.

---

## Phase 2: Dependencies

**⚠️ SKIPPED.** [plan.md](plan.md#dependency-decisions) states *No dependency change* — no runtime package, no dev package, no external binary, no engine bump. The Principle III reuse question (markdown parsers) is answered in [research.md R1](research.md#r1--is-there-a-library-for-parsing-the-extended-catalog). Nothing to do here; do not invent work.

---

## Phase 3: Foundational (Blocking)

**Purpose**: the plumbing every story needs. Nothing in Phases 4–9 can be committed until this is green — `goal.md` cannot be added to the fixture while `.gitignore` would swallow it, and no new skill can be created while `check_docs.py` would reject its description.

### The contracts are already written

- [x] T006 Re-read [contracts/goal-md.md](contracts/goal-md.md), [contracts/catalog-topics-md.md](contracts/catalog-topics-md.md) and [contracts/sources-yaml.md](contracts/sources-yaml.md) — these are the settled interface between the halves (constitution I). Do not re-litigate them here; changing one is a spec change

### Repo hygiene for the fifth format — 🔴 first

- [x] T007 🔴 Add a case to `tests/test_repo_hygiene.py` beside `test_no_personal_source_register_in_the_repo` (line 66) asserting no `goal.md` is versioned outside `tests/fixtures/` — fails, because nothing stops it today
- [x] T008 🔴 Add `"goal.md"` to the pattern tuple in `test_gitignore_covers_the_user_paths` (`tests/test_repo_hygiene.py:166`) — fails, `.gitignore` has no such entry
- [x] T009 🔴 Extend `test_the_demo_project_is_not_swallowed_by_gitignore` (`tests/test_repo_hygiene.py:146`) to assert the fixture's `goal.md` survives — fails; its docstring already names this exact hazard for `sources.yaml`
- [x] T010 Add `goal.md` to `.gitignore` beside `sources.yaml` (line 5), **and** `!tests/fixtures/**/goal.md` beside the existing negation (line 18), with a comment saying why — `goal.md` has no slash, so it matches at every level ([research.md R2](research.md#r2--where-does-goalmd-live-and-how-does-the-fixture-survive-gitignore))
- [x] T011 Add `goal\.md` to the grep pattern in `.githooks/pre-commit` (lines 7–8) so a stray goal is blocked before the round trip. The pattern is anchored (`^(knowledge/|catalog/|…|sources\.yaml)`), so this blocks a **root-level** `goal.md` only — the same reach `sources\.yaml` has there today. A `goal.md` deeper in the tree is caught by T010's `.gitignore` entry, which does match at every level; the hook is the second line of defence, not the first. Do not un-anchor the pattern to close the difference — that would start matching paths like `docs/goal.md.example`
- [x] T012 Verify T007–T009 now pass, and that `git check-ignore -v goal.md` reports the new rule while the fixture path does not

### Skill-name disambiguation — 🔴 first

- [x] T013 🔴 Create `tests/test_check_docs.py` — this module does not exist; `scripts/check_docs.py` has no coverage at all today. First case: a skill whose description names triggers but no domain word is reported. Fails, the rule does not exist
- [x] T014 🔴 Second case in `tests/test_check_docs.py` (**after** T013 — same file, T013 creates it; the [P] this task used to carry paired it with T007–T009, which are a different module): every shipped skill passes the rule — fails, because `catalog` and `ingest` descriptions do not say what the topics and sources are *for*
- [x] T015 Add the domain-word rule to `check_skills()` in `scripts/check_docs.py` (after the `"Triggers" not in description` branch, line 91), requiring `flashcard` or `flashcards` in the description
<!-- parallel-group: 2 (max 3 concurrent) — two skill files, no overlap -->
- [x] T016 [P] Retrofit `skills/catalog/SKILL.md` frontmatter description to name flashcards
- [x] T017 [P] Retrofit `skills/ingest/SKILL.md` frontmatter description to name flashcards

<!-- sequential -->
- [x] T018 Confirm `python3 scripts/check_docs.py` is green and T013–T014 pass

### The catalog parser — refactor, not new behaviour

- [x] T019 Extract the heading scan in `check_catalog()` (`scripts/check_project.py:163`) into a pure `parse_catalog(text)` returning topics, subtopics and their attribute lines, reporting nothing. **No new red test**: this changes no behaviour and is guarded by the existing catalog cases in `tests/test_check_project.py` (lines 204–220). Say so in the commit rather than faking a red
- [x] T020 Confirm `pytest tests/test_check_project.py` is unchanged-green after the extraction

**Checkpoint**: `goal.md` is a protected user-content path, the skill rule is enforced, and there is a parser to hang new rules on. Commit.

---

## Phase 4: User Story 1 — State what you are actually learning (P1) 🎯 MVP

**Goal**: `/learning-goal` captures the target into `goal.md`, with independent areas and conflict-aware re-runs.

**Independent Test**: `python3 scripts/check_project.py tests/fixtures/demo-project` — `goal.md` exists, frontmatter complete, at least one area with at least one topic.

### Test material first

- [x] T021 [US1] Write `tests/fixtures/demo-project/goal.md` per [contracts/goal-md.md](contracts/goal-md.md) — invented Kestrel Islands content (constitution VII), **two independent areas** so US2's area-separation rule has something to bite on, one required topic nothing covers (the future gap), one out-of-scope entry matching existing demo material

### 🔴 Red

<!-- sequential -->
- [x] T022 🔴 [P] [US1] `tests/test_check_project.py`: a `goal.md` missing `kind` is reported, the message naming the key — fails
- [x] T023 🔴 [P] [US1] `tests/test_check_project.py`: an unknown `depth` is reported, naming the value and the closed set — fails
- [x] T024 🔴 [P] [US1] `tests/test_check_project.py`: an `updated` that is not ISO is reported — fails

<!-- sequential -->
- [x] T025 🔴 [P] [US1] `tests/test_check_project.py`: an area with no topics is reported, naming the area — fails

<!-- sequential -->
- [x] T026 🔴 [US1] `tests/test_check_project.py`: a required topic absent from the catalog **warns** — fails
- [x] T027 [US1] *Regression guard, green from the start*: a project with no `goal.md` passes unchanged. Add it anyway — it is the assertion protecting SC-006, and it must never go red

**Checkpoint**: `pytest tests/test_check_project.py` red on five assertions. Commit.

### 🟢 Green — deterministic half

- [x] T028 [US1] Add `check_goal(project, report)` to `scripts/check_project.py` beside `check_sources()` — frontmatter via the existing `frontmatter()` helper, `updated` via the existing `DATE` regex, closed sets as module constants next to `SOURCE_TYPES`
- [x] T029 [US1] Wire `check_goal` into `check()` (`scripts/check_project.py:248`) **before** `check_catalog`, and pass the required topics through so the drift warning in T026 can fire
- [x] T030 [US1] Confirm every message names the file and the culprit, matching the existing house style

### 🟢 Green — model-driven half

- [x] T031 [US1] Write `skills/learning-goal/SKILL.md` — name `learning-goal` (not `goal`; generic names risk shadowing, **FR-025**), description naming triggers **and** flashcards, procedure covering: accept prose/text/URLs (FR-001), fetch requirement documents without registering them as sources (FR-004), group required topics into independent areas (FR-003), detect and ask about contradictions on re-run (FR-005), name what a narrowing change would orphan (FR-006), **merge without asking when the re-run only adds — preserving the existing areas and topics and moving `updated` to today (FR-007)**, refuse to invent a syllabus (FR-008)
- [x] T032 [US1] Confirm `python3 scripts/check_docs.py` accepts the new skill

### Refactor

- [x] T033 [US1] Clean up `check_goal` now that it is green — red, green, *refactor*

**Checkpoint**: US1 stands alone. A user can state a goal and have it validated, with nothing else built.

---

## Phase 5: User Story 2 — A catalog built from the goal (P2)

**Goal**: `/catalog` derives the tree from `goal.md` and marks gaps and out-of-scope material.

**Independent Test**: `python3 scripts/check_project.py tests/fixtures/demo-project --strict` with a catalog carrying one gap and one out-of-scope subtopic.

### Test material first

- [x] T034 [US2] Extend `tests/fixtures/demo-project/catalog/topics.md`: a `Goal:` header field, one subtopic with `Status: gap` and `References: none` (the topic T021 left uncovered), one with `Status: out of scope` keeping its references
- [x] T035 [US2] Check whether the out-of-scope subtopic chosen in T034 has cards in `tests/fixtures/demo-project/cards/*.yaml`. If it does, either pick a subtopic that has none, or delete those cards and update **both** hard-coded counts — `DEMO_CARD_COUNT` at `tests/test_e2e.py:25` and the bare `assert counts["cards"] == 31` at `tests/test_check_project.py:108` (both currently 31) — a demo that ships cards for its own out-of-scope subtopic contradicts US3

### 🔴 Red

<!-- sequential -->
- [x] T036 🔴 [P] [US2] `tests/test_check_project.py`: a subtopic with no references and no `Status: gap` is reported by name — fails, nothing checks this today
- [x] T037 🔴 [P] [US2] `tests/test_check_project.py`: `Status: gap` with `References: none` passes — fails
- [x] T038 🔴 [P] [US2] `tests/test_check_project.py`: an unknown `Status:` value is reported, naming subtopic and value — fails
<!-- sequential -->
- [x] T039 [US2] *Regression guard*: today's catalog shape, with no `Status:` anywhere, still passes

**Checkpoint**: red on three assertions. Commit.

### 🟢 Green — deterministic half

- [x] T040 [US2] Add the `Status:` and `References: none` rules to `parse_catalog()` / `check_catalog()` in `scripts/check_project.py` (invariants C-6, C-7 in [data-model.md](data-model.md))

### 🟢 Green — model-driven half

- [x] T041 [US2] Rewrite the ordering in `skills/catalog/SKILL.md`: when `goal.md` exists, build the hierarchy from its areas and required topics **first**, then attach `knowledge/` references; each area becomes its own top-level topic and areas are never merged
- [x] T042 [US2] Add the marking rules to `skills/catalog/SKILL.md`: uncovered required topic → `Status: gap` + `References: none` + the bullets describing what it should cover; unmatched material → `Status: out of scope` with references kept
- [x] T043 [US2] Add the no-goal path to `skills/catalog/SKILL.md`: build exactly as today, **and** tell the user the catalog covers the material rather than the topic, pointing at `/learning-goal`. This is the discovery path for the whole feature
- [x] T044 [US2] Add the closing report to `skills/catalog/SKILL.md`: covered / gap / out-of-scope counts, pointing at `/research-gaps` when there is a gap

**Checkpoint**: gaps and out-of-scope material are visible in the catalog file. US1 still passes its own test.

---

## Phase 6: User Story 3 — Cards stay inside the goal (P3)

**Goal**: `/cards` skips marked subtopics, reports out-of-scope as a bare count and gaps as a named warning.

**Independent Test**: run `/cards` over the demo project; no card carries an out-of-scope or gap subtopic.

### 🔴 Red

- [x] T045 🔴 [US3] `tests/test_check_project.py`: a card whose `subtopic` is marked `Status: out of scope` or `Status: gap` in the catalog **warns** — fails. This is the artifact-level assertion that makes US3 implementable at all; without it the story is only console output and constitution XI would call it under-specified
- [x] T046 [US3] *Regression guard*: a card for an ordinary subtopic warns about nothing

### 🟢 Green — deterministic half

- [x] T047 [US3] Extend `check_cards()` in `scripts/check_project.py` (line 202) to take the marked subtopics from `check_catalog()` and warn on a card that belongs to one. **Warning, not error** — the user may have named the subtopic explicitly, which **FR-020** permits

### 🟢 Green — model-driven half

- [x] T048 [US3] Add scope skipping to `skills/cards/SKILL.md`: with no arguments, skip `Status: out of scope` and `Status: gap`
- [x] T049 [US3] Add the asymmetric reporting to `skills/cards/SKILL.md` — out-of-scope as a **count only**, no warning, no list; gaps as a **warning that the deck does not cover the whole topic**, naming every gap and pointing at both ways to act. State the asymmetry's reason in the prompt so it survives editing: skipping out-of-scope is the feature working, a gap means the deck is incomplete
- [x] T050 [US3] Add the override to `skills/cards/SKILL.md`: naming an out-of-scope subtopic explicitly still generates it

**Checkpoint**: the low-code failure is fixed — off-goal material no longer becomes cards, and the user is told what is missing.

---

## Phase 7: User Story 4 — Close the gaps (P4)

**Goal**: `/research-gaps` fills gap subtopics from the web into a distinctly marked source type.

**Independent Test**: a `sources.yaml` entry of `type: research`, one knowledge file with a `url:` in its frontmatter, and the catalog entry no longer marked `Status: gap`.

### Test material first

- [x] T051 [US4] **Do this after T054, not before** — `test_the_demo_project_is_consistent` (`tests/test_check_project.py:99`) asserts the demo has zero errors, so a `research` source added while `SOURCE_TYPES` still rejects it turns an unrelated existing test red for the wrong reason. Add a `type: research` entry to `tests/fixtures/demo-project/sources.yaml` with a `gap:` naming the T034 gap subtopic, and one document under `tests/fixtures/demo-project/knowledge/<research-id>/` carrying `source` / `url` / `ingested` frontmatter — invented content, a plausible but non-resolving example URL

### 🔴 Red

<!-- sequential -->
- [x] T052 🔴 [P] [US4] `tests/test_check_project.py`: `type: research` without `gap` is reported, naming the source id — **assert the message text, not merely that an error fired**. Today `research` is an unknown type, so an error already appears for the wrong reason; a bare `assert report.errors` is green from the start and proves nothing. Make it red on the *missing-`gap`* wording
- [x] T053 🔴 [P] [US4] `tests/test_check_project.py`: `type: research` with `gap` and neither `path` nor `url` passes — fails

**Checkpoint**: red on two assertions. Commit.

### 🟢 Green — deterministic half

- [x] T054 [US4] Add `research` to `SOURCE_TYPES` in `scripts/check_project.py:28` with no location field (like `zotero`), and add the `gap`-required rule in `check_sources()`

### 🟢 Green — model-driven half

- [x] T055 [US4] Write `skills/research-gaps/SKILL.md` — name `research-gaps` (not `research`, **FR-025**), description naming triggers and flashcards, procedure covering: take `Status: gap` subtopics as the work list, exit cleanly when there are none, register findings as `type: research` with `gap:`, write one document per gap with its `url`, **never** write a document without a retrieved source, report gaps it could not close, and flip the closed catalog entries off `Status: gap`
- [x] T056 [US4] Add the offline degraded path explicitly to `skills/research-gaps/SKILL.md`: report, write nothing, never fill from the model's own recall
- [x] T057 [US4] Add a note to `skills/sources/SKILL.md` that `research` entries are written by `/research-gaps`, and that deleting one plus its knowledge folder returns its subtopics to `Status: gap`
- [x] T116 [P] [US4] `sources.example.yaml` — add a `type: research` entry **commented out**, with a line saying `/research-gaps` writes these and a user does not hand-author one. The spec's Format Contracts table lists this file under the `sources.yaml` change; leaving it out is why the table and the tasks disagreed. Commented, so the example register keeps demonstrating only what a user actually types

**Checkpoint**: a user can learn a topic their own material does not cover, and can still tell the two apart.

---

## Phase 8: User Story 5 — A subtopic under more than one topic (P5)

**Goal**: containment is many-to-many (`Parents:`), association is symmetric (`Related:`), and one card file is chosen by projection rather than by flattening the model.

**Independent Test**: `check_project.py` passes a two-parent subtopic and reports a dangling `Related:` name; `/cards` on the secondary parent generates once, into the primary's file.

**⚠️ This is the separable story.** It serves catalog fidelity and connection cards, not the source-bound-cards problem the feature exists for. If scope has to be cut, cut here — and note that the catalog then says "Access control is under Security" when the truth is "under both".

### Test material first

- [x] T058 [US5] Extend `tests/fixtures/demo-project/catalog/topics.md` with one two-parent subtopic (`Parents:` primary first), its reciprocal `Also covers:` line on the secondary topic, and one `Related:` pair

### 🔴 Red

<!-- sequential -->
- [x] T059 🔴 [P] [US5] `tests/test_check_project.py`: a `Parents:` naming a topic that does not exist is reported (C-1) — fails
- [x] T060 🔴 [P] [US5] `tests/test_check_project.py`: a primary parent that is not the heading the subtopic sits under is reported (C-2) — fails
- [x] T061 🔴 [P] [US5] `tests/test_check_project.py`: a non-primary parent with no reciprocal `Also covers:` is reported (C-3) — fails

<!-- sequential -->
- [x] T062 🔴 [P] [US5] `tests/test_check_project.py`: an `Also covers:` naming a subtopic whose `Parents:` omits that topic is reported (C-4) — fails
- [x] T063 🔴 [P] [US5] `tests/test_check_project.py`: a `Related:` name that is not a subtopic is reported (C-5) — fails

<!-- sequential -->
- [x] T064 🔴 [US5] `tests/test_check_project.py`: a two-parent subtopic counts **once** in `report.counts["subtopics"]` and appears once in the set returned to `check_cards()` (C-9) — fails
- [x] T065 [US5] *Regression guard*: a catalog with no `Parents:` and no `Related:` behaves exactly as before

**Checkpoint**: red on six assertions. Commit. There is deliberately **no acyclicity test** — the catalog is two levels deep and edges run only topic → subtopic, so the graph is bipartite and cycles cannot form ([data-model.md](data-model.md)).

### 🟢 Green — deterministic half

- [X] ⚠️ **Reopened, now closed by T122** T066 [US5] *(reopened — BUG-005)* Implement invariants C-1 to C-5 in `parse_catalog()` / `check_catalog()` in `scripts/check_project.py`. It was marked done and the five invariants do work — for names without a comma. `catalog_names()` splits on every comma unconditionally, so a name that contains one is torn into pieces that match nothing and all five checks fire at once ([BUG-005](bugs/BUG-005.md)). T120–T124 finished it and are green, so this closes with them
- [x] T119 [US5] For C-4, compare only the **name** on an `Also covers:` line: the contract writes `Also covers: Access control (cards in cards/security.yaml)` ([contracts/catalog-topics-md.md](contracts/catalog-topics-md.md)), so strip the trailing parenthetical before matching or every reciprocity check fails on a catalog that follows the contract
- [x] T067 [US5] Implement C-9 — `Also covers:` must not be parsed as a subtopic heading, or the existing `###` scan double-counts and `check_cards()` sees a duplicate name

### 🟢 Green — model-driven half

- [x] T068 [US5] Add multi-parent writing to `skills/catalog/SKILL.md`: a subtopic belonging under several topics is written **once** under its primary, carrying `Parents:` with the primary first; every other parent gets an `Also covers:` line naming where the cards live
- [x] T069 [US5] Add the primary-reassignment rule to `skills/catalog/SKILL.md`: if the primary parent is out of scope and another parent is required, the in-scope parent becomes primary
- [x] T070 [US5] Add the projection rule to `skills/cards/SKILL.md`: cards written once, into the primary parent's `cards/<topic-slug>.yaml`, with the primary topic as `topic:`; naming a secondary parent still reaches the subtopic and reports which file its cards went into
- [x] T071 [US5] Add connection cards to `skills/cards/SKILL.md`: use `Related:` for distinction and connection cards, written once rather than once per branch, and never for a target that is a gap or out of scope

**Checkpoint**: the catalog stops lying about shared subtopics, and connection cards exist.

---

## Phase 9: User Story 6 — The documentation describes the pipeline that exists (P6)

**Goal**: README, landing page, brand graphics and workflow docs stop saying five commands.

**Independent Test**: `python3 scripts/check_docs.py` green; no "five commands" anywhere outside `specs/`; `render_brand.py` reproduces the committed PNGs.

**This ships with whatever subset of US1–US5 lands, in the same PR.** A release whose landing page promises five commands while the plugin has seven is not a release.

### 🔴 Red

- [x] T072 🔴 [P] [US6] Add a case to `tests/test_repo_hygiene.py` asserting no versioned file outside `specs/` contains "five commands" (case-insensitive) — fails on all six files that match today: `README.md` (lines 1, 8, 46, 168), `docs/index.html` (lines 7, 11, 181, 361, 405), `docs/workflow.md` (line 26), `assets/brand/banner.typ` (line 1), `assets/brand/pipeline.typ` (line 1) and `assets/brand/social-card.typ` (line 23). Re-run `git grep -in "five commands"` before writing the assertion rather than trusting this list

### 🟢 Green — text

<!-- parallel-group: 10 (max 3 concurrent) — README.md, CLAUDE.md, docs/testing.md: three different files -->
- [x] T076 [P] [US6] `CLAUDE.md` — the pipeline line, and `goal.md` in the conventions list beside the other artifacts
- [x] T077 [P] [US6] `docs/testing.md` — the fixture table gains `goal.md` and the `research` source type; the manual checklist gains the rows from [quickstart.md](quickstart.md) §4
- [x] T073 [P] [US6] `README.md` — the banner alt text (line 1), the intro sentence (line 8), the `## The five commands` heading (line 46), the pipeline diagram alt text (line 48), the command table (lines 52–56) and the "five commands" mention near line 168. Mark `/learning-goal` and `/research-gaps` optional
<!-- sequential — T074 and T075 edit the same file -->
- [x] T074 [US6] `docs/workflow.md` — renumber the step sections, add one per new step in pipeline order, and rewrite Step 3 for the goal-first ordering
- [x] T075 [US6] `docs/workflow.md` — add a passage explaining what a gap is, what out-of-scope material is, and what the user does about each (**FR-040**), and fix the "five commands" sentence at line 26

### 🟢 Green — visible surfaces

- [x] T078 [US6] Read `docs/design.md` §"Type" and §"The screen surfaces" before touching anything visible (constitution XVI)
- [x] T079 [US6] `assets/brand/common.typ:67` — replace the `commands` tuple with the new pipeline
<!-- parallel-group: 11 (max 3 concurrent) — three brand sources, all after T079, all before T083 -->
- [x] T080 [P] [US6] `assets/brand/banner.typ` — the "five commands" comment (line 1) and the rendered command row
- [x] T081 [P] [US6] `assets/brand/pipeline.typ` — the comment (line 1) and the step entries (lines 33+), marking the optional steps
- [x] T082 [P] [US6] `assets/brand/social-card.typ:23` — the standfirst "Five commands."
<!-- sequential -->
- [x] T083 [US6] `python3 scripts/render_brand.py` and commit the regenerated PNGs. **Never** hand-edit a PNG (constitution IX)
- [x] T084 [US6] `docs/index.html` — **every** "five commands" occurrence outside the step strip: the `<meta name="description">` (line 7), `og:description` (line 11), the `/* Five commands */` CSS comment (line 181), the `hero__lead` paragraph "Five commands later you print an A4 sheet…" (line 361) and the `<h2>five commands</h2>` section heading (line 405). T085/T086 cover the strip itself; without this task T103 and SC-010 still fail on lines 361 and 405
- [x] T085 [US6] `docs/index.html` — the step strip markup (lines 408+): add the two steps, marking the optional ones visually distinct
- [x] T086 [US6] `docs/index.html` — the grid at line 182 and the breakpoint rules at lines 291–296 and 319. Do **not** go to seven equal columns: the caption measure drops from ~176 px to ~114 px under 13.5 px text ([research.md R3](research.md#r3--how-do-seven-steps-fit-a-five-column-strip)). Re-derive the orphaned-last-step rule for the new count instead of inheriting the five-step one
- [x] T087 [US6] Check the strip by eye at > 1080 px, 541–1080 px and ≤ 540 px — every step legible, optional steps readable as optional, nothing orphaned by accident. Also confirm SC-013's other half: the **README command table** still fits one screen at the desktop breakpoint now that it has seven rows
- [x] T088 [P] [US6] `docs/design.md` — update §"The screen surfaces" if the strip gained a new part

**Checkpoint**: the picture, the README and the plugin agree.

---

## Phase 10: Cross-Cutting

- [x] T089 Amend `.specify/memory/constitution.md` Principle I: the format table gains `goal.md`, making it five formats, not four
- [x] T090 Amend `.specify/memory/constitution.md` Identity section: the pipeline is no longer five steps
- [x] T114 Amend `.specify/memory/constitution.md` Principle XI: extend the existing "Layout and design" carve-out to cover **run output**. A requirement satisfied only by what a skill says during a run (FR-013, FR-016, FR-018, FR-019) has no on-disk artifact, so no `check_project.py` check can be written to fail against it — say so, and send it to the manual checklist the way layout already goes there. Without this, XI's model-driven clause ("if no failing check can be written, the requirement is under-specified") reads as forbidding four shipped requirements. See [plan.md](plan.md#complexity-tracking)
- [x] T091 Bump the constitution version and add a dated amendment note in the same style as the existing 2.2.0 / 2.1.0 entries, covering T089, T090 and T114
- [x] T092 Bump `version` in `.claude-plugin/marketplace.json` **and** `.claude-plugin/plugin.json` (both read `0.2.0` today) — the plugin gained two commands, and the two files drift apart if only one is bumped
- [x] T093 Confirm every relative markdown link resolves: `python3 scripts/check_docs.py` fails on a dead one
- [x] T094 English throughout — code, comments, docstrings, docs, commit subjects (constitution XIII)

- [x] T118 Wave G evidence ([plan.md](plan.md#test-plan-first)) — **before Phase 11, never after**. Copy `tests/fixtures/demo-project` to a scratch directory, run the four changed/new skills against the **copy**, and diff the result against the committed fixture. Where they disagree, the hand-written fixture is wrong and gets reconciled; where they agree, the prompts are proven to produce it. Two hard rules:
  - **Never run `/research-gaps` against the fixture or its copy for real.** It retrieves third-party web text, and constitution VII requires every byte of the demo project to be invented for this repo. T051's `research` document stays hand-written; the offline path is exercised by T112 instead.
  - If the reconciliation changes any fixture file, **re-run all of tasks.md Phase 11** — the gates and the e2e counts were measured against the old fixture

---

## Phase 11: Gates

- [x] T095 `ruff check .`
- [x] T096 `ruff format --check .`
- [x] T097 `pytest`
- [x] T098 `lernkarten check cards/example.yaml` — the spelling constitution XII and `CLAUDE.md` use; `bin/lernkarten check …` is the same thing from a clean checkout
- [x] T099 `python3 scripts/check_docs.py`
- [x] T100 `python3 scripts/check_project.py tests/fixtures/demo-project --strict`
- [x] T101 `python3 scripts/make_testdata.py && LERNKARTEN_E2E=1 pytest tests/test_e2e.py -v` — catches `DEMO_CARD_COUNT` if T035 changed it
- [x] T102 `git status` clean of user content — no real `goal.md`, `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries
- [x] T103 `git grep -i "five commands"` returns nothing outside `specs/`
- [ ] T104 Push the branch and open a pull request — `main` rejects direct pushes
- [ ] T105 PR description carries the **Principle VII note** (what user-content rule changed and why) and calls out the **constitution amendment** for a reviewer

---

## Phase 12: By Hand

**Purpose**: what no script can judge. The full checklist is [quickstart.md](quickstart.md) §4 and `docs/testing.md`.

- [ ] T106 `python3 scripts/demo.py ~/lernkarten-demo --raw`, then drive the new skills in a real Claude session
- [ ] T107 No-goal advisory: delete `goal.md`, run `/catalog` — says the catalog covers the material rather than the topic, points at `/learning-goal`
- [ ] T108 Reporting asymmetry: run `/cards` — out-of-scope as a bare count, gaps as a warning naming each one
- [ ] T109 Goal conflict: run `/learning-goal` twice with contradictory briefs — every contradiction listed and asked, nothing written until answered
- [ ] T110 Narrowing consequence: make a required topic out-of-scope on the second run — names the affected catalog subtopics and card files
- [ ] T117 Catalog closing report (FR-016): run `/catalog` on a project with at least one gap — covered / gap / out-of-scope counts are printed and `/research-gaps` is named. The fourth console-only requirement; the Complexity Tracking row in [plan.md](plan.md#complexity-tracking) lists T107/T108 for FR-013/018/019, and this is FR-016's
- [ ] T115 Additive re-run (FR-007): run `/learning-goal` a second time with a brief that only **adds** topics — merges without asking a single question, every existing area and topic survives, and `updated` moves to today. The counterpart to T109; between them they cover both halves of SC-005
- [ ] T111 Borrowed subtopic: `/cards <secondary parent>` — generated once, and the file it went into is reported
- [ ] T112 Offline: run `/research-gaps` with no network — reports unclosed gaps, writes nothing
- [ ] T113 Print duplex at 100 % scale and confirm nothing about the card changed — this feature must not have touched it

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)** → no dependencies
- **Phase 2 (Dependencies)** → skipped entirely
- **Phase 3 (Foundational)** → **blocks everything**. T010–T011 must land before any fixture `goal.md` is committed; T015–T017 before any new skill is created; T019 before any new catalog rule
- **Phase 4 (US1)** → needs Phase 3
- **Phase 5 (US2)** → needs US1 (the goal must exist and be valid before a catalog can be built from it)
- **Phase 6 (US3)** → needs US2 (`Status:` must exist before `/cards` can skip on it)
- **Phase 7 (US4)** → needs US2 (gaps must exist before they can be closed). Independent of US3 and US5
- **Phase 8 (US5)** → needs Phase 3's parser **and US2**. The graph rules themselves (C-1…C-5, C-9) need only the parser, but T069 (FR-015, the in-scope parent becomes primary) and T071 (FR-024, no connection card for a gap or out-of-scope target) both read `Status:`, which US2 introduces — and T058 edits the same fixture file as T034. Independent of US3 and US4
- **Phase 9 (US6)** → after the step list stops moving; ships in the same PR regardless
- **Phase 10–12** → last, in order

### Story independence

| Story | Depends on | Can ship without |
|---|---|---|
| US1 | Phase 3 | everything else |
| US2 | US1 | US3, US4, US5 |
| US3 | US2 | US4, US5 |
| US4 | US2 | US3, US5 |
| US5 | Phase 3 + US2 | US3, US4 — **and is the one to cut if scope must shrink** |
| US6 | whatever shipped | nothing — it ships with the rest |

### Parallel opportunities

- T001–T003 (setup) all at once
- T007–T009 (`test_repo_hygiene.py`) alongside T013 (`test_check_docs.py`) — different files. **T014 is not parallel with T013**: same file, and T013 creates it
- T016/T017 (two skill descriptions) — parallel
- T022–T025 (`goal.md` cases) and T059–T063 (graph cases) are independent of one another, so they can be **written in any order and committed together** — but all ten edit `tests/test_check_project.py`, so they are **not** concurrent work and carry no group marker. See the [P] definition above
- T073/T076/T077 (three documents) — parallel; T080–T082 (three brand sources) — parallel
- Once US2 lands, **US4 and US5 can proceed simultaneously** — different rules, different fixture regions

### Not parallel

- 🔴 and 🟢 for the same behaviour. Ever.
- `scripts/check_project.py` is touched by US1, US2, US3, US4 and US5 — serialize every edit to it. This is the busiest file in the feature and the likeliest merge conflict
- `tests/test_check_project.py` is edited by T022–T027, T036–T039, T045–T046, T052–T053 and T059–T065 — serialize every edit to it, exactly as for `scripts/check_project.py`. This is the omission that let the same-file [P] tasks look fan-outable
- `tests/fixtures/demo-project/catalog/topics.md` is edited by T034, T058 — serialize
- `assets/brand/common.typ` (T079) before the three graphics that read it (T080–T082), and all of them before `render_brand.py` (T083)

---

## Implementation Strategy

**MVP = Phase 3 + Phase 4 (US1).** That alone gives a user a validated, persistent statement of what they are trying to learn — useful on its own, and the criterion everything else needs.

**First useful increment = + US2 + US3.** That is the whole reported problem fixed: off-goal material stops becoming cards, and the user is told what the deck does not cover. If only one thing ships, ship this.

**Then US4**, which turns the named gap list into something the pipeline can close by itself.

**US5 last, and droppable.** It is the only story that does not serve the original complaint.

**US6 is not a phase you defer** — it ships with whatever landed.

## Notes

- Test-first is not waivable (constitution XI). A prompt change with no failing `check_project.py` check means the requirement is under-specified — go back to the spec rather than forward to the prompt
- The run-output requirements (no-goal advisory, out-of-scope count, gap warning) have **no** automated assertion, because nothing on disk records what a skill said. They are T107–T110, by hand. This is stated rather than hidden
- Never `git add -f` a real `goal.md`, `sources.yaml`, or anything under `knowledge/`, `catalog/`, `cards/` (except `example.yaml`) or `output/`
- Never hand-edit a rendered PNG — edit the Typst source and re-render
- Extend the demo project; never start a second corpus
- Commit at every 🔴 checkpoint, with the failure output in the message where it is not obvious

---

## Phase 12: Bugfix (BUG-001 to BUG-005)

**Bugfix**: 2026-08-19 — [BUG-001](bugs/BUG-001.md) to [BUG-005](bugs/BUG-005.md)
Updated from bugfix patch.

**Purpose**: the five defects reported against this feature's artifacts after it
merged. Every one of them is on the *accepted* path — nothing fails a build, so
every red artifact here is a check rather than a crash, exactly as constitution
XI's model-driven clause prescribes.

**Why one phase and not five.** Four of the five change
`scripts/check_project.py`, `skills/`, or `tests/fixtures/demo-project`, which
serializes most of the work whatever order it is written in. The 🔴/🟢 pairs are
still per-bug and none of them may be reordered.

### BUG-005 — a comma in a name (finishes the reopened T066)

- [X] T120 🔴 [US5] `tests/test_check_project.py`: a catalog with a topic named
      `Tides, currents & winds`, a subtopic naming it in `Parents:` (primary
      first) and the reciprocal `Also covers:`, validates **clean** — red today
      with five errors, none of which names the real cause (FR-049)
- [X] T121 🔴 [US5] `tests/test_check_project.py`: the same name reached through
      `Related:`, and a genuinely dangling name **after** a comma-bearing one on
      the same line, still reported — red. One test does not cover three call
      sites, and the second half guards against a fix that stops reporting
      dangling names at all (FR-049, FR-033, FR-034)
- [X] T122 [US5] Rewrite `catalog_names()` in `scripts/check_project.py` to take
      the set of declared names and match longest-first before splitting the
      remainder on commas. Every call site passes the names it validates
      against: topics for `Parents:`, subtopics for `Related:` and
      `Also covers:`. **This closes the reopened T066**
- [X] T123 [US5] Give one topic in `tests/fixtures/demo-project/catalog/topics.md`
      a comma in its name, referenced from all three attribute lines — the repo
      rule is that a new failure mode belongs in the demo project
- [X] T124 [US5] State it where the name is written, not only where it is read:
      `skills/catalog/SKILL.md` and the catalog contract under `contracts/` say
      a name may contain a comma and does not need escaping

**Checkpoint**: T120 and T121 green, T066 closes, `check_project.py --strict` on
the demo project exits 0.

### BUG-001 — the card markup contract

- [X] T125 🔴 [P] `tests/test_check_project.py`: a card whose `back` contains
      `**bold**` is reported, naming the card — red today, nothing looks at card
      markup at all (FR-043)
- [X] T126 🔴 `tests/test_check_project.py`: a card whose `back` contains a
      backslash directly followed by `*` is reported, naming the card — red.
      Same file as T125, so **not** parallel with it (FR-043)
- [X] T127 Implement both checks in `scripts/check_project.py`: `**...**` in
      `front` or `back`, and `\` immediately followed by `*`, `_`, `#`, `@`,
      `<`, `$` or a backtick. The message says what Typst will do, not just that
      it is wrong (FR-043)
- [X] T128 Write the rule into all three places that carry the contract —
      `CLAUDE.md`, `skills/cards/SKILL.md`, `docs/workflow.md`: `*bold*`,
      `_italic_`, `**...**` is markdown and yields two empty strong elements,
      and `\` is a line break only before whitespace (FR-041, FR-042)
- [X] T129 Add a card exercising both to
      `tests/fixtures/demo-project/broken/`, with its row in that folder's
      `README.md` — the established home for a failure mode with a named culprit

**Checkpoint**: T125 and T126 green; the three prose files agree with each other
and with the check.

### BUG-002 and BUG-003 — the Zotero writer

- [X] T130 🔴 `tests/test_ingest_sources.py`: two items in
      `tests/fixtures/zotero/library.json` sharing one title produce **two**
      documents, each carrying its own `zotero_key`, and the run reports `0
      skipped` against an empty knowledge directory — red today: one file, one
      "skipped" (FR-044, FR-045)
- [X] T131 🔴 `tests/test_ingest_sources.py`: a second run over the same library
      reports both as skipped and writes nothing new — the incremental path must
      survive the fix. Same file as T130, so serialize (FR-045)
- [X] T132 🔴 `tests/test_ingest_sources.py`: the summary contains the absolute
      path of the target directory (FR-046)
- [X] T133 In `scripts/zotero_ingest.py`: fall back to `<slug>-<zotero_key>.md`
      on a collision; decide "skipped" by reading the frontmatter `zotero_key`
      rather than by comparing mtimes; keep a set of paths written this run so a
      same-run collision can never take the skip branch; add `collisions` to the
      summary (FR-044, FR-045)
- [X] T134 In `scripts/zotero_ingest.py`: print the resolved absolute target
      directory in the summary. In `skills/ingest/SKILL.md:40`: pass `--project`
      explicitly and say in the prose that the working directory is not what
      decides (FR-046)
- [X] T135 [P] Add the two same-title items to
      `tests/fixtures/zotero/library.json` with their generator PDFs, and note
      in `tests/fixtures/zotero/README.md` what they are for

### BUG-004 — thin document versus failed extraction

- [X] T136 🔴 `tests/test_ingest_sources.py`: an item whose PDF yields a short
      but non-empty text is written **with that text** and a yield marker, and
      **without** `pending:` — red today, it is written as `pending:` with the
      text thrown away (FR-047)
- [X] T137 Split the two signals in `extract()`
      (`scripts/zotero_ingest.py:92-116`): no text at all → a scan → `pending:`;
      short text → return it with its length. The `len(text) < 200` threshold
      currently answers both questions and can only answer one (FR-047)
- [X] T138 Write the marker into the knowledge frontmatter contract at
      `skills/ingest/SKILL.md:76-90`, and teach `skills/catalog/SKILL.md` what a
      marked document may be used as evidence for — referenced yes, coverage of
      a required topic no (FR-047, FR-048)
- [X] T139 🔴 `tests/test_check_project.py`: the marker is accepted in knowledge
      frontmatter and a required topic whose only reference is a marked document
      is reported — the model-driven half's red artifact for FR-048, per
      constitution XI (FR-048)
- [X] T140 Implement that check in `scripts/check_project.py` (FR-048)
- [X] T141 [P] Add one marked document to
      `tests/fixtures/demo-project/knowledge/`, generated from a deliberately
      thin Typst source under `generators/`. *(Done in two halves, and the split
      is deliberate: the Zotero side needed a real PDF, so `generators/zotero-cover.typ`
      and ITEM11 make the third state reachable through the extractor. The demo
      project itself gets a hand-written marked document referenced **alongside**
      a full one — a project that is consistent, which is what that corpus is
      for. The failure case, a subtopic backed by nothing else, stays in
      `tests/test_check_project.py`, because a warning in the demo project would
      fail `check_project.py --strict` in CI forever.)*

### Gates

- [X] T142 [P] `ruff check . && ruff format --check .`
- [X] T143 `pytest`
- [X] T144 [P] `bin/lernkarten check cards/example.yaml`
- [X] T145 [P] `python3 scripts/check_docs.py`
- [X] T146 `python3 scripts/make_testdata.py` then
      `python3 scripts/check_project.py tests/fixtures/demo-project --strict` and
      `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` — this batch touches the
      pipeline and the fixture corpus, so the once-before-the-PR set in
      constitution XII is **not** skippable here the way it was for feature 002
- [X] T147 Run `/speckit.bugfix.verify` and confirm every report reads
      `Status: Patched` with its tasks closed

### Dependencies

- T120–T121 before T122; T122 closes T066
- T125–T126 before T127; T128 may run alongside T127 (different files), T129 after both
- T130–T132 before T133–T134; T135 before T130 can pass, since the test needs the fixture items
- T136 before T137; T139 before T140
- All of T142–T146 last

### Not parallel

- Everything writing `tests/test_check_project.py` (T120, T121, T125, T126,
  T139) — one file, the same [P] trap feature 002 named
- Everything writing `tests/test_ingest_sources.py` (T130, T131, T132, T136)
- Everything writing `scripts/zotero_ingest.py` (T133, T134, T137)
- Everything writing `scripts/check_project.py` (T122, T127, T140)
