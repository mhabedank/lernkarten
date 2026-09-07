# Tasks: Enumeration tiers

**Input**: Design documents from `/specs/011-enumeration-tiers/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [quickstart.md](quickstart.md),
[contracts/check-messages.md](contracts/check-messages.md), [checklists/](checklists/)

**Branch**: `feat/enumeration-tiers` · **Worktree**:
`~/Projects/mh_consulting/worktrees/lernkarten/counted-front/lernkarten`

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every
red assertion below runs through `check_project.check(...)` or
`check_docs`, and asserts on a list that already exists, so it fails on the
assertion and never on an `ImportError`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 = the tier rule and E-3 (P1) · US2 = E-2 (P2) · US3 = the rule is written down (P1)
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Phase organisation — by commit, not by story

Constitution XI fixes the order, and `plan.md` § Phase 1 lists the red
assertions in it: every red case lands together (commit 1), the checks together
(commit 2), the fixture third (commit 3), the prompts last (commit 4). Splitting
by story would put `skills/cards/SKILL.md` ahead of its own red check. Story
labels therefore ride on the tasks.

## Decisions this file makes (left open by `plan.md`)

| Left open by plan.md | Decided here |
|---|---|
| R-7: how much the demo project grows | **one card** — `V6TQ8` in `cards/signals.yaml`. Verified against the shipped checker: it reproduces **both** regressions on its own (three errors), exercises E-1-on-members, E-3a-satisfied, group parsing and the A-2 descent, and needs **no companion card** because all six flag names already appear on other cards in that file |
| whether the **split tier** goes in the fixture | **no**, and the README says why: after you split, you have ordinary cards. The split tier leaves *no mechanical trace* in the artifact — an anchor card is just a flat tier-3 card — so fixture material would demonstrate nothing a reader could check. E-3b's failing case lives in `tmp_path` like every other failing case (T024 precedent). This reverses the plan's provisional "full size" recommendation, which was made before that was understood |
| the new card's exact text and `id` | **T019**. `id: V6TQ8`, verified absent from the 32 existing ids; front 39 characters, back 84 |
| the tier constants | `FLAT_MAX = 5` and `GROUPED_MAX = 8` at module level in `scripts/check_project.py`, beside `MAX_FRONT`/`MAX_BACK` (data-model I-7) |
| helper names | `_groups(items)`, `_enumeration_size(items)`, `_check_shape(where, cards, language, report)` |
| which cases become `parametrize` rows | **T009** — `_groups`, `_enumeration_size` and the E-2 cue rule get one table each; anything that goes through `check()` stands alone |

---

## Phase 1: Setup

**Purpose**: record the baseline every number below is measured against.

- [X] T001 [P] Confirm the working copy: `git branch --show-current` is `feat/enumeration-tiers`, `git status` clean apart from `specs/011-enumeration-tiers/`. Touches no repo file.
- [X] T002 [P] Record the baseline: `python3 scripts/check_project.py tests/fixtures/demo-project` prints `32 cards, 0 warning(s)` and exits 0; `pytest -q` fully green. Paste both into the PR description later. Touches no repo file.

**Checkpoint**: green at 32 cards.

---

## Phase 2: Red — every assertion, no production code

**Purpose**: commit 1. Nothing under `scripts/` is in this commit; verify with `git show --stat`.

- [X] T003 🔴 [US1] Add the grouped-back fixtures to `tests/test_check_project.py` as module constants: `GROUPED_CARDS` (front `'Name the four steps.'`, back `'#list([*Discover*: alpha, beta], [*Define*: gamma, delta])'`, plus a second card naming all four members), `FLAT_SEVEN_CARDS`, `GROUPED_SEVEN_CARDS`, `LONG_TEN_CARDS`. Each carries `subtopic: 'Rhythm of the tide'` so the existing `GOOD_CATALOG` accepts it. *(File: `tests/test_check_project.py`)*
- [X] T004 🔴 [US1] `test_e1_counts_members_not_group_items` — `check(project(tmp_path, cards=GROUPED_CARDS))` reports **no** count finding. **Red today**: the shipped `_check_counts` reports `the front announces 'four' and the back enumerates 2`. This is research R-4, and it is the assertion that protects shipped behaviour. FR-002, data-model I-4. *(File: `tests/test_check_project.py`)*
- [X] T005 🔴 [US1] `test_a2_reports_a_member_not_the_group_label` — a grouped back whose member `delta` is named by no other card reports **`'delta'`** and **not** `'Discover'` or `'Define'`. **Red today**: `_item_key('*Discover*: alpha, beta')` returns `'discover'`, so the label is what gets reported. Research R-5, FR-011b, FR-011c, SC-007a. *(File: `tests/test_check_project.py`)*
- [X] T006 🔴 [US2] `test_a_counted_prompt_answered_in_prose_is_reported` — a front `'Name the four stages.'` over a prose back produces the E-2 **warning**, quoting `'four'` and `card 1`. Assert on `report.warnings`, which exists and is empty for this project today. FR-006, FR-010, contracts § E-2. *(File: `tests/test_check_project.py`)*
- [X] T007 🔴 [US2] `test_a_numeral_without_a_cue_is_not_an_enumeration_prompt` — `F3M2Q`'s front verbatim (`'Describe how the range is distributed over the six hours of the flood'`) over a prose back produces **nothing**. Green today by accident and it must stay green: it is the guard that a numeral-anywhere implementation fails. Research R-2, FR-008. *(File: `tests/test_check_project.py`)*
- [X] T008 🔴 [US1] `test_a_flat_list_past_the_grouped_boundary_is_reported` (E-3a, seven flat items → one warning) and `test_a_grouped_list_in_that_tier_is_silent`; `test_an_enumeration_of_ten_is_reported_whether_grouped_or_not` (E-3b, both shapes → one warning each, and it is E-3b's message, not E-3a's). FR-011, FR-012, data-model I-6, contracts § E-3a/E-3b. *(File: `tests/test_check_project.py`)*
- [X] T009 🔴 [P] [US1] Parametrized tables in `tests/test_check_project.py`: `_groups` (all-groups → parsed; mixed list → `None`; a label containing a star → not a group; a member list with one member → parsed), `_enumeration_size` (grouped → member count; flat → item count; `None` in → `None` out), and the E-2 cue rule (`'What are the four types of work?'` → prompt, per research R-2's motivating card `B7SGP`; `'Describe … over the six hours'` → not; `'Nenne die vier Warnstufen.'` → prompt; a Greek front → not, no cue table). *(File: `tests/test_check_project.py`)*
- [X] T010 🔴 [P] [US3] `test_the_cards_skill_states_the_tier_table` in `tests/test_check_docs.py` — `check_docs` fails when `skills/cards/SKILL.md` carries no tier table. **Red today**: neither the check nor the table exists. This is the model-driven half's red artifact (research R-6, constitution XI's table), and the first check in this repository about a skill's own text. SC-006. *(File: `tests/test_check_docs.py`)*
- [X] T011 Run `pytest -q` and confirm the shape of the failure, not just its presence: T004, T005, T006, T008, T009 and T010 fail **on their assertion**; T007 passes; every pre-existing test still passes. Touches no repo file.
- [X] T012 Commit: `test: red cases for enumeration tiers, and for two regressions grouping would cause`. Body names R-4 and R-5 as measured, not inferred. Nothing under `scripts/` in this commit.

**Checkpoint**: six assertions red for the right reason, and two of them describe behaviour that ships today.

---

## Phase 3: Green — the checks

**Purpose**: commit 2, all of it in `scripts/check_project.py` (constitution V — no new module; the four helpers it extends live there).

- [X] T013 [US1] Add the module constants beside `MAX_FRONT`/`MAX_BACK` in `scripts/check_project.py`: `FLAT_MAX = 5`, `GROUPED_MAX = 8`, and `GROUP_ITEM = re.compile(r"^\s*\*([^*]+)\*\s*:\s*(.+)$")`. Comment says what each is for and that the tier table in `skills/cards/SKILL.md` is the other place they live. Data-model I-7. *(File: `scripts/check_project.py`)*
- [X] T014 [US1] Implement `_groups(items)` — returns `[(label, [member, …]), …]` when **every** item matches `GROUP_ITEM`, else `None`. Members are the tail split on commas, stripped, empties dropped. A mixed list is not grouped (data-model I-2), and a member may not contain a comma (I-1). *(File: `scripts/check_project.py`)*
- [X] T015 [US1] Implement `_enumeration_size(items)` — member count when `_groups` returns groups, item count otherwise, `None` when `items` is `None`. Docstring states why it exists: E-1, E-3a, E-3b and the tier table read this one definition, because two definitions of "how many" already drifted once between features written four commits apart (research R-4). Data-model I-4. *(File: `scripts/check_project.py`)*
- [X] T016 [US1] Change `_check_counts` to compare the announced count against `_enumeration_size(items)` rather than `len(items)`. One line plus a comment; **T004 goes green**. FR-002. *(File: `scripts/check_project.py`)*
- [X] T017 [US1] Change `_check_orphans` to expand a grouped item into its members before `_item_key`, leaving a flat item exactly as it is. The label is never keyed and never reported (FR-011c). **T005 goes green.** Note in the docstring that the label check this replaces was not merely wrong but arbitrarily satisfied — in the fixture prototype `*Help*` passed because an unrelated card front says "call for help", while `*Traffic*` and `*Closure*` failed. *(File: `scripts/check_project.py`)*
- [X] T018 [US1] [US2] Implement `_check_shape(where, cards, language, report)` and call it in `check_cards` beside `_check_counts` and `_check_orphans`, per file, after the card loop, over the **unfiltered** `cards` list so `card {i}` agrees with every other message about that file. It emits, at most one per card: **E-2** (count ≥ 3, cue adjacent to the numeral, `items == []`), **E-3a** (`FLAT_MAX < size <= GROUPED_MAX` and not grouped), **E-3b** (`size > GROUPED_MAX`, grouped or not). Add `ENUM_CUES` — a per-language closed set, English `what are`, `name`, `list`, `state`, `give`, `which`; German `was sind`, `nenne`, `liste`, `zähle`, `welche` — matched at the start of the front with at most one article before the numeral (data-model §6). Messages verbatim from [contracts/check-messages.md](contracts/check-messages.md). **T006, T008, T009 go green; T007 stays green.** *(File: `scripts/check_project.py`)*
- [X] T019 Run `pytest -q`: everything green except T010, which Phase 5 closes. `python3 scripts/check_project.py tests/fixtures/demo-project` still reports `32 cards, 0 warning(s)` — the new checks fire on nothing that ships today, which is SC-002 measured rather than claimed. Touches no repo file.
- [X] T020 Commit: `feat: check the shape of an enumerated back, and count its members`. Body notes T010 is knowingly red and Phase 5 closes it.

**Checkpoint**: every check exists; the fixture is untouched and still green.

---

## Phase 4: The fixture

**Purpose**: commit 3. One card, chosen because it exercises four new code paths at once.

- [X] T021 [US1] Add card `V6TQ8` to `tests/fixtures/demo-project/cards/signals.yaml`, under `subtopic: 'The six flags'`, after `NKQK0`:

  ```yaml
    - id: V6TQ8
      subtopic: 'The six flags'
      front: 'Name the six flags of the Kestrel code.'
      back: '#list([*Traffic*: grey, blue], [*Help*: white, yellow], [*Closure*: red, black])'
      source: 'Field notes 3, "The six flags"'
  ```

  Verified against the shipped checker before this file was written: it produces **three errors** today — the E-1 miscount and two A-2 label findings — and **zero** after Phase 3. No companion card is needed: `grey`/`blue` are named by `BS1M5`, `red` by `W9238`, `white`/`yellow` by `NKQK0`, `black` by `A7BSD`. The grouping matches the source material (`knowledge/field-notes/signal-code.md`, "The six flags"). FR-002, SC-003. *(File: `tests/fixtures/demo-project/cards/signals.yaml`)*
- [X] T022 [P] Move both card counts from 32 to 33: `DEMO_CARD_COUNT` in `tests/test_e2e.py:27` (the page-count assertions derive from it) and the bare `assert counts["cards"] == 32` in `tests/test_check_project.py:164`. *(Files: `tests/test_e2e.py`, `tests/test_check_project.py`)*
- [X] T023 [P] Add a section to `tests/fixtures/demo-project/README.md` beside the three deck-level checks. It must name: what `V6TQ8` demonstrates (the grouped tier; E-1 counting members not group items; A-2 descending into a group); that its six members were already named by four other cards, which is why grouping cost one card and not seven; and **why the split tier is not in the fixture** — after a split you have ordinary cards, so there is no artifact a reader could check, and E-3b's failing case lives in `tmp_path` like every other failing case. FR-016. *(File: `tests/fixtures/demo-project/README.md`)*
- [X] T024 Run `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — `33 cards, 0 warning(s)`, exit 0 — and `pytest -q`. Touches no repo file.
- [X] T025 Commit: `test: the demo deck carries a grouped enumeration`.

**Checkpoint**: the fixture demonstrates the grouped tier and is green under `--strict`.

---

## Phase 5: The prompts

**Purpose**: commit 4. The rule, where a rule lives — and the check from T010 goes green here, which is the whole point of writing it first.

- [X] T026 [US3] Add the tier table to `skills/cards/SKILL.md` in the *Style rules* section, immediately after the counted-front rule PR #96 added. Four rows (1–2 a sentence · 3–5 flat · 6–8 grouped · 9+ anchor plus one card per group), the group shape shown once as `#list([*Discover*: a, b], [*Define*: c, d])`, and the rule that an enumeration is never split merely to shorten it (FR-003). **T010 goes green.** FR-001, FR-002, FR-004. *(File: `skills/cards/SKILL.md`)*
- [X] T027 [US3] Add the three new reactions to step 6 of `skills/cards/SKILL.md`, in the shape the three existing ones use: *answers in prose* → write the list, and move commentary that belongs to no item onto its own card; *flat list past six* → group it, and the group label is structure, so it needs no card of its own; *too long for one card* → write the anchor card that names the groups and states the total, then one card per group. FR-005. *(File: `skills/cards/SKILL.md`)*
- [X] T028 [P] [US3] State the tier rule in `CLAUDE.md` § Card style, one bullet, beside the counted-front bullet already there. Name the group shape and say the label is exempt from the "nothing is introduced only inside a list" rule. FR-005. *(File: `CLAUDE.md`)*
- [X] T029 [P] [US3] Implement the `check_docs.py` half of T010: assert that `skills/cards/SKILL.md` contains the tier table. Keep it a shape check — the four boundaries appear — not a wording check, or the file cannot be edited without breaking the build. *(File: `scripts/check_docs.py`)*
- [X] T030 Commit: `skill: state the enumeration tiers and the group shape`.

**Checkpoint**: a reader can state the tiers from the skill alone, and a check says so.

---

## Phase 6: Polish and the pull request

- [X] T031 The four gates: `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`. Touches no repo file.
- [X] T032 `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` — green with both counts at 33. Touches no repo file.
- [X] T033 Walk [quickstart.md](quickstart.md) § 3 by hand — six rows, including the two regression guards. Touches no repo file.
- [X] T034 Open the pull request. It must state: the two measured regressions and that their guards were written first; that the fixture grew by one card rather than six, and why; that the split tier is deliberately not in the fixture; and that issue #83 can now be closed, with #98 carrying what was split out of it. Touches no repo file.

---

## Dependencies

```
Phase 1 → Phase 2 (all red) → Phase 3 (checks) → Phase 4 (fixture) → Phase 5 (prompts) → Phase 6
                                     │                                      ▲
                                     └── T010 stays red across 3 and 4 ─────┘
```

- **T004 and T005 before T016 and T017.** They describe behaviour that ships today; written afterwards they would be tests of the fix rather than of the requirement.
- **T013 → T014 → T015 → T016/T017/T018.** One file, and each builds on the constant or helper before it.
- **T021 before T022.** The count changes because the card exists.
- **T026 before T029** would also work; the order above puts the prose first so the check is written against a file that already satisfies it — the one place in this plan where the check follows the change, because T010 already holds the red.

## Parallel opportunities

Small, and honestly so: eleven of the tasks touch `scripts/check_project.py` or `tests/test_check_project.py`, so they serialise. Genuine `[P]` sets:

- **T001, T002** — setup, no repo file.
- **T009, T010** — different test modules.
- **T022, T023** — counts and the README.
- **T028, T029** — `CLAUDE.md` and `scripts/check_docs.py`.

## Implementation strategy

**MVP is Phase 2 + Phase 3.** At that point both regressions are fixed and all
three findings exist; the fixture and the prompts make it teachable but nothing
depends on them to be correct.

If the feature has to be cut, cut **E-3b before E-3a before E-2**: E-3b is the
tier with no material anywhere, E-3a has one card, and E-2 is the one the issue
was actually reported for. What must **not** be cut is T016 and T017 — without
them this feature ships a shape that makes the previous feature's error fire
falsely.

---

## What execution changed

Recorded because the plan is only worth having if it says when it was wrong.

- **T029 moved ahead of T026.** As written, the tier table went in before the
  check that looks for it, which this file itself flagged as "the one place in
  this plan where the check follows the change". Reversed, the shipped-skill
  test fails on its assertion instead of on a missing attribute — which is what
  constitution XI asks for and what "fails with ImportError does not count"
  means.
- **Three e2e tests moved with the deck, and one of them was load-bearing.** At
  32 cards the last A8 sheet was *exactly* full, so a two-row divider block
  could not share it — the premise of
  `test_four_dividers_open_a_further_page_on_the_demo_deck`. At 33 cards three
  rows are free and the block fits. Nothing in tasks.md predicted this: the
  demo deck's card count was silently load-bearing for a Leitner test. The
  whole-deck test now asserts the invariant (the paper and the advisory agree)
  and the costing branch is asserted explicitly on `--topic Tides`, eleven
  cards, chosen to be in it. `--subtopic 'The six flags'` moved 3 → 4, and two
  comments in the `sheet_pages` table named a count that had moved.
- **The contract's two E-3 examples were written with number words** and the
  implementation renders digits from `_enumeration_size` and `FLAT_MAX`. The
  contract was corrected to the shipped text rather than the code to the
  contract: a message that quotes the constant it used cannot drift from it.
