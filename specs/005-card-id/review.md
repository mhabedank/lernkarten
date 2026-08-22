# Cross-model pre-implementation review: 005-card-id

**Reviewer**: Fable 5 (cross-model — did not author these artifacts) · **Date**: 2026-08-22
**Scope**: spec.md, plan.md, tasks.md, research.md, contracts/, data-model.md, quickstart.md, checklists/, plus the live code the feature touches.

## Summary

**Overall verdict: NOT READY** — but narrowly. The artifact set is unusually
disciplined (the red-first ordering, the C1/A1 fixes, and the measured Typst
numbers all held up under re-derivation), and none of the findings requires
re-planning. Three major findings must be folded into the artifacts before
implementation, because executing tasks.md exactly as written would (1) leave
SC-004 undelivered — Phase 7's own independent test cannot pass with Phase 7's
tasks — (2) leave the backfill writer able to corrupt legal YAML the fixtures
never exercise, and (3) leave `scripts/cardid.py` with a PyYAML import that
crashes `python3 scripts/check_project.py` on a machine that has never run
`deps.activate()`. All three are artifact edits, not design changes; distance
to READY is small.

| # | Dimension | Verdict |
|---|---|---|
| 1 | Spec–plan alignment | **WARN** |
| 2 | Plan–tasks completeness | **FAIL** |
| 3 | Dependency ordering | **PASS** |
| 4 | Parallelization correctness | **WARN** |
| 5 | Feasibility & risk | **WARN** |
| 6 | Standards compliance (constitution) | **WARN** |
| 7 | Implementation readiness | **WARN** |

---

## Findings (most severe first)

### F1 — MAJOR · `lernkarten check` never learns to validate ids; SC-004 is undelivered

**Location**: tasks.md T029–T032 (lines 183–189) vs spec.md SC-004 (line 204),
US5 (line 104), FR-013a (line 157); quickstart.md Scenario 4 (lines 82–96);
tasks.md Phase 7 independent test (line 167).

**What is wrong**: `lernkarten check` and `scripts/check_project.py` are two
different programs. `bin/lernkarten check` dispatches to `build_pdf.main()`
with `--check` (bin/lernkarten:51–57); `check_project.py` is invoked separately.
The spec names them as *distinct* members of the validating path (FR-013a:
"`lernkarten check` and `scripts/check_project.py`"), and SC-004 asserts against
the real command: "**`lernkarten check`** exits non-zero and names both
offenders". Quickstart Scenario 4 runs `lernkarten check …broken/duplicate-id.yaml`
and expects non-zero. Phase 7's own independent test says
"`bin/lernkarten check` on the broken fixtures — non-zero exit". Yet every
implementation task wires the four validations into `check_project.py` only
(T031), and every red test into `tests/test_check_project.py` only (T029, T030).
No task touches `build_pdf.py`'s check path. `duplicate-id.yaml` is schema-valid
(`front`/`back` present), so `lernkarten check` on it exits **0** — Phase 7's
independent test fails with Phase 7's tasks complete.

**Why it matters**: a success criterion that no task delivers ships as a false
claim, and the user-facing command (the one a contributor actually runs) keeps
printing duplicates silently — exactly the failure US5 exists to remove.

**Fix**: add a task pair before T031: 🔴 a case (in `tests/test_build_pdf.py`
or `test_e2e.py`) asserting `lernkarten check` exits non-zero naming both cards
on the duplicate fixture; 🟢 id validation in `build_pdf.load_cards` / the
`--check` path via `cardid.validate()`/`cardid.normalise()` (import direction
`build_pdf → cardid` is acyclic and already planned). Also decide and state
whether `lernkarten build` (without `--check`) errors or only warns on a bad id
— FR-013a says build "reads and renders ids" but is silent on whether it gates.

### F2 — MAJOR · The compose+splice writer breaks on legal YAML the fixtures never cover

**Location**: plan.md § Module placement (`insert_ids`, line 273), research.md
§ R-1, tasks.md T009/T010 (lines 78–79), T036 (line 213); data-model.md
`cards_in` shape (lines 83–91).

**What is wrong**: the approach was verified on three well-behaved block-style
fixtures. I probed `yaml.compose()` against adversarial but *valid* card YAML
(probe run 2026-08-22, PyYAML 6.x):

- **Flow-style card** — `- {subtopic: a, front: f, back: b}`: composes fine
  (`flow_style=True`, first key mid-line at col 5), but the described splice
  ("insert `id:` as first key, move the `- ` dash onto the new line") produces
  a block `id:` pair followed by a `{…}` flow mapping on the next line —
  **invalid or semantically scrambled YAML written back to the user's file**.
  Nothing in plan, data-model or tasks mentions `flow_style`; the `cards_in`
  shape in data-model.md carries no flow flag.
- **Alias cards** — `- &c … / - *c`: both sequence items resolve to the *same
  node object* with the *same marks* (verified: both report first key at line 3
  col 4). A mark-driven splice inserts twice at one position, or gives two
  cards one id; an alias card cannot carry its own id at all.
- **Dash and first key on different lines** — `- # note\n    front: …` and
  `-\n    front: …`: the first key's line has no dash on it, so "turn `- ` into
  two spaces" rewrites two spaces that were never a dash. Handleable, but the
  algorithm as described assumes same-line, and `remove_ids` as "exact inverse"
  must handle both shapes.

Block scalars, quoted first keys, `---` markers and a BOM all probed **clean** —
those are not the risk.

**Why it matters**: backfill is a *writing* path pointed at hand-written user
decks (US4's whole audience), FR-007 promises "no partial rewrite", and a file
that parses cleanly today can come back unparseable. That is corruption of user
content by the shipped tool.

**Fix**: (a) `cards_in` must detect `flow_style=True` mapping nodes and alias
nodes (node-identity check across the sequence) and **refuse the file with a
named reason** — FR-007's all-or-nothing then protects the whole invocation;
(b) cheap universal guard: after splicing, **re-parse the result and assert it
yields the same cards plus the inserted ids before writing** — turning every
unforeseen shape into an error instead of a corruption; (c) add a flow-style
card, an alias pair, and a comment-after-dash card to T009's inline test corpus
as refusal/round-trip cases. All three are additions to T009/T010/T036, not a
redesign.

### F3 — MAJOR · `cardid.py`'s route to `yaml.compose` is contradictory and breaks the fresh-machine gate

**Location**: plan.md line 153 ("`yamlio.py` # untouched — compose() is used
via PyYAML directly") vs line 108 (Constitution VI row: "cardid.py imports only
`yamlio` (and stdlib `secrets`/`re`)"); tasks.md T004 (line 72, same claim) vs
T010 (line 79, "via `yaml.compose()`").

**What is wrong**: `yamlio` exposes only `load()`; its PyYAML handle lives in
the private `_load_pyyaml()`, which is also the *only* place the deps bootstrap
runs for direct script invocations (yamlio.py:30–46). So "imports only yamlio"
and "uses compose() via PyYAML directly" cannot both be true. If the
implementer follows T010 and writes `import yaml` at module top:
`bin/lernkarten id` still works (T039 calls `deps.activate()` first), but
**`python3 scripts/check_project.py <proj> --strict` — a constitution XII gate
command — crashes with ImportError on any machine that has PyYAML only in the
deps cache**, because T031 makes `check_project` import `cardid`, and direct
script runs never call `deps.activate()`. Today that command works on such
machines precisely because yamlio bootstraps lazily.

**Why it matters**: it regresses a documented quality gate on exactly the
platform story (fresh plugin install, no pip'd pyyaml) that Principle II
exists to protect, and the plan's own Constitution VI row is built on the
contradictory claim.

**Fix**: pick one and write it down: either give `yamlio` a three-line public
accessor (e.g. `yamlio.pyyaml()` returning the bootstrapped module — amend
"yamlio untouched" in plan.md and add it to T004/T010), or have `cardid`
replicate the lazy `import yaml` / `deps.activate()` fallback (then amend
"imports only yamlio and stdlib" to include `deps`, which is a leaf, so
Principle VI still holds). The first keeps the bootstrap in one place and is
the better fit for Principle III.

### F4 — MODERATE · What does `--backfill` do with a pre-existing duplicate? Spec and contract contradict

**Location**: spec.md FR-013 (line 156) + FR-013a (line 157) vs
contracts/cards-yaml.md § The `id` subcommand, `--backfill` row (line 59:
"leave existing ids untouched").

**What is wrong**: FR-013 says "the **writing** path MUST reassign one of the
two automatically", and FR-013a enumerates the writing path as `--backfill`
**and** `--reassign`. The contract says `--backfill` "leaves existing ids
untouched". Both cannot hold when a user backfills two merged decks that
already share an id. No test (T033–T036) covers backfill-over-duplicates, so
the implementer decides silently — and US4 scenario 2's "byte-identical to
before" and FR-013's "MUST reassign" pull in opposite directions.

**Fix**: one sentence plus one test. Either (a) `--backfill` detects the
duplicate, reports it, exits non-zero pointing at `--reassign`, and writes
nothing (keeps the contract's "untouched" true; narrow FR-013's reassignment
duty to `--reassign`), or (b) `--backfill` reassigns too (then fix the contract
row). Option (a) is the safer default — reassignment stays an act the user
explicitly asked for.

### F5 — MODERATE · T021 is untestable at the level it demands

**Location**: tasks.md T021 (line 153: "Unit level, **not** e2e: … must not
skip silently without an engine"), plan assertion 11a; templates/card.typ:92–96.

**What is wrong**: the behaviour under test — empty id renders the side marker
alone, no `·` — lives in Typst (`card.id + " · " + …` is concatenated *inside*
`card.typ`'s `footer()`). A test in `tests/test_build_pdf.py` with no engine
cannot observe rendered output; all it can see is the payload dict, which
proves `id == ""` (T011 already covers that) and nothing about the separator.
As written, T021 either quietly becomes a duplicate of T011 or needs the
engine — contradicting its own "not e2e" note.

**Fix**: either (a) move the label composition into Python — `payload()` gains
a precomposed footer label (`"A45DK · 1/2"` / `"1/2"`), the template renders it
verbatim, and T021 asserts on the payload string at true unit level (this also
simplifies `card.typ`); or (b) accept that the assertion is engine-bound, move
it to `test_e2e.py`, and drop the "must not skip" claim. (a) honours the task's
intent; if taken, note it in plan.md's card.typ row.

### F6 — MODERATE · Overflow warnings go blind for id-less decks

**Location**: scripts/build_pdf.py `warn_about_overflow` (line 456:
`f"WARNING: card {card_id} does not fit"`) and `overflowing` (line 451:
`sorted(set(...))`); templates/card.typ:156/179 (`metadata(card.id)<overflow>`);
spec.md Edge Cases (line 129: "The existing overflow reporting for
`front`/`back` is untouched").

**What is wrong**: the overflow query names the culprit *by its id*. Today an
id-less deck reports "card tides-3 does not fit". After T012, every card in a
legacy deck has `id == ""`, so the warning reads "card  does not fit" — and the
`set()` dedup collapses *N* overflowing id-less cards into **one** anonymous
warning. The spec's claim that overflow reporting is untouched is false in
effect for exactly the backwards-compatibility population US2 protects. No
task covers it.

**Fix**: keep a diagnostic label separate from the printed id — e.g. the
template emits `metadata` carrying file-stem+index (or build_pdf substitutes
`f"{path.stem}-{i}"` into a `diag` field used only for the overflow metadata)
when `id` is empty. One task, one assertion in `test_e2e.py` or the existing
overflow test.

### F7 — MINOR · A2 fix incomplete: quickstart still uses the invocation the contract forbids

**Location**: quickstart.md Scenario 6 (line 116: `lernkarten id deck-a.yaml
deck-b.yaml`) vs contracts/cards-yaml.md line 61 (bare `lernkarten id <files>`
"exit non-zero with usage").

**What is wrong**: the contract fixed the flag surface *because* quickstart
used two spellings — but quickstart was not updated, so the validation playbook
demonstrates the exact invocation the contract defines as a usage error.

**Fix**: change Scenario 6 to `lernkarten id --reassign deck-a.yaml deck-b.yaml`.

### F8 — MINOR · T032 is a 🟢 with no 🔴 (constitution XI)

**Location**: tasks.md T032 (line 189).

**What is wrong**: the missing-id advisory has assertable parts — exit 0, and
**one** line per run rather than one per card (US2 scenario 2 names the count
as the assertable half; only the *wording* is manual-checklist). No red task
asserts either before T032 implements them. Also T032 names no file: the
behaviour belongs to the `lernkarten check` path (`build_pdf.py`), not to
`check_project.py` where the surrounding tasks live, and it mis-cites FR-005
(the render fallback) for the advisory.

**Fix**: add the exit-0 + line-count assertion to T029 or a new 🔴 before T032,
and name the module T032 edits.

### F9 — MINOR · Parallel group 2 is unsafe if T016 takes its "(or extend one)" option

**Location**: tasks.md T016 (line 121) vs T014 (line 119), group table line 310.

**What is wrong**: T014 edits all six demo decks; T016 says "Add a fixture deck
… **(or extend one)**". If the implementer extends an existing deck, two tasks
in one parallel group write the same file — violating the task list's own rule
(line 17). Groups 1, 3 and 4 verified safe; max-3 respected everywhere.

**Fix**: strike "(or extend one)" — require a new file.

### F10 — MINOR · Stale references and small drift

- tasks.md T052 (line 250) cites "(T022, **T040**)" — T040 was renamed T035a by
  the C1 fix; no T040 exists.
- plan.md line 366 says "17 assertions"; the revised table (line 343) says 20.
- plan.md line 103 (Constitution row I) says "the **four** file formats"; the
  constitution has counted five since 2.3.0.
- spec.md line 176 cites "Principle XIV" for design rules; that is XVI.
- tasks.md line 282: "US4 … needs Phase 7's normalisation" — `normalise()`
  lands in T006 (Phase 3), not Phase 7. Harmless but misleading about ordering.
- SC-008's "produces the **same** reassignment" (spec.md line 208) is ambiguous
  under `secrets.choice`: only the *choice of card* is deterministic; the new id
  differs every run. FR-013b states it correctly; a test author reading SC-008
  alone might assert id equality. One clarifying clause. Likewise FR-003b never
  names the bound — any value works, but naming one (e.g. 1 000 attempts per id)
  removes the last implementer guess.

---

## The five prior fixes — verified

| Fix | Verdict | Evidence |
|---|---|---|
| **C1** (e2e test sequenced after its code) | **CONFIRMED, with residue** | T004a exists in Phase 3 and registers `id` as an exit-0 stub in both `bin/lernkarten` and `scripts/lernkarten` (verified byte-identical today); T035a sits before T036–T039 and states why its red is "no ids written", not "unknown command". Residue: T052's stale "(T040)" reference (F10). |
| **A1** (round-trip test vacuous after T014/T015) | **CONFIRMED** | T009 mandates inline string constants, explicitly forbids reading `cards/example.yaml` and the demo decks, and states the decay mechanism; T014 and T015 both carry back-references to the warning. |
| **A2** (undefined `lernkarten id` flag surface) | **PARTIAL** | contracts/cards-yaml.md § The `id` subcommand fully defines `--backfill`, `--reassign`, and bare-invocation-as-usage-error — but quickstart.md Scenario 6 still demonstrates the bare form the contract now rejects (F7). |
| **A3** (duplicate detection normalisation) | **CONFIRMED** | FR-008: "Sharing is judged on the **normalised** id (FR-004), so `a45dk` and `A45DK` are a duplicate"; repeated in T029 and data-model.md. |
| **A4** (writing path never enumerated) | **CONFIRMED** | FR-013a enumerates both paths and places `lernkarten build` in neither. The enumeration did expose a new seam — making `--backfill` a writing path contradicts the contract's "leaves existing ids untouched" on duplicate input (F4) — but the fix itself is real. |

---

## What I checked that came back clean

- **The 8 pt numbers re-derive exactly.** Default `--margin 5` gives
  `cw = (210−10)/2 = 100 mm = 283.46 pt`, so `cw/3 = 94.49 pt` ✓; IBM Plex Mono
  advance is 0.6 em, so `A45DK · 1/2` (11 glyphs) at 8 pt = 52.80 pt ✓.
- **The wordmark is not squeezed.** At 8 pt, `id-w = 52.80 + 5 mm = 66.97 pt`;
  the wordmark box becomes `283.46 − 17.57 − 66.97 = 198.9 pt` (≈183 pt after
  insets) against ≈80 pt of letterspaced Jost 5 pt text — more than 2× headroom.
  The A8 grid scales `cw`, `id-w` and the type by one factor, so the proportion
  is invariant, as research claims.
- **The empty-id footer is well-formed by construction.** With the separator
  dropped, `id-w = measure("1/2") + 5 mm ≈ 28.6 pt`; the block, its rule and the
  wordmark keep their positions. Spec FR-005 names the fallback value and T023
  implements exactly it. (The only issue is *where* T021 tests it — F5.)
- **`secrets.choice` + redraw is the right generator** for FR-012 (no state, no
  network) and FR-003a; determinism is correctly located in *card selection*
  (FR-013b), not id values. Exhaustion is unreachable at 32⁵ but FR-003b turns
  it into an error anyway — sound.
- **Adversarial YAML that did NOT break the splice**: block scalars (`|`/`>`),
  quoted first keys, `---` document markers, a BOM, tabs (fail parse → reported).
  Only flow style, aliases and detached-dash layouts break it (F2).
- **Dependency ordering executes.** T004/T004a scaffolding before every red;
  US2 before US1 before US3 is correctly dependency-driven (fallback before
  fixtures carry ids, fixtures before rendering is measured); no task needs an
  artifact a later task creates.
- **The no-dependency decision is sound.** ruamel.yaml's rejection is argued on
  the requirement (reserialisation vs byte-identity), Principle III's
  hand-rolling test is answered head-on with the `minyaml` precedent, and
  Constitution II/IV are vacuously clean.
- **Constitution VII/VIII/XIV/XV/XVII**: all fixtures are invented text in the
  demo project, no binaries, branch name conforms, engine pin untouched, no
  card-content rules disturbed. T055–T057 gate them explicitly.
- **Scope guard holds**: no task, assertion or contract line smuggles in
  `--card`, a registry, encoded meaning or `@version`; T056 checks it again at
  the gate.
- **The design-floor reasoning (research C-3)** matches `docs/design.md`'s
  actual text: the id is exempted by name, and T042 protects the exempting
  sentence from edits.

---

## Orchestrator resolution — 2026-08-21

Every major and both partials were **independently verified** before being acted
on, rather than accepted on the reviewer's word.

| Finding | Verified how | Resolution |
|---|---|---|
| **F1** `lernkarten check` never reaches the validation | Read `bin/lernkarten`: `check` → `build_pdf.main()` with `--check`; `check_project` appears nowhere in the dispatcher | **Confirmed.** New **T029a** (🔴 on the real `bin/lernkarten check` path) and **T031a** (🟢 appending id errors to `load_cards`'s existing `errors` channel, which `main()` already prints and exits on under `--check`). One insertion point serves both entry points. |
| **F2** splice corrupts some legal YAML | Ran `yaml.compose()` against five adversarial shapes | **Confirmed, and narrowed.** Flow-style cards and aliased cards break it. The review also named dash-detached first keys — **that is wrong**; those, block scalars and quoted first keys all probe safe. New **T009a**/**T010a** refuse the two real cases and re-parse before writing. |
| **F3** `cardid` cannot reach `compose()` legally | `dir(yamlio)` → `['YamlError', 'load', 'main', 'sys']`; no public route | **Confirmed.** New **T004b–T004d** add a public `yamlio.compose()` through the existing `_load_pyyaml()` bootstrap. `cardid` keeps importing only `yamlio`, so Principle VI holds as written instead of by assertion. |
| **A2** partial | `grep` of `quickstart.md` | **Confirmed.** Line 116's bare `lernkarten id` now reads `--reassign`, matching the contract. |
| **C1** stale reference | `grep T040` | **Confirmed.** T052 now cites T022, T029a and T035a. |

`plan.md` and `data-model.md` also had the `yaml.compose()` / "imports only
yamlio" contradiction corrected at source, so no artifact still describes the
illegal import.

**Task count 63 → 70. Red-first assertions 20 → 23.** Ordering re-verified: every
🔴 precedes its 🟢.

Moderates and minors from this review are left open deliberately — they are
recorded above and are cheaper to judge against real code in Phase 9 (Verify).
