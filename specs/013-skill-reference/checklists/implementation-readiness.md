# Implementation Readiness Checklist: Sphinx documentation foundation

**Purpose**: Decide whether `plan.md` is ready to be turned into tasks and built
— not whether the requirements are well written, which is
[requirements.md](requirements.md)'s job and is already complete
**Created**: 2026-09-08
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [research.md](../research.md)
**Method**: every item below was checked against `plan.md`, `research.md`,
`contracts/docsite-layout.md`, `quickstart.md` **and the repository**. Where the
documents alone could not settle an item, the item says what would settle it.
An unchecked box is a finding, not an omission.
**Revision 2 (2026-09-08)**: the fifteen findings of revision 1 were all worked,
and each resolution is recorded inline under its item. Two — CHK015 and CHK041 —
were *converted* into stated ordering constraints rather than verified, because
they depend on Sphinx being installed, which it is not in this checkout. One,
CHK022, was closed by **this checklist's own suggestion being argued down**, with
three citations that the orchestrator verified. Six were verified by the
orchestrator directly rather than taken on report.

## Requirement coverage (all 42 FRs)

- [x] CHK001 Is every one of the 42 functional requirements addressed *somewhere* in the plan artifacts, by design rather than by mention? — thirty-six are cited by number in `plan.md`; six are not, and each was read individually rather than assumed. See CHK002–CHK004.
- [x] CHK002 Are the requirements `plan.md` never cites by number nevertheless designed for? [Coverage] — **FR-004** is answered verbatim by the vetting table (wheels, three platform tags, no compiler, `>=3.11` floor); **FR-013** by the *Project Structure* table plus § *`docs/index.html` (FR-014)*; **FR-021** by red row 12 and SC-004; **FR-026** by the constitution VII row. Uncited, not unaddressed.
- [x] CHK003 **FR-018 has no design and no assertion.** [Gap, Spec §FR-018] "The built site's internal links MUST be relative, so the site works under a sub-path and when opened from the filesystem" appears nowhere in `plan.md`, `research.md` or the contract. `html_baseurl` is never named. Sphinx's default *is* relative, so the requirement holds by accident of the default — but nothing states it and nothing would notice a later `conf.py` line that broke it. **What would settle it**: one `conf.py` decision recorded, plus one assertion (no `href="/…"` or `http(s)://…/lernkarten/` in `_site/docs`) folded into red row 13, which already walks the output for exactly this shape.

      **Resolved (2026-09-08, revision 2)**: new plan section *Relative internal links (FR-018)*: `html_baseurl` is left unset **deliberately**, with a `conf.py` comment naming FR-018, and the assertion (no `href="/…"`, no `mhabedank.github.io`) is folded into red row 13. Quickstart section 8 carries the grep.
- [x] CHK004 **FR-011 is carried only by "nothing changed".** [Coverage, Spec §FR-011] The Leitner interval gate and `tests/test_check_docs.py`'s path assertion survive because `LEITNER_PAGE` is untouched — verified in `scripts/check_docs.py:252`. But `plan.md` extends `markdown_files()` (FR-037) without stating that `check_leitner_intervals` does not read it, and manual row 51 scopes the reviewer to *diffs*, not to this gate. Low risk, worth one sentence in the FR-037 section.

      **Resolved (2026-09-08, revision 2)**: the FR-037 section now states that `check_leitner_intervals` reads `LEITNER_PAGE` directly and never goes through `markdown_files()`, so widening the glob cannot dilute it.
- [x] CHK005 Is FR-037's consequence for `check_docs.py` traced to the real function? [Consistency] — yes, and it is **more accurate in the contract than in the plan**: `plan.md` says "all five drift gates start reading them through `gated_files()`", but `check_sheet_capacity` (line 577) and `check_print_order` (line 597) call `markdown_files()` **directly**, and neither strips code blocks. The outcome is the same because a `docsite/` page is one `{include}`; the mechanism named is not. Note for implementation, not a blocker.
- [x] CHK006 Is the `{include}` design safe against the documents it will actually include? [Completeness] — checked by counting real H1s rather than trusting the claim: `docs/workflow.md`, `docs/design.md`, `docs/testing.md` and `CONTRIBUTING.md` each have **exactly one** `^# ` heading. The nine further `^# ` lines in `workflow.md` and one in `CONTRIBUTING.md` are shell comments inside fenced blocks. "The included document's own H1 becomes the page title" holds for all four.
- [x] CHK007 Are FR-031's four links real, at the paths the spec gives? [Traceability] — verified: `docs/design.md:336` (`index.html`), `docs/design.md:237` (`../assets/card-box.pdf`), `docs/workflow.md:31` (`../README.md#install`), `docs/workflow.md:252` and `CONTRIBUTING.md:178` (`CLAUDE.md`). The FR-029 "22 links" and the quickstart's "31" are different denominators (repository links vs. all relative links), which `research.md:106` states.
- [x] CHK008 Is the FR-012 headroom for 014 and 015 designed rather than asserted? [Completeness] — yes: a third and fourth `toctree` entry in `docsite/index.md`, plus `docsite/_ext/` and its purity test, named in the contract § 8.

## The four contradictions

- [x] CHK009 **C1** — is "do not hand-edit; put both links in `SERVED`" implementable? [Conflict, Plan §C1] Yes, and the reasoning was re-derived rather than trusted: `check_links` (`scripts/check_docs.py:175`) resolves a relative target against `path.parent` on the file system, so `../index.html` written into `docs/design.md` resolves to `<repo>/index.html`, which does not exist, and gate #4 goes red on that commit. Leaving the sources alone is the only resolution that keeps FR-024 and SC-011.
- [x] CHK010 **C1 leaves FR-031's own text incoherent, and nothing amends it.** [Conflict, Spec §FR-031] FR-031's opening sentence is "Four links … **MUST be retargeted by hand**". After C1 *none* of the four is retargeted by hand: two move into `SERVED` and two were already "via FR-029". The plan says "FR-031's table survives as the *enumeration*, only the mechanism moves", which is the right call — but the requirement still reads as an instruction to edit files, and its **Fix column is now wrong on two rows** (C2 makes the values `../../index.html` and `../../card-box.pdf`, and they are rendered output rather than source text). **What would settle it**: either a task that rewrites FR-031's lead sentence and Fix column to describe the transform's `SERVED` table, or an explicit note in the spec that FR-031 is superseded in mechanism by plan C1/C2. Left as-is, a later reader implements the hand-edit the requirement still asks for and breaks gate #4.

      **Resolved (2026-09-08, revision 2)**: `spec.md` FR-031 amended in place — the lead sentence now says all four are resolved at build time, the Fix column gives the rendered values, and the original wording plus the gate-#4 reason are quoted in an amendment note. Indexed under `### Amendments made during planning` (spec.md:77). **Verified by the orchestrator.**
- [x] CHK011 **C2** — is `"../" * (docname.count("/") + 1)` correct for the layout the plan actually ships? [Clarity, Plan §C2] Yes. `contributing/design` gives two `../`, reaching `_site/` from `_site/docs/contributing/`; the contract § 5 tabulates the same result. One line, and it is depth-derived rather than hard-coded, so a later third level costs nothing.
- [x] CHK012 **C3** — is the `refdomain == "doc"` branch stated precisely enough to build? [Clarity, Plan §C3] Yes: "targets absent from `env.all_docs`: put the suffix back, run the same lookup", plus the resolution order in contract § 6. It leaves FR-037's prescribed spelling (`[design.md](../docs/design.md)`) working in both directions, which is the point.
- [x] CHK014 **C4** — is the priority claim specific enough to implement? [Clarity, Plan §C4] Yes: `doctree-read` at `priority=100`, ahead of `DownloadFileCollector` at 500. See CHK015 for what cannot be re-verified here.
- [x] CHK015 **Every priority number in C3/C4 and R2 is a spike measurement that cannot be re-verified from this checkout.** [Assumption] `python3 -c "import sphinx"` fails in this worktree; `requirements-docs.txt` does not exist yet. So `SphinxPostTransform` at 5 vs. `MystReferenceResolver` at 9, `DownloadFileCollector` at 500, the 33-distribution closure, the 131 `border-radius` rules and the byte-identical rebuild are all trusted, not confirmed. They are recorded as measured in `research.md`, which is the right place for them. **What would settle it**: red row 1 lands `requirements-docs.txt`, then `pip install -r requirements-docs.txt` and re-run the R2 and R5 probes before row 8 is written. This is an ordering note for tasks, not a defect.

      **Resolved (2026-09-08, revision 2)**: **converted, not verified** — ordering constraint 2 in the red table: re-run the R2/R4/R5 probes once `requirements-docs.txt` lands and before row 8 is written. Unverifiable from this checkout by design, which is why it is a constraint rather than a claim.

## Success-criterion verifiability (all 14)

- [x] CHK015 Do SC-001, SC-002, SC-003, SC-004, SC-006, SC-011, SC-012 and SC-014 each have a named automated method? [Measurability] — yes: red rows 5/16, 6, 7, 12, 5, 8, 9 and 13 respectively, each with a quickstart command beside it.
- [x] CHK016 Do SC-005, SC-008 and SC-013 have manual rows, and are those rows numbered correctly? [Measurability] — yes. `docs/testing.md` runs to **43** today (the Leitner dividers, `docs/testing.md:281`), so 44/45/46 are the next three and no more, as FR-025 caps.
- [x] CHK017 Does SC-009 have a method? [Measurability] — quickstart § 6, plus red row 2 as the standing regression guard.
- [x] CHK018 **SC-007 states a target with no method.** [Gap, Spec §SC-007] "The deployed site serves `docs/index.html` at the root byte-identical to the repository copy, serves every relative link that page makes, and serves the documentation at `/docs/`, reachable from the landing page's `docs/` link in one click." Red row 15 checks the *workflow text*; the local preview checks everything except the `docs/` hop, and `research.md:245` concedes that hop is verifiable only over HTTP. Quickstart § 11 walks the deployed site — but § 11 is **not** one of the three numbered manual rows, so it is a suggestion no process requires. FR-025 caps the rows at three, which is why SC-007 has nowhere to go. **What would settle it**: either fold the deployed-site walk into row 52 (which already concerns "did it run on the PR" and is adjacent), or accept that SC-007 is verified by the same post-merge habit that already covers manual rows 33 and 34 and say so.

      **Resolved (2026-09-08, revision 2)**: SC-007 folded into manual row **46** rather than a fourth row, so FR-025's cap of three holds; rows 33 and 34 are the precedent for a post-merge deployed-site check. Quickstart section 11 is now labelled as row 52's script.
- [x] CHK019 **SC-010's second half has no method.** [Gap, Spec §SC-010] "The four pre-PR gates stay green" is decided by running them (quickstart § 5). "**and the pre-PR checklist has the same number of commands as before**" is not: no test reads `CONTRIBUTING.md` § *Before the pull request*, and the three new manual rows do not cover it. Grepped `tests/` — nothing asserts a gate count. **What would settle it**: one line in the existing `tests/test_repo_hygiene.py` asserting the command block still holds the same five lines. Cheap, and it is the only guard against FR-024's "no fifth gate" being quietly broken by a future feature.

      **Resolved (2026-09-08, revision 2)**: red row **24** in `tests/test_repo_hygiene.py` — the first fenced block under `CONTRIBUTING.md` section *Before the pull request* still holds exactly five command lines, scoped to the first block because the section carries a second one that is not a gate.
- [x] CHK020 Is the "four gates / five commands" wording consistent enough not to mislead the edit? [Clarity] — worth naming: `CONTRIBUTING.md:42–48` lists **five command lines** for what the project calls four gates (ruff twice). `plan.md` and `quickstart.md` both say "the same four commands". Nobody is wrong; a task that edits that block should not "fix" the count.

## Red-first order (constitution XI — non-waivable)

- [x] CHK021 Does the Phase 1 table name a failing assertion for each of the 20 rows, with the file that turns it green? [Completeness, Plan §Test plan first] — yes, and rows are ordered so each red precedes its implementation.
- [x] CHK022 **Three rows are green from the moment they are written, and the plan says so.** [Conflict, Constitution XI] Rows **2** (`test_the_docs_requirements_are_not_a_runtime_dependency`), **12** (`test_building_twice_is_byte_identical`) and **14** (`test_the_extension_imports_nothing_from_lernkarten`) are marked "(green by construction)". Constitution XI asks for red **on the assertion**, and it is not waivable — the plan's own Complexity Tracking says "Principle XI has no row here." Row 2 and row 14 are honest regression guards with no behaviour to satisfy, which is the established shape in this repository. Row 12 is different: it cannot even be collected before `scripts/build_docs.py` exists, so its first run is an *error*, not a red assertion. **What would settle it**: state in tasks that rows 2/12/14 are guards, not red-first cases, and that XI is satisfied by rows 1 and 3–20 — or make row 12 red first by asserting determinism against a deliberately non-deterministic first build.

      **Resolved (2026-09-08, revision 2)**: resolved, and **this checklist's own suggestion was argued down with evidence**. Making row 12 red would mean writing a deliberately non-deterministic build and then removing it — a spike promoted to a pull request, which constitution XI forbids (`constitution.md:423`) — and its first run would be an error, which XI refuses to count as red (`constitution.md:382`). The never-red guard has a documented precedent in this repository (`tests/test_landing_page.py:474`). All three citations **verified by the orchestrator**. New plan section *Guards, and how XI is satisfied*: 20 red-first rows, 4 guards (2, 12, 14, 24), each labelled.

      **Superseded (2026-09-09, revision 3)**: the 20/4 split above is a dated
      record and no longer the count. Analysis reclassified row 13 as a guard
      (it passes with zero fonts installed) and added guard row 25 for FR-028's
      two named prohibitions; the split is now **19 red-first, 6 guards** —
      rows 2, 12, 13, 14, 24, 25. The reasoning recorded here for row 12 is
      unchanged and still governs.
- [x] CHK023 **Rows 5–13 skip rather than fail without the docs requirements.** [Ambiguity, Spec §FR-023] FR-023 requires exactly that skip, and SC-006 asserts it. The consequence for XI is unstated: a contributor who writes rows 5–13 before installing `requirements-docs.txt` sees **skipped**, not red, and has not seen the red XI demands. **What would settle it**: one line in the task list — install `requirements-docs.txt` before writing rows 5–13, so the red is real.

      **Resolved (2026-09-08, revision 2)**: ordering constraint 1 in the red table — install `requirements-docs.txt` before writing rows 5-13, or the red is a skip rather than a failure.
- [x] CHK024 **The theme has no failing assertion at all.** [Gap, Spec §FR-027] FR-027's three obligations — the three inks, the three faces, every radius/shadow/gradient flattened — reach the red table only through row 13, which greps for third-party sub-resources and would pass with an unmodified theme plus a local `@font-face`. `docsite/_static/lernkarten.css` is therefore written **green-first**, and the ~90–130 lines the plan sizes are covered only by manual row 50 (which is a *rendering* judgement, not a "did the override land" check). **What would settle it**: one cheap assertion that costs nothing and is not a selector list — the built `_static/lernkarten.css` sets `--pst-font-family-base`, `--bs-font-sans-serif` and `--bs-font-monospace`, and contains the blanket `border-radius: 0` rule. The plan's own measurement (overriding the three `--pst-` variables alone does **not** change body text; five are needed) is exactly the kind of thing that regresses silently.

      **Resolved (2026-09-08, revision 2)**: red row **21** — the built `_static/lernkarten.css` sets `--pst-font-family-base`, `--bs-font-sans-serif` and `--bs-font-monospace` and carries the blanket `border-radius: 0` / `box-shadow: none` rule. Three variable names and one rule, not a selector list. **Verified by the orchestrator.**
- [x] CHK025 **FR-017's `paths:` trigger has no assertion.** [Gap, Spec §FR-017] `plan.md` enumerates seven new `paths:` entries. Nothing asserts them. `tests/test_landing_page.py:539` already asserts `assets/card-box.pdf` is in `paths:`, so the pattern exists and is one line per entry. Without it, a `docsite/**` entry dropped in a later edit means the site silently stops redeploying — the same class of failure PR #105 fixed.

      **Resolved (2026-09-08, revision 2)**: red row **22** — all ten `paths:` entries, one assertion each, following the pattern at `tests/test_landing_page.py:539`. **Verified by the orchestrator.**
- [x] CHK026 **FR-039's Principle V half has no red artifact.** [Gap, Spec §FR-039] Row 20 covers Principle **VI** — verified: `check_import_graph()` (`scripts/check_docs.py:371`) derives modules from `scripts/*.py` and errors for any not in the fenced block, and `GRAPH_LINE` accepts `build_docs, deps, engine, leitner ← leaves, import nothing local`. The Principle **V** half — a `docsite/` row, and `leitner.html` added to the `docs/` row (currently `.specify/memory/constitution.md:240`, four files) — is enforced by nothing, which FR-039 itself gives as the reason it would be skipped. **What would settle it**: a one-line assertion that Principle V's table names `docsite/` and `leitner.html`, or an explicit acceptance that it rides on review.

      **Resolved (2026-09-08, revision 2)**: red row **23** — Principle V's table has a `docsite/` row and its `docs/` row names `leitner.html`. **Verified by the orchestrator.**
- [x] CHK027 Is the FR-016 adaptation red-first and derivation-preserving? [Consistency, Spec §FR-016] — yes for the mechanism. Verified `landing_page_relative_refs()` (`tests/test_landing_page.py:546`): the current derived set from `docs/index.html` is exactly `{card-box.pdf, leitner.html}` plus the `data:` URL it excludes, so FR-014's `docs/` makes three, and the plan's `built = re.search(r"_site/docs\b", workflow) and ref.rstrip("/") == "docs"` admits only that one. No target leaves the set. See CHK029 for what this collides with.
- [x] CHK028 Are the three manual rows each justified by "no test can reach this"? [Measurability, Plan §The three manual rows] — yes, and row 50's justification is checkable: `test_reading_text_is_never_below_the_screen_floor` reads one hand-written file's `<style>` blocks and cannot reach a compiled stylesheet.

## The four gates, and the workflows

- [x] CHK029 **`pages.yml` is specified two incompatible ways, and one of them turns two existing tests red.** [Conflict, Plan §pages.yml vs. §test_landing_page.py vs. contract §7] `plan.md` § *`.github/workflows/pages.yml`* describes the rebuilt job as three steps: install, `python3 scripts/build_docs.py --site _site`, upload — **no `cp` lines**. The contract § 7 reinforces this ("Identical locally and on GitHub Pages"). But `plan.md` § *`tests/test_landing_page.py`* says "`card-box.pdf` and `leitner.html` still match only through their **`cp` lines**", and the repository confirms why that is necessary: `test_the_pages_workflow_assembles_every_relative_link` (line 562) requires a literal `^\s*cp\s+\S*<ref>\s+\S*_site/` in `pages.yml` for **every** derived ref, and `test_the_pages_workflow_publishes_the_box` (line 529) requires `cp …assets/card-box.pdf …_site/` specifically. **`test_the_pages_workflow_publishes_the_box` is named in no plan artifact.** A task-writer following the § *pages.yml* text drops the `cp` lines and goes red on two existing tests that SC-005 forbids weakening. **What would settle it**: state the decision — `pages.yml` keeps the three `cp` lines *and* `build_docs.py` performs the same copies (idempotent, and the duplication is what keeps the local preview identical to the deploy), or `--site` narrows to writing only `_site/docs/`. This is the one item that should be resolved before tasks are generated.

      **Resolved (2026-09-08, revision 2)**: resolved by a single authoritative plan section, *The `_site` assembly, stated once*, which every other section now points at. Decision: `pages.yml` keeps all three `cp` lines **and** `build_docs.py` performs the same copies — the `cp` lines are what the two tests read as text (CI never executes the workflow), the script's copies are what make the local build a preview. `test_the_pages_workflow_publishes_the_box` is now named and explicitly stated as untouched. A `--docs-only` flag was rejected as a second assembly path free to drift. **The orchestrator verified that all three plan sections and contract section 7 now agree.**
- [x] CHK030 **The `docs-build` CI job as designed does not run the tests FR-023 asks for.** [Gap, Spec §FR-023] FR-023: "CI MUST have a job that installs them and **runs those tests**." `plan.md` § *ci.yml* specifies the job as "installing `requirements-docs.txt` and running `python3 scripts/build_docs.py`". `quickstart.md` § 9 says the same job "does steps 1 **and 5**", where step 5 is the four gates including `pytest`. Red row 16 asserts the job exists, is not named `docs`, and runs on three OSes — not that it runs `pytest`. As written, rows 5–13 skip in every CI job and execute nowhere. **What would settle it**: add `pytest` to the `docs-build` job and extend row 16 to assert it.

      **Resolved (2026-09-08, revision 2)**: the `docs-build` job now runs three commands — `pip install -r requirements-dev.txt -r requirements-docs.txt`, then `build_docs.py`, then `python -m pytest`. The whole suite rather than the docs module, because it is the only leg exercising the transform, `{include}` resolution and text encoding on macOS. Red row 16 asserts both commands. **Verified by the orchestrator.**
- [x] CHK031 Is the `docs` job-id collision real and correctly avoided? [Consistency, Spec §FR-023] — verified: `.github/workflows/ci.yml:148` is `docs:` / "Skills & docs". `docs-build` is free.
- [x] CHK032 Does the plan account for ruff's widened scope with a measurement rather than a hope? [Completeness, Spec §FR-024] — yes. `pyproject.toml:19–24` declares `line-length = 100`, `target-version = "py312"`, `select = ["E","F","W","I","UP","B","C4","SIM"]` and **no `exclude`**, exactly as the plan states, so `docsite/conf.py` and `docsite/_ext/*.py` are inside gate #1 from their first commit. The plan's response — hand-write `conf.py` rather than copy the Sphinx template — is the right one. (`docsite/_build/` is covered by ruff's own default exclude list; `_site/` is not, but holds no Python.)
- [x] CHK033 Does the plan account for the constitution amendment `check_import_graph()` forces? [Completeness, Spec §FR-039] — yes, as red row 20, and correctly as a **gate** rather than a pytest case. Confirmed against `real_graph()`/`documented_graph()`: `build_docs.py` existing without a Principle VI line fails the *Skills & docs* job.
- [x] CHK034 Does the plan keep the gate count at four? [Consistency, Spec §FR-024] — yes: the docs build is a CI job and a local convenience, never a pre-PR command. `quickstart.md` § 5 runs the same block that is in `CONTRIBUTING.md` today.
- [x] CHK035 Is gate #4 (`check_docs.py`) safe under the FR-037 widening? [Consistency] — yes, subject to CHK005's correction. `check_links` strips fenced blocks via `CODEBLOCK` before reading targets, so a page whose whole body is a fenced `{include}` contributes no links; the drift gates read the raw text, and an include-only page carries no grid or capacity claim. The contract § 3 binds every future `docsite/` page to `.md`-suffixed relative targets, which is what keeps this true for 014.
- [x] CHK036 Does the plan account for gate #2 (`pytest`) staying installable without the docs tree? [Consistency, Spec §FR-002] — yes: a third manifest, `requirements-dev.txt` untouched, SC-006 asserting the suite passes with none of the 33 present.
- [x] CHK037 Does the plan account for gate #3 (`lernkarten check`)? [Consistency, Spec §FR-005] — yes: FR-003/FR-005 keep the tree out of `scripts/deps.py`, red row 2 guards it, SC-009 asserts it.

## Dependencies, assumptions and residual risk

- [x] CHK038 Is the Principle IV vetting table complete, with the failing gate stated rather than rounded down? [Completeness, Constitution IV] — yes. Thirty-three distributions is over Principle IV's "thirty packages to get one function" shape, and the plan says so and gives three structural mitigations instead of arguing the number away. `requests` is named before a reviewer can find it.
- [x] CHK039 Is the Dependabot claim true without an edit? [Assumption] — verified: `.github/dependabot.yml` declares `package-ecosystem: pip, directory: "/"`, which picks up a new root-level `requirements-docs.txt`.
- [x] CHK040 Is the "no new binary" claim true? [Consistency, Constitution VIII] — yes. `assets/fonts/` already holds `Archivo.ttf`, `Jost.ttf` and `IBMPlexMono-Regular.ttf` (plus `Archivo-Italic.ttf`), all named in Principle VIII and asserted by `test_every_committed_binary_under_assets_is_named_in_principle_viii`. The build **copies**; `woff2` conversion was rejected for exactly this reason (research R4).
- [x] CHK041 **The three version pins cannot be checked from this checkout.** [Assumption] `sphinx==9.0.4`, `myst-parser==5.1.0`, `pydata-sphinx-theme==0.21.0` were resolved during a networked spike; nothing in the repository records or re-verifies them, and no lock or hash is introduced (deliberately — the constitution's one open Reconciliation item). **What would settle it**: the first green `docs-build` run on all three OSes, which is also the first time the wheel matrix is exercised outside the spike.

      **Resolved (2026-09-08, revision 2)**: **converted, not verified** — the three pins are exercised for the first time by a green `docs-build` on all three operating systems; recorded as an ordering constraint rather than as a checked claim.
- [x] CHK042 **FR-029's ~30-line ceiling is reinterpreted rather than met, and the reinterpretation is asserted rather than agreed.** [Ambiguity, Spec §FR-029] FR-029's fallback clause is unconditional: "if the transform needs more than roughly 30 lines, it is abandoned in favour of hard-coded absolute GitHub URLs … recorded as an accepted cost in `plan.md`". The shipped module is **~42 lines**; the plan reads the ceiling as measuring only the FR-029 portion (~22 lines) and charges C3 and C4 to a budget the ceiling "was not measuring". That reading is defensible — C3 and C4 are failures the spec did not know about, and taking the fallback would *lose* `check_docs` coverage, which SC-005 forbids — but it is the plan overruling a requirement's own escape hatch, and it is recorded as a Phase 0 finding rather than as an accepted deviation. **What would settle it**: one sentence in the spec or the plan saying FR-029's ceiling is superseded, with that reason. It costs nothing and stops the question being reopened at review.

      **Resolved (2026-09-08, revision 2)**: `spec.md` FR-029 amended — the ceiling is recorded as **superseded**, with the reason (the lookup itself measures ~22 lines and is inside it; the extra ~20 are C3 and C4, which the fallback would not fix while costing 22 links of `check_docs` coverage that SC-005 protects). Indexed under `### Amendments made during planning`. **Verified by the orchestrator.**
- [x] CHK043 Is the theme work sized against something real? [Measurability, Plan §The theme work] — yes, and unusually well: 131 `border-radius` rules, 78 `box-shadow`, 33 sub-16 px `font-size` rules sorted into "must raise" (~8 + 2 variables), "exempt" and "never emitted", and the measured gotcha that the three `--pst-` font variables do not reach `body`. The two residual judgements are correctly pushed onto manual row 50 rather than pretended into a test. Not re-verifiable here (CHK015).
- [x] CHK044 Is the one surviving risk named? [Completeness] — yes: a theme upgrade that styles a new component escapes the font floor but not the blanket flattening; the exact pin makes it arrive only on a deliberate bump, which is when row 50 is walked again.

## Notes

**Verdict: not blocked, but one item should be settled before `/speckit-tasks`.**
`plan.md` is unusually thorough — the four contradictions are real, measured and
resolved, the theme is sized against a compiled stylesheet rather than estimated,
and the red-first table is more complete than most. Twenty-nine of the
forty-four items here are checked because they are true, not because checking was
the job; the other fifteen are findings.

**The one that should block**: **CHK029**. `plan.md` specifies `pages.yml` two
incompatible ways in two sections, `contracts/docsite-layout.md` § 7 agrees with
the wrong one, and `test_the_pages_workflow_publishes_the_box` — which hard-codes
a `cp assets/card-box.pdf … _site/` requirement — appears in no plan artifact.
Following § *pages.yml* literally turns two existing tests red, and the obvious
repair is to weaken them, which is exactly what SC-005 and FR-016 forbid. One
sentence resolves it.

**Three that are cheap now and expensive later**, all of the same shape — a
requirement with no failing assertion, so nothing notices when it regresses:
**CHK024** (the theme override), **CHK025** (`paths:`), **CHK030** (the CI job
does not run the docs tests it exists for). CHK030 is the sharpest: as designed,
red rows 5–13 execute in no CI job at all.

**Two the spec, not the plan, should close**: **CHK010** (FR-031 still instructs
a hand-edit that C1 forbids, and its Fix column is wrong on two rows) and
**CHK042** (FR-029's 30-line ceiling is overruled without being recorded as a
deviation). Both are documentation debt that a later reader implements as
instructions.

**Two gaps with no home under FR-025's three-row cap**: **CHK018** (SC-007, the
deployed site) and **CHK019** (SC-010's "same number of commands"). The cap is
right — it is what stops a manual checklist becoming a place to hide unassertable
claims — so these need either a cheap test (CHK019 is one line in
`tests/test_repo_hygiene.py`) or an explicit statement that they ride on the
same post-merge habit that already carries manual rows 33 and 34.

**What could not be verified from this checkout, and is trusted rather than
confirmed**: every number that came out of the Phase 0 spike. Sphinx is not
installed here and `requirements-docs.txt` does not exist yet, so the transform
priorities (5, 9, 100, 500), the 33-distribution closure, the three version pins,
the 131/78/33 stylesheet counts and the byte-identical rebuild are `research.md`'s
word. That is the correct place for them; the note exists so the first task after
`requirements-docs.txt` lands is to re-run those probes, not to assume them
(CHK015, CHK041).

**What was verified in the repository rather than read**: the ruff configuration
and its absent `exclude`; the `docs:` job id collision; `check_links`'s
file-system resolution and its code-block stripping; `markdown_files()`'s three
globs and its four callers; `check_import_graph()`'s derivation and `GRAPH_LINE`'s
grammar; `landing_page_relative_refs()`'s current derived set; both `pages.yml`
tests; `docs/testing.md` reaching 43; the four migrated documents having exactly
one H1 each (nine of `workflow.md`'s ten `^# ` lines are shell comments); all four
FR-031 links at the lines the spec gives; the vendored fonts; and the Dependabot
declaration.
