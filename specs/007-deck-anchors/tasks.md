# Tasks: Deck anchors — `depth` as a ceiling, and every term the deck uses is named by a card

**Input**: Design documents from `/specs/007-deck-anchors/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [quickstart.md](quickstart.md),
[contracts/](contracts/), [checklists/](checklists/)

**Branch**: `feat/deck-anchors` · **Worktree**:
`/Users/m.habedank/Projects/mh_consulting/worktrees/lernkarten/deck-anchors/lernkarten`

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every
red assertion below goes through `check_project.check(...)` and asserts on
`report.errors` — a list that **exists today and is empty** — so it fails on the
assertion, never on an `ImportError` or an `AttributeError`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 = A-1 anchor (P1) · US2 = A-2 orphan (P1) · US3 = `depth` is a ceiling (P2)
- 🔴 marks a task whose output must be a **failing** test before the next task begins
- `<!-- parallel-group: N -->` marks a fan-out set — up to 3 tasks, no two touching the same file
- `<!-- sequential -->` marks tasks that must run one after another

## Phase organisation — why it is by commit, not by story

`plan.md` §4 fixes a four-commit test-first sequence, and constitution XI makes
it non-negotiable: both stories' red cases land together (commit 1), both checks
land together (commit 2), the fixture follows (commit 3), the prompts last
(commit 4). Splitting the phases by story would put `skills/cards/SKILL.md`
before A-2's red case and break FR-025. The story labels are therefore carried
on the tasks rather than on the phases, and every FR still traces to exactly one
task.

## Decisions this file makes (deliberately left open by `plan.md`)

| Left open by plan.md | Decided here |
|---|---|
| the split of §3's fixture edits, one task or six | **five edit tasks in two fan-outs (three files, then two — group 10) + one checkpoint + three follow-up tasks** — the five data files are independent; the counts and the README follow the checkpoint |
| the new anchor card's exact front/back and its `id` | **T020**, front 65 characters, back 214, `id: R7XQ4` (verified absent from the 31 existing ids) |
| the alias phrasing beyond the measured anchors | **T018**, seven `Term:` lines quoted verbatim, in the inflected forms research R4 measured |
| the wording and placement of the `skills/cards/SKILL.md` additions | **T028**, six additions, each with its section and its FR |
| where FR-026's new step goes | **new step 6**, after the existing `lernkarten check` step, summary renumbered to 7 — schema errors get fixed before deck-level ones, so A-1/A-2 findings are not buried under YAML errors |
| which unit cases become `parametrize` rows | **T015** — `_list_items`, `_item_key` and `_mentions` get one parametrized table each; anything that goes through `check()` stands alone |
| `docs/testing.md` row numbering | **8l**, **11d**, **12-iii** (all three free today; step 12's existing sub-rows are `12-i` and `12-ii`, so the third follows that spelling rather than starting a second scheme) |

---

## Phase 1: Setup

**Purpose**: be able to verify the work, and record the pre-change baseline the
count budget is measured against.

<!-- parallel-group: 1 -->

- [x] T001 [P] Install the dev tooling: `python3 -m pip install --user -r requirements-dev.txt` (pytest, ruff). Touches no repo file.
- [x] T002 [P] Confirm the working copy: `git -C <worktree> branch --show-current` is `feat/deck-anchors` and `git status` is clean apart from `specs/007-deck-anchors/`. Touches no repo file.
- [x] T003 [P] Record the baseline: `python3 scripts/check_project.py tests/fixtures/demo-project --strict` prints `31 cards, 0 warning(s)` and exits 0, and `pytest -q` is fully green. Paste both into the PR description later. Touches no repo file.

**Checkpoint**: the tree is green at 31 cards. Every number in Phase 4 is
measured against this line.

---

## Phase 2: 🔴 Red — commit 1, `test:` (no production code)

**Purpose**: commit the failing cases before any implementation (FR-025,
SC-003, constitution XI).

**Rule for this whole phase — no exception**: not one test here may call
`_mentions`, `_list_items`, `_item_key`, `_check_anchors` or `_check_orphans`.
Calling a function that does not exist raises `AttributeError`, which
constitution XI explicitly does **not** count as red. Every assertion goes
through `check_project.check(project, check_project.Report())` and reads
`report.errors`.

Every task in this phase edits **`tests/test_check_project.py`** — the same
file, so none of them may be parallelised.

<!-- sequential -->

- [x] T004 🔴 [US1] Add the A-1 red case to `tests/test_check_project.py`. New module constant `TERM_CATALOG` — `GOOD_CATALOG` with `Term: Rhythm of the tide` inserted under `### Rhythm of the tide`, above `References:` — and the test:

  ```python
  def test_a_subtopic_with_a_term_and_no_anchor_is_reported(tmp_path):
      report = check(project(tmp_path, catalog=TERM_CATALOG))
      said = messages(report)
      assert "cards/tides.yaml" in said, said
      assert "Rhythm of the tide" in said, said
      assert "no card names the term" in said, said
  ```

  `project()` writes `cards/tides.yaml` from `GOOD_CARDS`, whose one card says *"How long is a tidal day?"* / *"24 h 50 min."* and names neither *rhythm* nor *tide*. **Red today because `report.errors` is empty** — `Term:` is not in `ATTRIBUTE`, so the line is discarded as body prose and nothing reads it. FR-010, FR-011, FR-014, contracts/check-messages.md §A-1.

- [x] T005 🔴 [US1] Add the two cases beside it in `tests/test_check_project.py`. Together they prove T004 is about the anchor and not about the `Term:` line existing — and they are **not the same colour**, which is the point of the pair:
  - `test_an_anchor_card_silences_the_check` — **green today, green after**. `TERM_CATALOG` plus a second card under `subtopic: 'Rhythm of the tide'` whose front reads *"What is the rhythm of the tide?"* → `assert not report.errors`.
  - `test_a_card_under_another_subtopic_does_not_anchor_it` — 🔴 **red today**, for exactly T004's reason: it asserts that the A-1 error **is** reported, and today `report.errors` is empty because nothing reads `Term:`. `TERM_CATALOG` extended with a second subtopic `### Slack water`, and the term-naming card filed under **that** subtopic in the same file → the A-1 error is still reported. This is FR-010's narrowed haystack (`anchor_text` keyed `(where, subtopic)`), and it is the only thing that distinguishes the shipped rule from the drafted one.

  Give the second subtopic a `References:` line pointing at `../knowledge/field-notes/a.md`, or `check_catalog` reports it as a branch with nothing behind it — a stray error that would make the test read as passing for the wrong reason. Story 1 scenario 2, CHK015.

- [x] T006 🔴 [US2] Add the A-2 red case to `tests/test_check_project.py`. New module constant `LIST_CARDS`:

  ```yaml
  topic: 'Signals'
  language: english
  cards:
    - subtopic: 'Rhythm of the tide'
      front: 'Name the four Ashwind warning stages.'
      back: '#list([Green], [Amber], [Ashwind], [Full Ashwind])'
      source: 'Field notes'
    - subtopic: 'Rhythm of the tide'
      front: 'What does the green stage mean?'
      back: 'Nothing unusual — the predicted tide holds.'
      source: 'Field notes'
  ```

  and `test_an_orphan_in_a_list_back_is_reported`, asserting `'Amber'` appears **verbatim** in `messages(report)`, that `card 1` appears (the 1-based index, never an `id` — FR-014), and that `'Green'` does **not**. **Red today because `report.errors` is empty.** FR-012, FR-014, SC-002, contracts/check-messages.md §A-2.

- [x] T007 [US1] Add the regression guard `test_a_subtopic_without_a_term_line_is_silent` to `tests/test_check_project.py`: `check(project(tmp_path))` — plain `GOOD_CATALOG` + `GOOD_CARDS` — asserts **neither an error nor a warning**. Green today and it must stay green: `GOOD_CARDS` is used at fifteen call sites and names neither *rhythm* nor *tide*, and it survives only because `GOOD_CATALOG` carries no `Term:` line. Research R7, FR-011a, CHK021, Risk 2.

- [x] T007a [US2] Add the second regression guard `test_the_shipped_example_deck_has_no_orphan` to `tests/test_check_project.py` — a `tmp_path` project whose card file is the text of the repo's **own** `cards/example.yaml`:

  ```python
  def test_the_shipped_example_deck_has_no_orphan(tmp_path):
      example = (ROOT / "cards" / "example.yaml").read_text(encoding="utf-8")
      root = with_figure(project(tmp_path, cards=example), "assets/example-figure.svg")
      report = check(root)
      assert not report.errors, messages(report)
  ```

  Green today and it must stay green. It is the **only automated** guard on FR-013a: weakening the maths gate to strip-maths-then-head-term turns two of the Kolmogorov card's three items into orphans and this test goes red. Nothing else would catch that before the pull request — `.github/workflows/ci.yml:120` runs the project checker against `tests/fixtures/demo-project` and against nothing else, and `lernkarten check cards/example.yaml` (T036) cannot report an orphan at all, because `bin/lernkarten` imports `engine`, `deps`, `cardid` and `build_pdf` and never `check_project`. T039 is the same question asked by hand.

  Three things it must get right, all verified against the file as it stands:
  - a **`tmp_path` copy, never `check(ROOT)`**. `check_cards` globs `<project>/cards/*.yaml`, and a contributor's own deck lives in exactly that folder — `cards/` (bar `example.yaml`), `catalog/`, `knowledge/` and `sources.yaml` are gitignored precisely because the repo root doubles as a scratch project. `check(ROOT)` would fail on their material rather than on ours.
  - `with_figure(..., "assets/example-figure.svg")`, because `example.yaml`'s card 10 names it as a `back_image` and a missing picture is an **error**, not a warning.
  - assert on `report.errors` **only**. `example.yaml`'s subtopics are not in `GOOD_CATALOG`, so the run reports ten `subtopic '…' is not in the catalog` warnings, which are correct and not this test's business.

  FR-013a, Risk 5, CHK019. *(File: `tests/test_check_project.py`)*

- [x] T008 Checkpoint — run `pytest tests/test_check_project.py -q` and confirm, item by item:
  - `test_a_subtopic_with_a_term_and_no_anchor_is_reported` **fails**, and the failure line is an `assert` on `said`, not an `AttributeError`, `ImportError` or `KeyError`;
  - `test_a_card_under_another_subtopic_does_not_anchor_it` **fails** the same way — it too asserts that an A-1 error is reported, and there is no A-1 yet;
  - `test_an_orphan_in_a_list_back_is_reported` **fails** the same way;
  - `test_an_anchor_card_silences_the_check`, `test_a_subtopic_without_a_term_line_is_silent`, `test_the_shipped_example_deck_has_no_orphan` and `test_the_demo_project_is_consistent` all **pass**;
  - the rest of the suite is untouched.

  Paste the three failure outputs into the PR description (constitution XI, SC-003).

- [x] T009 Commit: `test: red cases for the anchor and orphan checks`. Nothing under `scripts/` is in this commit — verify with `git show --stat`.

**Checkpoint**: `pytest` is red for exactly three reasons, all on assertions.

---

## Phase 3: 🟢 Green — commit 2, `feat:` the two checks

**Purpose**: turn T004 and T006 green, and let `test_the_demo_project_is_consistent`
go **red** — that is the feature's headline evidence that A-2 finds a real defect
(plan §4, R-4). It stays red until Phase 4.

All production code lands in **`scripts/check_project.py`** (constitution V, plan
§Structure Decision). No new file under `scripts/`. No new import edge.

<!-- sequential -->

- [x] T010 [US1] `Term:` parsing in `scripts/check_project.py` — three edits in one pass:
  1. `ATTRIBUTE` (line 61) becomes `^(Status|Parents|Also covers|Related|References|Goal|Term):(.*)$`.
  2. In `check_catalog`'s `for entry in catalog.subtopics` loop (~line 610), read `entry.attribute("term")`. If the key is present, `catalog_names(value)`; **zero aliases → error** `subtopic '{name}': 'Term:' is empty — name the term, or leave the line out`, worded after the invalid-`Status:` error one loop above; otherwise `terms[entry.name] = aliases`.
  3. `check_catalog` returns `subtopics, marked, terms` (line ~673), and `check()` (line 895) unpacks three.

  Do **not** touch `GOAL_DEPTHS` (FR-002). A `Term:` line on a `##` topic is silently ignored — `check_catalog` reads only `catalog.subtopics`, so this needs no code. FR-011, FR-011b, research R2, R9, data-model §1.

<!-- parallel-group: 2 -->

- [x] T011 [P] [US1] Fix the one external unpack of `check_catalog` in `tests/test_check_project.py:857` (`test_also_covers_is_not_parsed_as_a_subtopic`): `subtopics, marked, terms = check_project.check_catalog(...)`. It is the **only** call site outside `check_project.py` (verified by grep over `scripts/`, `tests/`, `bin/`). Risk 8, CHK114. *(File: `tests/test_check_project.py`)*
- [x] T012 [P] [US1] [US2] Add the shared private helpers to `scripts/check_project.py`, module level, all pure, placed next to the other module helpers:

  ```python
  LIST_HEAD = "#list("
  ITEM_SEPARATOR = re.compile(r"[—–,:;]|\s\(|\s-\s")   # em dash, en dash, comma, colon, semicolon, " (", " - "

  def _mentions(haystack_key, needle_key) -> bool   # f" {needle_key} " in f" {haystack_key} "
  def _list_items(back) -> list | None              # bracket-depth scan; None on an unbalanced scan
  def _item_key(item) -> str | None                 # maths gate, then head term, then topic_key
  ```

  `_mentions` is the whole matching rule and **both** checks call it, so they cannot drift. `_item_key` returns `None` for any item containing a `$` (the maths gate — **any** `$`, deliberately a superset of a balanced `$…$` span, per FR-013 as amended in review W4; FR-013a, **never** strip-maths-then-head-term); otherwise it cuts at the first `ITEM_SEPARATOR` match and normalises with the existing `topic_key()`. `_list_items` scans the `#list(` body by bracket depth so a nested `[…]` and `[$P(A) >= 0$ for every event $A$]` both parse, and returns `None` — skip the card, report nothing — on an unbalanced fragment. FR-011, FR-013, FR-013a, data-model §3. *(File: `scripts/check_project.py`)*

<!-- sequential -->

- [x] T013 [US2] Implement **A-2** in `scripts/check_project.py`: `_check_orphans(where, cards, report)`, called at the end of each file's body in `check_cards`, after the inner card loop, so findings come out per file in card order. Skip any element that is not a mapping or carries no `back` (FR-012a — `check_cards` already reports it as `card {i}: 'front' and 'back' are required`, and one malformed card must never yield two findings). Coerce a non-string `back` with `str()`, as the surrounding loop does. Haystack for card *i* is `front + " " + back` of every **other** card in the file, `topic_key`-normalised (I-5: an item named only on its own card is still an orphan). Message, verbatim per contract:

  ```python
  report.error(
      where,
      f"card {i}: '{item}' is enumerated and never named — no other card in this file mentions it",
  )
  ```

  `item` is the text between the brackets, **verbatim**, never the normalised head term.

  `i` is the card's position in the **unfiltered** `cards` list: `enumerate(cards, start=1)` over all of them, with the skip applied *inside* the loop and never as a filter before it. A skipped card still consumes an index, so A-2's `card {i}` always agrees with the `card {i}` of every other `check_cards` message about the same file — otherwise one file answers to two numberings. FR-012, FR-012a, FR-014, I-4, I-5, I-6, I-9, I-11.

- [x] T014 [US1] Implement **A-1** in `scripts/check_project.py`:
  - `check_cards`'s signature gains `terms=None` **after** `marked` and before `strict`, so no existing caller breaks;
  - a new accumulator `anchor_text = {}` beside `figure_faces` / `by_subtopic` (~line 727), keyed `(where, subtopic)`;
  - inside the per-card loop, next to the existing `by_subtopic.setdefault` (~line 826), append this card's `front + " " + back`;
  - `_check_anchors(anchor_text, terms or {}, report)` runs **after** the file loop, beside the existing `figure_faces` / `by_subtopic` judgements, iterating `sorted(anchor_text)` so output is stable across platforms (tests assert on messages);
  - `check()` passes `terms=terms`.

  A pair with no aliases (`terms.get(subtopic)` falsy) is skipped silently — FR-011a, I-3. A pair whose subtopic is marked `Status: gap`/`out of scope` **is still checked** — A-1 keys off cards existing, not off the mark, and it must not duplicate the existing "subtopic is marked" warning (FR-009a, I-10). Message, verbatim per contract, naming the **first** alias (FR-014a):

  ```python
  report.error(
      where,
      f"subtopic '{subtopic}': no card names the term ('{alias}') — "
      "one card in this file has to name the concept and say what it is",
  )
  ```

  FR-010, FR-014, FR-014a, FR-015, I-1, I-2.

- [x] T015 [US1] [US2] Add the helper unit tests to `tests/test_check_project.py`. They belong **here and not in Phase 2** — calling a function that does not exist raises `AttributeError`, which constitution XI rejects as a valid red (plan §4 commit 2, CHK110). Three parametrized tables plus four standalone cases:

  | Test | Shape |
  |---|---|
  | `test_list_items_extracts_what_is_between_the_brackets` | `@parametrize` over `(back, expected)`: `'#list([a], [b])'` → `["a", "b"]`; a nested `[…]` inside an item → extracted whole; `'#list([$P(A) >= 0$ for every event $A$])'` → extracted (the gate is `_item_key`'s job, not the scan's); `'#list([a], [b]'` → `None`; a back with no `#list(` → `[]` |
  | `test_item_key_applies_the_maths_gate_then_the_head_term` | `@parametrize` over `(item, expected)`: `'$P(Omega) = 1$'` → `None`; `'$sigma$-additivity for disjoint events'` → `None` (maths-mixed prose is skipped too); `'Parallelisation — sectioning and voting'` → `'parallelisation'`; one row each for the en dash, comma, colon, semicolon and `' ('` separators; `'Amber - the middle stage'` → `'amber'` (the **spaced** hyphen cuts — review W3); `'Half-mast signal'` → `'half mast signal'` (an unspaced hyphen is no separator; `topic_key` folds it); `'Amber'` → `'amber'`; `'нуля глубин'` → `'нуля глубин'` (Unicode survives) |
  | `test_mentions_matches_a_token_sequence_not_a_substring` | `@parametrize` over `(haystack, needle, expected)`: whole-token hit → `True`; `'Nipptidenhub'` vs `'Tidenhub'` → `False`; `'settlement'` vs `'settlements'` → `False`; a two-word alias spanning two tokens → `True` |
  | `test_an_empty_term_line_is_reported` | standalone, through `check()`: `Term:` with nothing after it, and `Term: (see above)`, both → error `'Term:' is empty` (FR-011b, I-7) |
  | `test_a_term_line_with_a_stray_comma_still_parses` | standalone: `Term: A,,B` → **no** error (`catalog_names` drops the empty element) |
  | `test_an_anchor_in_one_file_does_not_satisfy_another` | standalone: a `tmp_path` project with a second card file for the same subtopic, anchored in one and not the other → exactly **one** finding, naming the unanchored file (FR-010, Story 1 scenario 7) |
  | `test_an_item_named_only_on_its_own_card_is_still_an_orphan` | standalone (I-5) |

  *(File: `tests/test_check_project.py`)*

- [x] T016 Checkpoint — run and confirm all five:
  1. `pytest tests/test_check_project.py -q` → everything from T004–T007 and T015 passes;
  2. `test_the_demo_project_is_consistent` is now **RED**, and its message names exactly `'Skarn'` and `'Bellhorn'` in `cards/geography.yaml` — **two** findings, no others (CHK019). This is the feature's headline red: a pre-existing invariant broken by a real defect, not by an invented one;
  3. `python3 scripts/check_project.py .` reports **no** orphan in `cards/example.yaml` — all three Kolmogorov items carry a `$…$` span and are skipped by the maths gate (FR-013a, Risk 5);
  4. `lernkarten check cards/example.yaml` still exits 0;
  5. `ruff check . && ruff format --check .` is clean.

- [x] T017 Commit: `feat: check that every named term is anchored and no list item is orphaned`. Note in the commit body that `test_the_demo_project_is_consistent` is knowingly red and Phase 4 closes it.

**Checkpoint**: both new checks work; the demo fixture is the only thing failing.

---

## Phase 4: 🟢 Green — commit 3, `test:` the demo fixture

**Purpose**: turn `test_the_demo_project_is_consistent` green again and leave
`python3 scripts/check_project.py tests/fixtures/demo-project --strict` at **zero
errors and zero warnings** — the invocation CI runs (`.github/workflows/ci.yml:120`),
where a warning is a failure just as an error is.

**THE HARD BUDGET — read before touching anything here.** The demo deck ends at
**exactly 32 cards**: one card added to `cards/tides.yaml`, one existing back
reworded in `cards/geography.yaml`. At 33 the sheet counts move and ~15 real
assertions across `tests/test_e2e.py` change, several of them structural
(`marks[:4] == [{"1/2"}] * 4` → `marks[:5]`; `range(2)` → `range(3)`) — research
R5 enumerates them. At exactly 32 the a7 and a8 page counts do **not** move and
only four assertions change. Do not close `Skarn`/`Bellhorn` by adding cards, and
do not put the fix under `Relief and the crater` (it is `Status: out of scope`,
and `check_cards` warns for every card under a marked subtopic — under `--strict`
that is a CI failure). Risk 1, Risk 4, research R8, CHK101–CHK106.

<!-- parallel-group: 3 -->

- [x] T018 [P] [US1] Add **seven** `Term:` lines to `tests/fixtures/demo-project/catalog/topics.md`, each directly under its subtopic's description and above `References:`, verbatim:

  | Subtopic | Line to add |
  |---|---|
  | `### The five islands` | `Term: The five islands, five inhabited islands` |
  | `### Rhythm of the tide` | `Term: Rhythm of the tide, Tidenrhythmus, παλίρροια` |
  | `### Range and the rule of twelfths` | `Term: Tidal range, rule of twelfths, εύρος, правило двенадцатых` |
  | `### Chart datum and the Ovray rule` | `Term: Chart datum, нуля глубин` |
  | `### Tidenrhythmus` | `Term: Tidenrhythmus` |
  | `### Tidenhub` | `Term: Tidenhub` |
  | `### The six flags` | `Term: The six flags` |

  Add **no** `Term:` line anywhere else. `Settlements` and `Rules of use` are descriptions rather than named concepts — leaving them bare is the fixture's own demonstration of FR-011a. The three subtopics with no cards get none either: the line is inert without cards (I-2) and is added when cards arrive, per FR-027's "at latest" rule. `Tidenrhythmus`, `Tidenhub` and `The six flags` are anchored by the rewords of T019a/T019b at zero card cost — an earlier draft withheld their lines to protect the 32-card budget, which the cross-model review rejected as evasion-by-omission (W2). The aliases are written in the **inflected forms the cards actually use** (`нуля глубин`, not `нуль глубин`; `εύρος`) because `topic_key()` does no stemming — research R4 measured every one of them. FR-021, plan §3(a). *(File: `tests/fixtures/demo-project/catalog/topics.md`)*
- [x] T019 [P] [US2] Reword card `ZRKBA`'s `back` in `tests/fixtures/demo-project/cards/geography.yaml` — **one YAML line, no card added, no card removed**:

  ```yaml
      back: 'Torvig Harbour has the only deep-water pier. \ From there the mail boat redistributes goods to Little Kestrel, Ovray, Skarn and Bellhorn.'
  ```

  137 characters, well inside the ~400 budget; `\ ` is followed by whitespace so it is a line break and not an escape. This closes **both** A-2 orphans at once and leaves `Torvig`, `Little Kestrel` and `Ovray` anchored as they already were. It is also a better card than the one it replaces: it says where the goods actually go. FR-023, plan §3(b), research R5. *(File: `tests/fixtures/demo-project/cards/geography.yaml`)*
- [x] T020 [P] [US1] Add **exactly one** card to `tests/fixtures/demo-project/cards/tides.yaml` — the anchor for `Rhythm of the tide`, the only `(file, subtopic)` pair in the fixture that research R4 measured as unanchored. Append it after card `0TMD9`, before the two figure cards and their comment block:

  ```yaml
    - id: R7XQ4
      subtopic: 'Rhythm of the tide'
      front: 'What is the rhythm of the tide, and what does knowing it buy you?'
      back: 'The fixed daily pattern of the Ashwind tide: two high and two low waters in a tidal day, each about 50 minutes later than the day before. \ It tells you *when* to expect water, never *how much* — that is the range.'
      source: 'Field notes 2, "Basic quantities"'
  ```

  Acceptance, every item required by `--strict` (Risk 3, CHK106): `id` is five Crockford characters and unique — `R7XQ4` is verified absent from the 31 existing ids, re-check with `grep -rho 'id: [0-9A-Z][0-9A-Z]*' tests/fixtures/demo-project/cards/` before committing; `subtopic:` is in the catalog; `source:` present; front **65** characters (≤ `MAX_FRONT`, 120); back **214** characters (≤ `MAX_BACK`, 400) — both measured off the text above; emphasis is single-star; the `\ ` break is followed by a space. It names the term as a **token sequence** — *"the rhythm of the tide"* — which is what A-1 requires. Deck: 31 → 32. FR-021, FR-023, plan §3(c). *(File: `tests/fixtures/demo-project/cards/tides.yaml`)*

<!-- parallel-group: 10 -->

- [x] T019a [P] [US1] Two one-line rewords in `tests/fixtures/demo-project/cards/gezeiten-de.yaml` — **no card added, no card removed** (review W2, resolved as "anchor by reword"; plan §3(b2)):
  - card `HNHF1`'s back becomes, verbatim (one YAML line, 80 characters — the card already defines the concept; now it also names it, which is what A-1 asks):

    ```yaml
        back: 'Zwei Hochwasser und zwei Niedrigwasser pro Tidentag — das ist der Tidenrhythmus.'
    ```

  - card `R3WZ4`'s back: replace `Der Hub steigt` with `Der Tidenhub steigt` — one word, nothing else (122 characters after the edit).

  Leave card `P1H4B` alone: `Nipptidenhub` and `Springtidenhub` are single tokens and must **not** anchor `Tidenhub` — after this task the shipped fixture itself demonstrates the token-not-substring rule (research R4 finding 2). FR-021, FR-023, plan §3(b2). *(File: `tests/fixtures/demo-project/cards/gezeiten-de.yaml`)*
- [x] T019b [P] [US1] One one-line reword in `tests/fixtures/demo-project/cards/signals.yaml` — card `NKQK0`'s front becomes, verbatim (65 characters, still unique among the file's fronts; `the six flags` now appears as a token sequence):

  ```yaml
      front: 'Which two of the six flags call for help, and how do they differ?'
  ```

  The e2e assertion touching this file moves nothing: `test_a_subtopic_filter_narrows_the_build` asserts a card *count* (`"3 cards"`), not text. FR-021, FR-023, plan §3(b3). *(File: `tests/fixtures/demo-project/cards/signals.yaml`)*

<!-- sequential -->

- [x] T021 Checkpoint — **the count budget, made checkable**. Run, in this order:
  1. `python3 scripts/check_project.py tests/fixtures/demo-project --strict` → exit 0 and the literal line `OK: tests/fixtures/demo-project is consistent (…, 32 cards, 0 warning(s)).` Zero errors **and** zero warnings; anything else stops the phase (CHK116, CHK118).
  2. `grep -h '^  - id:' tests/fixtures/demo-project/cards/*.yaml | wc -l` prints **32**, and `git diff --stat tests/fixtures/demo-project/cards/` shows exactly four files changed: `tides.yaml` `+6/-0`, `geography.yaml` `+1/-1`, `gezeiten-de.yaml` `+2/-2`, `signals.yaml` `+1/-1`. **If the count is not 32, revert and re-plan — do not proceed.** Note the indent is **two** spaces, not four, and `grep -h … | wc -l` is what totals across the six files — `grep -c` prints a count per file and totals nothing. Verified against the tree: the same command prints 31 today.
  3. `pytest tests/test_check_project.py::test_the_demo_project_is_consistent` is green again.

  Re-run step 1 after *every* subsequent fixture edit, not once at the end (Risk 3, CHK117).

<!-- parallel-group: 4 -->

- [x] T022 [P] Move the card-count and page-count assertions in `tests/test_e2e.py`, all in one pass so the counts move once:

  | Line | Today | Becomes | Why |
  |---|---|---|---|
  | `:27` | `DEMO_CARD_COUNT = 31` | `= 32` | FR-023 |
  | `:97` | `assert "10 cards" in result.stdout` | `"11 cards"` | `--topic Tides` selects `tides.yaml`, which gained the anchor |
  | `:255` | `assert pdf_pages(target) == 8, "29 demo cards + …"` | `== 10`, and the message rewritten to *"32 demo cards + the one intact card of the broken file"* | the mixed build is 32 + 1 = 33 cards → 5 sheets |

  And correct the four stale prose comments, all of which already said the wrong number before this feature: `:81-82` ("29 cards"), `:415` ("29 demo cards"), `:745` ("29 cards"), `:1106` ("31 cards") → 32 in each. **Do not touch `:1110`** — `assert pdf_pages(target) == 2 * -(-DEMO_CARD_COUNT // 8)` derives from the constant and is correct at 32 (8 pages) without an edit. FR-023, SC-004, plan §3(e)–(f), CHK102. *(File: `tests/test_e2e.py`)*
- [x] T023 [P] Change the bare card count in `tests/test_check_project.py:164` (`test_the_demo_project_has_all_four_artifacts`): `assert counts["cards"] == 31` → `== 32`. This is the second of the two count sites FR-023 names; it moves in the same commit as `DEMO_CARD_COUNT`. *(File: `tests/test_check_project.py`)*
- [x] T024 [P] Add a section to `tests/fixtures/demo-project/README.md` for the two new failure modes (FR-024). It must name: A-1 and what satisfies it in this fixture (**seven** `Term:` lines; `cards/tides.yaml` gained the `Rhythm of the tide` anchor `R7XQ4`; the `Tidenrhythmus`, `Tidenhub` and `The six flags` rewords of T019a/T019b; `Nipptidenhub`/`Springtidenhub` left as they are, demonstrating that a substring is not a match; `Settlements` and `Rules of use` deliberately carry no `Term:` line because they are descriptions, so A-1 is silent on them; the three card-less subtopics carry none because the line is inert without cards); A-2 and what satisfies it (card `ZRKBA`'s reworded back names `Skarn` and `Bellhorn`); and that **both red cases live in `tmp_path`, not in `broken/`**, because `check_project.py` scans only `<project>/cards/*.yaml` and `<project>/catalog/topics.md` and never sees `broken/`. `broken/README.md` gains **nothing** — research R6 decided this, and a row there would contradict that file's stated premise, which documents reactions of `lernkarten check` and the build. FR-022, FR-024. *(File: `tests/fixtures/demo-project/README.md`)*

<!-- sequential -->

- [x] T025 Checkpoint — `pytest` fully green, and no page-count literal moved that should not have. At 32 cards the a7 and a8 sheet counts are identical to 31 (4 and 2 sheets), so **every** whole-deck assertion research R5 enumerates must still read exactly what it reads today. Confirm all of them, not a sample:

  | Site | Still reads |
  |---|---|
  | `:83`, `:118`, `:441`, `:751` | `pdf_pages(...) == 8` |
  | `:84`, `:442` | `"8 pages, duplex"` |
  | `:98`, `:419`, `:428`, `:782` | `pdf_pages(...) == 4` |
  | `:420` | `"4 pages, duplex"` |
  | `:485` | `sizes["a7"] == 8 and sizes["a8"] == 4` |
  | `:754-755` | `marks[:4] == [{"1/2"}] * 4` and `marks[4:] == [{"2/2"}] * 4` |
  | `:768` | `sheets == 4` |
  | `:783`, `:786` | `[{"1/2"}, {"1/2"}, {"2/2"}, {"2/2"}]` and `range(2)` |
  | `:845` | `"8 pages, simplex"`, `"pages 1-4"`, `"pages 5-8"` |
  | `:853` | `"8 pages, duplex, flip on long edge"` |
  | `:1110` | `2 * -(-DEMO_CARD_COUNT // 8)` — derived, still 8 |

  Only `:27`, `:97`, `:255` and `tests/test_check_project.py:164` are allowed to have moved (T022, T023). Anything else that changed means the deck is not at 32. Then re-run `python3 scripts/check_project.py tests/fixtures/demo-project --strict`.
- [x] T026 Commit: `test: the demo deck anchors its terms and orphans no list item`.

**Checkpoint**: the whole suite is green at 32 cards, and the fixture is clean
under `--strict`. Nothing under `skills/` has been touched yet — verify with
`git log --stat`, because FR-025 and SC-003 are about exactly that ordering.

---

## Phase 5: Commit 4 — `skill:` / `docs:` the prompts

**Purpose**: only now do the prompts change (FR-025, SC-003 — the checks are
committed red *before* either prompt is edited, visible in the commit order).

**Binding constraint for every task in this phase**: **no skill frontmatter may
change.** `scripts/check_docs.py` is a PR gate and it checks that `name` equals
the folder name and that `description` is ≥ 20 characters and contains the word
`Triggers`. All edits here are body prose. Do not "improve" a `description` in
passing (constitution X, CHK120). Every relative markdown link added must
resolve; prefer a backticked `scripts/check_project.py` over a link, as all five
skills already do (CHK121).

<!-- parallel-group: 5 -->

- [x] T027 [P] [US3] Rewrite the `## Depth` section of `skills/learning-goal/SKILL.md` (~line 74) so `depth` reads as a **ceiling**, not a slice. The three bullets currently read as mutually exclusive descriptions; they must state that the level names the **highest** card the deck carries and that each level includes the ones below it — `expert` implies `working` implies `awareness`. Do **not** touch the closed-set sentence near line 59 and do **not** change the legal values: they stay exactly `awareness`, `working`, `expert`, and `GOAL_DEPTHS` in `scripts/check_project.py` is untouched (FR-002, SC-005). Acceptance is SC-006: a cold reader can state without ambiguity that `depth: expert` carries `working` and `awareness` cards too. FR-001. *(File: `skills/learning-goal/SKILL.md`)*
- [x] T028 [P] [US1] [US2] Six additions to `skills/cards/SKILL.md`, each with its place fixed:

  | # | Where | What | FR |
  |---|---|---|---|
  | i | § Steps, step 3 (*Per subtopic*) | reference `goal.md` and its `depth` — the file mentions neither today — and state the cumulative reading from the card-writing end: an `expert` deck still carries the `awareness` and `working` cards | FR-003 |
  | ii | § Steps, step 3, next to the 3–8 guidance | the **anchor rule**: every subtopic that produces cards produces at least one card that names the concept the subtopic is about. State explicitly that the anchor is **one of** the 3–8 cards, not a card on top of them | FR-004, FR-008 |
  | iii | a short subsection after § Steps | the anchor's **content standard**: a functional definition — what the concept changes, what it costs, what it does not fix — and explicitly **not** a dictionary gloss. The anchor has to earn its recurring review like any other card | FR-006 |
  | iv | the same subsection, as its closing caution | **anchor, not coverage**: one card per *named* concept, never a definitional layer beneath everything. Say plainly that the model must **not** add a definition card for every term it mentions — spaced repetition is a fixed-budget instrument, and a deck padded with definitions of terms the learner meets daily is worse than one without them | FR-007 |
  | v | § Style rules, beside the existing `#list([a], [b])` bullet | **nothing is introduced only inside a `#list([…])` back** — every item enumerated there is also named by another card in the same file | FR-005 |
  | vi | § Steps, as a **new step 6**, after the existing `lernkarten check` step; the summary becomes step 7 | run `python3 scripts/check_project.py .` and say what to do when it reports: a missing anchor means writing the card that names the concept — **or, when a card in that file already names it in its own language, adding that language's alias to the subtopic's `Term:` line**, because then the metadata is stale, not the deck (review W5); an orphaned list item means writing (or rewording) a card that names it — never deleting the enumeration. This is load-bearing: **no skill in this repo runs the checker as a step today**, and step 5's `lernkarten check` cannot host A-1 because it never reads `catalog/topics.md` | FR-026, SC-008 |

  Two negative constraints on the same file. **FR-020**: step 3's fan-out gains **no** whole-deck merge pass — both checks are answerable inside one agent's output. **FR-009**: § *Scope — what to skip, and what to say about it* is **not** touched. A subtopic marked `Status: gap` or `out of scope` still gets no cards and therefore still needs no anchor; the anchor rule is added beside the existing scope rules, never on top of them. FR-009 is a requirement that this file stay as it is in that one section, and T028 is the only task that could break it. Acceptance is SC-006 and SC-008: a cold reader can state the anchor rule, the "anchor, not coverage" caution, and that a numbered step runs the checker. *(File: `skills/cards/SKILL.md`)*
- [x] T029 [P] [US1] Document the `Term:` line in `skills/catalog/SKILL.md`, in the optional-attribute list at lines 86–92, beside `Status:`, `Parents:` and `Related:`, in the same "means today's behaviour when absent" framing the list already uses. It must say: what the line is for; that aliases are **comma-separated** and must cover **every language the deck is written in**, because the check binds per card file; that matching is **literal with no stemming**, so write the form the cards actually use (`нуля глубин`, not `нуль глубин`); that an alias **may not contain a comma** (the line is split on every comma — write a comma-free alias instead); and that leaving the line out means the checker stays silent, so no existing catalog needs editing. **And — not only in the attribute list — one sentence in the writing guidance (§ Steps / § Format `catalog/topics.md`) instructing `/catalog` to write the line**: a subtopic whose heading names a concept (not a description of a group of facts) gets a `Term:` line, at latest when its cards exist, with an alias for every language the deck uses; the line is inert on a subtopic without cards, so writing it early costs nothing. Without this instruction A-1 has no writer and the format is dead (FR-027 as amended, review W1). *(File: `skills/catalog/SKILL.md`)*

<!-- parallel-group: 6 -->

- [x] T030 [P] [US1] Extend the **Topic catalog** convention bullet in `CLAUDE.md` (line 23 onward): add `Term:` to the existing "Optional per subtopic" sentence — one clause naming it as comma-separated aliases covering every language the deck uses, matched literally, and absent meaning the pre-feature behaviour. Do not restructure the bullet; the sentence already lists `Status:`, `Parents:` and `Related:` in exactly this shape. FR-027, CHK022. *(File: `CLAUDE.md`)*
- [x] T031 [P] Add three rows to the manual checklist in `docs/testing.md` (§ *The checklist*), and one clause to § *Checking a project that Claude wrote*. The rows are the constitution XI run-output carve-out: SC-006 and SC-008 are satisfied by what a prompt *says*, which leaves nothing on disk, so they are **named** here rather than left implicit (Risk 10, CHK124). Numbering — all three are free today:

  | Row | Step | Do | Expect |
  |---|---|---|---|
  | `8l` | `/learning-goal` | read § *Depth* cold | you can say that `depth: expert` carries `working` and `awareness` cards too — the level is a ceiling, not a slice (**SC-006**) |
  | `11d` | `/cards` | read `skills/cards/SKILL.md` cold | you can state the anchor rule **and** the "anchor, not coverage" caution that forbids a definition card for every term (**SC-006**) |
  | `12-iii` | `/cards` | run `/cards` end to end in a scratch project | a numbered step runs `python3 scripts/check_project.py .` after the merge, and the session says what it did about anything reported (**SC-008**) |

  Place `8l` after `8k`, `11d` after `11c`, and `12-iii` after `12-ii` — step 12 already has `12-i` and `12-ii`, so the new row continues that spelling and sits at the end of the group, not in front of it. In § *Checking a project that Claude wrote*, add the two new modes to the "reports what the next step would trip over" list — *a subtopic whose term no card names, a list item no other card explains*. *(File: `docs/testing.md`)*

<!-- sequential -->

- [x] T032 Checkpoint — `python3 scripts/check_docs.py` exits 0; `git diff skills/` shows **no** change inside any `---` frontmatter block; every relative link added by T027–T031 resolves. Then read all three prompts cold and confirm SC-006 and SC-008 by the criteria in `quickstart.md` §8.
- [x] T033 Commit in two: `skill: state the anchor rule and read depth as a ceiling` for `skills/*/SKILL.md`, then `docs: document the Term: line and the two new checks` for `CLAUDE.md` and `docs/testing.md`.

**Checkpoint**: the prompts now describe the rule the checks enforce, and the
commit order shows the checks landed first.

---

## Phase 6: Gates

**Purpose**: exactly what CI checks. All green before the pull request (SC-004,
CHK125).

<!-- parallel-group: 7 -->

- [x] T034 [P] `ruff check . && ruff format --check .` — no per-file ignore added, ruff not loosened (constitution XII). Read-only.
- [x] T035 [P] `pytest` — the full suite, green. Read-only.
- [x] T036 [P] `lernkarten check cards/example.yaml` — exit 0. `cards/example.yaml` is **unchanged** by this feature, so this is the ordinary schema-and-typeset gate and nothing more. It is **not** the FR-013a detector: `bin/lernkarten` imports `engine`, `deps`, `cardid` and `build_pdf` and never `check_project`, so `lernkarten check` cannot report an orphan whatever the maths gate does. The detectors are T007a (automated) and T039 (by hand). Read-only.

<!-- parallel-group: 8 -->

- [x] T037 [P] `python3 scripts/check_docs.py` — exit 0. Read-only.
- [x] T038 [P] `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — exit 0, `32 cards, 0 warning(s)`. This is the CI invocation verbatim (`.github/workflows/ci.yml:120`), where a warning fails the build. Read-only.
- [x] T039 [P] `python3 scripts/check_project.py .` — exit 0 over the repo itself, confirming no orphan is reported in `cards/example.yaml` (quickstart §5). This is the FR-013a check run by hand; T007a is the same question asked by `pytest`, which is what makes it a gate rather than a habit. Expect one pre-existing warning, `sources.yaml: no source register yet` — it is not an error and exit stays 0. Read-only.

<!-- sequential -->

- [x] T040 `python3 scripts/make_testdata.py`, then `LERNKARTEN_E2E=1 pytest tests/test_e2e.py`. Run once before the PR. Sequential because `make_testdata.py` **writes** into `tests/fixtures/` and must not race the read-only gates above. Expect `DEMO_CARD_COUNT = 32` and every page-count assertion satisfied. SC-004, quickstart §7.
- [x] T041 Confirm no dependency moved: `git diff pyproject.toml requirements-dev.txt scripts/deps.py` is empty (FR-017, CHK126), and `git diff --stat` under `scripts/` touches `check_project.py` and nothing else (constitution V, VI).
- [x] T042 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries. The fixture under `tests/fixtures/demo-project` is the one carve-out and every word added to it is invented Kestrel-archipelago material (constitution VII, CHK107).
- [x] T043 Push the branch and open the pull request against `main` (`main` rejects direct pushes). The description carries: the two pasted red failures from T008, the 31 → 32 count note, and the constitution VII note that the demo fixture changed.

---

## Phase 7: By Hand

**Purpose**: what no script can judge. Nothing visible changes in this feature —
no template, no press sheet, no brand graphic — so the print checklist does not
apply. What is left is the prompt half.

<!-- parallel-group: 9 -->

- [x] T044 [P] `docs/testing.md` rows `8l` and `11d`: read `skills/learning-goal/SKILL.md` § Depth and `skills/cards/SKILL.md` cold, and say the three things SC-006 asks for. Read-only.
- [ ] T045 [P] `docs/testing.md` row `12-iii`: `python3 scripts/demo.py ~/lernkarten-demo --raw`, drive `/cards` in a real Claude session, and watch the new step run `python3 scripts/check_project.py .` and report (SC-008). Writes only into the scratch folder.

---

## Dependencies & Execution Order

### Phase dependencies

```
Phase 1 (Setup)
   └─► Phase 2 (🔴 commit 1, test:)        ── no production code in this commit
          └─► Phase 3 (🟢 commit 2, feat:)  ── demo fixture goes red here, on purpose
                 └─► Phase 4 (🟢 commit 3, test:) ── fixture + counts; suite green again
                        └─► Phase 5 (commit 4, skill:/docs:) ── prompts last (FR-025)
                               └─► Phase 6 (Gates) ──► Phase 7 (By hand)
```

No phase may be reordered. Phase 5 **after** Phase 3 is the whole of FR-025 and
SC-003, and it is checked by reading `git log`, not by a test.

### Within a phase

- Phase 2 is one file end to end — strictly sequential.
- Phase 3 serialises every edit to `scripts/check_project.py` (plan.md: *"`scripts/check_project.py` is touched by nearly every story; serialize edits to it"*). The one fan-out is T011/T012, which are different files.
- Phase 4 fans out over three fixture files, then over two more (group 10 — two different files, so the max-3 rule holds), then gates on T021, then fans out over three follow-up files.
- Phase 5 fans out over five documents in two groups; nothing in it depends on anything else in it.

### Parallel groups

| Group | Tasks | Files touched | Shared file? |
|---|---|---|---|
| 1 | T001, T002, T003 | *(none — commands only)* | no |
| 2 | T011, T012 | `tests/test_check_project.py` · `scripts/check_project.py` | no |
| 3 | T018, T019, T020 | `tests/fixtures/demo-project/catalog/topics.md` · `tests/fixtures/demo-project/cards/geography.yaml` · `tests/fixtures/demo-project/cards/tides.yaml` | no |
| 10 | T019a, T019b | `tests/fixtures/demo-project/cards/gezeiten-de.yaml` · `tests/fixtures/demo-project/cards/signals.yaml` | no |
| 4 | T022, T023, T024 | `tests/test_e2e.py` · `tests/test_check_project.py` · `tests/fixtures/demo-project/README.md` | no |
| 5 | T027, T028, T029 | `skills/learning-goal/SKILL.md` · `skills/cards/SKILL.md` · `skills/catalog/SKILL.md` | no |
| 6 | T030, T031 | `CLAUDE.md` · `docs/testing.md` | no |
| 7 | T034, T035, T036 | *(read-only commands)* | no |
| 8 | T037, T038, T039 | *(read-only commands)* | no |
| 9 | T044, T045 | *(read-only / scratch folder outside the repo)* | no |

### Never parallel

- 🔴 and 🟢 for the same behaviour. Ever.
- Any two edits to `scripts/check_project.py`.
- Any two edits to `tests/test_check_project.py` — note it appears in group 2 **and** group 4, but never twice within one group.
- `scripts/make_testdata.py` (T040) against any test run — it writes into the fixture tree.

---

## Requirement → task traceability

| FR / SC | Task |
|---|---|
| FR-001, FR-002 | T027 |
| FR-003–FR-008, FR-020, FR-026 | T028 |
| FR-009 | T028 (§ *Scope* is left as it is — the anchor rule sits beside the scope rules, never on top of them) |
| FR-009a | T014 (A-1 keys off cards, not off the mark; no duplicate warning) |
| FR-010 | T004, T005, T014, T015 |
| FR-011, FR-011a | T010, T007, T014 |
| FR-011b | T010, T015 |
| FR-012, FR-012a | T006, T013, T015 |
| FR-013 | T012, T015, T016 step 3 |
| FR-013a | T012, T015, **T007a** (the automated guard), T016 step 3, T039 (by hand). **Not** T036 — `lernkarten check` never imports `check_project` |
| FR-014, FR-014a | T004, T006, T013, T014 |
| FR-014 index rule (I-11) | T013 (unfiltered `enumerate`, skipped cards still consume an index) |
| FR-015 | T013, T014 (`report.error`, never `report.warn`) |
| FR-016 | T004 (`project()` writes no `goal.md` unless asked) |
| FR-017 | T041 |
| FR-018 | *(nothing to do — the card schema is frozen; T019/T020 add no key)* |
| FR-019 | T014 (`anchor_text` keyed by `(where, subtopic)`) |
| FR-021, FR-023 | T018, T019, T019a, T019b, T020, T022, T023 |
| FR-022 | T004, T006, T024 |
| FR-024 | T024 |
| FR-025 | phase order; verified at T026's checkpoint and T043 |
| FR-027 | T029, T030 |
| SC-001 | T021, T038 |
| SC-002 | T006, T013 |
| SC-003 | T008, T026 checkpoint |
| SC-004 | T034–T038, T040 |
| SC-005 | T007, T027 |
| SC-006 | T027, T028, T031, T044 |
| SC-007 | T038 (the run stays under a second; both checks are pure text) |
| SC-008 | T028, T031, T045 |

---

## Notes

- **Test-first, always.** A test written after the code tells you what the code does; only a test seen failing tells you it does what was asked.
- **The 32-card budget is the single constraint that turns a two-line content fix into a fifteen-assertion diff if it is missed.** T021 exists to catch that before it happens.
- No new dependency, no new file under `scripts/`, no new import edge, no template touched, no brand PNG re-rendered.
- Never `git add -f` anything under `knowledge/`, `catalog/`, `cards/` (except `example.yaml`), `output/`, or `sources.yaml`.
- Every word added to the demo fixture is invented Kestrel-archipelago material. It is the one carve-out to the no-user-content rule and it stays that way (constitution VII).
