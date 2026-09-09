# Tasks: Sphinx documentation foundation

**Input**: design documents in `/specs/012-skill-reference/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[contracts/docsite-layout.md](contracts/docsite-layout.md), [quickstart.md](quickstart.md),
[checklists/implementation-readiness.md](checklists/implementation-readiness.md)

**Tests**: test-first is mandatory and not waivable (constitution XI). Every
behaviour below gets a failing assertion before the code that satisfies it, and
"fails with ImportError" does not count as red (`constitution.md:382`).

## How to read this file

**The order is `plan.md`'s, not a new one.** Plan section *Test plan first
(constitution XI) — the red order* fixes 25 numbered rows; every task below cites
the row it serves as **row N**, and the rows appear in ascending order with two
stated exceptions, each argued where it happens: rows **20 and 23** are pulled
forward into Phase 4 (the constitution amendment has to land in the same commit
as `scripts/build_docs.py`, or CI is red in between), and Phase 8 runs
**18, 21, 19** (three mutually independent rows, ordered so the fan-out is real).

- 🔴 marks a task whose output must be a **failing test**, failing on its
  assertion, before the next task starts.
- 🛡️ marks a **guard**: rows 2, 12, 13, 14, 24 and 25 — **six** of the
  twenty-five — which are green the moment they are written because they assert
  the *absence* of a behaviour. Plan section *Guards, and how XI is satisfied*
  says why that satisfies XI. A guard is labelled here rather than left to be
  discovered. Row 13 was labelled red-first in an earlier draft; research R4 had
  already measured that it passes on arrival, so it is labelled what it is and
  the assertion it was standing in for moved to row 21 (T044).
- **[P]** means the task can run concurrently with the others in its
  `<!-- parallel-group: N -->` block: different files, no dependency on an
  incomplete task. `<!-- sequential -->` marks a run of tasks that must not be
  fanned out.
- **[US1]…[US5]** name the user story a task serves. Tasks that serve none —
  setup, the constitution amendment, the gates — carry no story label. Because
  the red order interleaves stories, phases here are named after the rows they
  cover rather than after one story; the story label carries the mapping.

**The `_site` assembly is stated in exactly one place**: plan section
[*The `_site` assembly, stated once*](plan.md#the-_site-assembly-stated-once).
No task restates it. `pages.yml` keeps its three `cp` lines **and**
`build_docs.py` performs the same three copies; both are idempotent.

**Two ordering constraints are tasks, not notes** — T008 and T009. Neither may be
skipped or reordered: without T008 the red of rows 5–13 is a *skip*, and without
T009 the whole feature rests on numbers that cannot be checked from this
checkout.

## Path conventions

Single flat module, no `src/`. New in this feature: `requirements-docs.txt`,
`docsite/` (`conf.py`, `_ext/`, `_static/`, page sources) and
`scripts/build_docs.py`. Tests are `tests/test_<module>.py`; this feature adds
`tests/test_build_docs.py` and `tests/test_docsite_layout.py` and edits
`tests/test_check_docs.py`, `tests/test_landing_page.py` and
`tests/test_repo_hygiene.py`.

---

## Phase 1: Setup

**Purpose**: an environment that can show a red test, and a baseline that makes
every later red attributable.

<!-- parallel-group: 1 -->

- [x] T001 [P] Install the dev requirements: `python3 -m pip install --user -r requirements-dev.txt` (pytest, ruff)
- [x] T002 [P] Install the git hooks: `scripts/install-hooks.sh` — pre-commit (no user content), pre-push (no direct `main`)
- [x] T003 [P] Confirm the working branch is `docs/skill-reference` and the tree is clean: `git status --short && git branch --show-current`

<!-- sequential -->

- [x] T004 Baseline the four gates **green before any edit**, and record the run: `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`. Every red after this point has to be one this feature caused.

**Checkpoint**: the suite is green and the branch is right.

---

## Phase 2: The docs dependency channel (red rows 1–2) + the two ordering constraints

**Purpose**: land `requirements-docs.txt`, prove it never reaches a user, and
*install* it — because rows 5–13 skip without it and a skip is not a red.

<!-- sequential -->

- [x] T005 🔴 **row 1** Create `tests/test_docsite_layout.py` with `test_the_docs_requirements_are_pinned_exactly`: `requirements-docs.txt` exists at the repository root, names `sphinx`, `myst-parser` and `pydata-sphinx-theme` with `==` (never `>=`, never unpinned), and carries one comment line per package saying what it is for. Run it — red, the file does not exist (FR-002, FR-004)
- [x] T006 **row 1 green** Create `requirements-docs.txt`: `sphinx==9.0.4`, `myst-parser==5.1.0`, `pydata-sphinx-theme==0.21.0`, one comment each (build the site / read the Markdown that already exists / the theme pandas and numpy use). Exact pins, per plan § *Dependency Decisions* — Sphinx is a *tool* here, not a library. No transitive closure is pinned; that is the constitution's open Reconciliation item and this feature neither closes nor worsens it
- [x] T007 🛡️ **row 2 (guard)** Add `test_the_docs_requirements_are_not_a_runtime_dependency` to `tests/test_docsite_layout.py`: parse the package names out of `requirements-docs.txt`, assert none appears in `REQUIREMENTS` in `scripts/deps.py`, and that **no module in the import closure of `bin/lernkarten`** imports one (FR-003, FR-005, SC-009). **Scope it to the closure, never to `scripts/*.py` as a directory.** `bin/lernkarten` imports `engine`, `deps`, `cardid`, `setup_cmd` and `build_pdf` (lines 30–71); `check_docs.real_graph()` already derives every module's local imports, so walk it transitively from those five and check `bin/lernkarten` itself. A directory-wide rule goes **red at T015**, which writes `scripts/build_docs.py` and imports `sphinx` there on purpose, and the cheap repair — excluding `build_docs` by name — is a guard that no longer guards. `build_docs` is outside the closure **by construction**: it is a leaf that nothing imports, and so is any future docs-importing script, with nobody editing this test. FR-005's own wording is the narrow and correct one — "any script a **user's run** reaches". It is green on the first run and stays green through T015 — it guards FR-003/FR-005 against a *later* feature that puts Sphinx on a user-reachable module. Label it a guard in the docstring, in the shape `tests/test_landing_page.py:471` already uses
- [x] T008 **ORDERING CONSTRAINT 1 — install before any of rows 5–13 is written.** `python3 -m pip install --user -r requirements-docs.txt`, then confirm `python3 -c "import sphinx, myst_parser, pydata_sphinx_theme"` exits 0. Rows 5–13 skip when the docs requirements are absent (FR-023, SC-006); a contributor who writes them first sees **skipped**, not red, and has not seen the red constitution XI demands. Do not start T014 before this task is done
- [x] T009 **ORDERING CONSTRAINT 2 — re-verify the Phase 0 measurements now that Sphinx is installed, before row 8 (T026).** Every number in `research.md` R1/R2/R4/R5 came from a networked spike and cannot be checked from this checkout (`python3 -c "import sphinx"` fails here). Run these probes and record each result:
  1. **The three pins resolve to what they claim** — `python3 -c "import sphinx, myst_parser, pydata_sphinx_theme; print(sphinx.__version__)"` and `python3 -m pip show myst-parser pydata-sphinx-theme`
  2. **The 32-distribution closure, on all three platform tags** — `python3 -m pip download --only-binary=:all: --python-version 3.12 --abi cp312 --platform <tag> -r requirements-docs.txt -d /tmp/closure-<tag>` for `win_arm64`, `manylinux2014_x86_64` and `macosx_11_0_arm64`; count the wheels (**measured 32 each**, all resolving — the Phase 0 figure was 33 and is corrected throughout)
  3. **The transform priorities** — `python3 -c "from myst_parser.sphinx_ext.myst_refs import MystReferenceResolver; print(MystReferenceResolver.default_priority)"` (expected **9**, so the post-transform sits at **5**), and the `doctree-read` connect priority of `sphinx.environment.collectors.EnvironmentCollector` / `DownloadFileCollector` (expected **500**, so the `doctree-read` hook sits at **100**)
  4. **The stylesheet counts** — locate the installed `pydata_sphinx_theme/theme/pydata_sphinx_theme/static/styles/pydata-sphinx-theme.css` and count `border-radius` (expected 131), `box-shadow` (78) and `font-size` rules below 16 px (33), plus that `--pst-font-size-milli` and `--pst-sidebar-font-size` are both `0.9rem`
  5. Determinism, absolute paths and the offline build (R5) cannot be probed until `scripts/build_docs.py` exists — they are re-verified at **T034** and **T035**, which are named there for this reason

  If a probe disagrees with `research.md`, **stop and amend `research.md`** with the measured value rather than proceeding on the old number; if a pin no longer resolves, re-vet under constitution IV rather than bumping it silently. The pins are only truly exercised by the first green `docs-build` run on all three operating systems (T062)

**Checkpoint**: `requirements-docs.txt` exists, is pinned, is installed, is proven
off the runtime path, and the Phase 0 numbers are measurements again rather than
recollections.

---

## Phase 3: Foundational — the build output stays out, the gate reaches in (red rows 3–4)

**Purpose**: two invariants that must hold before anything writes into
`docsite/` or `_site/`.

<!-- parallel-group: 2 -->

- [x] T010 🔴 [P] [US5] **row 3** Add `test_the_build_directory_is_ignored` to `tests/test_docsite_layout.py`: `docsite/_build/` and `_site/` are matched by `.gitignore` (FR-022, constitution IX). Use the `git check-ignore` helper shape already at `tests/test_repo_hygiene.py:131` rather than parsing `.gitignore` by hand. Red — neither path is ignored today
- [x] T011 🔴 [P] [US5] **row 4** Add `test_check_docs_covers_the_docsite` to `tests/test_check_docs.py`: `markdown_files()` returns every `docsite/**/*.md` (FR-037). **Write it against a monkeypatched root** — `monkeypatch` `check_docs.ROOT` onto a `tmp_path` tree holding `docsite/user/page.md`, the shape `gated_project()` already uses at `tests/test_check_docs.py:194`. Asserting only against the real repository would pass vacuously today, because `docsite/` does not exist yet and an empty set satisfies "contains every"; that is a green test wearing a red label

<!-- parallel-group: 3 -->

- [x] T012 **row 3 green** [P] [US5] Add `docsite/_build/` and `_site/` to `.gitignore`, under the `# --- Build leftovers ---` section, each with a one-line comment saying it is generated (constitution IX)
- [x] T013 **row 4 green** [P] [US5] Extend `markdown_files()` in `scripts/check_docs.py` with `files += sorted((ROOT / "docsite").rglob("*.md"))`. Plan § *`scripts/check_docs.py` (FR-037)* names the three consequences and the **two different routes** into the drift gates: `check_a7_is_not_the_default`, `check_cut_count` and `check_borderless_size` go through `gated_files()`, while `check_sheet_capacity` (`scripts/check_docs.py:577`) and `check_print_order` (line 598) call `markdown_files()` **directly** and do not strip code blocks. `check_leitner_intervals` reads `LEITNER_PAGE` (line 252) directly and is untouched by the widening (FR-011)

**Checkpoint**: `pytest tests/test_docsite_layout.py tests/test_check_docs.py` green;
`python3 scripts/check_docs.py` still green.

---

## Phase 4: The build command and the migrated pages (red rows 5–7, and rows 20/23 pulled forward)

**Purpose**: one command that builds the site, the five documents reachable, and
warnings as errors.

> **Deviation from the plan's row order, stated rather than hidden.** Rows **20**
> and **23** (the FR-039 constitution amendment) sit at the end of `plan.md`'s
> table, but row 20's red is a *gate*, not a test: `check_import_graph()`
> (`scripts/check_docs.py:371`) derives the real import graph from `scripts/*.py`
> and fails the **Skills & docs** CI job for any module Principle VI's fenced
> block does not list. That red begins the moment `scripts/build_docs.py` exists
> (T015) and would stay red across every commit until the amendment. So the
> amendment lands **in the same commit as the script**, and row 23's assertion is
> written just before it so both halves of FR-039 are red first. Nothing else
> moves.

> **Expect a failing build between T024 and T033, and do not "fix" it.** Enabling
> `-W` at row 7 turns the 27 `myst.xref_missing` warnings the five migrated
> documents produce (`research.md` R2) and the two unresolved images into build
> failures. Rows 5 and 6 therefore go red again from T024 and come back green at
> **T033**, when the transform and `:relative-images:` are both in. That window
> is the point of rows 8–11; closing it early by hand-editing a source file is
> exactly what plan finding **C1** forbids.

<!-- sequential -->

- [x] T014 🔴 [US2] **row 5** Create `tests/test_build_docs.py` with a module-level skip that names `requirements-docs.txt` — mirror the engine skip in `tests/test_e2e.py` (FR-023, SC-006) — and `test_the_build_exits_zero_and_writes_an_index`: run the build as a subprocess with **`sys.executable`, never the string `python3`** — `[sys.executable, str(ROOT / "scripts" / "build_docs.py"), "--site", str(tmp)]`, the shape `tests/test_e2e.py:71` already uses — and assert exit 0 and an `index.html` under `<tmp>/docs/`. The Windows leg of `docs-build` is the **only** job where rows 5–13 execute rather than skip, and `python3` is not what that runner resolves; a hard-coded `python3` fails every one of them for a reason that has nothing to do with this feature. Red on its assertion, not on a skip (T008 is why)
- [x] T015 [US2] **row 5 green (1/3)** Write `scripts/build_docs.py` — new module, module docstring in the established style (what it does, the command that invokes it, why it exists). It: checks the docs requirements are importable and, if not, exits non-zero with one line naming `pip install -r requirements-docs.txt` (the courtesy `scripts/deps.py` and `scripts/engine.py` already extend); runs Sphinx into `<site>/docs/`; performs the three `shutil.copy2` copies and `Path.touch()` of `.nojekyll` per plan § *The `_site` assembly, stated once*; prints the path to open. **Two** options, `--site <dir>` and `--source <dir>`, both defaulting so that the no-argument form is the FR-019 command (`--site` already establishes that "no arguments" is about the default). `--source` defaults to `docsite/` and exists so a test never writes a probe page into the checked-in tree: an interrupted row 7 or row 10 would leave a `docsite/*.md` behind that turns the next build red, turns gate #4 red (FR-037 puts `docsite/**/*.md` inside `check_links`, and a probe's dead link is exactly what it reports) and trips row 25. `conf.py`'s `sys.path` insert of `_ext` is relative to the configuration directory, so a copied tree builds unchanged. **It imports no local module** — it is a new leaf of Principle VI's graph (FR-019, FR-038)
- [x] T016 **row 20 red (a gate, not a pytest case)** Run `python3 scripts/check_docs.py` immediately after T015 and record the failure: `check_import_graph()` reports `build_docs` as a module Principle VI's fenced block does not list. This is row 20's red, and it is why the amendment is a task
- [x] T017 🔴 **row 23** Add `test_principle_v_names_the_documentation_directory` to `tests/test_repo_hygiene.py`: Principle V's table in `.specify/memory/constitution.md` has a `docsite/` row, and its `docs/` row names `leitner.html`. Red — the table has neither today (`.specify/memory/constitution.md:232–240`). This is the half of FR-039 that **nothing else enforces**, which is precisely why it gets an assertion
- [x] T018 **rows 20 + 23 green — the constitution amendment (FR-039), in the same commit as T015.** Edit `.specify/memory/constitution.md`: Principle V's table gains a **`docsite/`** row (Sphinx configuration, page sources, the build-time extension and the stylesheet) and its `docs/` row additionally names **`leitner.html`**; Principle VI's fenced block gains `build_docs` on the leaves line, as `build_docs, deps, engine, leitner ← leaves, import nothing local` — the form `documented_graph()`'s `^([\w, ]+?)\s*(?:→|←)` pattern accepts verbatim. Bump **Version** to `2.8.0` and **Last Amended** to today, and add the changelog paragraph in the style of the `2.7.0` entry. Verify with `python3 scripts/check_docs.py` (row 20 green) and `pytest tests/test_repo_hygiene.py` (row 23 green)
- [x] T019 [US2] **row 5 green (2/3)** Write `docsite/conf.py` **by hand** — a copied Sphinx template does not pass `ruff check` at `line-length = 100` under `select = ["E","F","W","I","UP","B","C4","SIM"]`, and `pyproject.toml` declares no `exclude`, so this file is inside gate #1 from its first commit (FR-024). Set: project metadata, `extensions = ["myst_parser"]`, `myst_heading_anchors = 3` (FR-040 — exactly the depth `#the-box`, `#automated` and `#the-checklist` need), `html_theme = "pydata_sphinx_theme"`, `exclude_patterns`. **Leave `html_baseurl` unset, with a comment naming FR-018 and the `/docs/` sub-path** — Sphinx's HTML builder emits document-relative URIs by default, so FR-018 holds by the *absence* of a line, and the comment is what stops a later sitemap or Open Graph edit from removing it silently
- [x] T020 [US1] **row 5 green (3/3)** Write `docsite/index.md`: the root document, with **two** `{toctree}` directives — `user/index` and `contributing/index`. FR-012's headroom for 013 and 014 is a third and fourth entry in the same list, with no restructuring
- [x] T021 🔴 [US1] **row 6** Add `test_every_migrated_document_is_in_the_toctree` to `tests/test_build_docs.py`: walk the **built `toctree`** from the root document (the build environment, not the rendered sidebar — the sidebar is the theme's rendering of it and would tie the assertion to a theme version, SC-002). Assert all five migrated documents are reachable and that *user* and *contributing* are separate top-level branches
- [x] T022 [US1] **row 6 green** Write the page sources per [contracts/docsite-layout.md § 2](contracts/docsite-layout.md): `docsite/user/index.md`, `docsite/user/workflow.md`, `docsite/contributing/index.md`, `docsite/contributing/design.md`, `docsite/contributing/testing.md`, `docsite/contributing/guide.md`. Each migrated page is **one `{include}` and nothing else** — no wrapper heading, no `:heading-offset:`, no `:relative-docs:` (the contract says why each is forbidden); the included document's own H1 becomes the page title and the `toctree` entry, so nothing is retyped (FR-008). **Write the includes without options for now**: `:relative-images:` is row 11's green (T033) and adding it here would make that row green before it was ever red. Also write `docsite/user/leitner.md`, the FR-032 wrapper — a short signpost that introduces the method and links out to `../../docs/leitner.html`; it restates nothing (FR-008, FR-032)
- [x] T023 🔴 [US4] **row 7** Add `test_a_missing_reference_fails_the_build` to `tests/test_build_docs.py`: `shutil.copytree` `docsite/` into `tmp_path`, write a temporary page there carrying a dead cross-reference, build **that copy** (`--source <tmp_path>/docsite`, T015), and assert non-zero exit and that the message names **the source document and the target** (SC-003, FR-020). Remove the page and assert the build passes. **Never write the probe into the checked-in `docsite/`** — an interrupted run leaves a file that makes the build and gate #4 red, and the failure looks unrelated to whoever hits it
- [x] T024 [US4] **row 7 green** Pass `-W --keep-going` in `scripts/build_docs.py`. From this task the real build fails until T033 — see the note at the head of this phase
- [x] T025 [US5] **row 4, completed against the repository** Now that `docsite/**/*.md` exists, add the shipped-repository half of `test_check_docs_covers_the_docsite` in `tests/test_check_docs.py`: every file the real `docsite/` glob finds is in `markdown_files()`. The monkeypatched case from T011 stays — it is the one that can be red

**Checkpoint**: `python3 scripts/build_docs.py` runs and fails loudly on 27
unresolved repository links plus two images. That is the correct state, and
Phase 5 closes it.

---

## Phase 5: The repository-link transform (red rows 8–11)

**Purpose**: 27 unresolved links and 2 unresolved images become an internal
cross-reference, a site-root relative link, a GitHub URL or a rendered image —
**without any source file being edited** (plan finding C1; SC-011).

**Prerequisite**: T009. The priorities this phase hard-codes (post-transform 5
against MyST's 9, `doctree-read` 100 against `DownloadFileCollector`'s 500) are
spike measurements, and T009 is where they were re-measured.

<!-- sequential -->

- [x] T026 🔴 [US4] **row 8** Add `test_every_repository_link_resolves` to `tests/test_build_docs.py` — the transform's own test, which FR-029 requires. Assert the rendered `href` for a representative of **each of the four branches** of [contracts/docsite-layout.md § 6](contracts/docsite-layout.md): a `PAGES` hit (internal cross-reference, anchor preserved — `design.md#the-box`), both `SERVED` hits (`index.html` → `../../index.html` and `../assets/card-box.pdf` → `../../card-box.pdf`, the depth-aware ones, **C1**/**C2**), a file (`../templates/card.typ` → `…/blob/main/…`), a directory (`../assets/fonts/` → `…/tree/main/assets/fonts`) and the anchor-preserving GitHub case (`../README.md#install`)
- [x] T027 [US4] **row 8 green** Write `docsite/_ext/repolinks.py`: a `SphinxPostTransform` with `default_priority = 5` (ahead of `MystReferenceResolver` at 9, which warns instead of emitting `missing-reference` — the obvious `missing-reference` handler **does not fire**, research R2), catching `pending_xref` with `reftype == "myst"`. Resolve the target against `Path(node.source).parent` — the file the link was *written in*, which the node carries even inside an `{include}` — then apply the resolution order in contract § 6, with the `PAGES` and `SERVED` tables from contract §§ 4–5. Set `parallel_read_safe`/`parallel_write_safe` in `setup()`. Register it from `docsite/conf.py` (`sys.path` insert of `_ext`, `extensions += ["repolinks"]`). It **imports nothing from `scripts/`** — row 14 (T036) asserts that, and 013 inherits the directory and the rule
- [x] T028 🔴 [US1] **row 9** Add `test_the_method_page_is_never_duplicated` to `tests/test_build_docs.py`: no `_downloads/` anywhere in the build output, and exactly one `leitner.html` in the assembled `_site` (**C4**, FR-010, SC-012). Red — written as a relative path, the wrapper page's link becomes a MyST *download* and Sphinx copies the file to `_downloads/<hash>/leitner.html`, a second URL with a `download=""` attribute
- [x] T029 [US1] **row 9 green** Add the `doctree-read` hook at `priority=100` to `docsite/_ext/repolinks.py`, handling `download_reference` nodes — ahead of Sphinx's `DownloadFileCollector` at 500, so the node is rewritten before the file is collected
- [x] T030 🔴 [US4] **row 10** Add `test_a_docsite_page_may_link_a_repository_file` to `tests/test_build_docs.py`: FR-037's prescribed spelling from a `docsite/` page — `[design.md](../docs/design.md)` — renders as a link and the build stays clean (**C3**). **Write the temporary page at the root of a `copytree` of `docsite/` in `tmp_path`** and build it with `--source` (T015, and the same reason as T023) — at the tree's root, which is the depth that spelling is correct at; from a page in `docsite/user/` or `docsite/contributing/` the same link is `../../docs/design.md` (contract § 3). The branch under test is the depth-independent one — a `doc` target absent from `env.all_docs` — but a test written at the wrong depth fails on the path rather than on the branch, and would look like C3 reappearing. Red — MyST strips the `.md`, resolves it as a **docname**, finds nothing, warns (fatal under `-W`) and renders **no link at all**
- [x] T031 [US4] **row 10 green** Add the `refdomain == "doc"` branch to `docsite/_ext/repolinks.py`: for a `doc` target absent from `env.all_docs`, put the suffix back and run the same lookup. FR-037's spelling then works in both directions — the site links it and `check_docs.check_links` still resolves it on the file system
- [x] T032 🔴 [US1] **row 11** Add `test_the_images_are_rendered_not_linked` to `tests/test_build_docs.py`: `pipeline.png` and `example-cards.png` appear as `<img>` under `_images/`, never as GitHub URLs (FR-030, FR-041). Red — without `:relative-images:` the paths resolve against the *including* page
- [x] T033 [US1] **row 11 green** Add `:relative-images:` — and only that option — to every `{include}` under `docsite/`, per contract § 2. **The build is clean under `-W` from here**; re-run rows 5 and 6 and confirm they are green again

**Checkpoint**: `python3 scripts/build_docs.py` exits 0 with zero warnings, and
every source file still carries the relative path it had before this feature —
`check_docs.check_links` has lost no coverage (SC-005, SC-011).

---

## Phase 6: Output properties and the standing guards (rows 12–14)

**Purpose**: the three properties that must not regress later, plus the R5
measurements T009 could not reach.

<!-- sequential -->

- [x] T034 🛡️ [US2] **row 12 (guard)** Add `test_building_twice_is_byte_identical` to `tests/test_build_docs.py`: two builds, the HTML compared, `.doctrees/` and `.buildinfo` excluded — Sphinx's own incremental-build state, which SC-004 names for exactly this reason. It is a **guard**, deliberately written *after* row 5: before `scripts/build_docs.py` exists it cannot even be collected, and an error is not a red (`constitution.md:382`); making it genuinely red would mean writing a deliberately non-deterministic build and removing it, which is a spike promoted to a pull request. Determinism is Sphinx's property (research R5) — what this row defends is a future `conf.py` line that would destroy it. **Re-verify R5 here** (T009 item 5): the two builds are identical, no absolute path appears anywhere in the output, and the build makes no network call

<!-- parallel-group: 4 -->

- [x] T035 🛡️ [P] [US1] **row 13 (guard)** Add `test_the_site_loads_no_third_party_subresource` to `tests/test_build_docs.py`: no `<link>`, `<script>` or `<img>` with an `http(s)` URL anywhere in the built output (SC-014); **and**, folded in per plan § *Relative internal links (FR-018)*, no `href`/`src` beginning with `/` and none containing `mhabedank.github.io` — the two ways FR-018 breaks, both one grep. **It is a guard, not a red**: research R4 measured that the stock theme already loads no third-party sub-resource (FontAwesome ships bundled under `_static/vendor/`), and Sphinx's relative URIs are the default, so it passes on its first run and there is nothing to make red without first pointing an `@font-face` at a CDN or adding an `html_baseurl`. Say so in the docstring, in the shape rows 2/12/14/24 use. **What it cannot see is the other half of SC-014** — a build with no font at all satisfies it — so the assertion that the faces actually arrived lives on row 21 (T044)
- [x] T036 🛡️ [P] **row 14 (guard)** Add `test_the_extension_imports_nothing_from_lernkarten` to `tests/test_docsite_layout.py`: parse every `docsite/_ext/*.py` with `ast` and assert none imports a `scripts/` module. Green on the first run — it is the enforcement the spec's extraction decision promised, and 013's skill extension inherits it

**Checkpoint**: determinism, purity and the sub-resource rule all have standing
assertions.

---

## Phase 7: Publication (red rows 15–17)

**Purpose**: the landing page links into the site, CI actually runs the docs
tests, and the workflow builds and deploys it all-or-nothing.

> `pages.yml`'s `paths:` list stays at its **four existing entries** through
> this phase — `docs/index.html`, `docs/leitner.html`, `assets/card-box.pdf` and
> `.github/workflows/pages.yml`, which the file already lists. The **eight** new
> ones are row 22's green (T051); adding them here would make that row green
> before it was ever red.

> **The rows run 15, 16, 17 — ascending, on purpose.** Row 16 (`ci.yml`) and row
> 17 (`pages.yml`) touch different files and neither blocks the other, so row 16
> is taken first and the file needs no third exception to its own ordering rule.
> One consequence to expect rather than "fix": from T039 the `docs-build` job
> runs the whole suite, and row 15 is still red until T042, so CI is red in
> between. That is the red-first process working; the pull request is not opened
> until T062.

<!-- sequential -->

- [x] T037 [US3] **row 15 red — caused by a source edit, not by a new test** **Two edits, both in the button row at `docs/index.html:767–770`** (FR-014, FR-042). **(a)** Add a link pointing at **`docs/`** — the directory, not `docs/index.html`; FR-016's test matches the derived reference, so the two are not interchangeable (FR-014). **(b)** Retarget the existing `full walkthrough` button (line 769) from `https://github.com/mhabedank/lernkarten/blob/main/docs/workflow.md` to **`docs/user/workflow.html`**, the page the site now publishes. That button is the most literal instance of the complaint this feature exists to answer: the landing page's own call to action sends a newcomer to raw Markdown on GitHub, and after 012 it would do so from the same section that offers `docs/` into the site. It is decided the way FR-042 decided the README's three — leaving it reintroduces the split one link deep. `.button-row` is `flex-wrap: wrap` (`docs/index.html:152`), so a third button reflows rather than overflowing. Nothing else on the page changes. **Put it in the page body, not in the nav** — and this is not a preference. `NAV_LINKS = ("#how", "#cards", "#print", "#install")` (`tests/test_landing_page.py:201`), and `test_the_four_nav_links_sit_inside_the_disclosure_and_the_rest_does_not` (line 237) *filters to that tuple*, so a fifth nav link passes every assertion in the suite while silently falsifying `docs/testing.md` manual rows **20** ("all four links behind it") and **24** ("wordmark, four inline links, github"). That is the same shape as the box test PR #105 had to replace: a test that only knows what it was told. If a later change moves the link into the nav, those two rows move with it — they are named here so that is a decision rather than a discovery. Run `pytest tests/test_landing_page.py` and watch `test_the_pages_workflow_assembles_every_relative_link` (line 562) fail on **both** new derived references — `docs/` and `docs/user/workflow.html`, which is why T042's adaptation admits the subtree rather than one literal
- [x] T038 🔴 [US3] **row 16** Add `test_the_ci_docs_job_runs_the_docs_tests` to `tests/test_docsite_layout.py`: **parse `.github/workflows/ci.yml` with `yamlio`** (pyyaml is in `requirements-dev.txt`, and `tests/test_repo_hygiene.py:26` already imports `yamlio`), **select the job whose steps run `build_docs.py`**, and assert every clause **on that job object**: its id is **not** `docs` (that id belongs to the "Skills & docs" job at `ci.yml:148` and reusing it is a YAML error); its `strategy.matrix.os` is `ubuntu-latest`, `macos-latest` and `windows-latest`; its steps install `requirements-docs.txt`; **and its steps run `pytest`**. The last clause is the one that matters — without it rows 5–13 skip in every CI job and execute nowhere (FR-023, FR-034). **Scope it to the job, exactly as T050 scopes itself to the first fenced block.** Against `ci.yml` as *text*, four of the five clauses are already true today — `cards` and `e2e` list all three runners, `test` runs `python -m pytest`, and `requirements-dev.txt` is installed in four places — so an unscoped test is red on one clause and vacuous on the rest
- [x] T039 [US3] **row 16 green** Add the job to `.github/workflows/ci.yml`: id **`docs-build`**, name "Documentation build", matrix `[ubuntu-latest, macos-latest, windows-latest]`, Python 3.12, `shell: bash` like the other multi-OS jobs, and three run steps — `python -m pip install -r requirements-dev.txt -r requirements-docs.txt`, `python scripts/build_docs.py`, `python -m pytest`. The whole suite rather than the docs module, deliberately: it is the only leg that exercises the transform, `{include}` resolution and text encoding on **macOS**, which the `test` job does not cover at all. **`python`, not `python3`** — every other multi-OS job in `ci.yml` uses `python` under `shell: bash`, and a third convention inside one job risks a Windows leg failing for a reason that has nothing to do with this feature. `python3 scripts/build_docs.py` stays the documented human command (FR-019); the two are not in conflict
- [x] T040 🔴 [US3] **row 17** Add `test_the_deploy_is_all_or_nothing` to `tests/test_landing_page.py`: `pages.yml` runs the documentation build **before** `upload-pages-artifact`, in **one** job, so a failing build fails the job before anything is published (FR-033, SC-013 first half). Red — the workflow has no build step today. Write it **before** T041, or the rebuilt workflow makes it green on arrival
- [x] T041 [US3] **rows 15 + 17 green** Rebuild `.github/workflows/pages.yml` to four steps in this order: `checkout`; **the existing assembly block, unchanged** (`mkdir -p _site`, the three `cp` lines, `touch _site/.nojekyll`); install `requirements-docs.txt` then `python3 scripts/build_docs.py --site _site && test -f _site/docs/index.html`; `configure-pages` → `upload-pages-artifact` → `deploy-pages`. The `cp` lines stay — plan § *The `_site` assembly, stated once* is the single statement of why, and `test_the_pages_workflow_publishes_the_box` (`tests/test_landing_page.py:529`) is **not touched at all** and must stay green (FR-015, FR-033). **The `&& test -f _site/docs/index.html` is not decoration and must not be dropped**: it is a real post-condition — a build that exits 0 and writes nothing now fails before `upload-pages-artifact`, strengthening FR-033 — *and* it is the only honest way the workflow text comes to contain `_site/docs`, which is the token T042's adapted rule reads. Without it row 15 can never go green, and the quickest repair is a comment saying `_site/docs`, at which point the derivation reads a word that proves nothing
- [x] T042 [US3] **row 15 green** Adapt `test_the_pages_workflow_assembles_every_relative_link` in `tests/test_landing_page.py`: keep deriving the target set from `docs/index.html`, keep requiring **every** target, and teach it one second route — a target may also arrive because the documentation build writes `_site/docs/`, derived from the workflow text rather than allow-listed: `built = bool(re.search(r"_site/docs\b", workflow)) and (ref.rstrip("/") == "docs" or ref.startswith("docs/"))`. **The whole `docs/` subtree, not one literal** — FR-016's *permitted* clause says the second route is anything "produced by the documentation build into `_site/docs/`", and after T037 the page carries two such targets: `docs/` and the retargeted `docs/user/workflow.html`. A rule matching only the literal `docs` would reject the second and force it back onto a `cp` line that can never produce it. The token the first half reads is real from T041 — the build step ends with `test -f _site/docs/index.html`. **The derived set is unchanged**; this is the adaptation FR-016 permits, not the weakening it forbids (SC-005, manual row 45 reads this diff)

**Checkpoint**: `pytest tests/test_landing_page.py` fully green, including every
assertion that existed before this feature (SC-005).

---

## Phase 8: The surfaces and the documents (red rows 18, 19, 21)

**Purpose**: the README points at the site, `docs/design.md` describes the third
surface, and the theme is actually overridden rather than merely installed.

> The rows run **18, 21, 19** inside this phase. They are mutually independent —
> different tests, different files, no shared state — and pairing 18 with 21 is
> what makes groups 5 and 6 a real fan-out rather than a decorated chain. Row 19
> follows because it edits the same test file as row 18.

<!-- parallel-group: 5 -->

- [x] T043 🔴 [P] [US1] **row 18** Add `test_the_readme_points_at_the_published_pages` to `tests/test_repo_hygiene.py`: the three `README.md` references to migrated documents are site URLs, **and** `](docs/index.html)` inside `## The design` is untouched — `test_the_readme_still_names_the_landing_page_source` (line 287) pins it and no test is changed (FR-042)
- [x] T044 🔴 [P] [US1] **row 21** Add `test_the_theme_override_lands` to `tests/test_build_docs.py`: the built `_static/lernkarten.css` sets `--pst-font-family-base`, `--bs-font-sans-serif` and `--bs-font-monospace`, and carries the blanket `border-radius: 0` / `box-shadow: none` rule (FR-027). **And that the faces arrived**: the built `_static/` carries `Archivo.ttf`, `Jost.ttf` and `IBMPlexMono-Regular.ttf`, and `lernkarten.css` declares **four** `@font-face` blocks with `format("truetype")` (SC-014's positive half — row 13 is satisfied by a build with no font at all, so nothing else can see this). **Three variable names, one rule and the faces, deliberately not a selector list** — a list goes stale on the next theme release and becomes somewhere to put the next violation; and the measurement it pins is exactly what regresses silently, because overriding only the three `--pst-` variables leaves `body` on the system stack, and an `html_static_path` that never reached `assets/fonts/` leaves the whole site on it

<!-- parallel-group: 6 -->

- [x] T045 [P] [US1] **row 18 green** Retarget `README.md`'s three references at the published pages, by these exact strings (derived from contract § 4 and FR-013 — row 18's test matches them, and a test written without them can only assert the *absence* of the old link, which is a weak test): `docs/workflow.md` (line 79) → `https://mhabedank.github.io/lernkarten/docs/user/workflow.html`; `docs/design.md` (274) → `https://mhabedank.github.io/lernkarten/docs/contributing/design.html`; `docs/testing.md` (288) → `https://mhabedank.github.io/lernkarten/docs/contributing/testing.html`. Accepted cost, recorded in FR-042: `check_docs.check_links` skips `http` targets, so those three leave its file-system coverage; `REQUIRED_FILES` still requires the files to exist
- [x] T046 [P] [US1] **row 21 green** Write `docsite/_static/lernkarten.css` (~90–130 lines) and register it with `html_css_files` in `docsite/conf.py`, adding `assets/fonts/` to `html_static_path` so the faces are copied rather than converted (no new binary — constitution VIII, research R4). It contains: four `@font-face` blocks with `format("truetype")` and `font-weight: 100 900` on the two variable faces (Archivo, Jost) so Jost 400 and 500 come off one file; **five** font variables, not three — `--pst-font-family-base/-heading/-monospace` plus `--bs-font-sans-serif` and `--bs-font-monospace`, because `body` resolves `--bs-body-font-family` → `--bs-font-sans-serif` and never reads a `--pst-` variable; the nine inks of `docs/design.md` mapped onto the theme's `--pst-color-*` set; `*, *::before, *::after { border-radius: 0 !important; box-shadow: none !important; }` plus `--bs-gradient: none` (**no** blanket `background-image: none` — it would erase the navbar toggler, the admonition icons and the external-link marker, which are inline `data:` SVGs); and the **15 px Archivo-prose floor** — about ten declarations, chief among them raising `--pst-font-size-milli` and `--pst-sidebar-font-size` from `0.9rem` to `1rem`, with `pre`, `code`, `kbd`, icon glyphs, `sub`/`sup` and the keycap literal left alone (FR-035 binds Archivo prose only). Plan § *The theme work* is the measured selector inventory; do not re-derive it

<!-- sequential -->

- [x] T047 🔴 [US1] **row 19** Add `test_the_design_doc_describes_the_documentation_site` to `tests/test_repo_hygiene.py` — beside `test_the_design_doc_describes_the_box` (line 473): `docs/design.md` § *The screen surfaces* has **a row naming `docsite/`** (FR-036). Assert the row, never its ordinal: the table lists five rows today (landing page, banner, pipeline strip, social card, example cards), so the new one is the **third surface** and the sixth row, and an ordinal assertion would break the next time a graphic is added
- [x] T048 [US1] **row 19 green** Read `docs/design.md` before editing it (constitution XVI), then add to § *The screen surfaces* the row for the third surface — the sixth row of a five-row table (`documentation site` | ``[`docsite/`](../docsite/)`` — Sphinx + MyST, `pydata-sphinx-theme` overridden to the rules on this page). **The link target is `../docsite/`, a directory** — the same shape as the row above it, so `check_links` resolves it on the file system once the directory exists and FR-029's transform renders it `…/tree/main/docsite`; do not leave it as bare code text and do not hard-code a GitHub URL and the short paragraph naming what is **kept** from the theme (the two-level navigation, the bundled icon font, admonition colours doubled by icon and rule, the footer credit) and what is **overridden** (the inks, the three self-hosted faces, every radius/shadow/gradient, the 15 px floor). State it as a **rule, not a list of selectors**, for the reason `tests/test_landing_page.py` already gives about the type floor

**Checkpoint**: the site reads as the same system as the landing page — as far as
a test can say. The part only an eye can judge is manual row 44 (T063).

---

## Phase 9: The last assertions (rows 22, 24, 25)

<!-- parallel-group: 7 -->

- [x] T049 🔴 [P] [US3] **row 22** Add `test_the_pages_workflow_triggers_on_every_input` to `tests/test_landing_page.py`: **all twelve** `paths:` entries are present, one assertion per entry, following the pattern already at `tests/test_landing_page.py:539` — the **four** the file already has (`docs/index.html`, `docs/leitner.html`, `assets/card-box.pdf` and `.github/workflows/pages.yml` itself, which is easy to absorb silently into a count of three) and the **eight** new ones: `docs/*.md`, `CONTRIBUTING.md`, `docsite/**`, `requirements-docs.txt`, `assets/pipeline.png`, `assets/example-cards.png`, `scripts/build_docs.py` and **`assets/fonts/**`** (FR-017). `assets/fonts/**` is an input like any other: FR-027 and T046 make the build copy the three faces out of it through `html_static_path`, so a face that is replaced or re-hinted must redeploy the site. It was missing while the *count* was being reconciled from ten to eleven — the number was checked against itself and the list was never checked against FR-027. A dropped entry means the site silently stops redeploying — the class of failure PR #105 fixed
- [x] T050 🛡️ [P] [US5] **row 24 (guard)** Add `test_the_pre_pr_gates_have_not_grown` to `tests/test_repo_hygiene.py`: the **first** fenced `bash` block under `CONTRIBUTING.md` § *Before the pull request* (lines 42–48) still holds exactly **five** command lines — `ruff check .`, `ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`. Five lines for what the project calls **four gates**, because `ruff` runs twice; do not "fix" that count. **Scoped to the first block** — the section carries a second one (`make_testdata.py`, `LERNKARTEN_E2E=1 pytest`) which is not a pre-PR gate. Green on the first run: it is the only thing standing between FR-024's "no fifth gate" and a future feature quietly adding a sixth line (SC-010)
- [x] T050a 🛡️ [P] **row 25 (guard)** Add `test_the_docsite_holds_no_symlink_and_no_copy` to `tests/test_docsite_layout.py`: no path under `docsite/` is a symlink (`Path.is_symlink()`, walked recursively), and no file under `docsite/` repeats the bytes of a migrated document (`docs/*.md`, `CONTRIBUTING.md`) — FR-028's two mechanisms, which it excludes **by name** and which nothing enforced until this row. FR-028 says it is written "so that a later change does not 'simplify' it into a move"; that sentence had no gate. Green on the first run, for the same reason row 14 is: making it red would mean committing the arrangement the requirement forbids. **A pytest case, not a manual row** — FR-025 caps the manual checklist at three (44, 45, 46) and this does not touch that cap. Numbered `T050a` rather than inserted as `T051`: it was added after the list was written, and renumbering fifteen tasks to make the id ascending would break every cross-reference in this file for no gain — the same reason `docs/testing.md` carries rows 23a and 23b

<!-- parallel-group: 8 -->

- [x] T051 [P] [US3] **row 22 green** Add the **eight** new `paths:` entries to `.github/workflows/pages.yml` — the seven of plan § *`pages.yml`* plus **`assets/fonts/**`** — keeping the four existing ones (FR-017). Twelve in total, which is what T049 asserts
- [x] T052 [P] [US2] Add the **optional** docs install to `CONTRIBUTING.md` § *Development setup*: `python3 -m pip install -r requirements-docs.txt` and `python3 scripts/build_docs.py`, described as optional and only for working on the documentation. **Do not touch § *Before the pull request*** — T050 asserts that block still holds five lines (FR-002, FR-024)

**Checkpoint**: `pytest` fully green, `python3 scripts/check_docs.py` green.

---

## Phase 10: Docs & cross-cutting

<!-- parallel-group: 9 -->

- [x] T053 [P] Add the **three** manual rows to `docs/testing.md` — 44, 45 and 46, and no fourth (FR-025 caps them at three). The checklist reaches 43 today (the Leitner dividers, `docs/testing.md:270–281`), so add a `### The documentation site, 44–46` subsection under `## By hand` in the same shape. Row **44**: SC-008/FR-035 — at 375 px every page reads without horizontal scrolling and no Archivo prose renders below 15 px (a code sample and a letterspaced label are exempt). Row **45**: SC-005 — read the diff of `tests/test_landing_page.py` and `scripts/check_docs.py`; no assertion deleted, no target dropped from a derived set, no condition relaxed. Row **46**: SC-013 **and SC-007** — the documentation build ran on the pull request, then after the merge walk the deployed site per [quickstart.md § 11](quickstart.md). SC-007 rides on row 46 rather than taking a fourth row, the shape rows 33 and 34 already establish
- [x] T054 [P] Read every new page under `docsite/` for constitution VII and XIII: subject-agnostic (a format demonstrated, never a field of study) and English throughout, including the `leitner.md` wrapper and the two area indexes (FR-026)
- [x] T055 [P] Walk [quickstart.md](quickstart.md) §§ 1–8 against what actually shipped and correct any drift in the quickstart — including § 2's instruction to **serve** `_site` rather than open it (FR-014's `docs/` is a directory, and over `file://` a browser shows a listing)

**Checkpoint**: what the feature promises and what the documents say are the same
thing.

---

## Phase 11: Gates

**Purpose**: exactly what CI checks. Four gates, five command lines, and **no
fifth gate** (FR-024, SC-010).

<!-- parallel-group: 10 -->

- [ ] T056 [P] `ruff check . && ruff format --check .` — gate #1 now also reads `docsite/conf.py` and `docsite/_ext/*.py`; `pyproject.toml` declares no `exclude`, which is the scope widening FR-024 records
- [ ] T057 [P] `pytest`
- [ ] T058 [P] `lernkarten check cards/example.yaml`

<!-- sequential -->

- [ ] T059 `python3 scripts/check_docs.py` — including `check_import_graph()`, green since T018, and `check_leitner_intervals`, which the FR-037 widening cannot reach
- [ ] T060 In an environment where **none** of the three docs packages is installed (a fresh venv with `requirements-dev.txt` only): `pytest -q` passes with the docs-build tests reported as **skipped**, each naming `requirements-docs.txt`; `python3 bin/lernkarten check cards/example.yaml` and `python3 bin/lernkarten build cards/example.yaml -o output/cards.pdf` run unchanged (SC-006, SC-009, quickstart § 6)
- [ ] T061 `git status` clean of generated output and user content — no `_site/`, no `docsite/_build/`, no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binary
- [ ] T062 Push the branch and open the pull request (`main` rejects direct pushes), then confirm the **`docs-build` job is green on all three operating systems**. This run is the second half of ordering constraint 2 (T009): it is the first time the three pins and the wheel matrix are exercised outside the Phase 0 spike

---

## Phase 12: By hand

**Purpose**: the three numbered rows T053 wrote, walked (constitution XI).

<!-- sequential -->

- [ ] T063 **Manual row 44** — `python3 scripts/build_docs.py && python3 -m http.server -d _site 8000`, then open a documentation page at a **375 px** viewport. No horizontal scrolling; no Archivo prose below 15 px; and the judgement no measurement makes — does the flattened theme *read* as the same system as the landing page (constitution XVI)? Watch the two raised sizes (`--pst-sidebar-font-size`, `--pst-font-size-milli`) for a badly reflowed sidebar or admonition title
- [ ] T064 **Manual row 45** — read the diff of `tests/test_landing_page.py` and `scripts/check_docs.py`: no assertion deleted, no target dropped from a derived set, no condition relaxed (SC-005)
- [ ] T065 **Manual row 46** — confirm the documentation build ran on the pull request; then, after the merge, walk `https://mhabedank.github.io/lernkarten/` per [quickstart.md § 11](quickstart.md): the landing page is the repository copy, its `docs/` link reaches the documentation in one click, `/leitner.html` serves the method page and no copy of it exists under `/docs/` (SC-007, SC-012, SC-013)

---

## Dependencies & Execution Order

### Phase dependencies

Most of this feature is a **chain**, and the chain is the point: the manifest
before the install, the install before the tests, the tests before the build
script, the build script before the transform, the transform before the theme.

- **Phase 1 (Setup)** — no dependencies
- **Phase 2 (docs channel)** — after Phase 1. **T008 blocks every test from T014
  onward**; **T009 blocks T026**
- **Phase 3 (foundational)** — after Phase 2. Independent of Phases 4+ except
  that T025 completes T011 once `docsite/` exists
- **Phase 4 (build + pages)** — after T008. T018 must be in the **same commit**
  as T015 or the *Skills & docs* CI job is red in between
- **Phase 5 (transform)** — after Phase 4 and after T009. Closes the failing-build
  window T024 opens
- **Phase 6 (guards)** — after T033 (a clean build to assert against)
- **Phase 7 (publication)** — after Phase 5. The rows run **15, 16, 17**, ascending: row 16 (`ci.yml`) and row 17 (`pages.yml`) are independent, so row 16 goes first and this phase needs no exception to the file's ordering rule. T040 before T041 (or the rebuilt workflow makes row 17 green on arrival); T041 before T042
- **Phase 8 (surfaces)** — after Phase 5 for the theme rows (T044, T046); the
  README and design-doc rows need only Phase 1. Within the phase the rows run
  **18, 21, 19** rather than 18, 19, 21 — the three are mutually independent, and
  pairing 18 with 21 is what makes groups 5 and 6 a real fan-out instead of a
  pretend one
- **Phase 9** — T049 after T041 (there must be a rebuilt workflow to assert
  against); T052 after T050 (the guard has to exist before `CONTRIBUTING.md` is
  edited); T050a after Phase 5 (there must be a `docsite/` to walk)
- **Phase 10 (docs)** — after the behaviour it describes settles
- **Phase 11 (gates)** — last, and non-negotiable
- **Phase 12 (by hand)** — after the gates and, for T065, after the merge

### Story completion order

| Story | Priority | Delivered by | Independently testable when |
|---|---|---|---|
| **US1** — all the documentation in one navigable place | P1 | T020–T022, T028–T033, T035, T043–T048 | `python3 scripts/build_docs.py` builds and the toctree test (T021) passes |
| **US2** — build the docs locally with one command | P1 | T014–T015, T019, T034, T052 | the build exits 0 from a clean checkout with only `requirements-docs.txt` installed |
| **US3** — published without breaking what was reachable | P1 | T037–T042, T049, T051 | `pytest tests/test_landing_page.py` green, every pre-existing assertion included |
| **US4** — a reference that does not exist fails the build | P2 | T023–T024, T026–T031 | a dead cross-reference makes the build exit non-zero naming source and target |
| **US5** — the existing docs gates keep holding | P2 | T010–T013, T025, T050, and manual row 45 | the four gates pass and the pre-PR block still holds five command lines |

**MVP**: US1 + US2 + US3 (all P1) — Phases 1–7 plus T053. That is a built,
navigable, published site. US4 is already inside it (rows 7–10 are how the build
stays honest); US5 is the promise that nothing else broke.

### Parallel groups

Ten groups, holding 24 of the 66 tasks. They are short on purpose: most of this
feature is a chain, and marking a dependent task `[P]` produces a failed batch.

| Group | Tasks | Why they are genuinely independent |
|---|---|---|
| 1 | T001, T002, T003 | three environment commands, no shared file |
| 2 | T010, T011 | red tests in `tests/test_docsite_layout.py` and `tests/test_check_docs.py` |
| 3 | T012, T013 | greens in `.gitignore` and `scripts/check_docs.py` |
| 4 | T035, T036 | row 13 in `tests/test_build_docs.py`, row 14 in `tests/test_docsite_layout.py`; both after T034 |
| 5 | T043, T044 | red tests in `tests/test_repo_hygiene.py` (row 18) and `tests/test_build_docs.py` (row 21) |
| 6 | T045, T046 | their greens: `README.md`, and `docsite/_static/lernkarten.css` + `docsite/conf.py` |
| 7 | T049, T050, T050a | `tests/test_landing_page.py` (row 22 red), `tests/test_repo_hygiene.py` (row 24 guard) and `tests/test_docsite_layout.py` (row 25 guard) — three files, no shared state |
| 8 | T051, T052 | `.github/workflows/pages.yml` and `CONTRIBUTING.md` |
| 9 | T053, T054, T055 | `docs/testing.md`, a read-through of `docsite/`, a walk of the quickstart |
| 10 | T056, T057, T058 | three read-only gate commands |

### Not parallel

- 🔴 and 🟢 for the same behaviour. Ever.
- Anything touching `docsite/_ext/repolinks.py` — T027, T029 and T031 are three
  branches of one file, written in that order.
- Anything touching `docsite/conf.py` — T019, T027 and T046 each add to it.
- Anything touching `scripts/build_docs.py` — T015 and T024.
- T040, T041, T042 — one workflow and one existing test, in that order.
- T017/T018 and T016 — the constitution amendment is one commit with T015.

---

## Notes

- **Test-first is not waivable.** **Nineteen** rows are red-first; **six**
  (2, 12, 13, 14, 24, 25) are guards and are labelled 🛡️ where they appear. A
  guard asserts the *absence* of a behaviour, and there is nothing to make red
  without first writing the defect — the shape `tests/test_landing_page.py:471`
  already documents. Row 13 is one of them and an earlier draft did not say so:
  research R4 had already measured that it passes on arrival, so calling it
  red-first would have promised a red that could not happen *and* hidden the
  gap it was standing in for — that nothing asserted the three faces had
  actually reached the built site. That assertion is now on row 21 (T044).
- **The four gates must stay four.** `ruff check .`, `ruff format --check .`,
  `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`
  — five command lines, four gates, no sixth line (FR-024, guarded by T050).
- **Never hand-edit a migrated document to make a link work.** Plan finding C1:
  `check_docs.check_links` resolves a relative target against the file system, so
  `../index.html` in `docs/design.md` points at a file that does not exist and
  turns gate #4 red on the commit that writes it. The transform is the mechanism;
  the sources keep the paths they have.
- **No generated content and no tutorial.** 013 adds the reference area, 014 the
  tutorial — as a third and fourth `toctree` entry in `docsite/index.md`, with no
  restructuring (FR-012, contract § 8).
- **English throughout**: code, comments, docstrings, pages, commit messages
  (constitution XIII).
- Commit after each task or logical group, and always at a 🔴 checkpoint — the
  failing run is the artifact constitution XI asks for.
