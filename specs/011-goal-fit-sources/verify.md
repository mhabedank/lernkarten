# Verification Report — 011 goal-fit-sources (Phase 9)

**Branch**: `feat/goal-fit-sources` · **HEAD**: `1ba69f6` · **Diff verified**: `afe2781..HEAD` (19 files) · **Date**: 2026-09-09
**Verifier**: post-implementation gate, different model from the implementer, read-only.
**Suites**: not re-run here (orchestrator reports `pytest`, `LERNKARTEN_E2E=1`, `ruff`, `check_docs.py`, `check_project.py --strict`, `deps.py --check` all green). Re-run in this pass: `pytest tests/test_check_docs.py -q` (99 passed), `pytest tests/test_check_project.py -q` (202 passed), `python3 scripts/check_docs.py` (exit 0, 7 skills), `python3 scripts/check_project.py tests/fixtures/demo-project --strict` (exit 0, 33 cards, 0 warnings).

## Verdict

**The implementation matches what the artifacts promise.** No CRITICAL finding. Three WARNINGs, all fixable in one prompt paragraph or at the pull-request step; none is a constitution conflict in the code, none loses a gate, none touches a forbidden file. The one substantive drift is a wording in `skills/sources/SKILL.md` that reads FR-005 as a conjunction where the spec and manual row 4c read it as a disjunction.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| E1 | Spec Intent | **WARNING** (MEDIUM) | `skills/sources/SKILL.md:74-76` vs `spec.md:47,228`, `docs/testing.md:196` (row 4c) | The prompt says "`depth: expert` **with** `kind: interview` or `kind: meeting` weighs practitioner material up" — a conjunction. The spec's Problem section says "`depth: expert`, **or** `kind: interview` / `meeting`". Row 4c flips the demo goal from `depth: working` to `expert` while `kind: exam` stays, and expects the run to weigh the material **up**; under the prompt as written that pair matches neither rule. Gate C7 only asserts `kind`, `depth` and "which of the two" and cannot see this | Reword to "`depth: expert`, or `kind: interview` / `kind: meeting`, weighs practitioner material up; `kind: exam` with `depth: awareness` weighs it down" |
| G1 | Design & Structure | **WARNING** (MEDIUM) | `skills/sources/SKILL.md:11-26` (`## Steps`) | The numbered procedure was not updated. Step 3 reads "With arguments (…): create the source(s)". `/sources --discover` is an invocation with an argument, and nothing in `## Steps` branches to `## Finding sources` or `## Goal fit`; a model following the procedure literally could try to register `--discover` as a source. Every gate (D1, E3) is satisfied because the sections exist further down; no gate reads the procedure | Add two lines to `## Steps`: "With `--discover` or a request to find material: see *Finding sources* — register nothing." and "Before writing any entry, if `goal.md` exists: see *Goal fit*." |
| F1 | Constitution XIV | **WARNING** | `git log afe2781..HEAD` (and the two commits below it) | Commit subjects on the branch are `wip: fleet phase 5/7/8 …`; `wip:` is not one of the eight permitted prefixes. Branch name itself is compliant | T049 already says "commit subjects use the repo prefixes" — squash or reword before opening the PR. Flagged so it is not forgotten; a PR opened with these subjects would be a XIV violation |
| I1 | Design & Structure | INFO | `scripts/check_docs.py` `GOAL_FIT_RULES`, `DISCOVERY_RULES`, `EXPLICIT_REQUEST_RULES`, `PRACTITIONER_ADDENDUM`, `ARCHIVE_REACH` | These search the raw skill body; only `EXPERIENCE_RULES` collapses whitespace — and the wave-F comment gives the reason ("a gate a reflow can break is a gate somebody satisfies by moving a line"). Literal-space patterns such as `until the user picks`, `which of the two`, `ordinary registration path` fail if a reflow puts a line break inside them. Fails loud, not silent — the safe direction | Collapse whitespace once in a shared helper for all five tables |
| I2 | Requirement Coverage | INFO | `scripts/check_project.py:47`, `docs/testing.md:200` (row 4g) | `VERDICT_KEYS` refuses exactly the five names the contract enumerates. Row 4g's own wording names "no `verdict:`, no score"; `verdict`, `score`, `rating` are not refused (`rating: 5` validates — verified). Consistent with `contracts/sources-yaml-unchanged.md` and the recorded "no timestamp is ungated" decision | Optional: widen the tuple; if not, keep row 4g as the holder |
| I3 | Spec Intent | INFO | `skills/catalog/SKILL.md` and `skills/cards/SKILL.md`, content (1) of the material-base warning | FR-013.1 asks that the material be "named as incident and experience reports only"; both prompts say "its documents named or counted, and that nothing covering the topic in general is among them". The surrounding paragraph ("all of whose references are documents like these") supplies it; the clause is implicit rather than stated | Add "named as incident write-ups" to item 1 in both prompts |
| I4 | Spec Intent | INFO | `docs/workflow.md:112`, `skills/sources/SKILL.md:48-51` | "Registering … and listing make no network request **whatsoever**" — registration still probes the local Zotero API (`curl localhost:23119`), pre-existing behaviour FR-033 accepts "as today". Localhost survives row 4r's offline re-run, so the row holds; the sentence slightly overstates | "no request beyond the local Zotero probe" or leave as is |
| I5 | Spec Intent (SC-011) | INFO | `docs/index.html:489` | The landing page's `/sources` is an `<h3>` label with no description, so it is not a "place that describes `/sources`". Recorded scoping decision (T043) | none |
| I6 | Task Completion | INFO | `tasks.md` T037, T038 | Both human checkpoints are ticked `[x]` although the task text says "do not tick from the prompt text". `/tmp/lk-demo` carries evidence of a real drive today: an eleventh source `tide-office-journal` (`type: web`, `depth: 1`, no verdict key) written 13:19, `torvig-radio-outage.md` with `nature: experience` at 12:54, `catalog/topics.md` and `cards/signals.yaml` at 12:55. No transcript is in the tree, so the ticks rest on that scratch state | Phase 13 (T050–T053) is the authoritative evidence; treat T037/T038 as "exercised, transcript not retained" |
| I7 | Structure | INFO | `docs/testing.md:271-279, 293, 337-340` | Row ids 18–23a are duplicated across three different tables. Pre-existing (13 duplicates before and after); this feature's 25 rows are unique | none for this feature |
| I8 | Format contract | INFO | `CLAUDE.md` § Knowledge store | Lists only `source`, `path`/`url`, `ingested`; `nature:` is not added — by the spec's explicit "CLAUDE.md untouched" rule, and consistent with `content:`/`visual:`/`figures:` not being listed there either | none |

## The eight adversarial points

1. **Code vs. checks.** Read all four prompt sections in full. `skills/sources/SKILL.md` § Goal fit states FR-001–FR-009 and FR-029 in a form a model can act on (advisory, written anyway, id + goal line, kind/depth with "which of the two", one `/learning-goal` pointer, no persistence, no re-assessment on listing, "registering fetches nothing, so … say so in the sentence"). § Finding sources states the neutral contract (six fields with the class as free prose, ≤ 3/area ≤ 10/run, every area listed, one sentence never a number, three exclusions, two degraded paths, ordinary path on pick, the `/research-gaps` seam, network only in discovery). `/ingest` states the marker, its single value, "absence is the other state", whole-document not per-paragraph. Two places where the prose would not produce conforming behaviour: **E1** (FR-005 conjunction) and **G1** (procedure not wired).
2. **FR-013's four contents.** Both `/catalog` (lines 154-176) and `/cards` (lines 130-152) demand all four as a numbered list, say "write it in your own words", name "a selected sample" as insufficient, and write content (2) out in full ("published by the parties who came through the incident and had an account they were willing to show; whoever it ended badly for publishes nothing … stay missing however much of it there is"). Content (3) is the survived/fail-for-good pair; content (4) the general account or reference work. Advisory, blocks nothing, never a suggestion to go looking. **Demanded, not merely named.** Only I3 (item 1's "named as incident reports") is implicit.
3. **FR-039 separability — run, not assumed.** Throwaway copy at `$TMPDIR/…/SKILL.md`; the real file untouched (working tree clean afterwards). Excised `### Practitioner material` up to `## Wrap-up` (21 lines), monkeypatched `read_skill("sources")` to the excised text, ran **all 21** `check_*` functions in `check_docs.py`. Result: **exactly one fails** — `check_sources_skill_carries_the_practitioner_addendum` with three FR-019 messages; the other 20 report nothing, including the four other readers of the file. Class-word scan (`practitioner`, `incident`, `post-mortem`, `postmortem`, `company blog`) over `DISCOVERY_RULES`, `EXPLICIT_REQUEST_RULES`, `GOAL_FIT_RULES`, `ARCHIVE_REACH`: none. The committed D5b test does the same against five checks and passes.
4. **FR-007's negative.** On a temp copy of the demo: each of `fit`, `assessed`, `goal_fit`, `discovered`, `proposed_by` on `field-notes` gives one error naming the id and the key; `frobnicate: yes` and `rating: 5` give **zero** errors; the shipped fixture with `login: true` on `harbour-office-members` validates (0 errors, 0 warnings). The check runs before the type branch, as the task required. Confirmed blacklist, not allowlist.
5. **The `nature:` guard.** `nature: anecdote` → `knowledge/field-notes/torvig-radio-outage.md: 'nature: anecdote' is not one of experience`; `nature: 1` (YAML int) → same shape, no crash; key removed → 0 errors, 0 warnings. Demo project with the key: clean. A card off the experience-only subtopic without `source:` → error naming file, card 8 and subtopic. Only one project exists on disk (`tests/fixtures/demo-project`; `broken/` holds single card files, `zotero/` a library) and it validates.
6. **Scope containment.** `git diff --name-only`: none of `docs/index.html`, `assets/brand/*`, the PNGs, `scripts/render_brand.py`, `tests/test_landing_page.py`, `.specify/memory/constitution.md`, `CLAUDE.md`, `docs/design.md`, `templates/*`, `scripts/build_pdf.py`, `bin/lernkarten` appears. Every line containing "seven" in `README.md`, `docs/workflow.md`, `CLAUDE.md`, the constitution, `docs/index.html`, `skills/learning-goal/SKILL.md` is byte-identical before and after. `--discover` occurs in exactly `skills/sources`, `skills/research-gaps` (the FR-034 seam), `README.md`, `docs/workflow.md`, `scripts/check_docs.py`, tests and specs — never in ingest/catalog/cards/print/learning-goal.
7. **The 25 rows.** All present at `docs/testing.md:194-213, 231, 243, 259-261`, each with its FR (or research R1 for 4j) inside the row; 4s sits between 4k and 4l as the plan says; 12-series contiguous. Every row gives a stimulus and an observable a tester can decide. Rows that could read as unfalsifiable say so themselves: 4a marks FR-009 circular, 4k marks the *found* count "read, not verified", 4n-i is opportunistic and forbids "pass". Row 5 was recounted: nine ingestible files under `raw/field-notes/` (empty.md and the PNG excluded) — correct. One caveat: row 4c is decidable only under the disjunctive FR-005 reading (E1).
8. **Ungated requirements.** Mapping every active FR to a check: FR-004 (row 4d only), FR-038 (row 12-vi only), FR-032 (is the row set), FR-040's "no filter ships" half (D8 gates the hook only), FR-007's "no timestamp" clause, and withdrawn FR-028. **Nothing else lost its gate**: FR-003/005/006/009 → C6–C9, FR-007 → A5/A6, FR-010–015 → F1–F3 + A1–A3 + B1–B3, FR-016–027 → D1, D1a–i, D2–D4, D8, FR-019 → D6, FR-029 → C4, FR-033 → D1i, FR-034 → G1–G3, FR-035/036 → E3, FR-037 → E1/E2/E2a/E4, FR-039 → D5/D5b. All 18 new test functions plus the parametrised cases exist in `tests/test_check_docs.py` and `tests/test_check_project.py`.

## Skill checks A–G

- **A Task completion**: 54/60 done. Open: T049 (PR) and T050–T054 (by-hand rows, gates.md walk) — by design, not findings. T037/T038 see I6.
- **B File existence**: every task-referenced file exists; `tests/fixtures/demo-project/raw/field-notes/torvig-radio-outage.md` and its `knowledge/` twin are new and present.
- **C Requirement coverage**: 39 active FRs; 36 with automated evidence, 3 manual-only by recorded decision. 100 % have an artifact.
- **D Scenario/test coverage**: all six user stories have automated cases or named rows; edge cases (no goal, no network, partial experience report, paginated archive, unknown class) are each stated in a prompt and held by a gate or a row.
- **E Spec intent**: one minor divergence (E1), one procedural gap (G1).
- **F Constitution**: I (format change carried through skill, script, checker, fixture, docs) ✓; V no new file under `scripts/` ✓; VI no new import edge ✓; VII fixture extended with invented material, not duplicated ✓ (PR note pending at T049); VIII no binary ✓; X `check_skills` green ✓; XI every check has a red case on synthetic text plus a shipped-file guard; D5b is the deliberate real-file case ✓; XII gates green per orchestrator ✓; XIII English ✓; XIV branch ✓, commit subjects ✗ (F1); XV–XVII untouched ✓.
- **G Design consistency**: eight `check_docs` functions as planned; `NATURES` beside `CONTENT_STATES`/`VISUAL_KINDS`; `VERDICT_KEYS` beside `SOURCE_TYPES`; experience set threaded down the `sparse` road with the "all, not any" rule; FR-011 as an error; card count 33 with the Tides-topic repair to the divider tests exactly as T033 licensed.

## Task summary

| Phase | Tasks | Status | Notes |
|---|---|---|---|
| Setup | T001–T004 | done | baseline recorded |
| G stale network claim | T005–T006 | done | gate + rewrite verified |
| A `nature:` / verdict keys | T007–T009 | done | A1–A6 pass; behaviour re-verified by hand |
| B attribution error | T010–T011 | done | B1–B4 pass; error text names file, card, subtopic |
| C goal fit | T012–T014 | done | C1–C9 pass; E1 wording drift |
| D discovery C1/C2 | T015–T019 | done | D1–D8, D5b pass; excision reproduced |
| E silence | T020–T021b | done | E1–E4 pass; token absent in five skills |
| F experience rule | T022–T026 | done | F1–F4 pass; FR-013 four contents demanded |
| H fixture | T027–T035 | done | 33 cards, one `nature:` doc, no `Term:` on new subtopic |
| I prompts driven | T036–T038 | ticked | I6: scratch evidence, no transcript |
| J docs | T039–T043 | done | 25 rows, workflow/README both jobs, scope clean |
| Gates | T044–T048 | done | T049 open (PR) |
| By hand | T050–T054 | open | human, by design |

## Metrics

- Tasks: **54 / 60** complete (6 open by design)
- Requirement coverage: **39 / 39** active FRs with an artifact; 36 / 39 with an automated gate
- Files verified: **19** changed files, all read; 2 scripts, 5 prompts, 3 docs, 5 fixture files, 3 test modules, tasks.md
- Findings: **0 CRITICAL · 3 WARNING · 8 INFO**

## Next actions

1. Fix **E1** — one sentence in `skills/sources/SKILL.md:74-76` (disjunctive FR-005); C7 stays green either way, so run row 4c afterwards to prove it.
2. Fix **G1** — two lines in `## Steps` of the same file so the procedure reaches `## Goal fit` and `## Finding sources`.
3. At **T049**, reword/squash the `wip:` commits (F1) and carry the constitution VII note in the PR description.
4. Then the human half: T050–T054. Rows 4c and 4k–4s are where the two WARNINGs would have surfaced.

Implementation verified against spec, plan, tasks and constitution — ready for the two prompt edits above and then review.

## Remediation — 2026-09-09

Both prompt findings are fixed in `skills/sources/SKILL.md`. No gate could see
either, which is the point: they are the class of defect the by-hand rows exist
to catch, and E1 would have been caught by row 4c.

- **E1 — FIXED.** The FR-005 sentence bound `depth` and `kind` with *with*,
  making it a conjunction, while `spec.md` and row 4c read them as weighing
  independently. Rewritten so each of `depth: expert`, `kind: interview` and
  `kind: meeting` weighs practitioner material up on its own, and each of
  `kind: exam` and `depth: awareness` weighs it down on its own, with an
  instruction to say which way the run came down when the two pull against
  each other. Row 4c is now decidable as written.
- **G1 — FIXED.** `## Steps` was never wired to the sections this feature
  added, so a run following the procedure literally could have read
  `--discover` as a path to register. A new step 3 catches `--discover` (and
  its natural-language equivalents) *before* the argument step and sends it to
  *Finding sources*; the argument step now points at *Goal fit*; and a closing
  sentence states that steps 2, 4 and 5 are ordinary runs that reach no network
  and neither enter discovery nor mention it (FR-033, FR-036).
- **F1 — deferred to T049 by design.** The three `wip: fleet phase …` subjects
  are checkpoint commits on the branch; T049 already instructs that the pull
  request carry a constitution XIV prefix.

Re-verified after the edits: `python3 scripts/check_docs.py` exit 0,
`pytest tests/test_check_docs.py tests/test_check_project.py` 85 passed,
`ruff check .` and `ruff format --check .` clean.

**Residual findings: 0 CRITICAL, 1 WARNING (F1, deferred to the pull request),
8 INFO.**
