# Feature Specification: Sphinx documentation foundation

**Feature Branch**: `docs/skill-reference`

**Created**: 2026-09-08

**Status**: Draft (revised — scope split, see *Follow-on features*)

**Input**: User description: "Es gibt keine wirkliche API beschreibung und dokumentation, die webseite verriet nicht wie die einzelnen befehle im detail ausgeführt werden können. gute seiten haben eine übersicht. die sollten wir auch haben. jetzt stellt sich mir aber eine frage: in regulären code können dise aus dem code generiert werden, zum beispiel klassen anhand der docstrings usw. ist sowas auch für skills möglich, wenn ja wäre es nice die auto zu geniereien. vlt sollte jeder skill meta informatiojen dafür zu verfügung stellen. es gibt ein paar solcher dokumentationen die mir am besten gefallen und die ich für dieses projekt auch gerne hätte: 1. Django (python) 2. Pandas 3. numpy — diese sind extrem gut gestaltet, auto generiert und bieten einen echten value. was mir bei pandas und django sehr gut gefällt ist dass es ein sehr gutes tutorial hat und dass die classes, methoden usw. direkt verlinkt sind und man easy hinklicken kann; zudem gibt es noch Themenseiten — das gibt es bei pandas auch (zum Beispiel Visualisierung)."

**Scope note**: the original request is delivered in three features. **This spec is
012, the foundation only**: the toolchain, the theme, the rebuilt publication
workflow, and the migration of the documentation that already exists. It ships a
real, navigable documentation site with **no generated content yet**. The
generated skill/CLI reference is **013**; the tutorial and topic pages are
**014**. Both are recorded in [Follow-on features](#follow-on-features) so they
can be specified later without re-deciding anything.

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: none. All seven steps are *documented*; no step
changes behaviour, and no file a user's project holds is read or written.

**Implementation half**:

- [x] **Deterministic** — Python and configuration under `docsite/`, a dependency
      manifest, a rebuilt `.github/workflows/pages.yml`, and pytest cases. **No
      skill prompt changes in 012**; the `SKILL.md` frontmatter change belongs to
      013.

**Who runs into this**: **both** — the user driving Claude in their own project
(who today cannot find out how a command is actually run without opening the
plugin's `SKILL.md`), and a contributor to this repo (who today finds half the
documentation on a website and half in the repository, with nothing explaining
the split).

## Clarifications

### Session 2026-09-08 — decisions taken before this spec was written

These six were settled in the design conversation this specification came out
of. They are recorded here because the spec carries the decisions but not the
reasoning behind them. None of them is reopened in planning.

- Q: Which static site generator builds the documentation? (FR-001) → A: **Sphinx, with `myst-parser` for the Markdown sources and `pydata-sphinx-theme` for the theme.** Django, pandas and numpy — the three sites named as the target — are all Sphinx, and pandas and numpy both use `pydata-sphinx-theme`, so the look and the mechanics being asked for are the ones this toolchain already produces. Every feature the request praised is a Sphinx feature rather than a theme's: clickable cross-references between entities are domains, a tutorial with flow is a `toctree`, topic pages are the user guide, and search is built in. The property that actually decided it is narrower than any of those: a Sphinx domain makes a reference to something that does not exist a **build failure**, which is the drift protection this feature exists for and which this repository has so far bought with bespoke regex gates written after the drift shipped. `myst-parser` keeps the Markdown that already exists as Markdown, so no source file is converted to reStructuredText.
- Q: Does the generated site absorb `docs/index.html`? (FR-013) → A: **No — the landing page stays the site root, unchanged, and keeps `tests/test_landing_page.py`; the generated site lives under a sub-path.** The landing page is a hand-designed, self-contained file with a test suite of its own. Rebuilding it as a theme template would destroy the design and obsolete those tests, and it would buy nothing: the site needs a home page and already has a better one than a generator would produce. Django is the precedent — a bespoke home page with Sphinx behind it.
- Q: Where does the skill metadata for the generated reference live? → A: **Under the `metadata:` key of the `SKILL.md` frontmatter, as `metadata.docs` — never as new top-level keys.** The Agent Skills standard allows exactly five top-level frontmatter keys — `compatibility`, `description`, `license`, `metadata`, `name` — and rejects anything else, including Claude Code's own extended fields. The evidence is `github.com/anthropics/claude-code` issue #25380, which quotes the validator error `Attribute 'allowed-tools' is not supported in skill files. Supported: compatibility, description, license, metadata, name.` `metadata` is the free-form map the standard provides for exactly this purpose. This is not academic here: lernkarten ships as a Claude Code plugin marketplace, so a frontmatter key the validator refuses breaks an installation rather than a lint. The decision binds **013**, not 012; it is recorded here because this is where the reasoning was established.
- Q: Is the Sphinx extension that documents skills built in this repository, or in a separate public one? → A: **In this repository, with the extraction planned and its trigger written down.** The public artifact worth sharing is the `metadata.docs` **schema**, not the couple of hundred lines that read it — and that schema has no validated design yet. A schema with one consumer is a configuration format, not a standard; lernkarten is that first consumer and has to shake it out. Two repositories moving in lockstep would also add release friction during exactly the phase with the most iteration. So that "extract later" does not quietly become "never", the mitigation is part of the decision: the extension gets its own directory, imports nothing from lernkarten (enforced by a test, not by intent), carries its own tests, and the extraction trigger is written down now — the site live, plus the schema unchanged across one release. `sphinx-agent-skills` and `sphinx-skills` are both free on PyPI.
- Q: Is this one feature or several? → A: **Three.** 012 is the Sphinx foundation, 013 the generated skill and CLI reference, 014 the tutorial and the topic pages. As a single feature nothing would be visible until the very end; split this way each of the three merges something a reader can open.
- Q: How much of the existing documentation moves onto the site? (FR-007) → A: **All of it**, split into a user area (`docs/workflow.md`, the Leitner method page) and a contributing area (`docs/design.md`, `docs/testing.md`, `CONTRIBUTING.md`) — the way Django publishes both. The complaint being answered is that the content is split between the website and the repository for no reason a newcomer can see. A migration that moved only the user-facing half would leave that complaint half-standing, and it would leave the contributor documentation exactly where nobody found it.

### Session 2026-09-08 — answered during clarification

Five gaps found by reading this spec against the repository, and closed here.
Unlike the session above, these were open when the spec was written.

- Q: What happens to the links in the migrated documents that point at repository files rather than at documentation pages? (FR-020, FR-029) → A: **A small transform in the documentation configuration turns an unresolvable repository path into an absolute GitHub URL at build time; the sources keep their relative paths.** Read outside code fences, the five migrated documents carry 31 relative links, and 22 of them point at something that is not a documentation page — `../templates/card.typ`, four `../assets/logo*.svg`, four `../assets/brand/*.typ`, `../assets/fonts/`, `../.specify/memory/constitution.md`, `../CLAUDE.md`, `../README.md#install`, two fixture READMEs, `../specs/002-landing-page-fixes/bugs/BUG-011.md`, and more. Under FR-020 every one of them is a build failure, so this had to be decided before anything could be planned. Rewriting them in the source files was rejected because of what it costs elsewhere: `check_docs.check_links` skips any target beginning with `http` and requires the rest to exist **on the file system**, so hard-coded GitHub URLs would quietly remove two dozen links from the coverage `scripts/check_docs.py` provides today — the weakening SC-005 forbids. Leaving the relative path in the source and resolving it at build time is the only option under which both checks keep doing real work, which is what US4 scenario 3 means by "the two checks overlap deliberately". If the transform turns out to need more than roughly 30 lines, the fallback is hard-coded absolute URLs and the lost `check_docs` coverage is accepted explicitly rather than discovered later.
- Q: Where do the documentation configuration and page sources live, and how do files outside that directory reach the site? (FR-028) → A: **A new `docsite/` directory holds the configuration and the page sources; `docs/` keeps meaning "pages published by hand"; files outside it come in through MyST's `{include}`.** Putting the sources in `docs/` would place a Sphinx root page `docs/index.md` directly beside the landing page `docs/index.html` — two files one letter apart, one of them the site root and the other not, in the directory this feature exists to make legible. The separation also states the rule in one sentence a reviewer can check. **Symlinks are excluded**, and the spec says so rather than leaving it to be discovered: a symlink into the source directory needs developer mode on Windows, against FR-004 and SC-001.
- Q: How does `docs/leitner.html` get a navigation entry when it is not a documentation page? (FR-010, FR-032) → A: **A short Markdown page in the user guide introduces the method and links out to it; `leitner.html` is served only at the site root.** A `toctree` accepts documents and absolute URLs, not a relative `.html` file, so the entry FR-010 requires has no direct mechanism — and an absolute URL would break `file://` viewing, against FR-018. The wrapper gives a real sidebar entry and a real place in the reading order while the designed page stays byte-identical. The second half of the answer settles a question the first half opens: the page is **not** carried into the documentation tree as well, so it has exactly one URL — the one `docs/index.html` and `README.md` already link, and the one PR #105 made the workflow copy.
- Q: May a failing documentation build block the deploy of the landing page? (FR-033) → A: **Yes — the deploy is all-or-nothing — and the documentation build additionally runs in CI on every pull request.** Deploying the landing page without the documentation would leave the site half-updated: a new landing page linking into a stale documentation tree, which is hard to notice and harder to debug, and it is the same class of failure as the 404 PR #105 fixed. The objection to all-or-nothing is that a typo in a contributor document could take the public page offline; the pull-request job removes it, because the build has to be green before anything reaches `main`. FR-023 requires that job anyway, so this costs nothing new.
- Q: What sub-path is the documentation site published at, and what exactly does the landing page link? (FR-013, FR-014, FR-016) → A: **`/docs/`** — in one sentence: `docsite/` generates into `/docs/`. It is the path a reader guesses, and with the sources in `docsite/` the name is free of the clash that made it awkward. The landing page links **`docs/`**, the directory, not `docs/index.html`: it is what a reader would type, it survives a future change of root document, and it keeps the deployed URL free of a filename. That choice is not cosmetic — `test_the_pages_workflow_assembles_every_relative_link` matches the derived reference literally, so the two forms are not interchangeable and the adapted test's rule follows from this one. **On FR-016's "adapted, never weakened"**: what is protected is the *derivation*, not the mechanism. The test must keep deriving its target set from `docs/index.html` and no target may drop out of that set; what it may learn is that a target can also arrive in `_site` by a second route — produced by the documentation build into `_site/docs/` — rather than only by a `cp` line. The set of links checked is unchanged, so this is not a weakening, and FR-016 now says so instead of leaving a reviewer to reconstruct it.

### Session 2026-09-08 — second, adversarial clarification round

The first two sessions asked what was missing. This one tried to break the spec:
requirements checked against each other, and the spec checked against the
repository's own code. Two entries **narrow or widen a requirement written
earlier**, and say so rather than overwriting it silently.

- Q: Does the 15 px floor bind the whole theme, and what happens to the other visual rules `docs/design.md` states? (FR-027, FR-035, FR-036) → A: **Full alignment — and FR-035 is narrowed.** Two errors were found by reading `docs/design.md` instead of the spec. First, in the strict direction: `docs/design.md` line 58 says **"Reading text means Archivo"**, and constitution XVI repeats that the floor does not bind IBM Plex Mono literals or Jost labels. The *Print & Design Impact* bullet ("including code samples and tables") and FR-035's original wording ("every element the theme sets below it") therefore demanded **more than the rule they cite**; both are corrected to Archivo prose only, and a code sample is exempt. *(This narrows FR-035 as it was written on 2026-09-08 earlier the same day. The requirement is not withdrawn — the override is still required — only its scope is corrected to match `docs/design.md`.)* Second, in the loose direction, and much larger: `docs/design.md` §*The screen surfaces* says both existing surfaces are "built from flat colour and type only — **no gradients, no shadows, no rounded corners**", while `pydata-sphinx-theme` styles admonitions, buttons, the search field and the sidebar with radii and shadows by default. So FR-027 was never a type-size job. The decision is full alignment: the three inks, the three faces **self-hosted from `assets/fonts/`** (they are vendored and OFL-licensed, so the landing page's Google Fonts route is not reused), and the theme's shapes flattened. And because a normative document that describes two surfaces while three exist is stale, `docs/design.md` §*The screen surfaces* **gains a row for the documentation site** naming which theme conventions it may keep — a deliberate edit under constitution XVI, not a drive-by.
- Q: Every page the site generates is invisible to `scripts/check_docs.py`. Does that stay true? (FR-037) → A: **No.** `markdown_files()` is extended to cover every Markdown file under `docsite/`, and a test asserts that coverage so it cannot be silently lost. `markdown_files()` globs exactly three things — root `*.md`, `docs/*.md`, `skills/*/SKILL.md` — and `gated_files()` is that list plus `scripts/*.py` and `templates/*.typ`. A new `docsite/` is in neither, so every page 012 writes would sit outside the dead-link check *and* the five drift gates at once: the A7/A8-default token gate, the sheet-capacity gate, the cutting-instruction gate, the borderless-size gate and the print-order gate. Those gates exist because this repository shipped exactly that drift twice, and their own comments say a hand-written grep missed lines and they shipped. The consequence is written into FR-037 rather than left to be discovered: `check_links` resolves a relative link **against the file system**, so pages under `docsite/` may not use extension-less MyST cross-references and write a relative path to the source file **including its `.md` extension** instead. This matters most for **014**, whose tutorial and topic pages will be full of grid and card-size claims.
- Q: Two links resolve on the deployed site and are dead in a local build. Which promise gives way? (FR-018, FR-038) → A: **Neither — the build command assembles a miniature `_site`.** FR-031 retargets `docs/design.md`'s `index.html` to `../index.html` and its `../assets/card-box.pdf` to `../card-box.pdf`, which is right when deployed (from `/docs/`, `../` is the site root) and dead locally (from `docsite/_build/html/`, `../` is `docsite/`). US2 acceptance scenario 5 and FR-018 promise the opposite. Rather than narrowing that promise, the build places `docs/index.html`, `docs/leitner.html` and `assets/card-box.pdf` in the positions they occupy when deployed, so every link resolves in both settings. The second payoff decided it: the local build becomes a **preview a contributor can check FR-014 and SC-007 against before pushing**, instead of those being verifiable only after a deploy. This also settles **FR-019** on `python3 scripts/build_docs.py` — a plain `sphinx-build` cannot assemble anything.
- Q: This feature amends the constitution. How far? (FR-039) → A: **Both principles, inside 012, as a named task.** Principle **VI** carries a fenced dependency graph of every `scripts/*.py`, and `check_import_graph()` derives the real graph from the import statements and **fails the *Skills & docs* CI job** for any module the block does not list — so `scripts/build_docs.py` cannot merge without the edit. Principle **V**'s `docs/` row is a normative table listing four files; a new top-level `docsite/` is outside it. Nothing enforces V, so that half is a governance obligation rather than a red build — which is precisely why it would otherwise be skipped. The overdue correction rides along: Principle V's row, and the constitution as a whole, **never mentions `docs/leitner.html`**, although FR-011 promises that if the file ever moves its gates move with it. A promise about a file the governing document does not know exists is not a promise. The version and the *Last Amended* date are bumped per the governance rule.
- Q: Which success criteria are actually measurable, and does SC-001 still claim three platforms? (SC-001, FR-034, SC-002, SC-004, SC-005, SC-013) → A: **Three platforms — SC-001 stands and FR-034 widens to match it.** *(This widens FR-034, written earlier the same day as Windows-only. The reasoning that made Windows the minimum still holds; it was the minimum, not the target.)* `CONTRIBUTING.md` promises all three platforms work from one ordinary command, and this feature introduces two OS-sensitive points of its own — the path transform in `conf.py` and `{include}` resolution — plus text encoding, which is the same class of problem that already excluded symlinks. A portability claim nothing exercises is a claim rather than a property. On the rest: criteria a command can decide keep their present form; **SC-005** ("unweakened" is a judgement about a diff, not something a command reports) and **SC-013** (a property of the process, not of an artifact) become **numbered manual rows in `docs/testing.md`** — the mechanism constitution XI provides and SC-008 already uses. SC-002 gains a stated method, and SC-004 names its comparison explicitly: **byte-identical HTML output, excluding `.doctrees/` and `.buildinfo`**, because a naive whole-directory compare fails for reasons that have nothing to do with determinism.
- Q: After migration, does `README.md` still send a reader to raw Markdown in the repository? (FR-042) → A: **No — all three references point at the published site.** `README.md` links `docs/workflow.md` (line 79), `docs/design.md` (274) and `docs/testing.md` (288) as repository paths; after migration each is also a published page, and the premise of this whole feature is that a newcomer should not have to know which half of the project a document lives in. The narrower alternative — retarget the two user-facing links and leave the contributor one — was rejected: it reintroduces the split it is meant to remove, one link deep. **Verified against `tests/test_repo_hygiene.py` before deciding**: `test_the_readme_still_names_the_landing_page_source` pins `](docs/index.html)` inside `## The design`, which is a *different* link from `](docs/design.md)` in the same section, so retargeting does not break it and no test is changed. The accepted cost: `check_docs.check_links` skips `http` targets, so those three links leave its file-system coverage — but `REQUIRED_FILES` still requires all three files to exist, so deleting one is still caught.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - All the documentation is in one navigable place (Priority: P1)

Today a reader has to know where to look. The published site is one page,
`docs/index.html`. `docs/workflow.md`, `docs/design.md` and `docs/testing.md` are
Markdown files inside the repository; `CONTRIBUTING.md` is at the root;
`docs/leitner.html` is a second designed page that was, until recently, linked
from the landing page and from the README and served nowhere. Nothing tells a
newcomer that this split exists or why.

They open the site, follow one link off the landing page, and land in a
documentation site with a persistent sidebar and two clearly separated areas: a
**user guide** (how to use the thing) and a **contributing** area (how to work on
it). Everything that was scattered is in one of the two, reachable by browsing
rather than by knowing.

**Why this priority**: this is the user's actual complaint — content split
between the website and the repo for no reason a newcomer can see. It is also
the prerequisite for 013 and 014, which need a site to put pages into.

**Independent Test**: build the site from a clean checkout and assert that every
migrated document is reachable from the site's navigation tree, and that the user
area and the contributing area are separate top-level entries.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** the documentation is built, **Then** the
   navigation contains a user area holding `docs/workflow.md` and the Leitner
   method page, and a contributing area holding `docs/design.md`,
   `docs/testing.md` and `CONTRIBUTING.md`.
2. **Given** the built site, **When** any migrated document is opened, **Then**
   its text is the text of the source file — nothing was retyped or forked into a
   second copy.
3. **Given** `CONTRIBUTING.md`, **When** the repository is browsed on GitHub,
   **Then** the file is still at the repository root where GitHub's contribution
   prompts expect it — the site includes it by reference, it does not move it.
4. **Given** the built site, **When** a page is opened at a viewport of 375 px,
   **Then** it is readable without horizontal scrolling and no reading text
   renders below 15 px.

---

### User Story 2 - Anyone can build the docs locally with one command (Priority: P1)

A contributor wants to see their documentation change before opening a pull
request. There is no docs build today, so there is nothing to run.

They install one requirements file and run one command. The site builds offline,
on Windows, macOS or Linux, with Python 3.12, and opens in a browser from the
filesystem.

**Why this priority**: a documentation system nobody can run locally is a
documentation system that only CI can check, which is how documentation rots.

**Independent Test**: in a fresh virtual environment with only the docs
requirements installed and no network access, run the build command and assert it
exits 0 and produces an index page; run it twice and assert the second run
changes nothing.

**Acceptance Scenarios**:

1. **Given** a fresh checkout and the docs requirements installed, **When** the
   build command runs with no arguments and no network, **Then** it exits 0.
2. **Given** a build that emits any warning, **When** it runs, **Then** it exits
   non-zero — warnings are errors, so a broken reference cannot merge.
3. **Given** an unchanged checkout, **When** the build runs twice, **Then** the
   second run produces the same output as the first.
4. **Given** an environment without the docs requirements, **When** `pytest`
   runs, **Then** the docs-build tests **skip** with a message naming what to
   install, and the rest of the suite passes — the same shape
   `tests/test_e2e.py` already uses for the typesetting engine.
5. **Given** the built site opened from the filesystem, **When** its internal
   links are followed, **Then** they resolve — links are relative, never
   root-anchored.

---

### User Story 3 - The site is published without breaking what was reachable (Priority: P1)

`.github/workflows/pages.yml` today assembles `_site` by copying exactly two
files. That assembly has already produced one live 404: `docs/leitner.html` was
linked from the landing page and from the README and was never copied in. The fix
(PR #105) added a test that derives the relative links out of `docs/index.html`
and requires the workflow to copy each one.

The workflow is rebuilt to build the documentation site and publish it under a
sub-path, with `docs/index.html` still served at the root, unchanged. Nothing
that was reachable before becomes a 404, and the invariant that catches such a
404 still holds.

**Why this priority**: the deployment is the deliverable. A docs site that builds
locally and 404s in production has solved nothing, and this repository has the
scar to prove it.

**Independent Test**: assert the workflow's assembly step places the landing
page, the card box, the Leitner page and the generated site into `_site`, and
that the link-derivation test from PR #105 still passes against the new assembly.

**Acceptance Scenarios**:

1. **Given** the rebuilt workflow, **When** the site is assembled, **Then**
   `docs/index.html` is at the site root, byte-identical to the file in the
   repository.
2. **Given** every relative link in `docs/index.html`, **When** the assembly runs,
   **Then** each target exists in `_site` — the PR #105 invariant, adapted to the
   new assembly shape and never weakened.
3. **Given** the landing page, **When** it is read, **Then** it offers a link
   into the documentation site.
4. **Given** any file that feeds the documentation build, **When** it changes on
   `main`, **Then** the workflow's `paths:` trigger fires and the site
   redeploys.
5. **Given** `tests/test_landing_page.py`, **When** the suite runs after this
   feature, **Then** every existing assertion in it still passes.

---

### User Story 4 - A reference that does not exist fails the build (Priority: P2)

The reason to adopt a documentation system rather than write HTML is that the
system can *check* itself. This repository has already shipped documentation
drift twice — the `--grid` sweep and the A8-default sweep — and both had to be
turned into bespoke regex gates in `scripts/check_docs.py` after the fact.

A contributor writes a cross-reference to a document or section that does not
exist. The build fails and names the file and the reference, before the pull
request is opened.

**Why this priority**: it is the mechanism 013's entire value rests on. Standing
it up in the foundation means 013 inherits checked cross-references rather than
inventing them.

**Independent Test**: add a cross-reference to a non-existent target, build, and
assert the build exits non-zero naming the source file and the target; remove it
and assert the build passes.

**Acceptance Scenarios**:

1. **Given** a document containing a cross-reference to a target that does not
   exist, **When** the site is built, **Then** the build exits non-zero and the
   message names the source document and the missing target.
2. **Given** a document linking a file that has been deleted, **When** the site is
   built, **Then** the build fails rather than publishing a dead link.
3. **Given** the existing dead-link check in `scripts/check_docs.py`, **When**
   the gates run, **Then** it still covers the Markdown sources — the two checks
   overlap deliberately rather than one replacing the other.

---

### User Story 5 - The existing docs gates keep holding (Priority: P2)

`scripts/check_docs.py` carries checks bound to specific files and paths: the
Leitner interval check reads `docs/leitner.html` and compares it against
`scripts/leitner.py` in both directions, and `tests/test_check_docs.py` asserts
that file exists at that path. `tests/test_landing_page.py` asserts against
`docs/index.html` and against `pages.yml`. A migration that moves files silently
turns those gates into no-ops or hard failures.

A contributor runs the four gates after this feature and every one of them still
does what it did, against the same guarantees.

**Why this priority**: a migration that breaks the drift gates while claiming to
prevent drift is worse than no migration. This is a correctness requirement, not
a nicety.

**Independent Test**: run all four existing gates plus the full suite after the
migration and assert nothing was deleted, skipped or loosened; specifically, drop
an interval from the Leitner page and assert `check_docs.py` still reports it.

**Acceptance Scenarios**:

1. **Given** the Leitner method page after migration, **When** an interval that a
   divider prints is removed from it, **Then** `python3 scripts/check_docs.py`
   exits non-zero and names that interval.
2. **Given** the Leitner method page after migration, **When** it mentions an
   interval `scripts/leitner.py` does not define, **Then** the gate reports that
   too — the check stays bidirectional.
3. **Given** the four pre-PR gates, **When** they run after this feature,
   **Then** all four pass, and the pre-PR checklist has gained no fifth command a
   contributor has to remember.

---

### Edge Cases

- **Missing optional tooling**: the docs build must not need a typesetting
  engine, a network connection or a separately installed binary. A contributor
  with Python and one `pip install` must be able to build and read the site.
  (Constitution II.)
- **Docs requirements not installed**: `pytest` must still pass. The docs-build
  tests skip with a message naming what to install, exactly as
  `tests/test_e2e.py` skips without an engine.
- **Fresh install on each platform**: the build runs on Windows, macOS and Linux
  from one ordinary command; the output must contain no absolute paths and no
  platform-dependent path separators.
- **Python floor**: works on 3.12.
- **Encoding**: the migrated documents contain em dashes, ×, °, umlauts and
  typographic quotes, and `docs/workflow.md` contains fenced examples of Typst
  card markup. Output declares UTF-8, and a `#list([…])` example must render as
  text, not as markup.
- **Idempotence**: building twice produces the same output; deleting the build
  directory and rebuilding restores exactly it.
- **Local viewing**: the built index opens from `file://` with working internal
  links.
- **A document that is also a repository file GitHub renders**: `CONTRIBUTING.md`
  is read on GitHub *and* in the site. It has one copy and one location.
- **A hand-written HTML page inside a generated site**: `docs/leitner.html` is
  neither Markdown nor generated. It must survive with its design intact and its
  gates attached, reach the navigation through a wrapper page (FR-032), and be
  served at exactly one URL — the site root, never a second copy under `/docs/`.
- **A theme upgrade that reintroduces a shape**: FR-027 flattens radii, shadows
  and gradients the theme sets. A later version of the theme can style a new
  component the override does not name, so the flattening is written as broadly
  as the theme allows rather than as a list of selectors — the same reasoning
  `tests/test_landing_page.py` gives for stating the type floor as a rule instead
  of a list.
- **A font that is not there**: the three faces are served from the site itself
  (FR-027, SC-014), so the build must copy them out of `assets/fonts/` and the
  stylesheet must declare them. A missing face falls back to a system font and
  the surface silently stops matching the landing page.
- **A link that resolves in a checkout but not on the web**: the migrated
  documents carry 22 links to repository files (`../templates/card.typ`,
  `../.specify/memory/constitution.md`, four `../assets/logo*.svg`, …) and four
  more to things served at the site root. Under warnings-as-errors every one of
  them fails the build unless FR-029 and FR-031 handle it.

## Requirements *(mandatory)*

### Functional Requirements

**Toolchain (settled — not a plan-phase question)**

- **FR-001**: The documentation site MUST be built with **Sphinx**, using
  **`myst-parser`** for Markdown sources and **`pydata-sphinx-theme`** for the
  theme. The rationale is recorded and is not reopened in planning: Django,
  pandas and numpy — the three documentation sites the user named as the target —
  are all Sphinx, and pandas and numpy both use `pydata-sphinx-theme`. Sphinx
  domains give *checked* cross-references (a reference to something that does not
  exist fails the build), which is the drift protection this whole feature exists
  for; `myst-parser` means the Markdown this repository already has stays
  Markdown.
- **FR-002**: The documentation dependencies MUST be **development/CI only**,
  declared in a new **`requirements-docs.txt`**, separate from
  `requirements-dev.txt`. The reason for a third file rather than more lines in
  the second: `requirements-dev.txt` is what every contributor installs to run
  the four gates, and Sphinx plus a theme pulls a large transitive tree
  (docutils, Jinja2, Pygments, Babel, and the theme's own web assets) onto every
  contributor for a task most of them never perform. Separating it lets `pytest`
  stay installable in seconds, lets CI install it only in the docs job, and gives
  the Principle IV review one file to point at.
- **FR-003**: The documentation dependencies MUST NOT be routed through
  `scripts/deps.py`. That is the **runtime** channel, and a user running
  `lernkarten build` must never install Sphinx. This is stated explicitly because
  `CONTRIBUTING.md`'s dependency gates are written for runtime dependencies and a
  reviewer will otherwise apply them here.
- **FR-004**: Every documentation dependency MUST install with a plain
  `pip install` on Windows, macOS and Linux, from wheels, with no compiler, on
  Python 3.12.
- **FR-005**: `lernkarten build`, `lernkarten check` and every other runtime path
  MUST be unaffected: no import of a documentation package from anything under
  `bin/` or from any script a user's run reaches.

**Sources and migration**

- **FR-006**: Existing Markdown documentation MUST stay Markdown. No source file
  is converted to reStructuredText.
- **FR-007**: The site MUST present two separate top-level areas: a **user guide**
  holding `docs/workflow.md` and the Leitner method page, and a **contributing**
  area holding `docs/design.md`, `docs/testing.md` and `CONTRIBUTING.md`.
- **FR-008**: Each migrated document MUST have exactly one copy. The site
  includes the existing file; it does not duplicate, retype or fork it.
- **FR-009**: `CONTRIBUTING.md` MUST remain at the repository root, where GitHub
  reads it, and be pulled into the site from there.
- **FR-010**: `docs/leitner.html` is hand-written HTML with a bespoke design, not
  Markdown. It MUST be **embedded, not converted**: the file stays at
  `docs/leitner.html`, byte-identical, and reaches the navigation through the
  wrapper page FR-032 specifies. Converting it would destroy a designed page and
  detach the gates named in FR-011. It MUST be served at the **site root only** —
  `_site/leitner.html`, the URL `docs/index.html` and `README.md` already link and
  the one PR #105 made the workflow copy. It is **not** carried into the
  documentation tree as a second copy: one page, one URL.
- **FR-011**: The Leitner interval gate in `scripts/check_docs.py`
  (`LEITNER_PAGE`, `check_leitner_intervals`, checked in both directions against
  `scripts/leitner.py`) MUST keep working, and `tests/test_check_docs.py`'s
  assertion that `docs/leitner.html` exists at that path MUST keep passing. If any
  future change moves the file, the gates move with it — they are never weakened
  or deleted.
- **FR-012**: The site MUST NOT contain generated skill or CLI reference content
  in this feature, but its navigation structure MUST accommodate a reference area
  and a tutorial area being added later without restructuring what 012 ships.
- **FR-028**: The documentation configuration and page sources MUST live in a new
  top-level **`docsite/`** directory. `docs/` keeps its present meaning — pages
  published by hand — so the two are told apart in one sentence. Documents that
  live outside `docsite/` (`CONTRIBUTING.md` at the repository root, and the
  existing `docs/*.md`) MUST be pulled in with MyST's **`{include}`**, which
  keeps FR-008's one-copy rule: the file stays where it is and is read from
  there. Two mechanisms are **excluded by name**:
  - **Symlinks** into `docsite/`. They need developer mode on Windows, against
    FR-004 and SC-001, and would fail on a platform this repository supports.
  - A **build-time copy** of the source file into `docsite/`. It produces a
    second file on disk that a contributor can edit by mistake.

  A Sphinx root document inside `docs/` was rejected for a reason worth
  recording: `docs/index.md` would sit one letter from `docs/index.html`, one of
  them the site root and the other not, in the directory this feature exists to
  make legible.

  **`{include}` is forced, not preferred.** `scripts/check_docs.py`'s
  `REQUIRED_FILES` requires `docs/workflow.md`, `docs/design.md`,
  `docs/testing.md` and `docs/index.html` to exist at exactly those paths, and
  fails the *Skills & docs* gate otherwise. So including the files where they lie
  is the only option that keeps the gate green — it is not one of several equally
  good arrangements. This is stated so that a later change does not "simplify" it
  into a move.
- **FR-029**: Links in the migrated documents that point at repository files
  rather than at documentation pages MUST be resolved **at build time** by a
  transform in the documentation configuration, which rewrites an unresolvable
  repository-relative path into an absolute URL to the file on GitHub. **The
  source files keep their relative paths**, so `check_docs.check_links` — which
  skips any target beginning with `http` and requires the rest to exist on the
  file system — keeps checking all 22 of them. Hard-coding the URLs in the
  sources would silently drop those links out of `scripts/check_docs.py`'s
  coverage, which SC-005 forbids; resolving them at build time is what US4
  scenario 3 means by "the two checks overlap deliberately". Requirements on the
  transform:
  - It MUST resolve a path relative to the **source file's own location in the
    repository**, not relative to the page that includes it. `CONTRIBUTING.md`
    writes `docs/design.md` (from the repository root) while `docs/design.md`
    writes `../CONTRIBUTING.md` (from `docs/`); both must resolve.
  - A path that resolves to another **documentation page** MUST become an
    internal cross-reference, not a GitHub URL — `../CONTRIBUTING.md`,
    `docs/design.md`, `testing.md`, `design.md#the-box` and
    `workflow.md#when-something-goes-wrong` all name pages the site carries.
  - It MUST have **its own test**.
  - **Fallback, stated rather than left implicit**: if the transform needs more
    than roughly 30 lines, it is abandoned in favour of hard-coded absolute
    GitHub URLs in the sources, and the resulting loss of `check_docs` coverage
    is recorded as an accepted cost in `plan.md` rather than discovered later.
- **FR-030**: A file a page **renders** rather than links — today
  `assets/pipeline.png` in `docs/workflow.md` and `assets/example-cards.png` in
  `docs/design.md` — MUST be copied into the built site so the image appears. It
  MUST NOT be handled by FR-029's transform: a rewritten URL gives an image that
  loads from GitHub or not at all. Every such asset is an input to the build and
  therefore falls under FR-017's trigger.
- **FR-040**: MyST heading anchors MUST be enabled (`myst_heading_anchors`), to
  a depth that covers the headings the migrated documents already link.
  `docs/testing.md` links `design.md#the-box` (`docs/design.md:234`) and
  `workflow.md#when-something-goes-wrong` (`docs/workflow.md:344`); both target
  headings exist, but without generated anchors both are build failures under
  FR-020. One configuration line, named here because a silent one is how it gets
  missed.
- **FR-041**: The `{include}` of a document from outside `docsite/` MUST resolve
  that document's **relative image paths against the included file's own
  location** (MyST's `relative-images` option or an equivalent). Otherwise
  `../assets/pipeline.png` in `docs/workflow.md` and `../assets/example-cards.png`
  in `docs/design.md` resolve against the including page and the images do not
  appear. FR-030 requires them to appear; this names the mechanism that makes it
  true.
- **FR-031**: Four links in the migrated documents point at things served at the
  **site root**, not at repository files, and MUST be retargeted by hand. They
  are enumerated here so none is missed:

  | File | Link | Problem | Fix |
  |---|---|---|---|
  | `docs/design.md` | `index.html` | From inside `/docs/` this resolves to `/docs/index.html`, not to the landing page at the root | `../index.html` |
  | `docs/design.md` | `../assets/card-box.pdf` | The box is published at the site root as `card-box.pdf`; FR-029 would send the reader to GitHub instead of to the download the landing page offers | `../card-box.pdf` |
  | `docs/workflow.md` | `../README.md#install` | `README.md` is not a site page, and the anchor is a section of it | an absolute GitHub URL, via FR-029 — recorded here because the anchor must survive the rewrite |
  | `docs/workflow.md` | `../CLAUDE.md` (also in `CONTRIBUTING.md`) | Not a site page in 012; a reader following it from the site gets nothing | an absolute GitHub URL, via FR-029 |

  No migrated document links `leitner.html`, so FR-032's single-URL rule has no
  existing link to break.
- **FR-032**: The Leitner method page MUST reach the navigation through a **short
  Markdown page in the user guide** that introduces the method and links out to
  `leitner.html`. A `toctree` accepts documents and absolute URLs, never a
  relative `.html` file, so FR-010's navigation entry has no direct mechanism; an
  absolute URL would break `file://` viewing, against FR-018. The wrapper is not
  a second copy of the content and does not restate it — it is a signpost, so
  FR-008 holds.

**Landing page and publication**

- **FR-013**: `docs/index.html` MUST stay the site root, unchanged in content and
  design, and MUST keep passing every assertion in `tests/test_landing_page.py`.
  The generated documentation site lives under the sub-path **`/docs/`** — the
  arrangement Django uses. In one sentence: **`docsite/` generates into
  `/docs/`**.
- **FR-014**: The landing page MUST link into the documentation site, and the
  link MUST be **`docs/`** — the directory, not `docs/index.html`. It is what a
  reader would type, it survives a later change of root document, and it keeps
  the deployed URL free of a filename. The form is not cosmetic: FR-016's test
  matches the derived reference literally, so `docs/` and `docs/index.html` are
  not interchangeable and the adapted matching rule follows from this choice.
- **FR-042**: `README.md`'s three references to migrated documents —
  `docs/workflow.md` (line 79), `docs/design.md` (274) and `docs/testing.md`
  (288) — MUST point at the **published pages**, not at the repository files.
  After migration each is also a page of the site, and the premise of this
  feature is that a newcomer should not have to know which half of the project a
  document lives in; leaving them would reintroduce the split one link deep. Two
  boundaries hold:
  - **`](docs/index.html)` inside `## The design` does not move.**
    `tests/test_repo_hygiene.py::test_the_readme_still_names_the_landing_page_source`
    pins it, and it is a different link from `](docs/design.md)` in the same
    section — the contributor's reference to the file somebody edits, kept
    deliberately distinct from the reader's reference to the page. Verified
    against the test before this was decided; **no test is changed**.
  - **Accepted cost**: `check_docs.check_links` skips any target beginning with
    `http`, so those three links leave its file-system coverage. `REQUIRED_FILES`
    still requires all three files to exist, so a deletion is still caught.
- **FR-015**: `.github/workflows/pages.yml` MUST be rebuilt to run the Sphinx
  build and assemble `_site` from the landing page, the card box, the Leitner
  page and the built documentation, the last of which lands in **`_site/docs/`**.
- **FR-016**: The invariant added by PR #105 —
  `test_the_pages_workflow_assembles_every_relative_link`, which derives the
  relative links out of `docs/index.html` and requires the workflow to copy each
  one — MUST keep holding. If the assembly step changes shape, the test is
  **adapted, never weakened**. What "adapted, never weakened" protects is the
  **derivation, not the mechanism**, and this spec states the distinction so a
  reviewer does not have to reconstruct it:

  - **Protected**: the test keeps deriving its target set from `docs/index.html`
    itself, and **no target may drop out of that set**. No reference may be
    exempted, allow-listed or filtered out to make the new workflow pass.
  - **Permitted**: the test may learn that a target arrives in `_site` by a
    **second route** — produced by the documentation build into `_site/docs/` —
    rather than only by a `cp` line. The landing page's new `docs/` link (FR-014)
    is exactly such a target, and no `cp` will ever produce it.

  The set of links checked is unchanged, which is why the second route is an
  adaptation rather than a weakening. Any change that shrinks the derived set is
  a weakening and is refused.
- **FR-017**: The workflow's `paths:` trigger MUST cover every input to the
  documentation build — the migrated documents (`docs/*.md`, `CONTRIBUTING.md`),
  the documentation sources and configuration (`docsite/**`),
  `requirements-docs.txt`, every asset a page renders (FR-030), and the workflow
  file itself — so a change to any of them redeploys the site. The existing
  entries (`docs/index.html`, `docs/leitner.html`, `assets/card-box.pdf`) stay.
- **FR-018**: The built site's internal links MUST be relative, so the site works
  under a sub-path and when opened from the filesystem.
- **FR-033**: The deploy MUST be **all-or-nothing**: if the documentation build
  fails, the whole workflow fails and nothing is published, so the site is never
  half-updated — a new landing page linking into a stale documentation tree is
  the same class of failure as the 404 PR #105 fixed, and harder to notice.
  Because that makes a typo in a contributor document able to hold back a
  landing-page fix, the documentation build MUST **also run in CI on every pull
  request**, so the failure is caught before `main` and this case almost never
  fires. FR-023 requires that job anyway, so the mitigation costs nothing new.

**Build behaviour**

- **FR-019**: A single command with no arguments MUST build the whole site, with
  no network access required. **That command is `python3 scripts/build_docs.py`.**
  It was left to `plan.md` in the second clarification session and settled in the
  third: FR-038 requires the build to assemble a miniature `_site`, and a plain
  `sphinx-build` cannot assemble anything. The candidates are kept below because
  the reasoning is what stops the decision being reopened:

  | Candidate | Trade-off |
  |---|---|
  | `python3 scripts/build_docs.py` | Matches the repository's existing `python3 scripts/<name>.py` convention, works identically on all three platforms, and can print the "install `requirements-docs.txt`" message itself when the dependencies are missing. One more file in `scripts/`, which constitution VI's import graph then covers. |
  | A documented `sphinx-build` invocation | No new file. But it is not "a single command with no arguments" — it needs a source and a build directory — and it puts the arguments in a document that can go stale, which is the failure mode this feature exists to remove. |
  | A `lernkarten docs` subcommand | Discoverable through `--help`. Rejected: it puts a documentation concern into the user-facing CLI, against FR-005's boundary — a user running `lernkarten` must never meet Sphinx. |

  **Chosen: `python3 scripts/build_docs.py`.** It is the only candidate that is
  literally one command with no arguments, that keeps the runtime CLI clean, and
  that can do FR-038's assembly. It carries one obligation that is easy to miss
  and is therefore a requirement of its own: a new `scripts/*.py` module must be
  listed in Principle VI's dependency graph or `check_import_graph()` fails the
  *Skills & docs* gate — see FR-039. FR-024 stays intact: this is a local
  convenience and a CI job, never a fifth pre-PR gate.
- **FR-020**: The build MUST treat warnings as errors and MUST be strict about
  references: a cross-reference or link to a target that does not exist fails the
  build, and the message names the source document and the target. The 22 links
  in the migrated documents that point at repository files rather than at
  documentation pages are **not** exempted from this — they are resolved by the
  transform in FR-029, so strictness stays absolute and the migration still
  builds.
- **FR-021**: The build MUST be deterministic and idempotent: the same checkout
  produces the same output, and building twice changes nothing.
- **FR-022**: The build output MUST NOT be committed. The build directory
  (`docsite/_build/`, following FR-028's layout) goes into `.gitignore`,
  consistent with the rule this repository already applies to `output/`
  (constitution IX).
- **FR-023**: Tests that build the documentation MUST **skip** when the
  documentation dependencies are absent, with a message naming what to install —
  the pattern `tests/test_e2e.py` already uses. CI MUST have a job that installs
  them and runs those tests. That job's **id MUST NOT be `docs`**:
  `.github/workflows/ci.yml` already has a job with that id (display name
  "Skills & docs") running `scripts/check_docs.py`, and reusing it produces a
  YAML error discovered as a red CI run rather than at review.
- **FR-024**: The four existing pre-PR gates MUST still pass, and the pre-PR
  checklist MUST gain no fifth command; the docs build is a CI job and a local
  convenience, not a fifth thing to remember. **Gate #1's scope widens on the
  first commit**, and this is recorded so it is not met as a surprise:
  `pyproject.toml` declares no `exclude` for ruff, so `ruff check .` and
  `ruff format --check .` cover `docsite/conf.py` and every extension module from
  the moment they exist, at `line-length = 100` with
  `select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]`. A `conf.py` copied
  from the Sphinx template does **not** pass unmodified. The gate count is
  unchanged; what it reads is not.
- **FR-037**: `markdown_files()` in `scripts/check_docs.py` MUST be extended to
  cover every Markdown file under **`docsite/`** (recursively), and a test MUST
  assert that coverage so it cannot later be lost without a failure. Today the function globs exactly three things
  — root `*.md`, `docs/*.md`, `skills/*/SKILL.md` — and `gated_files()` is that
  list plus `scripts/*.py` and `templates/*.typ`. Every page this feature writes
  would otherwise sit outside the dead-link check **and** all five drift gates at
  once: the A7/A8-default token gate, the sheet-capacity gate, the
  cutting-instruction gate, the borderless-size gate and the print-order gate.
  Those gates exist because this repository shipped that exact drift twice.

  **The consequence for how pages are written is part of this requirement**, not
  something to discover later: `check_links` resolves a relative link **against
  the file system**, so a page under `docsite/` MUST NOT use an extension-less
  MyST cross-reference (`[the workflow](workflow)`). It writes a relative path to
  the source file **including its `.md` extension** (`[the workflow](workflow.md)`,
  `[design.md](../docs/design.md)`), which MyST resolves to the built page and
  `check_links` resolves to the file. This binds **014** hardest: its tutorial and
  topic pages will be full of grid and card-size claims, which is what the drift
  gates read.
- **FR-038**: The build command MUST also assemble a **miniature `_site`**,
  placing `docs/index.html`, `docs/leitner.html` and `assets/card-box.pdf` in the
  positions they occupy when deployed, so that a link out of the documentation
  tree resolves both locally and on the deployed site. Without it FR-031's
  `../index.html` and `../card-box.pdf` are correct when deployed and dead in a
  local build, and US2 acceptance scenario 5 and FR-018 promise the opposite. The
  second reason is worth as much as the first: the local build becomes the
  **preview a contributor can check FR-014 and SC-007 against before pushing**,
  rather than those being verifiable only after a deploy. This is also what
  settles FR-019 — a plain `sphinx-build` cannot assemble anything.
- **FR-039**: This feature MUST amend `.specify/memory/constitution.md`, as a
  named task rather than an afterthought, and MUST bump its version and
  *Last Amended* date per the governance rule:
  - **Principle V** ("Code boundaries") gains a **`docsite/` row**. Its table is
    normative and its `docs/` row lists four files, so a new top-level directory
    is outside it. Nothing enforces Principle V — no test reads it — which is
    exactly why this would otherwise be skipped.
  - **Principle V's `docs/` row additionally gains `leitner.html`.** The
    constitution does not mention that file anywhere, although FR-011 promises
    that if it ever moves its gates move with it. A promise about a file the
    governing document does not know exists is not a promise.
  - **Principle VI** gains a line for **`scripts/build_docs.py`** and its
    imports. This half is not optional and not cosmetic: `check_import_graph()`
    derives the real graph from the import statements in `scripts/*.py` and
    **fails the *Skills & docs* CI job** for any module the fenced block does not
    list.
- **FR-034**: The documentation build MUST run in CI on **Windows, macOS and
  Linux** — all three, matching SC-001 and the promise `CONTRIBUTING.md` already
  makes that all three work from one ordinary command. *(An earlier draft of this
  requirement asked for Windows only. That was the minimum, not the target, and
  it left SC-001 claiming more than anything verified; the widening is recorded
  in the third clarification session rather than made silently.)* A portability
  claim nothing exercises is a claim rather than a property, and this feature
  introduces two OS-sensitive points of its own — the path transform in the
  documentation configuration (FR-029) and `{include}` resolution (FR-028,
  FR-041) — plus text encoding, which is the same class of problem that already
  excluded symlinks.
- **FR-025**: Tests MUST be written first and seen failing (constitution XI).
  Nothing in this feature is model-driven, so the red artifacts are pytest cases:
  against the build, against the navigation tree, against the assembly step in
  `pages.yml`, against `markdown_files()`'s coverage of `docsite/` (FR-037), and
  against the preserved gates. Where the assertable part cannot carry the whole
  requirement, constitution XI asks for a numbered manual row instead of a
  pretended test. This feature adds **three** rows to the checklist in
  `docs/testing.md`, and no more: the type-size floor across the theme (FR-035,
  SC-008), the "gates unweakened" judgement (SC-005) and the deploy policy
  (SC-013). Each is named where it is claimed, so no success criterion implies an
  automated check that does not exist.

**Content rules**

- **FR-026**: Every page MUST stay subject-agnostic — examples demonstrate a
  format, never a field of study (constitution VII) — and MUST be in English
  (constitution XIII).
- **FR-027**: The theme MUST be brought into **full alignment** with
  `docs/design.md`, not merely recoloured. This is larger than it looks:
  `docs/design.md` §*The screen surfaces* says both existing surfaces are "built
  from flat colour and type only — no gradients, no shadows, no rounded corners",
  and `pydata-sphinx-theme` styles admonitions, buttons, the search field and the
  sidebar with radii and shadows by default. Three things are required:
  - **The three inks**, as `docs/design.md` gives them; colour never carrying
    meaning on its own.
  - **The three faces — Archivo, Jost, IBM Plex Mono — self-hosted from
    `assets/fonts/`.** They are vendored in this repository under the Open Font
    License, so the landing page's Google Fonts route is **not** reused: the
    documentation site loads no font from a third party.
  - **The shapes flattened**: no radii, no shadows, no gradients.
- **FR-036**: `docs/design.md` §*The screen surfaces* MUST gain a **row for the
  documentation site**, naming its source (`docsite/`) and which theme
  conventions it is allowed to keep. The table currently describes two surfaces
  while this feature ships a third, and a normative document that describes less
  than exists is stale — the condition the governance rule tells a contributor to
  fix rather than work around. This is a deliberate edit under constitution XVI,
  made with the rest of this feature, not a drive-by.
- **FR-035**: The 15 px floor MUST be reached by a **theme CSS override that
  raises every element carrying Archivo prose that the theme sets below it**, and
  that override MUST be covered by a **numbered row on the manual checklist in
  `docs/testing.md`**. Both halves are required and neither is optional.
  `pydata-sphinx-theme` sets several elements below `1rem` — sidebar captions,
  admonition titles, the footer — so an unmodified theme violates FR-027, SC-008
  and constitution XVI on the day it is installed.

  **The floor binds Archivo prose only.** `docs/design.md` states "Reading text
  means Archivo", and constitution XVI repeats that the type table gives Jost
  labels and IBM Plex Mono literals their own rows and that those are not prose.
  So a **code sample is exempt**, as is a letterspaced label. This is narrower
  than an earlier draft of this requirement, which said "every element the theme
  sets below it" and so demanded more than the rule it cites; the correction is
  recorded in the third clarification session rather than made silently. What is
  *not* narrowed is the obligation: the override is still required, and so is the
  manual row.

  No automated check can see any of it:
  `tests/test_landing_page.py::test_reading_text_is_never_below_the_screen_floor`
  reads the `<style>` blocks of one hand-written file and cannot reach a theme's
  compiled stylesheet. Constitution XI's rule for exactly this case is a numbered
  manual row, so this spec states one rather than implying a gate that does not
  exist.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | none | — |

**No format change.** The `SKILL.md` frontmatter change — a `metadata.docs` block
— belongs to **013**, not to this feature. 012 reads no skill metadata and writes
no generated page.

**Backwards compatibility**: nothing a user has on disk is affected, and no
command changes behaviour. For contributors the only new obligation is one more
optional `pip install` to build the docs locally; without it the suite still
passes, with the docs tests skipped.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: **a new set of published pages** — a third screen
  surface beside the readme and the landing page — plus **one link added to the
  landing page** and three README links retargeted at it (FR-042). The card, the
  press sheet, the mark and the README graphics are untouched, and
  `docs/index.html` keeps its design. `docs/design.md` §*The screen surfaces*
  gains a row for the new surface (FR-036), so the normative document describes
  all three.
- **Theme alignment is the largest visible task**: `docs/design.md` says both
  existing surfaces are flat colour and type — no gradients, no shadows, no
  rounded corners — and the stock theme is none of those things. FR-027 requires
  the three inks, the three faces self-hosted from `assets/fonts/`, and the
  shapes flattened.
- **Black-only laser print still readable**: N/A for the card. The site pages must
  nonetheless not use colour as the only distinction — an "optional step" badge
  needs a word or a shape, not a hue.
- **Minimum type size respected**: **yes** — 15 px is the floor for **Archivo
  prose** on every page. It does **not** bind IBM Plex Mono literals or Jost
  labels, so a code sample and a letterspaced label are exempt; `docs/design.md`
  ("Reading text means Archivo") and constitution XVI both scope it that way, and
  an earlier draft of this section claimed the floor covered code samples, which
  was stricter than the rule it cited. This is **not free**:
  `pydata-sphinx-theme` sets several elements below `1rem`, so the floor costs a
  theme CSS override (FR-035). Its gate is a **numbered manual row in
  `docs/testing.md`**, because no test in this repository can read a theme's
  compiled stylesheet. No automated check is claimed for it.
- **Brand PNGs need re-rendering**: no.
- **Duplex alignment unaffected**: yes — nothing about the PDF changes.
- **Additional**: `docs/design.md` MUST be read before the theme is configured
  (constitution XVI). A stock `pydata-sphinx-theme` beside this project's landing
  page is a visible regression even though nothing on the card moved.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** **No — and that
  is the point of this feature's shape.** Static site generation and checked
  cross-references are solved problems, and constitution III makes reuse the
  default. Sphinx is adopted rather than reimplemented. The one thing this
  project will eventually build itself is the Sphinx extension that documents
  Agent Skills, and that is 013's scope, justified there by the finding that no
  such extension exists.
- **New runtime dependency**: **none.** Nothing reaches `scripts/deps.py`
  (FR-003).
- **New dev dependency**: **yes** — `sphinx`, `myst-parser` and
  `pydata-sphinx-theme`, in a new `requirements-docs.txt` (FR-002). All three are
  pure-Python wheels on PyPI, install with a plain `pip install` on all three
  platforms, and support Python 3.12. The Principle IV vetting table
  (maintenance, licence, transitive tree, wheel coverage, pinning strategy) goes
  in `plan.md`.
- **New external binary**: **none.** A documentation toolchain requiring a
  separate binary install would fail constitution II's friction standard for
  contributors.
- **Anything this makes redundant**: not yet. The hand-written command list in
  `README.md` § "The commands" and the pipeline table in `docs/index.html` become
  candidates for removal in **013**, once something generates them; the bespoke
  drift gates in `scripts/check_docs.py` (`SHEET_CAPACITY`, the A7/A8 default
  tokens, the cutting-instruction check) likewise. 012 removes nothing.
- **Engine version change**: no.
- **Platforms verified**: **all three, in CI** — FR-034 requires the documentation
  build to run on Windows, macOS and Linux, matching SC-001 and the promise
  `CONTRIBUTING.md` already makes. Portability that nothing exercises is a claim
  rather than a property, and this feature adds two OS-sensitive points of its
  own (the path transform, `{include}` resolution) on top of text encoding.
- **Governance change**: **yes** — `.specify/memory/constitution.md` is amended
  (FR-039): Principle V gains a `docsite/` row and the overdue `leitner.html`
  entry, Principle VI gains `scripts/build_docs.py`, and the version and
  *Last Amended* date are bumped. The Principle VI half is enforced —
  `check_import_graph()` fails the *Skills & docs* gate without it — and the
  Principle V half is not, which is why it is a named task.
- **Ordering dependency**: **satisfied.** PR #105 (`fix/pages-site-assembly`) is
  merged — `a28174b` on `main`, merge commit `6ade04a` — and this branch is
  rebased onto it. `.github/workflows/pages.yml` already copies
  `docs/leitner.html` and lists it under `paths:`, and
  `test_the_pages_workflow_assembles_every_relative_link` is present in
  `tests/test_landing_page.py`. The deployed page was verified live after the
  merge. FR-016 therefore adapts an invariant that exists, rather than waiting
  for one.

### Key Entities

- **Documentation source**: an existing repository file included in the site
  unchanged — `docs/workflow.md`, `docs/design.md`, `docs/testing.md`,
  `CONTRIBUTING.md`.
- **Embedded page**: `docs/leitner.html` — hand-written HTML carried into the
  built site as-is, with a navigation entry and its existing gates intact.
- **Documentation area**: one of the two top-level groupings — *user guide* and
  *contributing*.
- **`docsite/`**: the new top-level directory holding the documentation
  configuration and the page sources. It generates into `/docs/`. Distinct from
  `docs/`, which keeps meaning "pages published by hand".
- **Repository-link transform**: the build-time rewrite (FR-029) that turns a
  relative path to a repository file into an absolute GitHub URL, so the source
  files keep the relative paths `scripts/check_docs.py` checks.
- **Wrapper page**: the short user-guide page (FR-032) that gives
  `docs/leitner.html` a navigation entry without converting or copying it.
- **`scripts/build_docs.py`**: the one command (FR-019). It builds the
  documentation and assembles the miniature `_site` of FR-038. Being a
  `scripts/*.py` module, it must appear in Principle VI's dependency graph
  (FR-039).
- **Miniature `_site`**: the local build's copy of the deployed layout — the
  landing page, the Leitner page and the card box in the positions they occupy
  when published — so links out of the documentation tree resolve in both
  settings, and a contributor can preview the site before pushing.
- **Site assembly**: the `_site` tree the publication workflow produces — the
  landing page at the root, the card box, the Leitner page, and the built
  documentation under a sub-path.
- **Docs requirements**: `requirements-docs.txt`, the development/CI-only
  dependency channel, distinct from `requirements-dev.txt` and from
  `scripts/deps.py`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One command with no arguments turns a clean checkout into a built
  documentation site, offline, on Python 3.12, on Windows, macOS and Linux.
- **SC-002**: All five migrated documents — `docs/workflow.md`,
  `docs/leitner.html`, `docs/design.md`, `docs/testing.md`, `CONTRIBUTING.md` —
  are reachable from the site navigation, and each exists in exactly one place in
  the repository. **Method**: a test walks the `toctree` the build produces,
  starting at the root document, and asserts that the set of documents it reaches
  contains a page for each of the five, and that the user area and the
  contributing area are separate top-level branches of it. The `toctree` rather
  than the rendered sidebar, because the sidebar is the theme's rendering of it
  and would tie the assertion to a theme version.
- **SC-003**: A cross-reference or link to a target that does not exist makes the
  build exit non-zero with a message naming the source document and the target.
- **SC-004**: Building twice on an unchanged checkout produces the same output,
  and no build output is tracked by git. **Method**: the **HTML output is
  byte-identical**, excluding `.doctrees/` and `.buildinfo`. Those two are
  Sphinx's own incremental-build state — pickled environment and a configuration
  hash — and a naive whole-directory comparison fails on them for reasons that
  have nothing to do with determinism.
- **SC-005**: Every assertion in `tests/test_landing_page.py` and every check in
  `scripts/check_docs.py` that existed before this feature still passes,
  unweakened — including the bidirectional Leitner interval check and the PR #105
  link-assembly invariant. **"Still passes" is decided by running the suite;
  "unweakened" is a judgement about a diff that no command reports**, so it is
  verified by a **numbered manual row in `docs/testing.md`** (constitution XI):
  the reviewer reads the diff of `tests/test_landing_page.py` and
  `scripts/check_docs.py` and confirms that no assertion was deleted, no target
  dropped out of a derived set, and no condition relaxed.
- **SC-006**: With the docs requirements **not** installed, `pytest` passes, with
  the docs-build tests reported as skipped and naming what to install.
- **SC-007**: The deployed site serves `docs/index.html` at the root
  byte-identical to the repository copy, serves every relative link that page
  makes, and serves the documentation at **`/docs/`**, reachable from the landing
  page's `docs/` link in one click.
- **SC-008**: On a 375 px-wide viewport every documentation page is readable
  without horizontal scrolling, and no reading text renders below 15 px. **This
  criterion is verified by a numbered manual row in `docs/testing.md`, not by a
  test** — the existing floor check reads one hand-written file's `<style>`
  blocks and cannot reach a theme's compiled stylesheet (FR-035).
- **SC-009**: `lernkarten build` and `lernkarten check cards/example.yaml` run
  unchanged in an environment where no documentation dependency is installed.
- **SC-010**: The four pre-PR gates stay green and the pre-PR checklist has the
  same number of commands as before.
- **SC-011**: No migrated document contains a link that resolves only inside a
  local checkout. Every relative link in the five migrated documents either
  resolves to a page of the site, renders as an asset copied into the site, or is
  rewritten to an absolute URL at build time — and every one of them still passes
  `scripts/check_docs.py`'s file-system check in the source file.
- **SC-012**: `docs/leitner.html` appears exactly once in the assembled `_site`,
  at the root, and the user guide reaches it through one navigation entry.
- **SC-013**: A documentation build that fails takes the whole deploy with it —
  nothing is published from a run whose docs build did not succeed — and that
  build has already run on the pull request that introduced the change. The first
  half is asserted against the workflow's shape; the second is a property of the
  process rather than of any artifact, so it is verified by a **numbered manual
  row in `docs/testing.md`**.
- **SC-014**: The built documentation site loads **no sub-resource from a third
  party** — the three faces are served from the site itself, out of
  `assets/fonts/`. The landing page's Google Fonts link is not copied onto the
  new surface.

## Assumptions

- The user is on Python 3.12+; the *reader* of the site needs only a browser.
- The published site is served by GitHub Pages from `pages.yml`. No custom
  domain, no search backend, no versioned documentation trees for old releases.
- Documentation search is out of scope for 012. Django, pandas and numpy all have
  it, and `pydata-sphinx-theme` ships a client-side search — turning it on is a
  later, cheap addition once there is enough content to search.
- Localisation is out of scope: the site is English (constitution XIII), even
  though the user wrote the request in German.
- Intersphinx (cross-project references) is not used in 012; if it is ever added,
  it must not make the build require the network.
- The theme is treated as a **starting point that is overridden**, not as a
  design. `pydata-sphinx-theme` was chosen because pandas and numpy use it and
  because Sphinx's mechanics are what this feature needs; its default visual
  language is not what `docs/design.md` describes, and FR-027 says so.
- The fonts stay vendored. `assets/fonts/` already holds Archivo, Jost and IBM
  Plex Mono under the Open Font License (constitution VIII names them as a
  deliberate exception to the no-binaries rule), so self-hosting them on the new
  surface adds no binary this repository does not already ship.
- `docs/testing.md` and `docs/design.md` are contributor documentation and go into
  the contributing area rather than being hidden — the user explicitly chose
  migrating everything over a user-docs-only site.
- No new corpus and no real subject matter is introduced; anything a page needs by
  way of example comes from the invented demo project (constitution VII).
- Existing behaviour relied on: `scripts/check_docs.py` already walks relative
  Markdown links and already reads `docs/leitner.html`, so both keep working
  against files that have not moved.

## Follow-on features

Recorded here so 013 and 014 can be specified later without re-deciding anything.
**No spec files exist for them yet.**

### 013 — Skill & CLI reference

The generated reference: one entry per skill and per `lernkarten` subcommand, an
overview page, and checked cross-references between them.

- **No existing tool does this.** PyPI and GitHub were searched: there is no
  Sphinx extension — and no MkDocs plugin — that documents Agent Skills /
  `SKILL.md` files. Every hit was the inverse: skills that teach an agent to *use*
  Sphinx. So 013 writes one.
- **Metadata goes in `metadata.docs` inside the `SKILL.md` frontmatter, not in
  new top-level keys.** The Agent Skills standard allows exactly five top-level
  frontmatter keys — `compatibility`, `description`, `license`, `metadata`,
  `name` — and *rejects* unknown ones, hard enough that it also rejects Claude
  Code's own extended fields. Evidence: `github.com/anthropics/claude-code` issue
  #25380, which quotes the validator error `Attribute 'allowed-tools' is not
  supported in skill files. Supported: compatibility, description, license,
  metadata, name.` `metadata` is a free-form map the standard provides for
  exactly this purpose. This matters concretely because this repository ships as
  a Claude Code plugin marketplace.
- **Candidate `metadata.docs` keys**, to be validated in 013 and not fixed now:
  `summary`, `reads`, `writes`, `after`, `before`. `arguments` and
  `argument-hint` already exist as standard fields and should be read from there
  rather than duplicated.
- **The CLI half is free**: `sphinx-argparse` (0.5.2, actively maintained,
  Python >= 3.10, Sphinx >= 5.1) reads the existing `argparse` parsers in
  `scripts/build_pdf.py`, `scripts/cardid.py`, `scripts/figures.py` and others.
- **The extension is built inside this repository, with a planned extraction.** It
  lives in its own directory, imports nothing from lernkarten (enforced by a test,
  not by intent), and has its own tests. The extraction trigger is written down
  now: once the docs site is live and the `metadata.docs` schema has gone one
  release without changing, it is extracted into a standalone package.
  `sphinx-agent-skills` and `sphinx-skills` are both free on PyPI (verified via
  the PyPI JSON API). Rationale for not starting a separate repository today: the
  schema is the real public contract and it has zero validated design so far;
  lernkarten is its first and only consumer and has to shake it out first.
- **A concrete success criterion for 013**: the pipeline order and its file
  mapping is currently hand-maintained in at least four places — `CLAUDE.md:3`,
  two README image alt texts, `docs/workflow.md:9`, plus `docs/index.html`.
  Generating it from `metadata.docs` collapses those to one source.
- **Deferred from 012**: how much of a `SKILL.md` becomes a reference entry — the
  `metadata.docs` block only, or metadata plus rendered sections of the prose
  body. This was FR-004 in the pre-split spec and is 013's to answer.

### 014 — Tutorial & topic pages

The Django-style tutorial and the pandas-style topic pages, written against the
foundation 012 ships and cross-linked into the reference 013 generates.

- The **tutorial** walks the pipeline end to end in order, marks
  `/learning-goal` and `/research-gaps` as optional, and links every command it
  names into its reference entry. `docs/workflow.md` — migrated by 012 — is its
  raw material.
- The **topic pages** explain a theme across several commands without restating
  their argument tables, the way pandas' "Visualization" page does.
- **Topic-page candidate set the user has seen, not chosen yet**: printing &
  grids; card style and Typst markup; the Leitner box; the four file formats;
  learning goals & gaps; use without Claude Code.
- **Deferred from 012**: which topic pages ship. This was FR-015 in the pre-split
  spec and is 014's to answer.
