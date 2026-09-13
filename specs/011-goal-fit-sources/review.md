# Pre-Implementation Review

**Feature**: Practitioner material, goal fit, and source discovery (issue #44)
**Artifacts reviewed**: spec.md, plan.md, tasks.md, research.md, data-model.md,
quickstart.md, contracts/discovery-proposal.md, contracts/knowledge-frontmatter.md,
contracts/sources-yaml-unchanged.md, checklists/requirements.md, checklists/gates.md,
analysis.md, `.specify/memory/constitution.md`, `CLAUDE.md`, `CONTRIBUTING.md`,
`docs/testing.md` — and the shipped files the plan proposes to change:
`scripts/check_docs.py`, `scripts/check_project.py`, `scripts/build_pdf.py`
(divider placement), `skills/{sources,ingest,catalog,cards,research-gaps}/SKILL.md`,
`tests/test_check_docs.py`, `tests/test_check_project.py`, `tests/test_e2e.py`,
`tests/test_testdata.py`, `tests/fixtures/demo-project/`.
**Review model**: Claude Fable 5.1
**Generating model**: not recorded in the artifacts (Phases 1–6)
**Worktree state at review**: branch `feat/goal-fit-sources` at `593a258` plus
uncommitted remediation edits under `specs/011-goal-fit-sources/`.
`pytest tests/test_check_docs.py tests/test_check_project.py` — 148 passed.
`python3 scripts/check_docs.py` — exit 0. `check_project.py … --strict` on the
fixture exits 1 only because `make_testdata.py` has not been run in this
worktree (four "does not exist (yet)" warnings), which T003/T004 cover.

## Summary

| Dimension | Verdict | Issues |
|-----------|---------|--------|
| Spec-Plan Alignment | WARN | US6 scenario 1 says `docs/workflow.md` is *not touched* while scenario 2 and T041 edit it; FR-037's skill list omits the one skill T006 writes the `--discover` token into |
| Plan-Tasks Completeness | WARN | two literal card counts and one e2e divider assertion that wave H breaks are not in any task; `docs/testing.md` row 5 goes stale; T037/T038 are human-session tasks sitting in an implementer wave |
| Dependency Ordering | PASS | every 🔴 task precedes its green; A→B data dependency real; H after A–G; verified against file contents |
| Parallelization Correctness | PASS | all four groups file-disjoint, ≤ 3 each; sequential claims verified |
| Feasibility & Risk | WARN | `test_four_dividers_open_a_further_page_on_the_demo_deck` fails at 33 or 34 cards — the "derived counts follow automatically" premise of T033 is false; D1 bundles ten assertions into one case |
| Standards Compliance | FAIL | D5b (T017) is green by construction against SC-016 — the shape constitution XI names as forbidden; five piece-A rules are routed to "run output only" although the same prompt-text gate that holds FR-002 could hold them |
| Implementation Readiness | WARN | two manual rows (4n, 4r) are not performable as written; the token each substring gate reads is left to the implementer, which is acceptable, but D1's ten-in-one shape means an omitted sub-assertion is invisible |

**Overall**: **NOT READY** — one FAIL and one feasibility defect, both fixable in
`tasks.md` in a single pass without reopening any settled decision. With F-1 and
W-1 fixed the verdict is READY WITH WARNINGS.

**WARN count**: 9 (W-1 … W-9). **FAIL count**: 1 (F-1).

---

## Findings

Most severe first.

### Critical (FAIL — must fix before implementing)

**F-1 — D5b does not test what SC-016 claims; it is green by construction.**
`tasks.md` T017; `plan.md` wave D row D5/D6; spec SC-016. SC-016 reads
*"deleting the addendum from `skills/sources/SKILL.md` fails exactly one check
and leaves the neutral checks green."* T017 says D5 and D5b run *"against
synthetic skill text through the `read_skill` seam, so the state of the shipped
`skills/sources/SKILL.md` is irrelevant to them."* That is precisely the
property SC-016 is about, discarded. The neutral check (T015) greps the **whole**
skill body, not a section — the shipped `read_skill()` returns the entire file.
If any token the neutral check demands (e.g. the "one sentence, never a number"
rule of FR-018, or the class-of-material line of D8) happens to be stated only
inside the practitioner sub-section, deleting that sub-section fails **two**
checks, SC-016 is false, and D5b — written by the same author against text the
author wrote to pass — never notices. Constitution XI: *"an assertion green by
construction, which is the shape this principle exists to forbid."*
**Failure scenario**: T019 writes the addendum sub-section and, while there,
states the FR-018 form rule ("one sentence, never a score") once, inside it;
T018's neutral section says "a credibility line" without the token the neutral
check reads. D1–D8 pass, D5/D5b pass, `check_docs.py` is green; issue #43 later
deletes nothing but *adds* a research addendum and finds the neutral check
reading the practitioner text after all.
**Fix (tasks)**: D5b must operate on the **shipped** skill text with the
addendum sub-section excised by heading (read the real file, cut from the
addendum's `###` heading to the next heading of equal or higher level, feed
that through the `read_skill` seam), and assert that exactly
`check_sources_skill_carries_the_practitioner_addendum()` reports and
`check_sources_skill_carries_the_discovery_contract()` does not. Keep the
synthetic D5 as the neutrality guard. Make the addendum heading a fixed string
the test can find (T019 should name it). This is one paragraph in T017 and one
sentence in T019.

### Warnings (WARN — recommend fixing, can proceed)

**W-1 — Wave H breaks an e2e assertion that no task anticipates, and T033's
premise is false.** `tasks.md` T033 says *"the derived `DEMO_A7_PAGES` /
`DEMO_A8_PAGES` / sheet counts follow from `sheet_pages()` automatically — do
not hand-edit them."* That is true of the derived constants but not of
`tests/test_e2e.py:1285`
`test_four_dividers_open_a_further_page_on_the_demo_deck`, which asserts
`pdf_pages(with_dividers) == DEMO_A8_PAGES + 2` and holds **only because 32 ≡ 0
(mod 16)**: at 32 cards the last A8 sheet is full and the divider block must
open a fresh one. At 33 or 34 cards (`scripts/build_pdf.py:216-257`,
`divider_block`) sheet 3 holds one card row, three rows are free, the two-row
block fits (`filled_to + gap + block_h + gap <= sheet_h`), and the dividers
share the sheet — pages stay `DEMO_A8_PAGES`, the assertion fails. It is
invisible to plain `pytest` (e2e skips without an engine) and only surfaces at
T035, where the implementer has to edit a spec-008 test with no task licensing
it. **Fix (tasks)**: T033 must name this test and say what to do — either
compute the expectation from `build_pdf.divider_block(DEMO_CARD_COUNT, 4, …)`
or build that case from a card subset that fills its sheets exactly (the test's
own docstring already says its counts "follow from `DEMO_CARD_COUNT`", so a
derivation is the honest repair). Which earlier phase: **tasks** (and plan §
Risks, which lists the `DEMO_CARD_COUNT` risk but not this one).

**W-2 — A second literal card count is missed.**
`tests/test_check_project.py:164` `assert counts["cards"] == 32` in
`test_the_demo_project_has_all_four_artifacts`. T033 moves only
`tests/test_e2e.py:27`; plan § Technical Context says *"`tests/test_e2e.py`
moves one constant"* and lists `tests/test_check_project.py` for waves A and B
only. Plain `pytest` (T044) catches it, so it is not silent, but it is a task
premise that is wrong and it will be edited without a task. **Fix (tasks)**: add
it to T033 or to a T031 note. Phase: tasks.

**W-3 — Five piece-A rules are routed "run output only" although the same
prompt-text gate that holds FR-002 could hold them.** plan § Which gate holds
which requirement routes FR-003, FR-004, FR-005, FR-006, FR-009 to *"no wave-C
case; run output only."* But T014 instructs the implementer to write every one
of those rules **into the prompt** ("the warning names the source `id` and the
`goal.md` line (FR-003); … reasons from `kind`/`depth` and says which (FR-005);
… at most one `/learning-goal` pointer per run (FR-006); … where it reasons
only from the URL … it says so (FR-009)"). If FR-002's "advisory" sentence is
gate-able as C2, FR-003's "names the id and the goal line" sentence is gate-able
by exactly the same substring shape, and so are FR-005's `kind`/`depth`, FR-006's
"one pointer" and FR-009's "say so". The run-output carve-out applies to the
*behaviour*, not to whether the prompt carries the rule; the plan uses it for
both. Constitution XI: *"if a requirement changes a file, it is assertable and
the clause above applies"* — `skills/sources/SKILL.md` is the file. The
consequence is concrete: a later edit that drops FR-003's sentence from the
prompt fails nothing automated. **Fix (plan + tasks)**: extend
`check_sources_skill_reads_the_goal()` with C6–C9 (id-and-line, kind/depth,
one pointer, unseen-source honesty), or state in the routing table *why* those
four sentences are deliberately ungated while FR-002's is not. Phase: plan.

**W-4 — D1 bundles ten assertions into one test case, so an omitted
sub-assertion is invisible.** T015 D1 reads *"a `sources` skill with no
`--discover` is reported. Also inside this one function: the found/shown
counts … ≤ 3 per area and ≤ 10 per run … one sentence and never a number …
paywalled … already in `sources.yaml` … no `goal.md` … no network … ordinary
registration path … network only in discovery mode … explicit request only."*
Ten rules, one named case, whose synthetic input is a skill missing
*everything*. A check function that forgot to assert, say, FR-024 or the
≤ 10 cap passes D1–D4 and D8 and ships. D2, D3, D4 and D8 each get their own
"missing exactly this" case; the other ten get none. This is the "red on the
bundle, never on the assertion" shape. **Fix (tasks)**: one negative case per
rule (a skill carrying everything *but* that rule), or drop those rules from
the automated column of the routing table and route them to rows 4k–4p, which
already exist. Phase: tasks.

**W-5 — T037 and T038 require a live Claude session with network and a hand on
the Wi-Fi switch, and sit in an implementer wave.** Wave I: *"drive `/sources`
against it in a real Claude session — a registration, a bare listing, a
removal, and `/sources --discover` — and edit … until every wave C, D and E
assertion passes and `--strict` exits 0 after accepting a candidate."* An
implementing agent cannot run a skill against itself in a user session, cannot
turn the network off (row 4p is inside T037's scope by implication), and will
either skip these or mark them done on the strength of the prompt text. The
By-Hand phase (T050–T053) already covers every row these two tasks touch.
**Fix (tasks)**: move T037/T038 to Phase 13, or mark them explicitly as
human-in-the-loop checkpoints that the implementer must *stop at* rather than
tick. Phase: tasks.

**W-6 — Two manual rows are not performable as written, which research R2
itself names as the failure mode FR-032 exists to prevent.** Row **4n**
(FR-021, FR-023, FR-024): a tester cannot make discovery *find* a paywalled
source or an unretrievable one on demand — the stimulus is not under the
tester's control (the fixture's `members.html` login page is on localhost,
which discovery does not search). Row **4r** (FR-033): "none of those three
makes a network request on discovery's behalf" — a Claude session exposes no
request log; the tester can only read the transcript, which is row 4q. FR-024
is performable (register a source, then discover). **Fix (plan)**: split 4n into
4n (FR-024, performable) and a note that FR-021/FR-023 are judged
*opportunistically* when a run happens to meet such a candidate, and either
give 4r an observable (the transcript shows no tool call reaching a URL) or
merge it into 4q. Phase: plan.

**W-7 — The `--discover` token gate excludes the one skill T006 writes the token
into, and the spec's FR-037 list does not cover it.** FR-037 names `/ingest`,
`/catalog`, `/cards`, `/print`. T006 puts `/sources --discover` into
`skills/research-gaps/SKILL.md` (correctly — FR-034 asks for the seam). So
`/research-gaps`, whose wrap-up already says *"If the user wants their own
material instead, `/sources` is the way"*, is the skill most likely to drift
into *"or run `/sources --discover`"* at the end of a run with open gaps — and it
is neither token-gated (it must carry the token) nor covered by row 12-vi
(which runs `/sources` → `/ingest` → `/catalog` → `/cards`). `/learning-goal`
is in the same position. Round 2's rationale ("no pointer at all … one nudge at
a time") applies to both. **Fix (spec, one sentence + tasks, one row)**: either
extend FR-037 to all five non-`/sources` skills and add `/learning-goal` and
`/research-gaps` runs to row 12-vi, or record in spec Assumptions that those two
are deliberately outside the silence rule. Phase: analyze (it is a coverage
gap the analysis should have seen; it edits spec text).

**W-8 — US6 scenario 1 contradicts scenario 2 and T041 on `docs/workflow.md`.**
`spec.md:192` — *"`docs/workflow.md`, `docs/index.html`, `CLAUDE.md` … are
**not** touched by this feature."* `spec.md:193` — *"When `/sources` is
described in the README, `docs/workflow.md` and its own `SKILL.md`, **Then** the
description names both jobs."* T041 edits `docs/workflow.md` in three places
(Step 1, Step 2, Step 5). The intent is plainly "the step count in
`docs/workflow.md` does not move" (spec line 15 says so), but scenario 1 as
written fails T043's own scope check. **Fix (spec)**: scenario 1 should say "the
seven-step description in `docs/workflow.md`", not the file. Phase: analyze.

**W-9 — `docs/testing.md` row 5 goes stale when T028 lands.** Row 5 expects
*"five files under `knowledge/field-notes/`"* from `/ingest field-notes`. T028
adds a sixth raw file to `raw/field-notes/`. No task edits row 5; T039/T040 add
rows only. Also `tests/fixtures/demo-project/README.md`'s raw-material table
(T032 adds a row, fine) and the demo README's "six card files" / "seven `Term:`
lines" sentences should be re-read after T030/T031 in case the new subtopic
gets a `Term:` line. **Fix (tasks)**: add "update row 5's count" to T040.
Phase: tasks.

### Observations (informational)

**O-1 — T005's red claim is true, and the false-positive guard is correctly
scoped.** Verified against the shipped repository: `skills/research-gaps/SKILL.md:17`
reads *"**This is the only step that reaches the network**"*. Across the whole
`gated_files()` set the phrase "reaches the network" occurs exactly twice —
there and `CONTRIBUTING.md:82` (*"an accidental push to `main` fails before it
even reaches the network:"*), whose paragraph carries no "only". `--discover`
occurs nowhere outside `specs/`. So G3 fails on its assertion against a clean
checkout and G2 has a real thing to guard. One caution for the implementer: the
*rewritten* paragraph T006 produces will likely keep "the only one that puts
material into the project the user did not choose" beside "reaches the
network"; the exclusivity regex must bind "only" to the network clause
(`only\s+(?:step|one)\s+that\s+reaches\s+the\s+network`), not to the paragraph.

**O-2 — The substring gates are written by the same author as the prompt they
gate.** Every wave C–F check reads a token the implementer chooses and the
prompt the implementer writes. That is inherent to constitution XI's
prompt-change rule and not a defect of this plan, but it bounds what "red"
means here: the reds of waves C–F prove the *shipped* 55-line skill lacks a
discovery mode, which nobody doubted. The value of these gates is entirely as
**drift** detectors after the fact, and the plan is honest about that in
§ The two halves. Reviewers should read them as such.

**O-3 — FR-035 is asserted in two functions.** T015 D1 includes "entry is by
explicit request only (FR-035)"; T020 E3 asserts the same sentence in a
separate function whose stated purpose is that *"one function holding both
cannot say which rule broke."* When the sentence is dropped, two checks fail.
Drop FR-035 from D1's list.

**O-4 — FR-007 has a writable negative check that the plan does not consider.**
`check_sources()` (`scripts/check_project.py:317-370`) accepts unknown keys on
an entry (`login:` relies on that), so a `fit:` key would validate silently
today. A one-line "a `sources.yaml` entry carries `fit:`/`assessed:` — the
verdict lives in the run" error is writable and cheap. The plan's "nothing to
validate — that is the point" is a choice, not a consequence; say so, or add
the check.

**O-5 — The fixture extension will survive `--strict`.** Verified the invariants:
the new subtopic under `## Signals, flags and the radio` needs no `Parents:`/
`Also covers:` (single parent), a `Term:` line is optional and if present must
be anchored by a card in `cards/signals.yaml`, the knowledge twin needs ≥ 200
body characters to avoid "barely any text" (the existing field-notes documents
run 1.4–2.1 kB), `path:` must point at the T028 file, and `check_cards` only
warns on a missing `source:` so the FR-011 error is the only new red. Nothing in
`test_testdata.py` enumerates `raw/field-notes/` (it asserts three specific
files exist). `TIDES_CARD_COUNT` is untouched by adding to `signals.yaml`.

**O-6 — Wave order and parallel groups verified.** Every 🔴 task strictly
precedes the task that greens it. Group 1 (`install-hooks.sh` vs
`make_testdata.py`), group 2 (three `SKILL.md`), group 3 (fixture README vs
`test_e2e.py`), group 4 (`testing.md` vs `workflow.md` vs `README.md`) are
file-disjoint; T039 precedes group 4 on the same file. T021a after T021 is
right: the absence becomes checkable once the token exists. T028/T029 could be
parallel but the twin's `path:` names the raw file, so sequential is fine.

**O-7 — `checklists/gates.md` counts "CHK001 – CHK065" in T054 but the file now
runs to CHK070** (section G added by the remediation). T054 should say CHK070.

---

## Answers to the eight adversarial questions

**1. Is the test-first discipline real or ceremonial?** Real for the
deterministic half, thin but honest for the prompt half, and ceremonial in one
place.
- **T005 (G3)**: genuinely red against the shipped repo for the claimed reason —
  verified (O-1). G1/G2 pass immediately by design; the plan says so.
- **T007 (A1)**: red on its assertion — `check_knowledge` ignores `nature:`
  today (`scripts/check_project.py:372-428` never reads it). Real.
- **T010 (B1)**: red on its assertion — `check_catalog` returns three values
  and `check_cards` has no experience set; the test would fail on the *error
  count*, not on an import, provided the test calls `check()` rather than the
  new signatures. The task should say "call `check_project.check()`" so the red
  is on the assertion and not a `TypeError` from a signature that does not
  exist yet. Borderline; one sentence fixes it.
- **T012 (C1–C3), T013 (C4), T015 (D1–D4, D8), T016 (D6), T020 (E3), T022
  (F1–F3)**: each red against the shipped skill because the shipped skill lacks
  the token — trivially true, and each also proves the gate fires on synthetic
  text. Real but weak (O-2). D1's ten-in-one bundle is where it turns ceremonial
  (W-4): ten rules, one case.
- **T021a (E1/E2)**: not red against the repo and not claimed to be; synthetic
  positives that prove the gate fires. Correctly labelled.
- Fourteen 🔴 markers: thirteen hold; T010's needs the one-sentence note.

**2. Are the guards genuinely guards?** A3 (absence never a finding), A4, B3
("all, not any"), B4, C5, D7, E4, F4 and G2 can each fail for a defect a
plausible implementer would commit (an `any()` instead of `all()`; a regex on
the bare words; a prompt edit that forgot one section). **D5** can fail only if
the test author writes non-neutral synthetic text — a defect in the test, not
in the product — so it is a documented invariant rather than a guard. **D5b**
as specified cannot fail for the defect SC-016 is about (F-1). Fix D5b and it
becomes the strongest guard in the wave.

**3. Are the seven ungated requirements honestly ungated?**
- FR-003, FR-004, FR-005, FR-006, FR-009: **not honest as stated.** The
  *behaviour* is run output, but the *prompt sentence* carrying each rule is
  exactly as gate-able as FR-002's "advisory" sentence, which the plan does
  gate as C2. A check could have been written for each (W-3). FR-004 is the
  weakest of the five — "never about the subject in general" is hard to
  tokenise — and could reasonably stay a row.
- FR-007: a check *could* be written (O-4); leaving it out is defensible if
  said.
- FR-038: genuinely run-only. A script cannot know which sources the user
  named. Honest.

**4. FR-039's separability claim** — *not* mechanically true as the checks are
specified. It depends on where the implementer happens to put each sentence,
because the neutral check reads the whole file, and the only test of the
property runs on synthetic text (F-1). It becomes mechanically true once D5b
excises the addendum from the shipped text by heading.

**5. The `--discover` token gate** — the residual risk is bounded in the four
skills it reads, and row 12-vi does cover the paraphrase for those four. It is
**not** bounded for `/research-gaps` (which must carry the token) or
`/learning-goal` (never gated, never rowed), and those are the two skills whose
wrap-ups already point at other steps (W-7). The paraphrase row is honest; the
skill list is short by two.

**6. Prompt-level requirements no check and no row could distinguish** — the
ones whose stimulus a tester cannot produce or whose effect a tester cannot
observe: **FR-021** ("did not retrieve" — the transcript shows what was
proposed, not what was fetched and dropped), **FR-023** (needs a paywalled find
on demand), **FR-033**'s "no network request" (no request log in a session;
only "no mention" is observable, which is FR-036), and **FR-027**'s *found*
count (the tester sees the number the run prints and has no way to check it).
FR-009 ("says so when it reasons only from the URL") is judgeable but only when
the tester knows the run did not look, which the run itself reports — circular.
FR-004 is a judgement a human can make. Everything else in the seven-and-rows
set is observable.

**7. Scope drift** — none of the named kinds. Checked: no class vocabulary or
`CLASSES` tuple (forbidden with stop-and-flag), no filter argument, no second
addendum, no frontmatter key beyond `nature:`, no `/ingest` pagination, no
`depth:` change, no dependency, no brand re-render, no `docs/index.html` edit
(T043 re-verifies), no step-count change. Two small additions beyond the FRs,
both recorded: research R1's "a goal written later does not re-judge" sentence
(gated by C3) and R3's caps (prompt constants). The one *unplanned* edit the
feature will force is the divider e2e test (W-1) — a test in spec-008's
territory that a task must license.

**8. The demo fixture** — it will survive `--strict` if T028–T031 follow the
conventions listed in O-5. `DEMO_CARD_COUNT` moves by one or two as the tasks
assume, and the derived page constants do follow. What the tasks miss: (a)
`tests/test_check_project.py:164` hard-codes 32 (W-2); (b)
`test_four_dividers_open_a_further_page_on_the_demo_deck` holds only at a
multiple of 16 and **fails at 33 or 34** (W-1) — verified against
`divider_block()`; (c) `docs/testing.md` row 5's "five files" (W-9). (a) and (c)
are caught by the gates or by a reader; (b) is caught only under
`LERNKARTEN_E2E=1`, which T035 does run — but the implementer then has to
change an assertion no task owns.

---

## Settled decisions I would question

Said once, not re-litigated:

- **FR-037's list of four skills.** Round 2's rationale ("no pointer at all")
  argues for silence in *every* run the user did not start with `--discover`,
  and `/research-gaps` and `/learning-goal` are runs. Listing four of six reads
  as an oversight rather than a choice; if it is a choice, the spec should say
  why those two may mention it.

---

## Recommended Actions

- [ ] **F-1 (tasks)** T017: make D5b read the shipped `skills/sources/SKILL.md`, excise the addendum sub-section by its heading, and assert exactly one check reports. T019: fix the addendum heading text so the test can find it.
- [ ] **W-1 (tasks + plan § Risks)** T033: name `test_four_dividers_open_a_further_page_on_the_demo_deck` and derive its expectation from `build_pdf.divider_block()` (or build it from a sheet-exact subset); add the row to plan § Risks.
- [ ] **W-2 (tasks)** T033: also move `tests/test_check_project.py:164`.
- [ ] **W-3 (plan)** Either add C6–C9 to `check_sources_skill_reads_the_goal()` for FR-003/005/006/009, or write into the routing table why those prompt sentences are ungated while FR-002's is not.
- [ ] **W-4 (tasks)** T015: one negative case per rule in D1, or move the ten rules to the manual column.
- [ ] **W-5 (tasks)** Move T037/T038 to Phase 13 or mark them as human checkpoints the implementer stops at.
- [ ] **W-6 (plan)** Split row 4n; give 4r an observable or fold it into 4q.
- [ ] **W-7 (analyze → spec)** Extend FR-037 and row 12-vi to `/research-gaps` and `/learning-goal`, or record the exclusion in Assumptions.
- [ ] **W-8 (analyze → spec)** US6 scenario 1: "the seven-step description in `docs/workflow.md`", not the file.
- [ ] **W-9 (tasks)** T040: update `docs/testing.md` row 5's file count.
- [ ] **O-3 (tasks)** Drop FR-035 from T015's D1 list; E3 owns it.
- [ ] **O-7 (tasks)** T054: CHK070, not CHK065.
- [ ] **Q1/T010 (tasks)** T010: state that the wave-B cases call `check_project.check()` so the red is on the assertion, not on a signature that does not exist yet.

---

## Remediation — 2026-09-08

**Read this section as the current state; everything above is the audit record
of the review and is left exactly as it was written.** The one FAIL, all nine
warnings and the seven observations are addressed below — fixed, or left with
the reason. The pass was **artifact-only**: nothing under `scripts/`, `skills/`,
`docs/`, `tests/` or `README.md` was touched, and no task was executed. What
moved is `tasks.md`, `plan.md`, `spec.md` (two places), `quickstart.md`,
`checklists/gates.md` and `checklists/requirements.md`.

### F-1 — D5b was green by construction. Fixed, and it is a red artifact again.

**D5b now reads the file that ships.** It was split out of T017 into its own
task, **T018a**, placed between T018 (the neutral section) and T019 (the
addendum), and it does this:

1. `body = check_docs.read_skill("sources")` — the shipped text, before any
   monkeypatch.
2. `assert ADDENDUM_HEADING in body`, where
   `ADDENDUM_HEADING = "### Practitioner material"` is a module-level constant
   in `tests/test_check_docs.py`. **This is the assertion it is red on.**
3. Cut from that heading line to the next line matching `^#{1,3}\s` — a heading
   of equal or higher level — or to end of file.
4. Feed the remainder through the `read_skill` seam.
5. Assert that `check_sources_skill_carries_the_practitioner_addendum()` reports
   and that the **other four** checks reading that file —
   `check_sources_skill_carries_the_discovery_contract()`,
   `check_sources_skill_reads_the_goal()`,
   `check_sources_skill_states_the_archive_reach()` and
   `check_sources_skill_states_the_explicit_request()` — report nothing. One of
   five fails; four stay green, which is SC-016's "exactly one" made mechanical.

**The excision is by heading on purpose.** Cutting by the addendum's prose would
pass silently if the prose were reworded; cutting by a heading the test names
verbatim means a rename fails step 2 with a message saying which heading it
looked for. **T019 was given the matching obligation**: the sub-section opens
with the line `### Practitioner material`, spelled exactly that way, and may be
renamed only together with the constant.

**The marker is restored.** T018a carries 🔴. At its position the shipped skill
has the neutral section (T018) and no addendum, so the red is exactly one thing —
the heading is missing — and T019 is the green. Placing it *after* T018 rather
than beside T017 is deliberate: before T018 it would be red for two reasons at
once and the message would not say which. **T017 keeps D5 unchanged** and
unmarked: a neutrality guard on synthetic text that can fail only for a defect
in the test, which is a documented invariant and is correctly classified as one.

`checklists/gates.md` **CHK020** now lists the guards as A4, A6, B4, C5, D5, D7,
E4, F4 and asks explicitly that **D5b sit on the red side**; **CHK037** was
rewritten from "deleting the practitioner sub-section fails exactly one check"
to the excision procedure against the shipped file. `plan.md`'s wave-D table
gains a **D5b** row and a paragraph saying why D5 and D5b are different kinds of
artifact.

### W-1 — the divider assertion. Fixed, with the arithmetic verified rather than asserted.

**The review is right, and it is worse than one test.** Verified by running
`scripts/build_pdf.divider_block()` and `scripts/leitner.py` directly. A8 is the
4 × 4 grid on a 297 × 210 mm sheet at a 5 mm margin, so a card is
71.75 × 50 mm; `GAP_MM = 8.0`, `GROWTH_MM = 1.5`, `LAYOUT[4] = (2, 2)`,
`LAYOUT[3] = (3,)`. A four-divider block is `2 × 51.5 + 8 = 111.0` mm tall, a
three-divider block `51.5` mm, and the block shares the last sheet when
`filled_to + 8 + block_h + 8 <= 210`, with `filled_to = 5 + used_rows × 50`.

| Deck | `used_rows` | `filled_to` | needed | shares? |
|---|---|---|---|---|
| 32 cards, 4 dividers | `32 % 16 = 0` → 4 | 205 | 332 | **no** — a further sheet. This is why the assertion passes today |
| **33** cards, 4 dividers | `33 % 16 = 1` → 1 | 55 | 182 | **yes** — pages stay `DEMO_A8_PAGES`, the `+ 2` fails |
| 34 cards, 4 dividers | `34 % 16 = 2` → 1 | 55 | 182 | yes — the same failure |
| 11 Tides cards, 4 dividers | 3 | 155 | 282 | **no** — a further sheet |
| 8 Signals cards, 3 dividers | 2 | 105 | 172.5 | yes |
| 9 Signals cards, 3 dividers | 3 | 155 | 222.5 | **no** — and that breaks a *second* test |

**Two tests break at 33, not one.** Besides
`test_four_dividers_open_a_further_page_on_the_demo_deck`
(`tests/test_e2e.py:1285`), the `added` half of
`test_the_run_says_which_paper_case_it_is_in` (`:1325`) asserts
`"further sheet" in added.stderr` for the whole deck at four dividers — the same
branch, the same failure. And a **third** would have broken had wave H added two
cards: `test_three_dividers_share_a_sheet_with_a_short_deck` builds
`--topic Signals`, which goes from 7 cards to 9, and at 9 the three-divider block
stops sharing.

**The decision, written into `tasks.md` T031 and T033 and into `plan.md` § Risks.**

- **Option (a) — keep the count a multiple of 16 — was rejected.** It means
  adding **16** cards for one invented incident write-up: a fixture change out of
  all proportion to FR-011, and one that would break the card-style rules it
  exists to demonstrate.
- **Option (b) is taken and licensed in writing.** Wave H adds **exactly one**
  card, so `DEMO_CARD_COUNT` goes 32 → 33 and `cards/signals.yaml` goes 7 → 8.
  T031 now says *exactly one* rather than "one or two", with the 9-card
  arithmetic beside it and a stop-and-flag if a second card turns out to be
  needed — that is what keeps the third test alive.
- **Both broken assertions are rebuilt on `--topic Tides`**, 11 cards, which
  fills three of four rows on one sheet and therefore *is* the "no room left"
  branch the tests were written for (`155 + 127 = 282 > 210`). `TIDES_CARD_COUNT`
  is the one count this feature pins as unchanged, and T033 adds
  `assert 5 <= TIDES_CARD_COUNT <= 16` so a future move of `cards/tides.yaml`
  fails with a message rather than an arithmetic surprise. The `--topic Signals`
  companion keeps the "shares the sheet" branch, so both branches of
  `divider_block()` stay covered.
- T033 also names the two **docstrings** that say "32 cards" (`:464`, `:1220`).

**The two companions.** `tests/test_check_project.py:164`
(`assert counts["cards"] == 32`) is item 2 of T033 — **W-2** closed. `docs/testing.md`
row 5's "five files under `knowledge/field-notes/`" becomes six, written into
**T040** with the note that it is the only shipped row this feature's fixture
work invalidates — **W-9** closed. T032 additionally has to re-read the demo
README's "seven `Term:` lines" sentence, and **T030 now forbids a `Term:` line**
on the new subtopic, which keeps that count still and avoids the anchor
obligation a `Term:` line would create.

### W-3 and O-4 — five gates written. The user's decision, implemented.

| Requirement | Check | Where | Is the gate as strong as the requirement? |
|---|---|---|---|
| **FR-003** | case **C6** in `check_sources_skill_reads_the_goal()` | wave C, T012a 🔴 → T014 | **No.** It asserts the *rule is stated in the prompt*. It cannot see a warning. Behaviour stays on rows 4b/4f |
| **FR-005** | case **C7**, same function | wave C, T012a → T014 | **No.** Rule stated only; it cannot see which of `kind`/`depth` a run reasoned from. Rows 4a/4b/4c |
| **FR-006** | case **C8**, same function | wave C, T012a → T014 | **No.** Rule stated only; it cannot count a run's pointers. Row 4i |
| **FR-009** | case **C9**, same function | wave C, T012a → T014 | **No, and circular beyond that** — see below. Row 4a |
| **FR-007** | cases **A5/A6**, `VERDICT_KEYS` refused in `check_sources()` | wave A, T008a 🔴 → T008b | **Yes**, for the on-disk half, which is the whole of what FR-007 forbids. The obligation *is* an absence and the check sees exactly it |

**No new check function**: C6–C9 extend the function T012 already writes, so
`check_docs.py` still gains **eight**. Each of C6–C9 is its **own** case, so a
failure names which sentence left the prompt.

**FR-007's check rejects five key names, never unknown keys in general.**
`check_sources()` (`scripts/check_project.py:317-370`) reads `id`, `type` and the
type's required field and ignores everything else — `login: true` on the demo
fixture's `harbour-office-members` entry relies on that. An allowlist of
permitted keys would invalidate `login:`, would invalidate every project on disk
carrying a key this repo has not thought of, and would be a behaviour change no
requirement asks for. FR-007 forbids a **verdict** on the entry, not
extensibility. `VERDICT_KEYS = ("fit", "assessed", "goal_fit", "discovered",
"proposed_by")` is exactly the negative
[contracts/sources-yaml-unchanged.md](contracts/sources-yaml-unchanged.md)
§ *The change* already enumerates; **no project on disk carries any of the five**
— checked, including `tests/fixtures/demo-project/sources.yaml` — so nothing
becomes newly invalid. The contract's "no timestamp" clause is **not** gated,
because a timestamp has no fixed key name, and that is said where the check is
described.

**FR-009's circularity is stated, not papered over.** C9 asserts the prompt
carries the rule; it cannot see an invention. Row 4a cannot decide it either: the
only evidence a tester has that a run did not look at a source is the run's own
statement that it did not, which is the thing under test. The routing cell says
*"rule stated only, and circular beyond that"*, and FR-009 heads the new
`plan.md` § **What no artifact can decide**.

**Counts moved.** Requirements with **no automated assertion at all**: seven →
**two**, FR-004 and FR-038 (plus FR-032, which *is* the row set, and FR-040's
ungated half). Two-column coverage: twenty-eight → **thirty-three** of
thirty-nine, the six single-column rows being FR-004, FR-030, FR-031, FR-032,
FR-034 and FR-038. Tasks: 56 → **60** (T008a, T008b, T012a, T018a). Test cases:
~33 → ~48. New constants: ~2 → ~3. `docs/testing.md` rows: 24 → **25**.
Check functions in `check_docs.py`: **still eight**. `plan.md`, `tasks.md`,
`quickstart.md` and `checklists/gates.md` (CHK002, CHK003, CHK004, CHK010,
CHK011, CHK020, CHK037, the Notes) all carry the new numbers, and gates.md gains
a **section H, CHK071 – CHK075**, for the five new gates and what they are worth.

### The remaining findings

| ID | Resolution |
|---|---|
| **W-2** | Closed. `tests/test_check_project.py:164` is item 2 of T033, edited there rather than discovered at T044 |
| **W-4** | Closed. D1's ten rules are now **ten cases** — D1 (no `--discover` at all) plus **D1a – D1i**, each a synthetic skill carrying everything *but* that one rule, so a failure names the rule. The plan's routing table points at the specific case (FR-018 → D1c, FR-020 → D1h, FR-023 → D1d, FR-024 → D1e, FR-025 → D1f, FR-026 → D1g, FR-027 → D1a, FR-033 → D1i) |
| **W-5** | Closed by marking rather than by moving. T037 and T038 carry 🧑 **HUMAN CHECKPOINT — stop here, do not tick from the prompt text**, and wave I's preamble says why: an agent cannot drive a skill against itself in a user session or turn the network off, everything both tasks verify is also covered by Phase 13, so nothing is lost by stopping and the only thing lost by *ticking* is the evidence that the prompts run. They stay in wave I because T036 (the `description` rewrite) genuinely belongs there and the three read as one unit |
| **W-6** | Closed, both halves. Row **4n** is split: 4n keeps FR-024 (performable — register, then discover) and new row **4n-i** takes FR-021 and FR-023 with the honesty written into the row: open every proposed URL, a 404 or a paywall **fails** the row, and if none is any of those the outcome is **"not exercised", never "pass"**. Row **4r** got an observable instead of being merged into 4q: re-run the registration, the listing and the removal **with the network off** — all three must behave exactly as online (US5 scenario 3) — because a session exposes no request log but the network is a fact |
| **W-7** | Half closed, half named precisely. `skills/learning-goal/SKILL.md` becomes the **fifth** token-gated file (new case **E2a**); `--discover` occurs nowhere in it today, so the token is exact there too. `/research-gaps` **cannot** be gated — T006 writes `/sources --discover` into it for FR-034's seam — so what holds it is stated instead: T006's one-paragraph scope, row **12-vi** extended to run `/learning-goal` **and** `/research-gaps`, and a new `spec.md` § Assumptions bullet recording why FR-037 names four skills and how the other two are held. The residual risk — a paraphrase inside `skills/research-gaps/SKILL.md` that row 12-vi's run happens not to emit — is written down in `plan.md` § Risks and accepted |
| **W-8** | Closed. `spec.md` US6 scenario 1 now reads *"the seven-step description in `docs/workflow.md`"*, with a parenthetical saying the file **is** edited in three places by T041 and that what may not move is the count and the order. That is what spec line 15 always meant and what T043 actually checks |
| **W-9** | Closed. See W-1's companions above: T040 moves row 5 to six files, T032 re-reads the demo README's "seven `Term:` lines", T030 forbids a `Term:` line on the new subtopic |
| **O-1** | Noted, no change needed. The exclusivity-regex caution is already in T005's implementer note |
| **O-2** | Noted, no change needed, and the remediation does not weaken it: C6–C9 are the same shape of gate and the plan says so in every routing cell rather than only in § The two halves |
| **O-3** | Closed. FR-035 is dropped from D1's list; **E3** owns it alone, and the routing cell says why (*"asserting it twice means one dropped sentence fails two checks"*) |
| **O-4** | Implemented — see the five-gate table above |
| **O-5** | Noted. T030's new "no `Term:` line" instruction is consistent with it |
| **O-6** | Noted. The four parallel groups are unchanged; group 3's description now names both test modules T033 touches, and the file-serialisation list is corrected (`check_docs.py` nine tasks, `check_project.py` three, `test_check_docs.py` eleven, `test_check_project.py` four) |
| **O-7** | Closed. T054 walks **CHK001 – CHK075** |
| **Q1 / T010** | Closed. T010 carries the note: call `check_project.check()`, not the internal functions, because T011 changes three signatures and a direct call would go red on a `TypeError` rather than on the error count |

### Deliberately left, with the reason

- **The findings above this section are not rewritten.** They are the audit
  record of what the review found, not a statement of what is still there.
- **FR-004 stays ungated.** *"Never about the subject or the publisher in
  general"* is a statement about what a warning does **not** say, and there is no
  token whose absence carries it. The review says the same (question 3). Row 4d.
- **FR-040's "no filter ships" half stays ungated.** A negative check would have
  to name an argument spelling that does not exist, and inventing one is the
  thing FR-040 forbids. Unchanged from the plan's own reasoning.
- **T037 and T038 stay in wave I** rather than moving to Phase 13, marked as
  checkpoints. Moving them would separate T036 from the two tasks that verify it.
- **`/research-gaps` is not token-gated**, and cannot be. Named above; the
  residual risk is accepted rather than engineered around with a
  paragraph-scoped gate that would be one more thing to keep true.
- **FR-021, FR-023, FR-027's *found* count and FR-009 are not decidable** by
  anything this feature ships. They are recorded in `plan.md` § *What no artifact
  can decide* with what *is* decidable of each, rather than given a row a tester
  would have to lie on.
- **`analysis.md` is not rewritten either**, for the same reason; one sentence
  was added to its remediation section pointing here, because its "seven
  requirements have no automated assertion" line is now superseded.

### Re-validation

- `checklists/gates.md` — CHK002, CHK003, CHK004, CHK010, CHK011, CHK020 and
  CHK037 rewritten; the Notes corrected from seven ungated requirements to two;
  new **section H (CHK071 – CHK075)**.
- `checklists/requirements.md` — re-validated and annotated. Counts unchanged
  (6 stories, 40 FRs / 39 active, 17 SCs); the two spec edits recorded; SC-016
  noted as measurable for the first time.
- **Task ids**: 60 — T001 – T054 contiguous, plus T008a, T008b, T012a, T018a,
  T021a, T021b. Zero duplicates, zero gaps.
- **Cross-references**: every task id, case id and row id cited in a routing or
  traceability table appears in its list, and vice versa. Row `4n-i` is in both
  row tables, both routing tables and both By-Hand tasks.
- **Zero** `[NEEDS CLARIFICATION]` markers outside prose stating that none
  remain. **Zero** occurrences of "rider" outside `analysis.md`'s finding 6,
  which is a statement *about* the word.
- `python3 scripts/check_docs.py` — **exit 0**.


---

## Second pass — 2026-09-08

**Scope**: the remediated artifacts, re-read against the shipped repository at
`593a258` (worktree, uncommitted edits under `specs/011-goal-fit-sources/`).
Every claim in § Remediation was checked against the file it names, not the
report. `python3 scripts/check_docs.py` exit 0;
`pytest tests/test_check_docs.py tests/test_check_project.py` 148 passed.
`scripts/build_pdf.divider_block()` was run directly for the W-1 arithmetic.

### Verdict

| Dimension | Verdict | Issues |
|-----------|---------|--------|
| Spec-Plan Alignment | WARN | spec.md:57 (Q2's consequence) still says piece A is verified "not by `check_project.py`" and `contracts/sources-yaml-unchanged.md:46` still says discovery entries are validated "with no change" — both now false because of A5/A6 (N-4); the contract enumerates four verdict names, not the five `VERDICT_KEYS` claims it enumerates (N-5) |
| Plan-Tasks Completeness | WARN | plan.md still says "one or two cards" in three places (:164, :222, :571) while T031 and the W-1 fix depend on **exactly one** (N-2); T040 propagates a row-5 count that is already stale on `main` (N-3) |
| Dependency Ordering | WARN (regressed from PASS) | T018a step 5 asserts `check_sources_skill_states_the_explicit_request()`, which T020 writes — D5b cannot go green at T019 as stated (N-1) |
| Parallelization Correctness | PASS | four groups unchanged and still file-disjoint; T008a/T008b/T012a/T018a are all inside sequential blocks; no id collisions (60 ids, T001–T054 + six suffixed) |
| Feasibility & Risk | PASS | W-1 arithmetic independently reproduced and correct; the Tides guard `5 <= TIDES_CARD_COUNT <= 16` is the exact range of the further-sheet branch |
| Standards Compliance | PASS | F-1 closed — D5b is red on its assertion against the shipped file; C6–C9 labelled "rule stated only" in every place that cites them; A5/A6 honest; D1a–D1i one case per rule |
| Implementation Readiness | WARN | "four other skills" survives in five places after E2a made it five (N-6); plan.md's wave-E table is split by a prose paragraph between the E4 and E3 rows (N-7) |

**Overall**: **READY WITH WARNINGS.** No finding is green-by-construction and
none reopens a settled decision. N-1 and N-2 should be fixed before the first
commit — each is one sentence — because an implementer who follows the text
literally hits N-1 at T019 and N-2 at T031. The rest is staleness.

### Status of the original findings

| ID | Status | Evidence |
|---|---|---|
| **F-1** | **CLOSED** | T018a reads `check_docs.read_skill("sources")` (the real `SKILLS/sources/SKILL.md`, `scripts/check_docs.py:357-360`), asserts `"### Practitioner material" in body` first, excises to the next `^#{1,3}\s` line, monkeypatches the seam, asserts one-of-five. Against the shipped 55-line skill the heading is absent, so step 2 fails on its assertion — a real red. T019 names the heading verbatim. The excision works: `read_skill` returns the whole file as one string, the five checks all read through that seam, and `^#{1,3}\s` matches `#`, `##` and `###` lines and nothing else in that file (`#list(` has no whitespace after `#`). "Exactly one of five" is true only *after T021* — see N-1 |
| W-1 | CLOSED | arithmetic reproduced below; T031 pins exactly one card, T033 items 3–4 rebuild both assertions on `--topic Tides`, plan § Risks carries the row |
| W-2 | CLOSED | T033 item 2 names `tests/test_check_project.py:164` |
| W-3 | CLOSED | C6–C9 in T012a, routed in plan § Which gate with "rule stated only" in each cell; CHK071 |
| W-4 | CLOSED | D1, D1a–D1i in T015 and plan wave D, each "everything but that one rule"; FR-035 dropped from D1 |
| W-5 | CLOSED | T037/T038 carry 🧑 with "stop here, do not tick"; wave-I preamble states why |
| W-6 | CLOSED | row 4n (FR-024, performable) and 4n-i (FR-021/023, "not exercised" never "pass"); row 4r re-runs the three ordinary invocations offline |
| W-7 | CLOSED | `skills/learning-goal/SKILL.md` gated (E2a); `--discover` confirmed absent from it and from `research-gaps` today; row 12-vi runs both; spec § Assumptions bullet records the `/research-gaps` exclusion |
| W-8 | CLOSED | spec.md:192 now reads "the seven-step description in `docs/workflow.md`" with the parenthetical |
| W-9 | CLOSED as written, but see N-3 | T040 moves row 5's count; the number it moves it *to* is wrong |
| O-3 | CLOSED | E3 alone owns FR-035 |
| O-7 | CLOSED | T054 walks CHK001 – CHK075; gates.md runs to CHK075 |
| Q1/T010 | CLOSED | T010 says call `check_project.check()` |

### Independent W-1 arithmetic

`build_pdf.divider_block(cards, count, GRIDS["4x4"], 5)` run directly:
sheet 297 × 210, card 71.75 × 50, `GAP_MM = 8.0`, `GROWTH_MM = 1.5`,
`LAYOUT = {3: (3,), 4: (2, 2)}`. Block heights 111.0 (four) and 51.5 (three).
Shares when `5 + used_rows × 50 + 8 + block_h + 8 <= 210`.

| Deck | Block page | Last card page | Branch |
|---|---|---|---|
| 32 cards, 4 dividers | 2 | 1 | further sheet — why `:1285` and `:1325` pass today |
| **33**, 4 | 2 | 2 | **shares — both assertions fail** |
| 34, 4 | 2 | 2 | shares |
| 11 (Tides), 4 | 1 | 0 | further sheet — the replacement is in the right branch |
| 7 (Signals today), 3 | 0 | 0 | shares |
| **8** (Signals after T031), 3 | 0 | 0 | **shares — `test_three_dividers_share_a_sheet_with_a_short_deck` survives** |
| 9 (Signals if two cards), 3 | 1 | 0 | further sheet — the third test would break |

The remediation's table is correct in every row. The guard range is also
right: with four dividers the block shares only when `used_rows <= 1`, i.e.
`cards % 16` in 1..4; every count in 5..16 has `used_rows >= 2` and opens a
sheet. `--topic Tides` selects exactly `cards/tides.yaml` (substring match on
`'Kestrel Islands: Tides'`, `build_pdf.py:416`; no other topic contains it),
and the "further sheet" text is the literal at `build_pdf.py:755`. One
cosmetic note: the test name `…_on_the_demo_deck` stops being accurate once it
builds a subset; T033 should rename it.

### FR-007 check safety — verified

`check_sources()` (`scripts/check_project.py:317-370`) reads `id`, `type`, the
type's required field, `gap` for `research`, and nothing else — an unknown key
is never touched, which is what `login: true` on `harbour-office-members`
relies on. Grepped every `sources.yaml` reachable on this machine (the fixture,
`sources.example.yaml`, the main checkout's, and five private projects): none
carries `fit`, `assessed`, `goal_fit`, `discovered` or `proposed_by` at any
indentation. Nothing becomes newly invalid.

### C6–C9 labelling — verified honest

plan § Which gate holds which requirement says "rule stated only" in the FR-003,
FR-005, FR-006 and FR-009 cells; T012a carries the same paragraph; the
traceability table in tasks.md says "the rule is stated in the prompt — nothing
more"; gates.md CHK071 asks for exactly that; requirements.md's re-validation
says "where the check is weaker than the requirement — all four of C6–C9 — the
plan now says so". No success criterion was changed and none over-claims:
SC-001 – SC-003 remain run-output criteria measured on rows 4a–4i.

### New findings

**N-1 (WARN, must fix — Dependency Ordering) — T018a's green is at the wrong
task.** `tasks.md:307` has D5b assert that the excised text is clean under
`check_sources_skill_states_the_explicit_request()`. That function is first
written at **T020** (`tasks.md:342`), two tasks and one wave later. At T018a the
test is red on step 2, which is honest. But at **T019** — the task tasks.md names
as D5b's green — step 2 passes and step 5 raises `AttributeError`, which
constitution XI says is not a test outcome at all; D5b then fails on E3's
assertion after T020 (the sentence is not in the file yet) and goes green only
at **T021**. The remediation moved D5b's assertion count from two checks to five
without noticing that the fifth belongs to a later wave. **Fix (one sentence
each)**: T018a asserts the *four* checks that exist at its position
(`reads_the_goal`, `states_the_archive_reach`, `carries_the_discovery_contract`,
`carries_the_practitioner_addendum`) and says "T021 extends this to the fifth";
T021's GREEN line gains "and D5b now asserts one-of-five". Alternatively T018a
moves after T021 — but then T019 precedes it and the heading exists, so the red
is lost; the first option is the right one.

**N-2 (WARN, must fix — Plan-Tasks Completeness) — plan.md still licenses two
cards.** `plan.md:164` ("the one or two new demo cards"), `:222`
(`cards/signals.yaml  # ← one or two cards`) and `:571` (wave H: "one or two
cards in `cards/signals.yaml`"). T031 says **exactly one** and its arithmetic
shows a second card breaks `test_three_dividers_share_a_sheet_with_a_short_deck`.
tasks.md names plan.md "the ordering authority"; an implementer reading wave H
in the plan is told the opposite of what T031 says. Three word-level edits.

**N-3 (WARN — Plan-Tasks Completeness) — T040 writes a stale number.** Row 5's
"five files under `knowledge/field-notes/`" was true at `51f0434`, when
`raw/field-notes/` held five non-empty files. Since then `tide-office-cover.md`
(BUG-004), `chart-notes.md` (`92628bb`) and the generated `harbour-log.txt`
(`make_testdata.py:287`) were added, so `/ingest field-notes` produces eight
today — the row is already stale on `main`, outside this feature. T040 and plan
§ Risks say "becomes six", which propagates the stale count with one added. The
fix belongs to T040 all the same, since it is the task that touches the row:
count the non-empty files under `raw/field-notes/` (recursively, after
`make_testdata.py`) at the time of the edit and write that number — nine after
T028 — rather than "five plus one". quickstart.md:128 says six too.

**N-4 (WARN, low — Spec-Plan Alignment) — two sentences now contradicted by
A5/A6.** `spec.md:57` (clarification Q2): "Consequence: every piece-A
requirement is verified by named manual rows under FR-032, not by
`check_project.py`" — FR-007 is piece A and is now verified by A5/A6.
`contracts/sources-yaml-unchanged.md:46`: a picked candidate "is validated by
today's `check_project.py` with no change" — `check_sources` gains the
`VERDICT_KEYS` refusal. Neither changes an obligation; both are one-clause
edits, and the clarification log can take a dated addendum rather than a
rewrite.

**N-5 (WARN, low — Spec-Plan Alignment) — `goal_fit` is not in the contract.**
T008a, T008b, plan wave A and the remediation all say the five names are "the
ones `contracts/sources-yaml-unchanged.md` § *The change* already enumerates".
The contract (`:22-23`) enumerates **four**: `fit`, `assessed`, `discovered`,
`proposed_by`. `goal_fit` is a reasonable fifth, but the claim that the contract
names it is false, and CHK004/CHK073 point a reviewer at the contract to check
the list. Add `goal_fit` to the contract's sentence, or drop the "already
enumerates" wording.

**N-6 (WARN, low — Implementation Readiness) — "four other skills" survives
E2a.** `plan.md:101`, `:203`, `:530`; `tasks.md:335`, `:731` still describe the
negative token gate as running over four skills. T021a, E4, the routing table
and spec § Assumptions say five. Cosmetic, but the plan's own § Scale/Scope is
one of the five and it is the sentence an implementer reads first.

**N-7 (WARN, low — Implementation Readiness) — the wave-E table is broken.**
`plan.md:541-552`: the `/research-gaps` paragraph sits between the E4 row and
the E3 row of the same markdown table, so E3 renders as a stray line outside
the table. Move the paragraph below the E3 row (the text following it,
"the rows are grouped by function", already expects E3 to be in the table).

**N-8 (OBSERVATION) — analysis.md's counts are superseded.** Its re-validation
still says "Task ids: 56". The remediation added a pointer at `analysis.md:241`
to review.md, which is enough; noted so nobody reconciles the two.

### Checks that the remediation did not break

- **No new task is green by construction.** T008a's A5 is red because
  `check_sources` ignores unknown keys (verified above). T012a's C6–C9 are red
  because the shipped skill states none of the four sentences (55 lines, no
  `goal.md`). T018a is red on the heading. T008b, T014, T019 are the greens.
- **Ids**: T001–T054, T008a, T008b, T012a, T018a, T021a, T021b — 60, no
  duplicates. Case ids A5/A6, C6–C9, D1a–D1i, E2a collide with nothing.
- **File serialisation** in § Not parallel is correct: nine tasks on
  `check_docs.py`, three on `check_project.py`, eleven on `test_check_docs.py`,
  four on `test_check_project.py`.
- **`--topic Signals` companion** still covers the shares branch at 8 cards.
- **`check_project.py` on the fixture**: adding one card to `signals.yaml`, one
  subtopic with no `Term:` line, one `nature: experience` document — O-5's
  invariants still hold; `tests/test_check_project.py:879`'s `subtopics == 2`
  is a tmp project, not the fixture.

### Would I implement from these artifacts now?

Yes, after N-1 and N-2 — two edits of one sentence each, both in the artifact
that owns them. Without N-1 an implementer reaches T019, sees D5b raise
`AttributeError`, and has to choose between skipping ahead and editing the test;
without N-2 an implementer who reads plan wave H before T031 may add the second
card that breaks the third e2e test. Everything else here is staleness a reader
can see through. The discipline is intact: every 🔴 is red on its assertion
against the shipped repository, and the one that was not (D5b) now is.

---

## Third pass fixes — 2026-09-08

**The second pass's findings above are left exactly as written** — they are the
audit record. This section says what was done about N-1 to N-7. The pass was
**artifact-only**: nothing under `scripts/`, `skills/`, `docs/`, `tests/` or
`README.md` was touched, and no task was executed. What moved is `tasks.md`,
`plan.md`, `spec.md`, `quickstart.md`, `contracts/sources-yaml-unchanged.md` and
`checklists/gates.md`.

### N-1 — D5b asserted a check that did not exist yet. Fixed by splitting the assertion across two tasks.

The set of checks reading `skills/sources/SKILL.md` **grows during the feature**,
and D5b's "exactly one of N" has to grow with it. Verified against `tasks.md`
which functions exist where:

| Check | Written at | Exists at T018a? |
|---|---|---|
| `check_sources_skill_reads_the_goal()` | T012, extended T012a | yes |
| `check_sources_skill_states_the_archive_reach()` | T013 | yes |
| `check_sources_skill_carries_the_discovery_contract()` | T015 | yes |
| `check_sources_skill_carries_the_practitioner_addendum()` | T016 | yes |
| `check_sources_skill_states_the_explicit_request()` | **T020** | **no** |

- **T018a** now asserts **one of four**: `..._carries_the_practitioner_addendum()`
  reports, and `..._carries_the_discovery_contract()`, `..._reads_the_goal()` and
  `..._states_the_archive_reach()` are clean on the excised text. A paragraph
  says why the fifth is not named here — naming it would make D5b raise
  `AttributeError` at T019, which is not a test outcome.
- **T021** now extends step 5 to the fifth check, once both the check (T020) and
  the sentence it reads (T021) exist, and re-runs `pytest tests/test_check_docs.py`.
  Its GREEN line says so.
- **T018a's red is unchanged**: step 2, `assert ADDENDUM_HEADING in body`,
  against a shipped `skills/sources/SKILL.md` that carries no
  `### Practitioner material` heading. T019 is still its green, and now honestly
  so — every check T018a names exists before T018a runs.
- **The excision by heading is untouched**, as the second pass asked.
- Propagated: `plan.md` wave-D D5b row and the D5-versus-D5b paragraph,
  `checklists/gates.md` CHK037 (now naming both the four and the five and the
  task each belongs to), `tasks.md`'s FR-039 traceability row (T021 added).
  `contracts/discovery-proposal.md` already said "exactly one of the checks"
  with no number and needed no edit.

### N-2 — "one or two cards" removed from `plan.md`, with the reason stated once.

`plan.md:164` (Constitution row XVII), `:222` (the file tree comment) and wave H
all said "one or two"; T031 says **exactly one** and the e2e arithmetic depends
on it. All three now say exactly one. The **reason** is written in **one place**
— wave H, next to the fixture description, because that is the paragraph an
implementer reads before T031 — and it points at § Risks for the full
arithmetic rather than repeating it: 8 Signals cards keep the three-divider block
sharing the last sheet (`105 + 8 + 51.5 + 8 = 172.5 <= 210`), 9 open a further
one (`222.5 > 210`) and break
`test_three_dividers_share_a_sheet_with_a_short_deck`. A second card is a
**stop-and-flag** back to the plan.

### N-3 — the row-5 count was wrong in both directions. Counted, and the task now says to count.

**Counted directly**, in this worktree, at
`tests/fixtures/demo-project/raw/field-notes/`, recursively, against
`git ls-files` plus the generators in `scripts/make_testdata.py`:

| File | Source | Ingests to a document? |
|---|---|---|
| `kestrel-islands.md` | versioned | yes |
| `tide-cycle.txt` | versioned | yes |
| `signal-code.md` | versioned | yes |
| `appendix/wind-log.txt` | versioned | yes — the recursion case |
| `übersicht-inseln.md` | versioned | yes — the slug case |
| `chart-notes.md` | versioned (`92628bb`) | yes |
| `tide-office-cover.md` | versioned (BUG-004) | yes |
| `harbour-log.txt` | generated (`make_testdata.py:287`) | yes — the Windows-1252 case |
| `empty.md` | versioned | **no** — zero bytes; the row itself says it is reported, not invented |
| `diagrams/signal-flags.png` | generated (`make_testdata.py:256`) | **no** — a picture `chart-notes.md` links to, judged as that document's figure |

**Eight today. Nine after T028.** So "five" is stale on `main` (it was true at
`51f0434`) and the remediation's "six" would have shipped a second wrong number.

**T040 no longer hard-codes anything.** It now instructs: run
`make_testdata.py`, count the ingestible files under `raw/field-notes/`
recursively with the two exclusions above, and write **that** number — with
"eight today, nine after T028" given as a figure to *verify*, not to trust,
and the rot itself named as the reason. `plan.md` § Risks, `plan.md` wave J,
`plan.md`'s file-tree comment and `quickstart.md` § 5 all say the same.

### N-4 — two sentences that A5/A6 made false.

- `spec.md` clarification Q2 gains a dated amendment: FR-007's *negative* is the
  one piece-A obligation `check_project.py` does verify, because a stored verdict
  would be a key on disk and its absence is checkable. Everything else in piece A
  — what a run *says* — stays on manual rows. The clarification's answer text is
  otherwise unchanged.
- `contracts/sources-yaml-unchanged.md` § *What a discovery run may write*: "it
  is validated by today's `check_project.py` with no change" becomes "validated
  on exactly the same terms as any other entry … **and, from this feature
  onwards, no `VERDICT_KEYS` name on it**". The point the bullet was making —
  discovery gets no validation of its own — is preserved and restated.

### N-5 — `goal_fit` added to the contract.

`contracts/sources-yaml-unchanged.md` § *The change* now enumerates all five
names, so the claim in T008a, T008b, `plan.md` wave A and CHK004/CHK073 that the
contract "already enumerates" them is true. A short paragraph beside it states
that this sentence **is** the enumeration `VERDICT_KEYS` is written from, that
"no timestamp" is deliberately outside the tuple because a timestamp has no
fixed key name, and that the list is forbidden names and never an allowlist.

### N-6 — "four other skills" corrected to five where it means the gated set.

Corrected in the five places where the number describes the **token gate's**
file set: `plan.md` § Scale/Scope, `plan.md`'s `check_docs.py` file-tree comment,
`plan.md` wave E's "two checks, not one" paragraph, `tasks.md`'s wave-E preamble
and `tasks.md`'s resolved-question 2. Each now reads "five … FR-037's four plus
`skills/learning-goal/SKILL.md` (case E2a)". `checklists/gates.md` CHK027 too.

**Left alone on purpose**: the places that say *"FR-037 names four skills"* —
`plan.md` § Risks, `spec.md` § Assumptions, `tasks.md` T021a's residual-risk
paragraph, `checklists/requirements.md`. FR-037 *does* name four; the gate reads
five. That distinction is the whole content of the W-7 resolution and flattening
it would lose the reason `/learning-goal` is gated without being named.

### N-7 — the wave-E table is well-formed again.

The `/research-gaps` paragraph moved from between the E4 and E3 rows to below the
E3 row. The table now runs E1, E2, E2a, E4, E3 uninterrupted, which is the order
the following sentence ("the rows are grouped by function … E3 stands alone")
already described. No row text changed.

### Re-validation

- **Markdown tables**: every table in the feature directory checked
  programmatically for a separator row and a constant column count — **zero**
  malformed tables.
- **Task ids**: 60 — T001 – T054 contiguous, no gaps, no duplicates, plus
  T008a, T008b, T012a, T018a, T021a, T021b.
- **Cross-references**: every `T###` cited anywhere in the feature directory
  (outside `review.md` and `analysis.md`, which are audit records) is a defined
  task. `checklists/gates.md` runs CHK001 – CHK075 with no gaps, which is what
  T054 walks.
- **`[NEEDS CLARIFICATION]`**: zero outside prose stating that none remain.
- `python3 scripts/check_docs.py` — **exit 0**.

### Found while fixing, beyond N-1 to N-7

- **`tests/fixtures/demo-project/README.md`'s raw-material table is missing two
  rows** — `chart-notes.md` and `tide-office-cover.md` are on disk and versioned
  but not listed, which is the same drift that produced N-3. It is a shipped-file
  defect outside this feature's scope, so **nothing was edited**; T032 is the
  task that opens that table, and an implementer who is there anyway may add the
  two rows. Recorded here so it is not lost.
