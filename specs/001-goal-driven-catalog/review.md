# Pre-Implementation Review — Round 2

**Feature**: Goal-driven catalog (`specs/001-goal-driven-catalog/`)
**Artifacts reviewed**: current spec.md, plan.md, tasks.md, data-model.md, contracts/ (3), quickstart.md, `.specify/memory/constitution.md`, plus the live tree (`scripts/check_project.py`, `sources.example.yaml`, `.claude-plugin/*.json`) to re-verify claims
**Review model**: Claude Fable 5 (same model as round 1, fresh context)
**Scope**: verify the round-1 fixes landed, hunt for damage from the fix pass, and give data-model.md / contracts/ / quickstart.md the hard read they had not yet had

## Round 1 (summary, closed)

Round 1 found 3 FAIL (five parallel groups marking same-file edits to `tests/test_check_project.py` as concurrent; T014 [P] colliding with T013; an unmarked same-file task inside group 10) and 7 WARN (T051 interim breakage, T052's inverted red rationale, FR-016 uncovered, plan Wave G taskless, T035 missing the second hard-coded 31, C-6 vs the backwards-compat claim, plugin.json unbumped). All ten were addressed by the fix pass; every fix was re-verified against the current text below. Round 1's positive findings (T114 amendment judged pragmatic, T019 refactor exemption legitimate, line references accurate, test-first ordering genuine) stand unchanged.

## Round-1 item verification

| # | Item | Fix real? |
|---|------|-----------|
| F1 | Groups 4–9 same-file [P] | **PASS** — T022–T024/T025, T036–T038, T052–T053, T059–T061, T062–T063 all sit under `<!-- sequential -->`; only groups 1, 2, 10, 11 carry `parallel-group` markers; the Format section now defines [P] as ordering-independence and says "fan out on the group markers, never on [P] alone". Residual: see N1, N6 |
| F2 | T014 [P] vs T013 | **PASS** — [P] removed; the task explains the history and the T013-first ordering explicitly |
| F3 | Group 10 unmarked same-file task | **PASS** — group 10 is now T076/T077/T073 (CLAUDE.md, docs/testing.md, README.md — genuinely three distinct files, no other task writes them); T074/T075 sit under an explicit `<!-- sequential — same file -->` marker; the group comment is now accurate |
| W1 | T051 breaks suite interim | **PASS** — T051 opens with "Do this after T054, not before" and names the exact failing test and reason; the T052/T053 red checkpoint does not need the fixture, so the phase stays coherent |
| W2 | T052 accidentally green | **PASS** — T052 now demands asserting the missing-`gap` message text and states why a bare `assert report.errors` proves nothing |
| W3 | FR-016 uncovered | **PASS** (task) — T117 exists in Phase 12 and correctly identifies itself as the fourth console-only check. **Half-applied**: the recommended quickstart §4 row was not added — see N4 |
| W4 | Wave G taskless | **PASS** (task exists) — T118 added in Phase 12. But the task as written has fresh problems — see N2 |
| W5 | T035 second count | **PASS** — T035 names both `tests/test_e2e.py:25` and `tests/test_check_project.py:108`, both verified still reading 31 |
| W6 | C-6 vs compat claim | **PASS** — spec.md lines 635–642 now carve out C-6 as the one deliberate exception, scoping the claim to "every *well-formed* artifact" and naming the one-line fix |
| W7 | plugin.json version | **PASS** — T092 bumps both `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json`; verified both currently read `0.2.0` |

**Task-ID audit**: `grep -oE '^- \[.\] T[0-9]{3}' tasks.md` yields exactly 118 lines, T001–T118, no duplicate, no gap. The out-of-sequence placements are all deliberate insertions in sensible positions: T116 in Phase 7 (its subject), T114 between T090 and T091 (T091 explicitly covers T089/T090/T114), T117/T118/T115 in Phase 12. The group-10 rebuild lost nothing and duplicated nothing; phase ordering is intact.

## Round-2 verdict

| Dimension | Verdict | Issues |
|-----------|---------|--------|
| Spec-Plan Alignment | **PASS** | C-6 carve-out (W6) closed the one contradiction; nothing new |
| Plan-Tasks Completeness | **PASS** | All four round-1 gaps closed by T035/T092/T117/T118; only the quickstart §4 rows lag (N4, minor) |
| Dependency Ordering | **WARN** | T118 sits after the gates (T097/T100/T101) and the PR push (T104) that its output would invalidate (N2) |
| Parallelization Correctness | **PASS** | Groups 1, 2, 10, 11 verified file-disjoint against the tree; markers correct; but the stale "Parallel opportunities" lines are the exact residue of round 1's bug (N1) |
| Feasibility & Risk | **WARN** | T118's literal reading collides with constitution VII and the hard-coded counts (N2); FR-036's matching rule is undefined and the contracts' own examples contradict exact matching (N3) |
| Standards Compliance | **PASS** | Unchanged from round 1; cosmetic plan/checklist staleness remains, informational only |
| Implementation Readiness | **PASS** | The fixes were applied precisely, with reasons inlined where future editors need them — T051, T052 and T084 are model examples of self-defending tasks |

**Overall**: **READY.** No FAIL remains. The two WARNs are one task's wording (T118) and one underspecified matching rule (FR-036) — both fixable in minutes and neither blocks starting Phase 1. The findings below are complete; nothing was withheld to soften the verdict, and nothing was added to pad it.

## New findings (round 2)

1. **N1 (WARN)** — tasks.md "Parallel opportunities" (lines 405–406) still lists "T022–T025 … — parallel" and "T059–T063 … — parallel", the very same-file `tests/test_check_project.py` sets the fix pass just demoted to sequential; the Format preamble's "fan out on the group markers, never on [P] alone" governs, but an orchestrator scanning that section by title could reintroduce round 1's FAIL — delete or reword the two lines ("independent, any order — but same file, do not fan out").
2. **N2 (WARN)** — T118 (tasks.md line 366) tells the implementer to regenerate `tests/fixtures/demo-project` by running the four skills *against it* in Phase 12, i.e. after `pytest`/`--strict`/e2e gates (T097/T100/T101) and the PR push (T104): committed regenerated card output would break both hard-coded 31-counts (`tests/test_e2e.py:25`, `tests/test_check_project.py:108`) with no stated loop back through Phase 11, and a real `/research-gaps` run would write retrieved third-party web text into a fixture that constitution VII and the repo rules require to be invented content — reword T118 to run the skills against a *scratch copy* of the fixture as evidence, reconciling (not verbatim-committing) any divergence, and to re-run Phase 11 if the fixture changes.
3. **N3 (WARN)** — FR-036 (spec.md:564) / T026 / goal-md.md rule "every required topic appears in `catalog/topics.md`" never defines *appears*, and the contracts' own examples break exact matching: the goal bullet "What low-code is, and where the boundary to no-code runs" (contracts/goal-md.md:25) maps to catalog subtopic "What low-code is" (contracts/catalog-topics-md.md:20), so an exact-name check warns falsely on the contract's own example pair — either state the matching rule (e.g. goal bullets are short names, prose goes elsewhere) or fix the goal-md example to use heading-matchable names.
4. **N4 (minor)** — quickstart.md §4 has no row for the `/catalog` closing report (T117/FR-016) or the additive re-run (T115/FR-007), and T077 copies §4's rows into `docs/testing.md`, so both omissions propagate to the shipped checklist — add the two rows.
5. **N5 (minor)** — the `Also covers:` line format carries a parenthetical ("Also covers: Access control (cards in cards/security.yaml)", contracts/catalog-topics-md.md:18) that C-4's name comparison (T066) must strip, but no rule says so — one sentence in the contract's "The new lines" table would prevent a naive exact-match implementation from erroring on the contract's own example.
6. **N6 (minor)** — tasks.md's "Not parallel" list still lacks `tests/test_check_project.py` (round 1 recommended adding it); the Format preamble now covers the hazard, so this is belt-and-braces only.

## Recommended actions (all optional before starting; N1–N3 worth doing)

- [ ] N1: reword or delete the two stale "Parallel opportunities" lines (T022–T025, T059–T063)
- [ ] N2: reword T118 — scratch copy, reconcile not verbatim-commit, re-run Phase 11 on fixture change
- [ ] N3: define FR-036's matching rule, or make the goal-md.md example bullets heading-matchable
- [ ] N4: add the T117 and T115 rows to quickstart §4
- [ ] N5: note the parenthetical-stripping rule for `Also covers:` in the catalog contract
- [ ] N6: add `tests/test_check_project.py` to the "Not parallel" list
