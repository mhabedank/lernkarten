---
description: "Task list for 003-readme-landing-link"
---

# Tasks: The README links the landing page up front

**Input**: Design documents from `/specs/003-readme-landing-link/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[quickstart.md](./quickstart.md). No `contracts/` — no file format is touched.

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). US1
opens with a test task that must be committed *failing on its assertion*. US2 is
a regression guard for behaviour that already exists, so it cannot go red —
T010 substitutes a mutation check, which is the only honest way to prove such a
guard guards anything. That substitution is called out where it happens, never
assumed.

**Organization**: grouped by user story so each can be implemented and verified
independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which user story the task serves (US1, US2)
- Always name the exact file path
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Path Conventions

Four files change, all at the repository root or one level down. No `scripts/`,
no `bin/`, no `skills/`, no `templates/`, no fixtures.

- Docs: `README.md`, `docs/testing.md`
- Tests: `tests/test_repo_hygiene.py`, `tests/test_landing_page.py`

---

## Deviation from plan.md — read before starting

[plan.md](./plan.md) says "One case, not three", putting all four invariants
from [data-model.md](./data-model.md) into a single pytest case. **This task
list splits them into two cases**, one per user story:

| Case | Invariants | Story | Red-first? |
|---|---|---|---|
| `test_the_readme_points_a_newcomer_at_the_landing_page` | 1, 2, 3 | US1 | yes — T004 |
| `test_the_readme_still_names_the_landing_page_source` | 4 | US2 | no — green from the start, mutation-checked in T010 |

**Why**: the plan's own argument for one case was that the invariants "concern
the same file and the same question". Invariant 4 is a *different* question with
a different reader — the contributor looking for `docs/index.html`, not the
newcomer looking for the live URL — and it belongs to a different user story.
Keeping it in the same case would mean a US2 regression (someone deletes the
source reference) reports as a failure of a test named for US1's concern, and
would leave US2 with no independently runnable verification at all, which is the
one thing the spec's Independent Test line promises. Two narrow cases also match
how `tests/test_repo_hygiene.py` is already built — every case in it states one
claim.

**T017 reconciles the spec, plan and data-model wording with this**, so the artifacts
do not drift. Do not skip it.

---

## Phase 1: Setup

**Purpose**: get the environment able to verify the work.

- [X] T001 [P] Install the dev tooling: `python3 -m pip install --user -r requirements-dev.txt` — pytest and ruff are all this feature needs
- [X] T002 [P] Install the git hooks: `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [X] T003 Create the branch: `git switch -c docs/readme-landing-link` — the `docs/` prefix is required by constitution XIV

**Deliberately absent**: `python3 scripts/make_testdata.py` and
`bin/lernkarten engine --check`. Nothing here builds a PDF, reads a fixture or
touches the typesetting engine, so both would be setup for work this feature
does not do.

**Checkpoint**: `python3 -m pytest tests/test_repo_hygiene.py -q` runs green on
an unmodified checkout.

---

## Phase 2: Dependencies — **skipped**

[plan.md](./plan.md) says "No dependency change". No package, dev tool or binary
is added, replaced or removed, and the engine version is untouched. The phase is
deleted rather than filled with "N/A" tasks.

## Phase 3: Format Contracts — **skipped**

[data-model.md](./data-model.md) says "No format change". None of `sources.yaml`,
knowledge frontmatter, `catalog/topics.md` or the card schema moves, so nothing
blocks the stories below and no `check_project.py` rule is needed.

---

## Phase 4: User Story 1 - A newcomer finds the live page without scrolling past the intro (Priority: P1) 🎯 MVP

**Goal**: `README.md` carries a link to `https://mhabedank.github.io/lernkarten/`
in its opening block, so a reader meets the live page before the install
instructions instead of 168 lines later.

**Independent Test**:
`python3 -m pytest tests/test_repo_hygiene.py -k points_a_newcomer -q` passes on the
branch and fails on `main`.

**No test-material phase**: the subject of the assertion is the repository's own
`README.md`, which is in every checkout by definition. Nothing is added under
`tests/fixtures/demo-project/`, and `DEMO_CARD_COUNT` does not move.

### 🔴 Red — the test, before the README is touched

- [X] T004 🔴 [US1] Add `test_the_readme_points_a_newcomer_at_the_landing_page` to `tests/test_repo_hygiene.py`, asserting invariants 1–3 of [data-model.md](./data-model.md): bound the opening block with `re.search(r"^## ", text, re.M)` on `README.md`; assert `https://mhabedank.github.io/lernkarten/` appears inside it, after `Claude_Code-plugin` and before `assets/example-cards.png`. Add the URL as a module-level constant beside `BLOCKED`/`ALLOWED`. Give the case a docstring saying why the anchors are a badge URL and a file path rather than prose (see [research.md](./research.md) R2), and make the failure message name `README.md`. **Do not touch `README.md` in this task.**
- [X] T005 🔴 [US1] Run `python3 -m pytest tests/test_repo_hygiene.py -k points_a_newcomer -q` and confirm it fails **on the assertion** — not on an `ImportError`, a `FileNotFoundError` or an `AttributeError` from `re.search` returning `None`. Paste the failure into the pull request description; it cannot be reproduced once T006 lands.

**Checkpoint**: commit here, red. This commit is the artifact constitution XI
asks for.

### 🟢 Green — the README

- [X] T006 [US1] Insert the link into the opening block of `README.md`, between the introductory paragraph (ends line 11) and the `assets/example-cards.png` screenshot (line 13), in the shape issue #26 offers: `**[See it →](https://mhabedank.github.io/lernkarten/)**`. FR-003 leaves the exact wording free — it must read as an invitation to *look*, not to read further. Change nothing else in the file.
- [X] T007 [US1] Run `python3 -m pytest tests/test_repo_hygiene.py -q` and confirm the whole module is green, `test_the_repo_does_not_still_promise_five_commands` included — it reads the same file and must not have been disturbed.
- [X] T008 [US1] Refactor `tests/test_repo_hygiene.py`: if the opening-block slice is worth naming, lift it to a small helper beside `versioned_files()` so US2's case can reuse it. Red-green-**refactor** — the third step is not optional either.

**Checkpoint**: US1 stands alone. The link is in the file, the assertion covering
it was seen failing first, and nothing else in the suite moved.

---

## Phase 5: User Story 2 - A contributor still finds the source of the page (Priority: P2)

**Goal**: the `docs/index.html` reference in `## The design` survives, so a
contributor still finds the file they have to edit.

**Independent Test**:
`python3 -m pytest tests/test_repo_hygiene.py -k landing_page_source -q` passes,
and `python3 scripts/check_docs.py` independently confirms the relative link
resolves.

**This story has no 🔴 step, and that is deliberate.** FR-004 protects
behaviour that exists today, so a guard for it has nothing to fail against.
T010 replaces the red step with a mutation check, which is the only way to
learn whether a green-from-birth assertion is load-bearing or decorative.

- [X] T009 [US2] Add `test_the_readme_still_names_the_landing_page_source` to `tests/test_repo_hygiene.py`, asserting invariant 4: `README.md` still contains a relative link to `docs/index.html`. Docstring must state that this passes on `main` on purpose, and name FR-004 as what it guards. Sequential after T008 — same file.
- [X] T010 [US2] Mutation-check T009: temporarily delete the `docs/index.html` link from `## The design` in `README.md`, run `python3 -m pytest tests/test_repo_hygiene.py -k landing_page_source -q`, confirm it **fails**, then restore the link with `git checkout -- README.md` (or by hand if T006 is uncommitted — check `git status` first, restoring the wrong way loses T006's edit). Record in the pull request that the check was done.
- [X] T011 [US2] Run `python3 scripts/check_docs.py` and confirm it prints `OK: …` — the relative `docs/index.html` link still resolves, and the new absolute URL from T006 is skipped by design at `scripts/check_docs.py:174`, so no gate change is needed.

**Checkpoint**: both stories stand on their own, and each has a command that
proves it without the other.

---

## Phase 6: Docs & Cross-Cutting

**Purpose**: the manual half of the requirement (FR-007), and the three places
that describe a boundary this feature moves.

- [X] T012 Add row **33** to the table under "The landing page" in `docs/testing.md`, after row 32, in the existing `# / At / Do this / Expect` shape: at github.com on an ordinary laptop window, the README opening block shows the link without scrolling past the intro paragraph; it reads as an invitation to look; and `https://mhabedank.github.io/lernkarten/` actually loads. This is the half no test reaches, named here because constitution XI requires naming rather than implying it.
- [X] T013 Rewrite the closing paragraph of that same section in `docs/testing.md` (lines 271–273): drop "and the readme still buries the landing page", which **is** issue #26 and would tell the next reader the bug is still open. "Two things are known" becomes "One thing is known and is not a regression" — the card toggle still does not explain itself. Sequential after T012, same file.
- [X] T014 Widen the `tests/test_repo_hygiene.py` row in the eight-levels table in `docs/testing.md` (line 117, currently "no user content, no committed binaries") to cover the doc-text guards the module now holds. Sequential after T013, same file.
- [X] T015 [P] Widen the module docstring of `tests/test_repo_hygiene.py` (lines 1–5). "Guards that the repo stays subject-agnostic" was already strained by `test_the_repo_does_not_still_promise_five_commands`; with two more doc-text guards it is plainly too narrow. Say what the module now covers: user content, committed binaries, and what a release must and must not say in its docs.
- [X] T016 [P] Correct the module docstring of `tests/test_landing_page.py` (lines 4–5): it says `test_repo_hygiene.py` has "its **one** landing-page check". After this feature it has two. Keep the boundary the docstring draws — how the page is *built* versus what a release ships in its docs — because that boundary is exactly what put T004 and T009 where they are ([research.md](./research.md) R1).
- [X] T017 Reconcile `specs/003-readme-landing-link/spec.md`, `specs/003-readme-landing-link/plan.md` and `specs/003-readme-landing-link/data-model.md` with the two-case split described at the top of this file: plan.md's "One case, not three" paragraph in Phase 1 → Test plan first, and its test-plan table; data-model.md's invariant list. spec.md's FR-005 → FR-005a/FR-005b and its FR-007/SC-005 three-check count are already reconciled — confirm rather than re-edit them. Leaving any of them contradicting this file would be caught by `/speckit-analyze` and would mislead anyone reading the plan first.
- [X] T018 [P] Confirm English throughout — the new test names, docstrings, README line, `docs/testing.md` row and every commit subject (`test:` for T004/T009, `docs:` for T006/T012–T016).

**Deliberately absent**: `docs/workflow.md` (the user-facing flow is unchanged),
`docs/design.md` (no visible rule moves — the README is typed and coloured by
GitHub), `CLAUDE.md` (no card or format convention moves), `docs/index.html`
(it already links back to the repository in four places and never mentions the
README), and `REQUIRED_FILES` in `scripts/check_docs.py` (no new file ships).

**Checkpoint**: nothing in the repository still describes the old boundary or
the old bug.

---

## Phase 7: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

- [X] T019 [P] `ruff check .` — the only Python touched is `tests/test_repo_hygiene.py` and `tests/test_landing_page.py`
- [X] T020 [P] `ruff format --check .`
- [X] T021 `python3 -m pytest` — all green, and **no test that ran before is now skipped** (SC-004). Run it once with networking off (or confirm by reading the diff) that the new assertions reach no socket — FR-006 forbids a network call, so the suite stays green offline and during a Pages outage
- [X] T022 [P] `bin/lernkarten check cards/example.yaml` — unaffected, it never reads `README.md`
- [X] T023 [P] `python3 scripts/check_docs.py` — expect `OK: … skills, version …, docs links and required files are fine.`
- [X] T024 `grep -rn "buries" . --exclude-dir=.git --exclude-dir=specs` returns nothing. Before T013 it returns `docs/testing.md:273`; `specs/` is excluded because it records what was true when each feature was specified
- [X] T025 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries. The PR description carries the constitution VII note the gate asks for: the only content added is a URL to this project's own landing page, which is a link and not a subject-specific example
- [X] T026 Push the branch and open a pull request against `main` — direct pushes are rejected server-side and by `.githooks/pre-push`. Reference issue #26 so it closes on merge
- [X] T027 Confirm the branch is `docs/readme-landing-link` and every commit subject is prefixed (`test:`, `docs:`)

**Deliberately absent**, because nothing in the pipeline or the test data
changed: `python3 scripts/make_testdata.py`, the `LERNKARTEN_E2E=1` run,
`python3 scripts/check_project.py tests/fixtures/demo-project --strict`, the
borderless and other-language builds, and the Python-floor build. Running them
would prove nothing about this feature; skipping them is recorded here so the
omission reads as a decision rather than an oversight.

---

## Phase 8: By Hand

**Purpose**: manual checklist row 33 — what no command can judge. The rows for
printing, duplex alignment, cutting and the photocopy test do not apply, because
nothing here is typeset.

- [ ] T028 On the pull request page on github.com, look at the rendered `README.md` in an ordinary laptop window: is the link visible without scrolling past the intro paragraph?
- [ ] T029 Read the link as a newcomer would — does it invite you to *look*, or does it read like one more thing to read? FR-003 is a writing requirement and this is the only place it is checked
- [ ] T030 Open `https://mhabedank.github.io/lernkarten/` in a browser: it loads, and it is the page you expected. FR-006 keeps this out of the test suite on purpose — a network call would fail the suite offline and during any Pages outage

**Checkpoint**: row 33 walked. The feature is done.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: no dependencies
- **Dependencies (2)**, **Format Contracts (3)**: skipped — nothing blocks on them
- **US1 (4)**: depends on Setup
- **US2 (5)**: depends on T008 only because it edits the same file. The *story* is independent of US1 — its assertion passes with or without T006
- **Docs (6)**: T012–T014 after US1 (they describe what T006 did); T015–T016 after US2 (they describe the module's final shape); T017 after both
- **Gates (7)**: last
- **By Hand (8)**: after T026, since row 33 is read off the pull request page

### Within US1 — the ordering that matters

1. 🔴 T004 writes the assertion, T005 sees it fail on the assertion — commit here
2. 🟢 T006 edits `README.md`
3. T007 confirms green, T008 refactors

Never move T006 above T005. That is the one rule in this file with no exception
(constitution XI).

### Parallel Opportunities

- T001 and T002 in parallel; T003 after (or before — it depends on neither)
- T015 and T016 in parallel with each other and with T012–T014 — three different files
- T019, T020, T022, T023 in parallel — four independent commands
- T028–T030 are one sitting, not really parallel work

### Not Parallel

- 🔴 T005 and 🟢 T006. Ever.
- T004, T008, T009 and T015 all edit `tests/test_repo_hygiene.py` — strictly sequential
- T012, T013 and T014 all edit `docs/testing.md` — strictly sequential
- T006 and T010 both touch `README.md`, and T010 deliberately breaks it for a moment. Check `git status` before restoring, or T010 eats T006's edit

---

## Implementation Strategy

**MVP is US1 alone** — T001–T008 plus T012, T013, T019–T027. That ships issue
#26's fix, guarded by a test that was seen failing, with the stale note in
`docs/testing.md` removed. It is a complete, mergeable change on its own.

**US2 is one task's worth of insurance** on top. It protects a link nobody is
currently trying to delete, which is exactly why it is P2 and why its value is
future-tense: the next person who tidies the design section will find out
immediately rather than at review time.

**Incremental delivery**: MVP → US2 → the docstring and reconciliation tasks
(T014–T017). All three could be one pull request; the feature is small enough
that splitting it would cost more in review overhead than it buys.

---

## Notes

- **Test-first, always.** T005 is the whole point of the exercise. A green test
  written after T006 would tell you the README contains a link; only the failure
  captured in T005 tells you the link was put there because it was asked for.
- **The one green-from-birth test is flagged**, not hidden. T010's mutation
  check is what makes T009 more than decoration.
- Never `git add -f` anything under `knowledge/`, `catalog/`, `cards/` (except
  `example.yaml`), `output/`, or `sources.yaml`.
- No binary is committed and none is generated — this feature adds no test
  material of any kind.
- `docs/design.md` was read (constitution XVI) and needs no edit: it governs the
  card, the mark and the landing page, none of which changes.
- Commit after each task or logical group, and **always** at the 🔴 checkpoint
  after T005.
