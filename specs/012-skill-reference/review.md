# Pre-Implementation Review

**Feature**: Sphinx documentation foundation (012)
**Artifacts reviewed**: spec.md, plan.md, tasks.md, research.md, data-model.md,
contracts/docsite-layout.md, quickstart.md, checklists/requirements.md,
checklists/implementation-readiness.md
**Review model**: Claude Fable 5.1 (`claude-fable-5-1`)
**Generating model**: not recorded in the artifacts; a different model family
per the orchestrator's brief
**Method**: every claim that names a file, a line or a function was read in the
repository, not compared across the documents. Sphinx is not installed in this
checkout, so nothing research.md measured with it was re-measured; what *could*
be checked from here without Sphinx is listed at the end.

## Summary

| Dimension | Verdict | Issues |
|---|---|---|
| Spec-Plan Alignment | **FAIL** | red row 2 widens FR-005 from "any script a user's run reaches" to "anything under `scripts/`", which `scripts/build_docs.py` itself violates (C1); the landing page's existing GitHub link to `docs/workflow.md` sits outside FR-042's reasoning (W5) |
| Plan-Tasks Completeness | WARN | `assets/fonts/` is a build input missing from the `paths:` enumeration (W1); three tasks lack the exact strings their tests need (W6); doctrees have no stated home (O1) |
| Dependency Ordering | PASS | every stated constraint verified; both exceptions to the row order are argued and correct |
| Parallelization Correctness | PASS | all ten groups checked file by file; no same-file conflict; max three respected |
| Feasibility & Risk | **FAIL** | T041's workflow carries no `_site/docs` token, so T042's adapted test is red after T041 and a comment would satisfy it (C2); rows 7 and 10 write into the real `docsite/` (W3); T014's `python3` fails the Windows leg (W4) |
| Standards Compliance | PASS | constitution II, IV, V, VI, VIII, IX, XI, XVI all read against the file; guard reasoning has the precedent it cites |
| Implementation Readiness | WARN | row 16's test is vacuous on four of five clauses unless scoped to the job (W2); W6 |

**Overall**: **NOT READY** — two blockers, C1 and C2. Each is a one-sentence
fix in plan.md and tasks.md and neither reopens a decision; after them the
verdict is READY WITH WARNINGS. No re-planning is needed.

## Findings

### Critical (FAIL — must fix before implementing)

1. **Red row 2 cannot be the guard it is labelled, because `scripts/build_docs.py` imports a docs package.**
   *plan.md* § Test plan first, row 2; *tasks.md* T007.
   Row 2 asserts "nothing under `bin/` or `scripts/` imports one [of the three docs packages]" and is labelled a guard that is "green on the first run" and guards "against a *later* feature". T015, eight tasks later, writes `scripts/build_docs.py`, which the plan says imports `sphinx.cmd.build` and checks that `sphinx`, `myst_parser` and `pydata_sphinx_theme` are importable. Any grep or AST test over `scripts/*.py` goes red at T015. The implementer then has two choices, and the path of least resistance is the worse one: exclude `build_docs.py` by name (a name list, the shape the artifacts reject everywhere else) or re-scope. FR-005's own wording is narrower and correct: "any script a **user's run** reaches".
   **Fix**: scope row 2 to the import closure of `bin/lernkarten`. `bin/lernkarten` imports `engine`, `deps`, `cardid`, `setup_cmd` and `build_pdf` (lines 30–71); `check_docs.real_graph()` already derives each module's local imports; walk it from those five and assert no module in the closure imports a docs package. `build_docs` is outside the closure by construction (a leaf nothing imports), so the guard is green at T007, stays green through T015, and goes red only if a future feature makes a user-reachable module import Sphinx — which is exactly what FR-005 forbids. One sentence in plan row 2 and in T007.

2. **T041's rebuilt `pages.yml` carries no `_site/docs` token, so T042's adapted test stays red — and a comment would turn it green.**
   *plan.md* § `tests/test_landing_page.py` (FR-016); *tasks.md* T041, T042.
   The adaptation is `built = bool(re.search(r"_site/docs\b", workflow)) and ref.rstrip("/") == "docs"`, described as "derived from the workflow text, not allow-listed" and "verified against a draft workflow". The draft is not in the artifacts. T041's four steps are `checkout`, the unchanged `cp` block, `pip install -r requirements-docs.txt` then `python3 scripts/build_docs.py --site _site`, and the three Pages actions. None of that text contains `_site/docs`; the script writes `<site>/docs/` internally. An implementer following T041 and T042 verbatim ends Phase 7 with row 15 red, and the quickest green is `# builds into _site/docs` in a comment — at which point the "derivation" reads a token that proves nothing, which is the first failure family in its purest form.
   **Fix**: T041's build step ends with a post-condition — `python3 scripts/build_docs.py --site _site && test -f _site/docs/index.html`. That gives the workflow text an honest `_site/docs` (a check the deploy actually runs, not a declaration), strengthens FR-033 (a build that exits 0 but writes nothing still fails before upload), and the adapted regex then matches something that means what the test says it means. Say so in T041 and in the plan section.

### Warnings (WARN — recommend fixing, can proceed)

1. **`assets/fonts/` is an input to the documentation build and is not in the `paths:` enumeration.** *plan.md* § `pages.yml`; *tasks.md* Phase 7 note, T049, T051. FR-017 says the trigger "MUST cover every input to the documentation build". FR-027 and T046 make the build copy the three faces out of `assets/fonts/` via `html_static_path`. The eleven entries — reconciled three ways after the earlier "ten" — are consistent with each other and still incomplete: the count was checked, the enumeration was not checked against FR-027's inputs. A font swap would not redeploy. Add `assets/fonts/**`; the count becomes twelve in all four places. (Second failure family; the previous fix corrected the number and left the list.)

2. **Row 16's test passes four of its five clauses against today's `ci.yml` unless it is scoped to the job.** *tasks.md* T038. The clauses "runs on `ubuntu-latest`, `macos-latest` and `windows-latest`", "installs `requirements-dev.txt`" and "runs `pytest`" are all already true of `ci.yml` as text — the `cards` and `e2e` jobs list all three runners, and the `test` job runs `python -m pytest`. Only "installs `requirements-docs.txt`" and "runs `build_docs.py`" are red today. T050 already carries the right instruction for the same shape ("scoped to the first block"); T038 does not. **Fix**: load `ci.yml` with `yamlio` (pyyaml is in `requirements-dev.txt` and `tests/test_repo_hygiene.py` already imports `yamlio`), select the job whose steps run `build_docs.py`, and assert `strategy.matrix.os`, the job id, and the steps on that object. (First failure family — a five-clause test in which four clauses check nothing.)

3. **Rows 7 and 10 write a temporary page into the checked-in `docsite/`, and nothing else is possible because `build_docs.py` has only `--site`.** *tasks.md* T023, T030; *plan.md* § The build command. A test interrupted between writing `docsite/probe.md` and removing it leaves a file that makes the next `python3 scripts/build_docs.py` red, makes gate #4 red (FR-037 puts `docsite/**/*.md` inside `check_links`, and the probe's dead link is exactly what it reports), and trips row 25 if the probe copied anything. The quickstart does the same by hand and that is fine there. **Fix**: a `--source <dir>` option defaulting to `docsite/` (FR-019's "no arguments" is about the default, as `--site` already establishes); the two tests `shutil.copytree` `docsite/` into `tmp_path`, add the probe there, and build the copy. `conf.py`'s `sys.path` insert of `_ext` is relative to the conf directory, so a copied tree builds unchanged.

4. **T014 says to run `python3 scripts/build_docs.py` as a subprocess; on the Windows leg of `docs-build` — the only job where these tests execute — `python3` is not what the runner resolves.** `ci.yml`'s own comment on the `cards` job says so, and the plan's `python` vs `python3` paragraph guards the workflow against it but not the tests. `tests/test_e2e.py:71` already does it right: `[sys.executable, str(CLI), *args]`. Say `sys.executable` in T014, or every row 5–13 test fails on Windows for a reason unrelated to the feature.

5. **The landing page already links the raw `docs/workflow.md` on GitHub, and no artifact decides what happens to it.** `docs/index.html:769`: `<a class="button button--ghost" href="https://github.com/mhabedank/lernkarten/blob/main/docs/workflow.md">full walkthrough</a>`. FR-042 retargets the README's three links at the published pages because "leaving them would reintroduce the split one link deep"; after 012 the landing page — the page a newcomer reaches first — offers `docs/` into the site and, in the same install section, the raw Markdown of the page the site now publishes. Two decisions are needed and neither is written: (a) retarget it, or leave it and say why; (b) if it is retargeted to `docs/user/workflow.html`, it joins `landing_page_relative_refs()` and the adapted rule `ref.rstrip("/") == "docs"` rejects it. The spec's FR-016 "permitted" clause already says the second route is anything "produced by the documentation build into `_site/docs/`", so the adaptation should admit the subtree — `ref == "docs" or ref.startswith("docs/")` — rather than one literal. (Second failure family: "where the walkthrough lives" is now one truth in README, landing page and site.) This is also the natural place for T037's new link, which T037 does not locate.

6. **Three tasks omit the exact string their test has to match.** T045 does not give the three URLs (derivable from contract § 4 and FR-013: `https://mhabedank.github.io/lernkarten/docs/user/workflow.html`, `…/docs/contributing/design.html`, `…/docs/contributing/testing.html`) — and row 18's test, written without them, can only assert the *absence* of `](docs/workflow.md)`, which is a weak test. T048's new `docs/design.md` row links `docsite/` with an ellipsis for the target; it is `../docsite/`, a directory, so the transform emits `/tree/main/docsite` and `check_links` resolves it once the directory exists. T037 does not say where in the body the `docs/` link goes (see W5).

### Observations (informational)

1. **Doctrees have no stated home and will be deployed.** The plan runs Sphinx "into `_site/docs/`" with no `-d`; Sphinx then writes `.doctrees/` inside the output directory, and `upload-pages-artifact` publishes dot-directories because `.nojekyll` is set. `docsite/_build/` is gitignored by FR-022 but nothing in the plan writes there. `-d docsite/_build/doctrees` fixes both and gives the gitignore entry its reason. SC-004's exclusions are unaffected.

2. **Row 6 could assert content for one extra line.** It walks the toctree for five docnames. `CONTRIBUTING.md` is the one migrated document no transform test reads a link from, so an empty `docsite/contributing/guide.md` passes rows 6–11. Asserting that each toctree entry's title equals its source file's H1 (which the plan says is the mechanism) turns US1 scenario 2 — "its text is the text of the source file" — from unasserted into asserted.

3. **Windows path separators in the transform.** Contract § 6 step 1 builds `name` relative to the repository root and looks it up in `PAGES`/`SERVED`, whose keys are POSIX strings. `Path.relative_to` stringifies with backslashes on Windows. `.as_posix()` is one word in the contract; the three-OS `docs-build` job would catch its absence, which is what FR-034 is for, but a red Windows leg on the first CI run is avoidable.

4. **The three pins were verifiable after all.** `pip index versions` reached PyPI from this checkout: `sphinx` 9.0.4, `myst-parser` 5.1.0 and `pydata-sphinx-theme` 0.21.0 all exist and are the current releases. That closes the existence half of CHK041; the wheel matrix and everything measured with an installed Sphinx remain research.md's word, as the artifacts already say.

5. **Stale history in the readiness checklist.** CHK021 and CHK022 still say "20 rows" and "20 red-first, 4 guards" against the current 25/19/6. They are a dated revision record, so not wrong, but they are the second failure family inside the artifact written to catch it.

6. **Two second-family instances in the repository, outside 012's scope, worth a ticket**: `ruff==0.16.5` in `requirements-dev.txt` against `ruff==0.16.2` in `ci.yml:26`, `CONTRIBUTING.md:237` and constitution IV; and `docs/testing.md` has two rows numbered `23a` (lines 252 and 254). The second matters slightly to T053, whose numbering precedent is itself broken.

7. **This checkout runs Python 3.11.7**, below the project's 3.12 floor. T001–T004 (install and baseline) may not behave as written here; the environment, not the plan, is the issue.

## The two failure families — searched systematically

**Family 1, a test that is green without checking anything.** I took each of the 25 rows and asked what state of the repository *today* makes its assertion true. Rows 1, 3, 5–11, 15, 17–23 are red for the stated reason. Row 4 and row 13 were already fixed by earlier passes and the fixes hold. New instances: **row 16** (W2 — four of five clauses true today), **row 15's adaptation** (C2 — its second route can be satisfied by a comment), and **row 2** (C1 — the opposite defect: a guard that cannot stay green, whose likely repair is a name list). Rows 12, 14, 24, 25 are guards and honestly labelled.

**Family 2, one truth in several places.** Counts checked across plan, tasks, contract, quickstart and checklist: 25 rows / 19 red / 6 guards (consistent; stale only in the checklist's revision record), 66 tasks / 24 in groups / 10 groups (consistent — the orchestrator's brief said eleven; the file has and says ten), 11 `paths:` entries (consistent, and wrong — W1), five command lines / four gates (consistent), manual rows 44–46 against a checklist that reaches 43 (verified), the 31 / 22 / 9 / 2 / 20 link denominators (consistent with the checklist's verification), constitution 2.7.0 → 2.8.0 (verified, and the bump size matches the 2.6.0 → 2.7.0 precedent). Every `file:line` citation in plan.md and tasks.md was checked and is correct. New instance: **the walkthrough's location** (W5), now stated in README, landing page and site.

## The scope question

**The shape holds, and I would not split 012 again.** Two forcing functions make the parts inseparable, and the artifacts identify both correctly: `-W` turns the 27 unresolved links in the five included documents into build failures the moment they are included, so the transform is not optional once the migration is; and `check_import_graph()` fails CI the moment `scripts/build_docs.py` exists, so the constitution amendment is not optional once the build script is. The 66-task count is not 66 behaviours: it is roughly 25 behaviours doubled by the red/green discipline, plus fourteen process tasks (Phases 1, 11, 12) and three documentation tasks. That is a medium feature with an unusually explicit task list, not a large one.

The only clean seam is the theme — T044, T046, T047, T048, T063 and FR-027/FR-035/FR-036 — which could ship as a dark launch: site live at `/docs/`, unlinked from the landing page and README until the stylesheet lands. I would still not do it. The cost is a second PR and deploy cycle for about 130 lines of CSS whose inventory is already measured, and constitution XVI says a stock theme beside the landing page is a visible regression the moment it is public; a dark launch only hides that from readers who do not guess the URL. What *should* be resisted is anything being added to 012 — search, intersphinx, any 013 or 014 content — and the spec's Assumptions already draw that line.

## What was verified in the repository, and what could not be

**Verified**: `pages.yml`'s four `paths:` entries and three `cp` lines; `ci.yml`'s `docs:` job id and the `python`-under-`bash` convention; `pyproject.toml`'s ruff config with no `exclude`; `markdown_files()`'s three globs and the two direct callers at 577 and 598; `check_links`' file-system resolution and `http` skip; `real_graph()`'s derivation (a bare-name match against `scripts/*.py` stems, so `import sphinx` in `build_docs.py` is ignored by the graph check — but not by row 2 as written); `GRAPH_LINE` accepting the leaves form; `LEITNER_PAGE` read directly; `NAV_LINKS` and the four-link filter; `landing_page_relative_refs()` and both workflow tests; the `ignored()` helper; `test_the_readme_still_names_the_landing_page_source`; Principle V's four-file `docs/` row; Principle VI's block; the XI "ImportError" and spike clauses; the governance version precedent; `docs/design.md` § The screen surfaces with five rows; `docs/testing.md` reaching 43; the two rendered images and the `docs/index.html:769` link; `assets/fonts/` contents; `.github/dependabot.yml`; the three pins on PyPI.

**Not verifiable here**: everything research.md measured with an installed Sphinx — the post-transform priorities, the 33-distribution closure and its wheel matrix, the 131/78/33 stylesheet counts, the byte-identical rebuild, and that the stock theme loads no third-party sub-resource. T009 re-measures them at the right moment and the artifacts say so; I have no reason to doubt them and no way to confirm them.

## Recommended Actions

- [ ] **C1** — plan.md row 2 and tasks.md T007: scope the guard to the import closure of `bin/lernkarten` via `check_docs.real_graph()`; state that `build_docs` is outside it by construction.
- [ ] **C2** — tasks.md T041 and plan.md § `tests/test_landing_page.py`: the build step ends with `&& test -f _site/docs/index.html`, which is what the adapted regex reads.
- [ ] **W1** — add `assets/fonts/**` to the `paths:` enumeration in plan.md § `pages.yml`, the Phase 7 note, T049 and T051; eleven becomes twelve.
- [ ] **W2** — T038: parse `ci.yml` with `yamlio`, select the job by its `build_docs.py` step, assert on that job.
- [ ] **W3** — plan.md § The build command and T015: add `--source <dir>` defaulting to `docsite/`; T023 and T030 build a `copytree` of `docsite/` in `tmp_path`.
- [ ] **W4** — T014: `sys.executable`, not `python3`, in the subprocess call.
- [ ] **W5** — decide `docs/index.html:769` in spec FR-042 or FR-014; widen the FR-016 adaptation to `ref == "docs" or ref.startswith("docs/")` in plan.md and T042.
- [ ] **W6** — T045: the three URLs; T048: `../docsite/`; T037: the button row at `docs/index.html:767–770`.
- [ ] **O1** — T015: `-d docsite/_build/doctrees`.
- [ ] **O2** — T021: assert each toctree title equals its source H1.
- [ ] **O3** — contract § 6 step 1: `.as_posix()`.
