# Lernkarten Constitution

Most rules below were derived from something already in this repository — the
source is named after each one. Where a rule is documented at length elsewhere,
this file states it once and links out rather than keeping a second copy that
can drift. [CLAUDE.md](../../CLAUDE.md),
[CONTRIBUTING.md](../../CONTRIBUTING.md), [docs/design.md](../../docs/design.md)
and [docs/testing.md](../../docs/testing.md) remain the detailed references.

Principles II, III, IV, XI and XIV were set by decision rather than derived —
they overruled what the repository said at the time. Each is marked *Decided*
and names where it now lives. The repository has since been brought into line;
what is settled and what is still open is in
[Reconciliation](#reconciliation).

## Identity

`lernkarten` is a Claude Code plugin plus a Python command line tool that turns
a knowledge source — a folder, a PDF collection, a Zotero library, a website —
into a print-ready flashcard PDF. MIT licensed, distributed as a plugin through
`.claude-plugin/marketplace.json`.

The pipeline is seven steps, two of them optional: `/learning-goal` →
`/sources` → `/ingest` → `/catalog` → `/research-gaps` → `/cards` → `/print`.
Every feature belongs to one of those steps or to the machinery under them.

`/learning-goal` and `/research-gaps` are skippable by design. A project with no
`goal.md` behaves exactly as it did when the pipeline was five steps, which is
what keeps the optional pair honest: they have to earn their place on every run
rather than being imposed on users who do not want them.

**Who the user is**: someone already running Claude Code. That is the audience
this project actually has, and it is a *somewhat technical* one — a person who
can run a terminal command and install a package. Principles II–IV follow from
that and from nothing else.

## Core Principles

### I. Two halves, coupled only by file formats

The pipeline splits into a **model-driven half** (`/sources`, `/ingest`,
`/catalog`, `/cards` — implemented as prompts in `skills/*/SKILL.md`) and a
**deterministic half** (`/print` and everything below it — `bin/lernkarten`,
`scripts/*.py`, `templates/*.typ`).

The two halves never call into each other's internals. Their entire contract is
five file formats:

| Artifact | Format |
|---|---|
| `goal.md` | the learning goal: frontmatter (`goal`, `kind`, `depth`, `updated`), `## Required topics` grouped into `### <Area>`, `## Out of scope`. Optional — absent means the pipeline behaves as it did before it existed |
| `sources.yaml` | source register; every entry has a unique kebab-case `id`. `type: research` is written by `/research-gaps` and carries the `gap` it closes instead of a `path`/`url` |
| `knowledge/<source-id>/<document>.md` | text with one frontmatter block (`source`, `path`/`url`, `ingested`) |
| `catalog/topics.md` | topics (`##`) and subtopics (`###`), each with a description and references into `knowledge/`. Optional per subtopic: `Status: gap` \| `out of scope`, `Parents:` (every topic it belongs under, primary first), `Related:`; optional per topic: `Also covers:`. Every one absent means the pre-goal behaviour |
| `cards/<topic-slug>.yaml` | `topic`, `language`, `cards[]` with `subtopic`, `front`, `back`, optional `source` |

Changing one of these five formats is a breaking change: it touches the skill
that writes it, the script that reads it, `scripts/check_project.py`, the demo
project and the docs. Treat it as such.

The catalog is a **graph**, not a tree: containment is many-to-many, so a
subtopic may name several `Parents:`. It stays two levels deep and edges run
only topic → subtopic, so the graph is bipartite and no cycle can form — there
is nothing to check for acyclicity. What does need checking is reciprocity,
because the failure this format invites is half an edit.

*Source: `skills/`, `scripts/`, `docs/testing.md` ("The pipeline has two
halves"), `CLAUDE.md` conventions.*

### II. Dependencies are allowed — friction is not *(Decided)*

The original rule was "standard library only", and its reason was **usability**:
a non-technical person should not have to install anything. That reason no
longer holds. This is a Claude Code extension; the user already has a terminal
and a working Claude install. Optimising for someone who has neither costs real
quality and buys nothing.

So the rule is no longer "no dependencies". It is **no friction**:

> A dependency is acceptable when a user on Windows, macOS or Linux gets it with
> one ordinary command and no further work.

The supported Python floor is **3.12** (`requires-python = ">=3.12"`), which is
part of this principle rather than incidental to it: the floor decides which
libraries are eligible at all. It has already been set twice by that fact — off
3.9 because it was end of life, then off 3.11 because PyYAML publishes no
`win_arm64` wheel for cp311 and Windows on ARM is a platform the engine
supports.

Concretely, to be acceptable a Python dependency must:

- install from PyPI with a plain `pip install`, on every supported Python
  version, on **Windows, macOS and Linux** — the three are equal, none is an
  afterthought;
- ship **prebuilt wheels for all three platforms**, or be pure Python. An
  sdist-only package that needs a C/C++/Rust toolchain to build is *friction*
  and is rejected, however good it is;
- need no system package manager (`apt`, `brew`, `choco`), no manual `PATH`
  edit, no post-install step, no compiler;
- work offline once installed.

For **external binaries** (not Python packages) there are exactly two
acceptable shapes:

1. **Self-fetching and checksum-pinned**, the way `scripts/engine.py` handles
   Typst: the tool downloads the pinned build for the platform on first use and
   verifies its SHA-256. `engine.py` already covers Darwin arm64/x86_64, Linux
   x86_64/aarch64 and Windows AMD64/ARM64 — that is the pattern to copy.
2. **Genuinely optional**, where absence degrades the path or skips the test but
   never fails it — the way `pdftotext` is treated today.

A binary the user must install by hand for a *core* path is neither, and is not
acceptable.

Every dependency still has to clear Principle IV before it goes in.

**Delivery.** There is no install step between `/plugin install` and the skills
calling `bin/lernkarten` — no virtualenv, no `pip` hook, just whatever Python the
user has. A runtime dependency therefore has to fetch itself, or permitting one
on paper does not make it shippable.

`scripts/deps.py` does that: pinned requirements, installed once into a cache
directory keyed by Python version and machine, reported by
`lernkarten deps --check`. Two details are load-bearing rather than incidental:

- **`pip install --target`, not a virtualenv.** `python3 -m venv` needs
  `ensurepip`, which Debian and Ubuntu ship separately as `python3-venv`. A
  bootstrap that can fail with "now apt-get something" would breach the rule
  above on the most common Linux family there is.
- **`--only-binary :all:`.** A package with no wheel for the user's platform
  fails loudly instead of compiling on their machine. The friction rule,
  enforced rather than merely written down — and it has already changed a
  decision, by moving the Python floor off 3.11.

*Decided. Reconciled in `CONTRIBUTING.md` ("Dependencies"), `CLAUDE.md`,
`pyproject.toml`, `requirements-dev.txt`, `README.md` and `docs/index.html`, and
implemented in `scripts/deps.py`.*

### III. Reuse over reimplementation *(Decided)*

Do not reinvent the wheel. If a maintained library or tool does the job, and it
clears Principles II and IV, **use it** rather than writing our own.

This reverses the old default. Hand-rolling is now the exception and needs a
stated reason in the plan — "it was fun" and "it is only 200 lines" are not
reasons. Legitimate ones: nothing suitable exists; every candidate fails II or
IV; the need is a three-line slice of a library that would drag in thirty
packages.

Areas where a library is almost always the right answer: parsing and emitting
file formats (YAML, HTML, DOCX, PDF, images), text extraction, HTTP, encoding
detection, date handling.

Two pieces of this repository existed *only* because of the rule this principle
replaces. Both are gone:

- `scripts/minyaml.py`, 222 lines of hand-written YAML parser, is now
  `scripts/yamlio.py` — a thin layer over PyYAML that owns the error message and
  the bootstrap and nothing else.
- the `sips`/`magick` shell-out in `scripts/make_testdata.py` is now Pillow, a
  development dependency.

Neither was removed automatically. Each was a normal change: spec, plan,
tests-first, pull request. What the retired rule no longer buys is an argument.

*Decided. Stated in `CONTRIBUTING.md` ("Dependencies") and carried out in
`scripts/yamlio.py` and `scripts/make_testdata.py`.*

### IV. Dependency quality gates *(Decided)*

Permission to add dependencies is not permission to add *any* dependency. Every
new one — runtime, dev, or a self-fetched binary — is vetted against all of the
following before it is declared. Record the answers in the plan; a dependency
that cannot be justified in a few lines is not understood well enough to adopt.

**Maintained**

- A release within roughly the last 12 months.
- Issues and pull requests are being triaged, not piling up unanswered.
- Not archived, not deprecated, not "looking for a maintainer".

**Production-ready**

- A stable release line. No alpha, beta or release candidate.
- Either ≥ 1.0, or a pre-1.0 package with a long, obviously stable track record
  and wide adoption.

**Actually used by others**

- Meaningful download volume and real dependent projects. A package with a
  handful of weekly downloads is a liability, not a shortcut.

**Trustworthy provenance**

- Identifiable maintainer or organisation, and a public source repository.
- Release history on PyPI matches that repository; published artifacts
  correspond to the tagged source. Prefer projects with signed or attested
  releases.
- **Name is not a typo-squat** of something popular. Check the character-level
  spelling against the package you actually mean.
- No install-time scripts that build, download or phone home.

**Licence** compatible with this project's MIT licence.

**Proportionate cost**

- A shallow transitive tree. A library that pulls thirty packages to solve one
  function fails this gate; copy the three lines instead (that is a legitimate
  Principle III exception).
- Import cost does not visibly slow a cold `lernkarten` invocation.

**No known unfixed advisory** at the time of adoption.
`.github/dependabot.yml` already watches this repo; keep it covering whatever
manifest declares the dependency.

**Declared honestly**

- Every declared dependency is actually imported somewhere. Unused dependencies
  get deleted, not left "in case".
- Each one carries a version bound and a one-line comment saying what it is for.
- Developer *tools* are pinned exactly, the way `ruff==0.16.2` already is, so
  formatting never shifts under a contributor. Runtime *libraries* get a
  compatible range, so users are not held to one patch release.

A dependency that stops meeting these — abandoned, or an advisory with no fix —
is a defect to be scheduled, not a fact of life.

*Decided. Extends `.github/dependabot.yml` and the existing exact pin of ruff in
`requirements-dev.txt`.*

### V. Code boundaries

| Directory | Holds |
|---|---|
| `bin/lernkarten` | the user-facing entry point; dispatches `build`, `check`, `engine` |
| `scripts/*.py` | flat, importable modules — the whole implementation |
| `skills/<name>/SKILL.md` | one prompt per pipeline step, terse and action-oriented |
| `templates/card.typ`, `templates/cards.typ` | the card and the press sheet |
| `assets/brand/*.typ` | brand graphics, rendered to PNG by `scripts/render_brand.py` |
| `tests/` | pytest modules plus the shared fixture corpus |
| `docs/` | `workflow.md`, `design.md`, `testing.md`, `index.html` (the landing page) |

New code goes into an existing module where one fits. A new file under
`scripts/` needs a reason and a module docstring in the established style: what
it does, the commands that invoke it, and why it exists.

*Source: repository layout, `scripts/check_docs.py` `REQUIRED_FILES`.*

### VI. The script dependency graph stays acyclic

`scripts/` is flat: modules import each other by bare name after
`bin/lernkarten` inserts the directory on `sys.path`. The current direction of
travel is:

```
deps, engine               ← leaves, import nothing local
yamlio                     → deps (only to bootstrap PyYAML)
build_pdf                  → engine, yamlio
check_project              → build_pdf, yamlio
check_docs                 → yamlio
make_testdata              → engine
demo                       → make_testdata
render_brand               → engine
zotero_ingest, zotero_stub → (no local imports)
```

No cycles, and no import from `scripts/` into `tests/`. Whatever sits at the
bottom of this graph must stay a leaf, because everything depends on it — today
that is `deps` and `engine`. The rule survived Principle III retiring `minyaml`:
`yamlio` took its place and reaches only for `deps`, and only to install the
parser it wraps.

*Source: the import statements in `scripts/*.py`.*

### VII. The repo holds tools, never knowledge

This is a public, subject-agnostic repository. `sources.yaml`, `knowledge/`,
`catalog/`, `cards/` (except `example.yaml`) and `output/` are gitignored on
purpose, enforced by `.githooks/pre-commit` and asserted by
`tests/test_repo_hygiene.py`. Never override that with `git add -f`.

The single exception is `tests/fixtures/demo-project` — a miniature project
about an invented archipelago, written for this repo. Extend it when you need
test material, and keep inventing rather than quoting.

Examples and docs demonstrate a *format*, not a field of study.

*Source: `.gitignore`, `.githooks/pre-commit`, `tests/test_repo_hygiene.py`,
`CONTRIBUTING.md` ("Ground rule: no content in the repo").*

### VIII. No committed binaries

The binary test material — PDFs, the scan, the JPEG, the DOCX, the Zotero
attachments — is *generated* from Typst sources in
`tests/fixtures/demo-project/generators/` by `scripts/make_testdata.py`. So the
whole test corpus stays reviewable as text and the git history stays free of
blobs.

The one deliberate exception is the brand PNGs under `assets/`, which are
committed because nobody should have to run a renderer to read the README.

*Source: `.gitignore`, `scripts/make_testdata.py`, `docs/testing.md`
("generated, not versioned"), `scripts/render_brand.py`.*

### IX. Sources of truth, never generated artifacts

- The card layout is `templates/card.typ`; the press sheet
  `templates/cards.typ`. Never the PDF, never a generated intermediate.
- Brand graphics are `assets/brand/*.typ`; re-render with
  `python3 scripts/render_brand.py` after touching them or the card.
- Nothing in `output/` is ever hand-edited — changes go through the YAML.

*Source: `CLAUDE.md` ("Never hand-edit anything in `output/`"), `docs/design.md`
("edit the Typst source, never a generated file").*

### X. The skill contract

Every skill is `skills/<name>/SKILL.md` with YAML frontmatter carrying:

- `name`, identical to the folder name;
- `description` of at least 20 characters that contains the word `Triggers` and
  names them — without triggers Claude Code finds the skill less reliably.

A skill describes a procedure, not a theory: terse and action-oriented.
`python3 scripts/check_docs.py` enforces all of this, plus that every relative
markdown link in the docs resolves and every expected open-source file exists.

*Source: `scripts/check_docs.py`, `CONTRIBUTING.md`.*

### XI. Test-first (NON-NEGOTIABLE) *(Decided)*

Write the test first. Watch it fail. Then make it pass. Red → green → refactor.

A test written after the code passes tells you the code does what it does. Only
a test that was seen failing tells you it does what was *asked*. This project
now requires the second kind.

**In the deterministic half** (`scripts/`, `bin/`, `templates/`): a pytest case
at the level `docs/testing.md` prescribes — unit, ingest, e2e, contract — is
committed failing, for the *right reason*, before the implementation. "Fails
with ImportError" does not count as red; make it fail on the assertion.

**In the model-driven half** (`skills/`): a prompt has no unit test, so the
test-first artifact is a **check in `scripts/check_project.py` plus a case in
`tests/test_check_project.py`** that fails against what the current prompt
produces. Then change the prompt until it passes. If no failing check can be
written, the requirement is not yet specified sharply enough — go back to the
spec, do not go forward to the prompt.

**Bug fixes**: reproduce first. The failing test names the culprit and stays in
the suite forever.

**Layout and design**: the assertable part still comes first — page count, card
count, an overflowing card reported rather than shrunk, an exit code. Whether it
*looks* right is not a pytest question and belongs on the manual checklist in
`docs/testing.md`.

**Run output**: the same carve-out, for the same reason. A requirement satisfied
only by what a skill *says* during a run — an advisory line, a count, a warning
naming what is missing — leaves nothing on disk, so no `check_project.py` check
can be written that fails against it. The artifact is identical either way.
Those requirements go on the manual checklist and are **named there**, never
left implicit. This is a narrow exception and it is not a licence: if a
requirement changes a file, it is assertable and the clause above applies. When
in doubt, ask what a test would open — if the answer is "nothing", it belongs
here; if the answer is a path, it does not.

**Spikes** are allowed, and are thrown away. Explore in a scratch branch, learn
the answer, then build it test-first. A spike is never promoted straight to a
pull request.

Test placement is unchanged and still follows `docs/testing.md`:

| Module | Level |
|---|---|
| `test_yamlio.py`, `test_engine.py`, `test_build_pdf.py` | unit, no typesetter |
| `test_deps.py` | the dependency bootstrap: no package, no pip, a failing pip |
| `test_testdata.py` | the generator; that the scan really has no text layer |
| `test_ingest_sources.py` | the web source over a local server, zotero over the stub |
| `test_e2e.py` | runs `bin/lernkarten` as a subprocess and takes the PDF apart |
| `test_check_project.py` | the artifacts of the four model-driven steps |
| `test_repo_hygiene.py` | no user content, no committed binaries |

Where new work belongs: a new **build feature** → a case in `tests/test_e2e.py`;
a new **failure mode** → a file in `tests/fixtures/demo-project/broken/`, a row
in that folder's README, and a case proving the error names the culprit; a new
**rule about what the skills write** → `scripts/check_project.py` +
`tests/test_check_project.py`; new demo cards → update `DEMO_CARD_COUNT`.

Tests needing the typesetting engine **skip** rather than download 30 MB unasked
(`LERNKARTEN_E2E=1` opts in); tests needing `pdftotext` skip where it is absent.
Extend the demo project — never start a second corpus.

*Decided. Reconciled in `docs/testing.md` ("Write the test first") and
`CLAUDE.md`.*

### XII. Quality gates

Four commands, all green before every pull request. CI runs the same:

```bash
ruff check . && ruff format --check .       # lint + format
pytest                                     # tests
lernkarten check cards/example.yaml        # card schema + PDF build
python3 scripts/check_docs.py              # skill frontmatter + doc links
```

Plus, once, before a pull request that touches the pipeline:

```bash
python3 scripts/make_testdata.py                                  # binary test material
LERNKARTEN_E2E=1 pytest tests/test_e2e.py                         # fetches the engine
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

ruff config is normative and lives in `pyproject.toml`: line length 100,
`select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]`. Do not loosen it
per-file without a comment saying why.

*Source: `CONTRIBUTING.md`, `docs/testing.md`, `.github/workflows/ci.yml`.*

### XIII. English everywhere

Code, comments, docstrings, docs, commit messages and skill text are English.
The *cards a user generates* are of course in the language of their sources —
which is what the `language:` key in each card file is for, and why nobody has
to remember a flag at print time.

*Source: `CLAUDE.md` ("The project language is English"), `CONTRIBUTING.md`.*

### XIV. Branch model and commits *(branch naming Decided)*

`main` is protected: direct pushes are rejected server-side, and
`.githooks/pre-push` stops them before the round trip (install once with
`scripts/install-hooks.sh`). Every change goes through a branch and a pull
request with green CI.

**Branch names are `<prefix>/<short-kebab-case>`.** Always a prefix, always a
slash:

```
fix/card-margin
feat/zotero-collection-filter
docs/design-bands
ci/windows-matrix
```

Prefixes are the commit prefixes: `fix/`, `feat/`, `skill/`, `build/`, `docs/`,
`ci/`, `test/`, `design/`. Bare names in the existing history (`e2e-testing`,
`landing-responsive`) are legacy — do not copy them.

Commit subjects are short, imperative and prefixed the same way: `skill:`,
`build:`, `docs:`, `ci:`, `test:`, `design:`, `fix:`, `feat:`.

*Branch naming decided, and now written into `CONTRIBUTING.md` ("Branch model")
and `CLAUDE.md`. Protection from `.githooks/pre-push`.*

### XV. The engine is pinned

The cards are typeset with Typst — one self-contained binary, fetched once on
first build and verified against a checksum, so nobody installs a document
toolchain. Version and per-platform SHA-256 live in `scripts/engine.py`, for all
six supported platform pairs. When you bump the version, bump **every**
platform's checksum with it. `LERNKARTEN_ENGINE` points at a binary of your own
and bypasses all of it.

This is also the reference implementation of Principle II's self-fetching
pattern. A future binary dependency should look like this one.

*Source: `scripts/engine.py`, `CONTRIBUTING.md`.*

### XVI. Design rules

Read [docs/design.md](../../docs/design.md) before changing anything visible —
the card, the mark, the readme graphics, the landing page. The rules that hold
across all of them:

- The card is 105 × 74.25 mm landscape (A7), three bands that never move.
- Colour never carries meaning on its own; every colour is doubled by a shape
  or a position. A black-only laser print has to work.
- Reading text is never smaller than 11 pt printed or 15 px on screen.
  *Reading text* is Archivo — the type table in `docs/design.md` gives Jost
  labels and IBM Plex Mono literals their own rows, and those are not prose.
  A note beside a heading and a caption under a sample are prose and are
  bound by the floor; a letterspaced label is not. The floor is scoped, not
  relaxed.
- The layout never shrinks type to fit — a card whose text does not fit is
  *reported*, not silently squeezed.

If a change makes the card prettier on screen and worse on a photocopier, it is
the wrong change.

*Source: `docs/design.md`.*

### XVII. Card style

One card = one fact. Front at most ~2 lines, back at most ~6 — two cards beat
one overloaded card. Active recall prompts ("What…?", "Why…?", "Name…"), never
yes/no. `front`/`back` are **Typst** markup, not LaTeX, written in single
quotes. Card language follows the source unless the user says otherwise, and
always goes into the file's `language:` key.

The full escaping and maths rules are in [CLAUDE.md](../../CLAUDE.md) and apply
to contributions too.

*Source: `CLAUDE.md` ("Card style"), `cards/example.yaml`.*

## Reconciliation

The Decided principles once contradicted files still in the repository. Most of
that is now settled, on two branches stacked on `e2e-testing`:

- `docs/dependency-policy` — the floor (since raised to 3.12), and the policy
  written into `CONTRIBUTING.md` (a new "Dependencies" section with the gates),
  `CLAUDE.md`, `pyproject.toml`, `requirements-dev.txt`, `README.md` and
  `docs/index.html`; test-first written into `docs/testing.md` and `CLAUDE.md`;
  branch naming written into `CONTRIBUTING.md` and `CLAUDE.md`.
- `ci/windows-matrix` — windows-latest legs on the `test`, `cards` and `e2e`
  jobs, advisory at first and blocking once the bugs they found were fixed.

### Settled

| # | Was | Now |
|---|---|---|
| II | `CONTRIBUTING.md` "the standard library only … is a bug" | replaced by the friction standard and the quality gates |
| II | `README.md` / `docs/index.html` promised no `pip install` ever | still say nothing needs installing today, without pledging it |
| II | `pyproject.toml` comment claimed nothing from PyPI | it now says why the list stays empty: nobody pip-installs a plugin, so `scripts/deps.py` holds the real requirements |
| II | floor `>=3.9`, end of life | `>=3.12`, with the ruff target and CI matrix moved in step |
| II | Windows unverified by CI | windows-latest legs on three jobs, blocking a merge like the others |
| XI | `docs/testing.md` gave placement, not ordering | a "Write the test first" section, including the prompt-change case |
| XIV | history had bare branch names | `<prefix>/<name>` documented in `CONTRIBUTING.md` and `CLAUDE.md` |

### Still open

| # | Item | Why it is still open |
|---|---|---|
| IV | dependencies are pinned by version, not by hash | `engine.py` refuses a binary whose SHA-256 does not match; pip is trusted on TLS and PyPI alone. `--require-hashes` would close the gap at the cost of a per-platform hash table to maintain on every bump |

Each open item is a normal piece of work: spec, plan, tests-first, pull request.
None of them is something this constitution changes on its own.

## Governance

This constitution is the normative summary; where it links out, the linked file
carries the detail. The repository and this file now agree — the open items in
[Reconciliation](#reconciliation) are unfinished *work*, not disagreements about
the rule.

- Every derived rule traces to something in the codebase. A rule that no longer
  does is stale and should be removed, not worked around.
- Amendments go through a pull request like anything else.
- Adding a dependency requires the Principle IV answers in the plan, and a
  reviewer who read them. This is the gate that replaces "no dependencies" —
  it only works if it is applied.
- A **runtime** dependency reaches the user through `scripts/deps.py`, so it
  must be pinned exactly and must have a wheel for every supported platform.
  `--only-binary :all:` will refuse it otherwise, at the user's expense rather
  than the reviewer's.
- Principle VII (no content in the repo) additionally requires an explicit note
  in the pull request description saying what changed and why.
- Principle XI is not waivable per-change. "I'll add the test after" is how a
  suite stops meaning anything.
- The four gates in Principle XII are enforced by CI; the merge is blocked
  otherwise.
- Complexity must be justified. A flat `scripts/` directory and a shallow
  dependency tree are still the goal — Principles II–IV loosened *what may be
  imported*, not *how much may be built*.

**Version**: 2.4.0 | **Ratified**: 2026-08-17 | **Last Amended**: 2026-08-19

*2.4.0 — principle XVI's type floor now says what it binds. "Reading text is
never smaller than 11 pt printed or 15 px on screen" was written about the card,
where every word is reading text; on a screen there is a register between prose
and a label that the sentence had no vocabulary for, and each contributor
decided for themselves. Feature 002's specification shows one of them deciding
three incompatible ways in a single document — exempting the band note,
recording it as below the floor, and certifying the page as compliant — while
`docs/index.html` sat under the floor in six places. The floor is **scoped, not
relaxed**: it binds Archivo prose, and the type table in `docs/design.md` is
what makes Jost labels and Plex Mono literals a different thing rather than an
exception. Scoping it also made it assertable, which is why it is now a test
(`tests/test_landing_page.py`) rather than a sentence. See
[BUG-006](../../specs/002-landing-page-fixes/bugs/BUG-006.md).*

*2.3.0 — the goal-driven catalog. Principle I's contract is now **five**
formats, not four: `goal.md` joins it, `sources.yaml` gains the `research`
type, and `catalog/topics.md` gains `Status:`, `Parents:`, `Also covers:` and
`Related:` — all optional, so every artifact written before this still
validates. The catalog is therefore a bipartite graph rather than a tree, which
adds reciprocity invariants and no acyclicity check. The Identity pipeline is
seven steps, two optional. Principle XI's layout carve-out is extended to run
output, because four requirements in this feature (the no-goal advisory, the
catalog counts, the out-of-scope count, the gap warning) are satisfied by what a
skill says rather than by what it writes, and XI as written would have called
them under-specified rather than sending them to the manual checklist where they
belong.*

*2.2.0 — the floor moved to 3.12, decided by a dependency rather than by
taste: PyYAML has no cp311 win_arm64 wheel and Windows on ARM is a supported
platform. Principle II's delivery half is now built (`scripts/deps.py`, via
`pip install --target` rather than a virtualenv, because ensurepip is not
universal). Principle III's two hand-rolled leftovers are gone — `minyaml` to
PyYAML, the `sips`/`magick` shell-out to Pillow — so Principle VI's leaves are
now `deps` and `engine`.*

*2.1.0 — set the Python floor at 3.11 and recorded the delivery mechanism as the
gating half of Principle II (a runtime dependency cannot ship until
`bin/lernkarten` bootstraps a cached virtualenv). Reconciled the repository with
the Decided principles; the section is now Reconciliation, split into settled and
still open.*

*2.0.0 — breaking. Reversed the zero-dependency rule (II), added reuse-first
(III) and dependency quality gates (IV), made test-first mandatory (XI),
mandated `<prefix>/<name>` branch names (XIV). Principles renumbered: old
III–XV are now V–X, XII–XIII, XV–XVII.*
