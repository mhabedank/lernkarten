# Specification Analysis Report — 011 goal-fit sources

**Run**: 2026-09-08 · **Branch**: `feat/goal-fit-sources` · **HEAD**: `593a258`
**Artifacts read**: `spec.md`, `plan.md`, `tasks.md`, `research.md`,
`data-model.md`, `quickstart.md`, `contracts/*` (3), `checklists/*` (2),
`.specify/memory/constitution.md`, `CLAUDE.md`, `CONTRIBUTING.md`,
`docs/testing.md`, plus the shipped repository for every cited line number.

**Read-only.** Nothing outside this file and `.analyze-done` was written.

## Verdict

**0 CRITICAL · 3 HIGH · 6 MEDIUM · 9 LOW.** No constitution MUST is violated and
every one of the 39 active requirements reaches an artifact. The three HIGH
findings are a coverage hole (`/cards` half of FR-013), a routing table that
labels six requirements with a phrase its own checklist forbids, and one task
whose 🔴 marker contradicts the checklist that classifies the same case as a
guard. All three are fixable by editing the artifacts named; none requires
re-opening a settled decision.

## Findings

| ID | Category | Severity | Location | Summary | Recommendation |
|----|----------|----------|----------|---------|----------------|
| C1 | Coverage gap | **HIGH** | `tasks.md:329` (T025), `plan.md:519` | **FR-013's `/cards` half has no task and no gate.** Spec US3 scenario 5 says the selected-sample statement is required "when `/catalog` **or `/cards`** reports on it", `data-model.md:248` says "the same selected-sample sentence reappears in `/catalog` **and `/cards`** output", and `quickstart.md:254` says "the `/catalog` **and `/cards`** runs must also have said" it. But the routing table gives FR-013 only **F2** (the catalog check), T025 (the `cards` prompt edit) does not mention it, F3 does not assert it, and row **12-v** (the `/cards` manual row) covers FR-011/FR-012/SC-009 only. Row **9f** is a `/catalog` row. | Either add the selected-sample rule to T025 and to F3, and cite FR-013 in row 12-v — or narrow FR-013/US3-5/data-model/quickstart to `/catalog` alone. Do not leave the four artifacts disagreeing. |
| R1 | Traceability / constitution XI | **HIGH** | `plan.md:507-515`, `checklists/gates.md:29` | **Six routing entries are the bare phrase `gates.md` CHK002 forbids.** CHK002 requires every routing entry to be "a wave id (A1, D6, G3), or a `docs/testing.md` row id — **never** the bare phrase 'the manual checklist' or '**the prompt**'". FR-001, FR-002, FR-004, FR-005, FR-006 and FR-009 all carry `the rule is in the prompt` in the `check_docs.py` column. Worse, it is inaccurate in both directions: FR-001 **is** wave C's C1 and FR-002 **is** C2 (so they should name a case), while FR-004, FR-005, FR-006 and FR-009 have **no** wave-C case at all. This makes `plan.md:550`'s claim that "the ones with no automated row at all are FR-003, FR-007 and FR-038" untrue — ten requirements have no automated assertion, not three. | Replace the six cells: `C1` for FR-001, `C2` for FR-002, and an explicit `— (run output, row 4x)` for FR-004/005/006/009. Then correct the closing sentence. `plan.md:497` ("The whole of piece A's behaviour (FR-001 – FR-009)" is not automated) is the honest statement and the table should match it. **No requirement is left unheld** — all six reach named `docs/testing.md` rows — so this is a labelling defect, not a gate hole. |
| T1 | Test-first / inconsistency | **HIGH** | `tasks.md:241-245` (T017) vs `checklists/gates.md:50` (CHK020) | **T017 is marked 🔴 for a case the checklist classifies as a guard.** CHK020 lists the guard rows as "(C5, **D5**, D7, E4, F4, A4, B4)" — D5 among them. `tasks.md:34` defines 🔴 as "a task whose output must be a **failing** assertion before the next task begins", and T017 says "**RED against the shipped skill; green in shape**", which is self-contradictory: D5 and D5b run against **synthetic** text via the `read_skill` seam, so the shipped skill's state is irrelevant to them. With T015 and T016 already landed, both pass immediately. An implementer obeying the 🔴 marker would have to make D5 fail — which can only be done by writing a **non-neutral** C1 check, the exact outcome FR-039 and SC-016 exist to prevent. | Drop the 🔴 from T017 and label D5/D5b as guards, matching A3, E4 and G2, which are already handled that way (T009, T021b, T026 carry no 🔴). |
| D1 | Stale reference | MEDIUM | `quickstart.md:238`, `checklists/gates.md:29` | **Residue of the resolved `8h` → `8m` rename.** T040 is instructed to "correct the two `8h` references in `plan.md`" — but `8h` also survives in `quickstart.md:238` ("rows 8h, 9f, 12-v") and in CHK002's row-id list ("4a–4s, **8h**, 9f, 12-v, 12-vi"). Neither is assigned to any task, so the collision with `docs/testing.md:211`'s existing `/learning-goal` row would ship in two artifacts. | Extend T040's correction scope to `quickstart.md:238` and `checklists/gates.md:29`. |
| D2 | Inconsistency | MEDIUM | `plan.md:100,215,494,541,623`, `quickstart.md:112`, `tasks.md:402` | **Three different manual-row counts.** `plan.md` says "~22" in five places, `quickstart.md` says "Twenty-one", `tasks.md` says "**Twenty-three**" and shows the arithmetic (19 `/sources` rows 4a–4s + 4 pipeline rows). Twenty-three is correct. `tasks.md` flags the disagreement but assigns no task to fix `plan.md` or `quickstart.md`, and `gates.md` CHK011 is written against the wrong number ("the ~22 rows the plan claims"). | Fix the count to 23 in `plan.md` (5 sites), `quickstart.md:112` and CHK011, in the same task that fixes the `8h` residue. |
| S1 | Coverage gap | MEDIUM | `spec.md:352` (SC-002) | **SC-002 is the only success criterion cited nowhere downstream** — zero occurrences in `plan.md` and zero in `tasks.md`. Every other SC (001, 003–017) is named at least once. SC-002 is the measurable form of FR-003 ("every off-goal warning names the source id and quotes the goal line"), which is one of the deliberately ungated requirements, so its criterion going unnamed is exactly where it matters most. The behaviour *is* covered by rows 4b and 4f — only the SC number is missing. | Add SC-002 to row 4b (and 4f) in `plan.md` § The named rows and in T039's row table, beside the SC numbers already carried there. |
| S2 | Inconsistency | MEDIUM | `spec.md:161` (US4 scenario 12) | **US4 scenario 12's field enumeration is stale after round 4.** It says a non-practitioner candidate "carries every C1 field (name, location, what it serves, one credibility sentence, a registerable entry)" — **five** fields, omitting the **class** field FR-017 gained in round 4. `data-model.md:169-176` and `contracts/discovery-proposal.md:113-120` both list **six**, and T018 says "the **six** per-candidate fields". Read alone, scenario 12 implies a non-practitioner candidate need not name its class, which scenario 13, FR-017 and SC-017 all contradict. | Add "which class of material it is" to scenario 12's parenthetical. |
| S3 | Duplication | MEDIUM | `tasks.md:493-494` (T051, T052) | **Rows 4q and 4r are assigned to two By-Hand tasks.** T051 says "Run rows **4k – 4s**", which spans 4l…4r; T052 says "Run rows **4q, 4r**, 12-vi". A tester following the list runs the same two rows twice, and neither task owns them. | Narrow T051 to "4k–4p, 4s" and leave 4q/4r to T052, which is where they belong thematically (piece D, the silence). |
| G1 | Underspecification | MEDIUM | `tasks.md:119` (T005 implementer note) | **The gate's scope is justified against the wrong function.** `plan.md:399` and `research.md:177` specify `check_network_claim_is_not_exclusive()` over **`gated_files()`**; T005's note reasons about **`markdown_files()`** ("covers root `*.md`, `docs/*.md` and `skills/*/SKILL.md` only"). `gated_files()` (`scripts/check_docs.py:407-421`) is strictly wider — it adds `scripts/*.py` (minus `check_docs.py` itself) and `templates/*.typ`. The note's *conclusions* hold for both scopes (verified: `specs/**` and `tests/test_deps.py` are outside either, and `CONTRIBUTING.md:82` is the single live false positive across the whole gated set), but an implementer copying the note's reasoning could scope the check to `markdown_files()` and silently narrow FR-034/SC-010. | State `gated_files()` in T005's note and drop the `markdown_files()` sentence, or say explicitly that the wider set is intended. |
| X1 | Stale reference | LOW | `plan.md:154`, `data-model.md:158`, `research.md:124` | **Three `spec.md:NN` citations point at the wrong line.** `plan.md:154` cites `spec.md:299` for "`docs/design.md` is not a gate" — that text is at **spec.md:327**; `spec.md:299` is a row of the resolved-questions table. `data-model.md:158` cites `spec.md:193` for "a source that is both" — actual **208**. `research.md:124` cites `spec.md:192` for the "areas nothing findable serves" edge case — actual **207**. (`research.md:32` → `spec.md:13` and `plan.md:635` → `spec.md:32` are both **correct**.) | Re-point or drop the three. |
| X2 | Stale reference | LOW | `plan.md:238`, `research.md:179`, `tasks.md:112` | **`check_print_order` is cited at `:557-572` in three artifacts; it is actually at `scripts/check_docs.py:561-573`.** The function is the shape T005 copies, so the pointer is load-bearing for the implementer. | Update to `:561-573`. |
| X3 | Stale reference | LOW | `plan.md:590` | Cites `docs/testing.md:295` for "Rows 1–14 need a Claude session in the demo folder"; the sentence is at **`docs/testing.md:293`** (and reads "Steps 1–14"). | Update. |
| X4 | Stale reference | LOW | `spec.md:45`, `spec.md:50` | `spec.md:45` cites `scripts/check_project.py:38-39` for the closed `kind`/`depth` sets; `GOAL_KINDS` is at **:39** and `GOAL_DEPTHS` at **:40**. `spec.md:50` cites `:31` for `type: web`; `SOURCE_TYPES` opens at **:32** and `web` is at **:35**. | Update both. |
| X5 | Arithmetic | LOW | `plan.md:549` | "**Twenty-six** of the thirty-nine active requirements name an artifact in two of the three columns." Counting the table, **32–33** do (only FR-003, FR-030, FR-031, FR-032, FR-034, FR-038 — and FR-007 if its "nothing to validate" cell is not counted — have a single populated column). | Recount or drop the number. |
| X6 | Arithmetic | LOW | `plan.md:100` | "**4** new or edited fixture files"; the Project Structure block at `plan.md:207-212` lists **five** (`raw/field-notes/<incident>.md`, `knowledge/field-notes/<incident>.md`, `catalog/topics.md`, `cards/signals.yaml`, `README.md`), and tasks T028–T032 confirm five. | Change to 5. |
| X7 | Arithmetic | LOW | `tasks.md:119` | "the **seventeen** quotations of the stale claim in this feature's own spec/plan/research". Actual count across all seven feature artifacts is **nine** (spec 3, plan 2, tasks 2, research 1, checklists 1). Harmless — `specs/**` is outside the gate either way — but the number is wrong. | Drop the count or say "the quotations". |
| X8 | Style | LOW | `plan.md:576-577`, `tasks.md:424-425` | **Row `4s` is listed between `4k` and `4l`** in both row tables (deliberate — it is 4k's addendum companion), and the plan/tasks **skip `12-iv`**, jumping from the existing `12-iii` to a new `12-v`. `tasks.md:580` acknowledges the `12-iv` gap as "harmless, left as a gap". Both are defensible; neither is flagged where a reader first meets the table. | Add a one-line note under each row table, or re-letter. |
| X9 | Overstatement | LOW | `spec.md:360` (SC-010) | SC-010 says the stale network claim must be reported "when the 'only step that reaches the network' claim reappears **anywhere**". The gate covers `gated_files()` only — `tests/` and `specs/` are outside it, as research R5 and T005 both note. "Anywhere" is not what ships. | Qualify SC-010 to "anywhere `check_docs.py` gates", matching R5. |

## Coverage summary

### Functional requirements — 39 active, 39 covered (100 %)

| Requirement | Has task? | Task IDs | Gate reached |
|---|---|---|---|
| FR-001 – FR-009 | yes | T012, T013, T014 · T050 | C1/C2/C3 (FR-001/002/008) + rows 4a–4j. FR-004/005/006/009 manual only — see **R1** |
| FR-010 | yes | T022, T024, T025 · T053 | F2, F3 · row 12-v |
| FR-011 | yes | T010, T011, T022, T025 · T053 | F3 · B1–B3 (`check_project.py`, error) · row 12-v |
| FR-012 | yes | T025 · T053 | F3 · row 12-v |
| FR-013 | **partial** | T022, T024 · T053 | F2 · row 9f — **`/cards` half unassigned, see C1** |
| FR-014 | yes | T022, T024 · T053 | F2 · row 9f |
| FR-015 | yes | T007, T008, T022, T023, T029 · T053 | F1 · A1–A3 · row 8m |
| FR-016 – FR-018, FR-020 – FR-027 | yes | T015, T018 · T051 | D1–D4, D8 · rows 4k–4p |
| FR-019 | yes | T016, T019 · T051 | D6 · row 4s |
| FR-028 | n/a | *withdrawn, not reused* | — |
| FR-029 | yes | T013, T014 · T050 | C4 · row 4h |
| FR-030 | yes | T005, T012, T013, T015, T016, T020, T021a, T022 | *is* the eight check functions |
| FR-031 | yes | T007, T008, T010, T011 | *is* waves A and B |
| FR-032 | yes | T039, T040 | *is* the 23 rows |
| FR-033 | yes | T015, T018 · T052 | D1 · row 4r |
| FR-034 | yes | T005, T006 | G1, G2, G3 |
| FR-035, FR-036 | yes | T015, T020, T021 · T052 | D1, E3 · rows 4k, 4q |
| FR-037 | yes | T021a, T021b, T024 · T052 | E1, E2, E4 · row 12-vi |
| FR-038 | yes | T052 | row 12-vi only — deliberate |
| FR-039 | yes | T015, T016, T017, T018, T019 | D5, D5b, D6 |
| FR-040 | yes | T015, T018 · T051 | D8 (hook) · row 4k. "No filter ships" half deliberately ungated |

### Success criteria

16 of 17 cited in `plan.md` and/or `tasks.md`. **SC-002 is cited nowhere** — see **S1**.

### Unmapped tasks

**None.** All 56 tasks trace to a plan wave, a gate, or the By-Hand checklist.
T001–T004 (Setup), T044–T049 (Gates) and T050–T054 (By Hand) carry no story by
the file's own stated convention (`tasks.md:32`).

## The eight focus areas

| # | Area | Verdict |
|---|---|---|
| 1 | **Coverage** | **PASS with one gap.** All 39 active FRs map to ≥ 1 task; no orphan tasks. FR-013's `/cards` half (**C1**) is the single hole. |
| 2 | **Constitution XI routing** | **PARTIAL.** Every FR reaches `check_docs.py`, `check_project.py` or a *named* `docs/testing.md` row — no rule is unheld. But the four deliberately ungated requirements are **not** the only ones without an automated assertion: FR-004, FR-005, FR-006 and FR-009 have none either, hidden behind the phrase "the rule is in the prompt" (**R1**). All four are legitimate run-output carve-out cases and all four have named rows, so the defect is in the plan's labelling and in its own count, not in the routing. |
| 3 | **Test-first ordering** | **PASS with one mislabel.** Every check's adding task strictly precedes the task that greens it (T005→T006, T007→T008, T010→T011, T012/T013→T014, T015→T018, T016→T019, T020→T021, T021a→T021b, T022→T023-25→T026). Merging a check function with its cases into one task is correct here and is argued from constitution XI at `tasks.md:42-52`. T021a's placement after T021 is deliberate and lands *before* T024, the catalog edit it gates — correct. Only **T1** (T017's 🔴) is wrong. |
| 4 | **Parallel-group honesty** | **PASS, all four.** G1: `scripts/install-hooks.sh` (writes `.git/hooks/`) vs `scripts/make_testdata.py` (writes fixture binaries). G2: `skills/ingest`, `skills/catalog`, `skills/cards` — three distinct `SKILL.md`. G3: `tests/fixtures/demo-project/README.md` vs `tests/test_e2e.py`. G4: `docs/testing.md`, `docs/workflow.md`, `README.md` — and T039 (same file as T040) is sequential *before* the group opens, which the file states. Verified against the actual file list; no shared file in any group. (T040 additionally edits `plan.md`; still disjoint from T041/T042.) |
| 5 | **Numbering integrity** | **PASS.** 56 task ids, T001–T054 contiguous plus T021a/T021b, zero duplicates, zero gaps. FR-001–FR-040 all present; **FR-028 is not reused** anywhere — its five other occurrences are all references to the withdrawal. SC-001–SC-017 complete. Every task id and row id cited in the traceability table resolves. |
| 6 | **Terminology** | **PASS.** **Zero** occurrences of "rider"/"riders" anywhere under `specs/011-goal-fit-sources/` — the round-4 rename to "material-class addendum" is complete, including the check-function name `check_sources_skill_carries_the_practitioner_addendum()`. `[NEEDS CLARIFICATION]` appears only at `checklists/requirements.md:20` and `:144`, both prose stating that none remain. |
| 7 | **Scope drift** | **PASS.** Nothing in `plan.md` or `tasks.md` adds excluded behaviour. No class vocabulary or `CLASSES` tuple (forbidden with a stop-and-flag at `tasks.md:65-67`), no filter argument, no second addendum, no frontmatter key beyond `nature:`, no `/ingest` pagination, no `depth:` change, no sixth source type, no new dependency, no new file under `scripts/`, no brand re-render, no `docs/index.html` edit (recorded as a scoping decision at `plan.md:376-383` and re-verified by T043), no constitution amendment. Seven steps hold throughout. |
| 8 | **Stale cross-references** | **MOSTLY PASS — 5 of ~40 rot.** **Verified correct**: `skills/research-gaps/SKILL.md:17` (the exclusivity claim is exactly there), `skills/ingest/SKILL.md:69` (WebFetch), `skills/ingest/SKILL.md:92-111` (frontmatter block, exact) and `:27-28` (the `test_testdata.py` hazard), `scripts/check_docs.py:168` (`markdown_files`), `:79-121` (`check_skills`), `:357` (`read_skill`), `:363-374` (`check_print_skill_relays_setup`), `:575` (`main`), `tests/test_check_docs.py:193` (`gated_project`) and `:386-403`, `tests/test_testdata.py:265-273`, `docs/testing.md:211` (the `8h` collision is real), `:203`, `:193`, `:222`, `skills/catalog/SKILL.md:67` ("discovered") and `:60-67` (the tone precedent), `scripts/build_pdf.py:745` ("discovers"), `CONTRIBUTING.md:82` (the one live false positive — confirmed by a repo-wide sweep), `scripts/check_project.py:32-38`, `:47`, `:54`, `:146`, `:249`, `:372`, `:380`, `:425-426`, `:428`, `:690` (sparse *is* the fifth parameter), `:958`, `:1097-1098`, `:1180-1181`, `tests/test_e2e.py:27` (`DEMO_CARD_COUNT = 32`) and `:49` (`TIDES_CARD_COUNT = 11`), `tests/test_deps.py:10`, `scripts/demo.py:61-63`, `docs/index.html:489-492` (five words), `tests/fixtures/demo-project/catalog/topics.md:73` (`## Signals, flags and the radio`), and `--discover` absent from the whole repository outside `specs/`. **Rotten**: X1 (three `spec.md:NN`), X2 (`check_print_order`), X3 (`docs/testing.md:295`), X4 (two `check_project.py` refs). |

## Known-discrepancy residue check

The orchestrator named two Phase-5 resolutions to check for residue.

- **`8h` → `8m`**: **residue found.** `plan.md:521` and `:585` still say `8h` but
  are explicitly assigned to T040. `quickstart.md:238` and
  `checklists/gates.md:29` still say `8h` and are assigned to **nobody** — see
  **D1**.
- **seven vs eight check functions**: **clean.** No "seven small functions"
  survives. `plan.md:92`, `:190`, `:240`, `:277`, `quickstart.md:31`,
  `tasks.md:518` and `:554` all say eight, and the eight are enumerated at
  `tasks.md:589-596`. Verified against the repository: `check_docs.py` currently
  wires **thirteen** checks into `main()`, matching `plan.md:240`'s "beside the
  thirteen already there".

## Constitution alignment

No violation found. Spot-checks:

- **I** (format change carries its entourage) — `nature:` reaches
  `skills/ingest`, `skills/catalog`, `skills/cards`, `check_project.py`, the demo
  project and `docs/workflow.md`. All six are in the file list and all six have
  tasks (T023, T024, T025, T008, T029, T041).
- **V** — no new file under `scripts/`; the eight checks land in `check_docs.py`,
  argued at `plan.md:229-247`.
- **VII** — fixture extended, invented content, PR note required (T049).
- **X** — the four `description` assertions are enumerated before the rewrite
  (T036), verified against `check_skills` at `scripts/check_docs.py:79-121`.
- **XI** — red-before-green holds throughout (see focus area 3). The run-output
  carve-out is used as written, not extended.
- **XII** — the four gates are T044; the e2e run is T035/T046, correctly marked
  required rather than optional because `DEMO_CARD_COUNT` moves.

## Metrics

| | |
|---|---|
| Functional requirements (active) | 39 (FR-028 withdrawn) |
| Success criteria | 17 |
| User stories | 6 |
| Tasks | 56 (T001–T054 + T021a, T021b) |
| FR coverage (>= 1 task) | **39 / 39 = 100 %** |
| SC coverage (cited in plan or tasks) | 16 / 17 = 94 % |
| Unmapped tasks | 0 |
| Parallel groups verified disjoint | 4 / 4 |
| Cited line numbers verified | ~40, of which **5 rot** |
| Ambiguity findings | 2 |
| Duplication findings | 1 |
| Critical issues | **0** |

## Next actions

No CRITICAL issue blocks `/speckit-implement`. Recommended before starting:

1. **Fix C1** — decide whether FR-013 binds `/cards` and make the four artifacts
   agree. This is the only genuine coverage hole and it is cheapest to settle
   before T022 writes F2/F3.
2. **Fix T1** — drop T017's 🔴. Left as it is, it points an implementer at a
   non-neutral C1 check, which is the failure FR-039 exists to prevent.
3. **Fix R1** — relabel the six routing cells and correct the "no automated row"
   count. Purely editorial, but `gates.md` CHK002 currently evaluates "no".
4. Fold **D1**, **D2**, **S1**, **S2**, **S3**, **G1** and the nine LOW items
   into one editorial pass over `plan.md`, `quickstart.md`, `spec.md` (one line)
   and `checklists/gates.md`. None changes a decision.

Items 1–3 are edits to `spec.md` / `plan.md` / `tasks.md` and are out of scope
for this analysis phase, which is read-only.

**Ready to implement**: **yes, after items 1 and 2.** The artifact set is
unusually thorough — the test-first ordering is sound, the parallel claims are
honest, the scope guards are explicit, and the overwhelming majority of the
cited line numbers survive verification against the shipped repository.

---

## Remediation — 2026-09-08

**Read this section as the current state; the findings table above is the record
of what was found, not of what is still there.** Every one of the 18 findings is
resolved. **0 CRITICAL · 0 HIGH · 0 MEDIUM · 0 LOW residual.**

The pass was artifact-only: nothing under `scripts/`, `skills/`, `docs/`,
`tests/` or `README.md` was touched, and no task was executed. `docs/testing.md`
itself is still T039/T040's work — what changed here is the **planned** row set.

### The decision the user made, and what it moved

**FR-013 no longer prescribes a phrase.** The requirement used to demand the
sentence *"published incidents are a selected sample"*, which is jargon: it
names the effect for a reader who already knows it and says nothing to the
reader the warning exists for. FR-013 now demands **four contents** — checkable
in shape, free in wording:

1. which subtopic is affected and what it rests on (incident and experience
   reports only, with the count or the documents named, and that nothing
   covering the topic generally is among them);
2. why that material base is skewed, **written out** rather than named;
3. what that means for the cards drawn from it — how a *survived* failure
   unfolds, not what it takes to fail for good;
4. what would balance it — a general account or a reference work.

It stays **non-blocking**: a statement about the state of the sources, never an
error, never a reason to refuse anything, never a pointer at discovery (FR-037).
A **worked example** in the demo project's invented vocabulary (a Torvig signal
failure, an Ovray Cove grounding, the Fenmouth tide office, the flag code) is
written **once**, in `spec.md` § FR-013; `data-model.md` § 5,
`contracts/knowledge-frontmatter.md` and `contracts/discovery-proposal.md` point
at it instead of restating it (constitution VII: no real field of study appears
anywhere in it).

**FR-019 got the same treatment, and only that treatment.** Its second property
was the same jargon. It now demands the *content* — that material of this kind
is published only by the parties who came through the incident, so the cases
that ended badly are not among what can be found — and says explicitly that the
phrase "a selected sample" is neither required nor, standing alone, sufficient.
**What FR-019 means is unchanged**: which candidates it applies to, that a
non-practitioner candidate is held to neither property, and that the credibility
sentence stays *one* sentence (FR-018). The same rewording was carried to the
places that quoted the phrase: `data-model.md` §§ 5–6,
`contracts/discovery-proposal.md` § C2, `quickstart.md` row 4s, and the
*Experience report* key entity in `spec.md`.

### Findings, one by one

| ID | Severity | Resolution |
|---|---|---|
| **C1** | HIGH | **FR-013 binds `/catalog` *and* `/cards`** (the spec's reading wins). `plan.md`'s routing row now reads **F2, F3** and **9f** + **12-iv**; wave F's F3 case asserts the `/cards` half; **T022** F2/F3, **T025** (the `/cards` prompt edit) and **T053** carry it; the traceability table splits FR-013 from FR-014. New named row **12-iv** for the `/cards` half — id verified free against the shipped `docs/testing.md`, whose 12-series runs `12`, `12-i`, `12-ii`, `12-iii`. It also closes the `12-iv` gap X8 flagged. |
| **R1** | HIGH | The six `the rule is in the prompt` cells are gone: **FR-001 → C1**, **FR-002 → C2**, and FR-004/FR-005/FR-006/FR-009 → *no wave-C case; run output only* with their named rows. The closing claim is corrected: **seven** requirements have no automated assertion (FR-003, FR-004, FR-005, FR-006, FR-007, FR-009, FR-038), each reaching a named row; FR-032 has none either because it *is* the row set. X5's "twenty-six" recounted to **twenty-eight**. `gates.md`'s Notes updated from "three" to the seven. |
| **T1** | HIGH | **T017's 🔴 removed.** It is now *Guards D5 and D5b*, with the reason written in: both run against synthetic text through the `read_skill` seam, so they pass the moment T015/T016 land, and the only way to make D5 red is a **non-neutral C1 check** — the failure FR-039/SC-016 exist to prevent. Matches `gates.md` CHK020, which already lists D5 as a guard. A "do not fix the marker back to 🔴" line is attached. |
| **D1** | MEDIUM | `8h` → `8m` in `quickstart.md:238` and in CHK002's row-id list. T040's ⚠ note and the *Open items* entry now say the artifact-side references are already corrected, so T040 only writes `8m` into `docs/testing.md`. Zero `8h` row references survive outside the two notes that explain the collision. |
| **D2** | MEDIUM | One count everywhere: **24** rows — 19 `/sources` (4a–4s) + 5 pipeline (8m, 9f, **12-iv**, 12-v, 12-vi). It was 23 before this pass; the FR-013 `/cards` row makes it 24. Fixed in `plan.md` (5 sites), `quickstart.md`, `tasks.md` and CHK011. |
| **S1** | MEDIUM | **SC-002 now has a home**: rows **4b** and **4f** in `plan.md` § The named rows and in T039's row table, and the FR-003 routing cell names it. All 17 success criteria are cited. |
| **S2** | MEDIUM | US4 scenario 12's field list gains **"which class of material it is"** — six fields, matching FR-017, `data-model.md` § 4 and `contracts/discovery-proposal.md`. |
| **S3** | MEDIUM | **T051 narrowed to 4k–4p and 4s**; 4q and 4r belong to **T052** alone, stated in both tasks. Each row is run once. |
| **G1** | MEDIUM | T005's note now reasons about **`gated_files()`** (`scripts/check_docs.py:407-421`) — root `*.md`, `docs/*.md`, `skills/*/SKILL.md`, `scripts/*.py` except `check_docs.py`, `templates/*.typ` — with an explicit "do not scope it to `markdown_files()`, that would narrow FR-034/SC-010". |
| **X1** | LOW | The three `spec.md:NN` citations are **re-pointed by section instead of by line**, because a line number in a spec that is still being edited rots again: `plan.md` → *spec.md § Print & Design Impact* (the sentence is now at `spec.md:346`, having moved from 327 when FR-013 grew), `data-model.md` → *spec.md § Edge Cases, A source that is both* (now `:208`), `research.md` → *spec.md § Edge Cases* (now `:207`). |
| **X2** | LOW | `check_print_order` re-cited as **`:561-572`** in `plan.md`, `research.md` and `tasks.md`. Verified in the shipped file: `def` on 561, last body line 572, 573 is the blank line after it. |
| **X3** | LOW | `docs/testing.md:295` → **`:293`**, with the note that the sentence reads "Steps 1–14". |
| **X4** | LOW | `spec.md:45` → `scripts/check_project.py:39-40` (`GOAL_KINDS`, `GOAL_DEPTHS`); `spec.md:50` → `SOURCE_TYPES` at `:32-38`, `web` at `:35`. |
| **X5** | LOW | Recounted from the table: **28** of 39 name an artifact in two of three columns. |
| **X6** | LOW | `plan.md:100` "4 new or edited fixture files" → **5**, matching the Project Structure block and T028–T032. |
| **X7** | LOW | The "seventeen quotations" count is gone; the rewritten T005 note says which artifacts quote the stale claim without counting them. |
| **X8** | LOW | A one-line note under **both** row tables explains that `4s` sits beside `4k` on purpose. The `12-iv` gap is no longer a gap — **C1's new row fills it**, so the 12-series is contiguous. |
| **X9** | LOW | SC-010's "anywhere" is qualified to **"anywhere `check_docs.py` gates"**, with `gated_files()` enumerated and `tests/`/`specs/` named as outside it (research R5). |

> **Superseded in part on 2026-09-08 by the cross-model review remediation** —
> see [review.md § Remediation](review.md). Finding **R1**'s resolution below
> says *"**seven** requirements have no automated assertion"*; it is now **two**
> (FR-004 and FR-038). FR-003, FR-005, FR-006 and FR-009 gained cases C6–C9 and
> FR-007 gained cases A5/A6, on the ground that a check *could* be written for
> each. Finding **T1**'s resolution — dropping T017's 🔴 — still holds for **D5**
> and no longer for **D5b**, which was split into T018a, made to read the shipped
> `skills/sources/SKILL.md`, and marked 🔴 again. The task count below (56) is now
> 60 and the row count (24) is now 25. This paragraph is the only edit to this
> file; the rest is left as the audit record.

### Deliberately not changed

- **The findings table and metrics above** are left as the record of the
  2026-09-08 analysis run. Rewriting them would destroy the audit trail; this
  section is the delta.
- **`docs/testing.md` itself.** The rows are still T039/T040's work. Only the
  *planned* row set moved, in `plan.md`, `tasks.md`, `quickstart.md` and
  `gates.md`.
- **The word "rider"** survives in exactly one place: finding 6 above, which
  records that it appears nowhere else. That is a statement *about* the word.
- **`check_print_order` cited as `:561-572` rather than `:561-573`**, because
  573 is the blank line after the function.

### Re-validation

- `checklists/requirements.md` — re-validated and annotated: every box still
  ticks, counts unchanged (6 stories, 40 FRs / 39 active, 17 SCs), and FR-013 is
  *more* testable as four contents than as one phrase.
- `checklists/gates.md` — CHK002 and CHK011 corrected; the Notes' "three
  requirements with no automated row" corrected to the seven; a new **section G
  (CHK066 – CHK070)** covers FR-013's four contents, its two-step routing, its
  non-blocking status, FR-019's content-not-phrase rule, and the worked
  example's constitution-VII vocabulary.
- **Task ids**: 56 — T001–T054 contiguous plus T021a/T021b, zero duplicates,
  zero gaps.
- **Cross-references**: every relative link under `specs/011-goal-fit-sources/`
  resolves; every row id cited in a routing table appears in a row list and
  vice versa.
- **Zero** `[NEEDS CLARIFICATION]` markers outside prose stating that none
  remain.
- `python3 scripts/check_docs.py` — **exit 0**.

