# Implementation Plan: Practitioner material, goal fit, and source discovery

**Branch**: `feat/goal-fit-sources` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-goal-fit-sources/spec.md`
(GitHub issue #44, status *Clarified*: 6 user stories, 40 numbered requirements
with FR-028 withdrawn — 39 active, 17 success criteria, four clarification
rounds, no open markers)

## Summary

Make practitioner material — incident post-mortems, case studies, engineering
blogs — usable, by wrapping judgement around the existing fetch. `/sources`
reads `goal.md` and says what it expects a source to contribute or warns that it
serves nothing the goal asks for; `/ingest` records the recognition on disk as
`nature: experience`, which `/catalog` and `/cards` read so a single company's
outage is carded as evidence about that case rather than as a general rule; and
`/sources` gains a **discovery mode**, entered only when the user asks for it at
invocation, that proposes candidate sources and writes nothing until the user
picks.

The discovery mode is specified in two layers (spec round 3). **C1** is the
discovery contract and is **material-class neutral**: it holds for any kind of
source and mentions none. **C2** is the addenda — what one class of material
additionally requires of its credibility sentence — and this feature ships
**exactly one**, the practitioner-material addendum (FR-019). The plan carries that
split into the gates: the neutral contract and the addendum are asserted by
*separate* checks (FR-039), so [issue #43](https://github.com/mhabedank/lernkarten/issues/43)
can attach a research-literature addendum later by adding a check rather than by
editing a neutral one. **Nothing about #43 is implemented here** — no arXiv, no
new source type, no bibliographic identity.

Round 4 changed two things and neither adds behaviour beyond one field. The term
**addendum** replaces round 3's contract jargon everywhere, which is editorial —
the check function this plan proposes is renamed with it. And FR-017 gains one field: every
candidate names **which class of material it is**. That class is prompt-level run
output — no vocabulary, nothing validated, nothing on disk, and not the `nature:`
key of FR-015 — and it exists because the run already determines the class (the
C2 addendum could not fire otherwise). **FR-040 records what is deliberately not
built**: choosing which classes discovery *searches* is a second axis, out of
scope here, with FR-017's class as the hook a later filter would attach to. This
plan ships **no filter, no class-selection argument and no class vocabulary**.

The technical approach is almost entirely prompt work with deterministic gates
around it. One format key is added (`nature:`, optional and additive), two
scripts gain checks, five `SKILL.md` files change, the demo fixture gains one
invented experience report, and `docs/testing.md` gains the named manual rows
that constitution XI's run-output carve-out requires. **No new dependency, no
new module, no new pipeline step, and nothing printed changes.**

## Technical Context

**Language/Version**: Python `>=3.12` (`pyproject.toml`), ruff targeting `py312`.
Unchanged by this feature.

**Secondary language**: Typst — untouched here. Nothing this feature does
reaches `templates/`, `assets/brand/` or the build.

**Runtime dependencies**: `pyyaml==6.0.3` via `scripts/deps.py`. **Unchanged.**

**Dev dependencies**: `pytest`, `ruff==0.16.2`, `pillow`, `pyyaml`. **Unchanged.**

**Optional external tools**: `pdftotext`. Irrelevant here.

**Storage**: plain files. This feature adds **one optional frontmatter key** to
one of them and nothing else. `sources.yaml` is byte-for-byte the same format it
is today — see [contracts/sources-yaml-unchanged.md](contracts/sources-yaml-unchanged.md).

**Testing**: pytest. The two modules that move are
`tests/test_check_project.py` and `tests/test_check_docs.py`.
`tests/test_e2e.py` moves **one constant and two assertions**: `DEMO_CARD_COUNT`
goes 32 → 33, and the two divider cases that held only because 32 is a multiple
of 16 are rebuilt on the Tides subset — see § Risks and tasks T031/T033 for the
arithmetic. `tests/test_check_project.py` additionally carries a literal
`counts["cards"] == 32` that moves with it. Test-first is mandatory and the
split between the two gates is fixed by FR-030 / FR-031 / FR-032 — it is not
re-litigated here.

**Lint/format**: ruff, line length 100, unchanged.

**Typesetting engine**: unchanged. This feature never invokes it.

**Target Platform**: Windows, macOS, Linux. Nothing platform-specific is added;
the network access discovery uses is Claude Code's own.

**Project Type**: CLI tool + Claude Code plugin. The centre of gravity is the
plugin half.

**Performance Goals**: unaffected. `check_project.py` gains one membership test
per knowledge document, one five-name key test per source entry, and one set
intersection per subtopic.

**Constraints**: every project on disk must validate unchanged; a project with
no `goal.md` must see no new behaviour at all; the pipeline stays at **seven**
steps.

**Scale/Scope**: ~3 new constants (`NATURES` and `VERDICT_KEYS` in
`check_project.py`) and **eight** new check functions in `check_docs.py`. Two of those eight are pairs a single function could not report
separately: the discovery check is **two** functions — the neutral C1 contract
and the C2 practitioner addendum — because FR-039 requires them separable, and
the wave-E silence check is **two** — a negative token gate over the five other
skills (FR-037's four, plus `skills/learning-goal/SKILL.md`, case E2a) and a
positive gate on `skills/sources/SKILL.md` — because the two
assertions have opposite polarity and one function cannot say which of them
broke. ~48 new test cases; 5 skills edited (one of them roughly tripling in length) and
a sixth, `skills/learning-goal/SKILL.md`, **read** by a gate but not edited;
5 new or edited fixture files; **25** new rows in `docs/testing.md` — 20 `/sources`
rows (4a–4s plus 4n-i) plus 5 pipeline rows (8m, 9f, 12-iv, 12-v, 12-vi).
`check_project.py` gains **two** validations, not one: the `nature:` membership
test of FR-015 and the verdict-key refusal of FR-007.

## Dependency Decisions

**No dependency change.** No runtime package, no dev package, no external
binary, nothing removed.

### Reuse check (constitution III)

**Is anything being hand-rolled here?** **No.** Answered in full in
[research.md § R6](research.md#r6--is-a-library-or-a-dependency-needed-anywhere-here):

- `goal.md` is read with the existing `frontmatter()` / `parse_goal()` helpers
  in `check_project.py`, and as prose by the skills — which is exactly what
  `/catalog` and `/cards` already do.
- `sources.yaml` goes through `scripts/yamlio.py`, unchanged.
- `nature:` is one tuple and one membership test beside `CONTENT_STATES` and
  `VISUAL_KINDS`. There is no parser here to write or to import.
- Discovery reaches the network through the web access Claude Code already has,
  the way `/research-gaps` does. No HTTP client, no crawler, no install step for
  the user.
- The negative doc gates use `re`, already imported by `check_docs.py`.

If implementation finds that a dependency *is* needed, that is a stop-and-flag
back to this plan, not a `pip install`.

### Vetting (constitution IV)

Not applicable — no dependency is proposed, so there is no table to fill.

**Removals**: none.

## Constitution Check

*GATE: passed before Phase 0 research; re-checked after Phase 1 design — see
[Post-design re-check](#post-design-re-check).*

| # | Gate | Pass? |
|---|---|---|
| I | The two halves stay coupled only through the file formats | ⚠ **yes, with work.** One format changes: `knowledge/*.md` frontmatter gains `nature:`. That is a breaking-change-shaped edit by Principle I's own definition, so it carries the full list with it — skill, script, `check_project.py`, demo project, docs. All five are in the file list below. `sources.yaml` and `cards/*.yaml` are untouched, which keeps `build_pdf.py` and the card template out of this feature entirely |
| II | **(GATED)** New dependency installs cleanly everywhere | ✅ **n/a** — none proposed |
| III | **(GATED)** Nothing hand-rolled that a library does | ✅ see Reuse check above |
| IV | **(GATED)** Vetting table completed | ✅ **n/a** — none proposed |
| V | Code lands in an existing module | ✅ **no new file under `scripts/`.** See [Structure Decision](#structure-decision) |
| VI | Import graph acyclic; leaves stay leaves | ✅ unchanged. No new import edge in either direction |
| VII | **(GATED)** No user content; examples stay subject-agnostic | ⚠ **yes, with work.** The demo fixture is **extended, never duplicated** — one invented archipelago incident write-up. Nothing is quoted from anyone. The goal-fit assessment is scoped by FR-004 to *this source for this goal*, never to a subject or a publisher, so the repo acquires no opinion about anyone's field. **Needs the explicit note in the PR description** |
| VIII | No binaries committed | ✅ the new fixture material is markdown text. No generator needed |
| IX | Typst sources edited, never generated files | ✅ **n/a** — nothing visible changes |
| X | Skill frontmatter valid | ⚠ **yes, with care.** `skills/sources/SKILL.md`'s `description` gains discovery. It must keep `name: sources`, ≥ 20 characters, the word `Triggers`, and the domain word `flashcard` — all four asserted by `check_skills` (`scripts/check_docs.py:79-121`) |
| XI | **(NON-WAIVABLE)** Every behaviour tested first | ✅ see [Test plan first](#test-plan-first). Every requirement has either a red assertion or a **named** manual row, and the constitution's own run-output carve-out is what the manual rows sit in — this feature *uses* that clause rather than being ahead of it, unlike feature 001 which had to add it |
| XII | The four gates pass; ruff not loosened | ✅ plus `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` once, because the fixture card count moves |
| XIII | English throughout | ✅ |
| XIV | Branch `<prefix>/<short-kebab-name>`; `main` untouched | ✅ `feat/goal-fit-sources` |
| XV | Engine version unchanged | ✅ untouched |
| XVI | `docs/design.md` read before a visible change | ✅ **n/a.** Nothing visible changes: seven steps stand, `assets/brand/*.typ` and the three PNGs are untouched, `scripts/render_brand.py` is not run, the landing-page step strip keeps its layout. `docs/design.md` is not a gate for this feature (spec.md § Print & Design Impact, closing paragraph) |
| XVII | Card style and Typst escaping respected | ✅ the one new demo card follows `CLAUDE.md` like any other |

**Open-item check**: this feature does not touch the constitution's one
[Still open](../../.specify/memory/constitution.md#still-open) item —
dependencies pinned by version rather than by hash. It neither closes it nor
works around it, because it adds no dependency.

## Project Structure

### Documentation (this feature)

```text
specs/011-goal-fit-sources/
├── plan.md                              # this file
├── research.md                          # Phase 0 — the three deferred items, and three more
├── data-model.md                        # Phase 1 — three entities that never touch disk, one that does
├── contracts/
│   ├── knowledge-frontmatter.md         #   the one format change: `nature:`
│   ├── sources-yaml-unchanged.md        #   the negative contract, written down so it survives
│   └── discovery-proposal.md            #   the output contract of the discovery mode
├── quickstart.md                        # Phase 1 — how to prove it works
├── checklists/requirements.md           # already present, from /speckit-specify
└── tasks.md                             # Phase 2 — NOT created by /speckit-plan
```

No `bugs/` folder yet, and none is manufactured.

### Source Code (repository root)

Only the rows this feature touches. Everything omitted is untouched.

```text
scripts/
├── check_project.py        # ← NATURES; nature: validation in check_knowledge;
│                           #   VERDICT_KEYS; the FR-007 refusal in check_sources;
│                           #   the experience-only subtopic set threaded to check_cards
└── check_docs.py           # ← 8 new checks on skills/*/SKILL.md, wired into main();
                            #   the discovery pair is neutral contract + practitioner
                            #   addendum, the silence pair is negative token gate
                            #   (five other skills, incl. learning-goal)

skills/
├── sources/SKILL.md        # ← piece A (goal fit) + piece C (C1 neutral discovery
│                           #   contract, C2 practitioner addendum) + piece D (silence)
├── ingest/SKILL.md         # ← writes nature: experience
├── catalog/SKILL.md        # ← reads it; FR-013 material-base warning, FR-014 rule-vs-case
├── cards/SKILL.md          # ← reads it; FR-011 attribution, FR-012 scale
└── research-gaps/SKILL.md  # ← line 17: the stale "only step that reaches the network"

tests/
├── test_check_project.py   # ← waves A and B, plus the literal card count of wave H
├── test_check_docs.py      # ← waves C–G
├── test_e2e.py             # ← DEMO_CARD_COUNT, and the two divider assertions
│                           #   that held only at a multiple of 16 (§ Risks)
└── fixtures/demo-project/
    ├── raw/field-notes/<incident>.md        # NEW — invented, committed text
    ├── knowledge/field-notes/<incident>.md  # NEW — carries nature: experience
    ├── catalog/topics.md                    # ← one subtopic, experience-only
    ├── cards/signals.yaml                   # ← exactly one card, with source:
    └── README.md                            # ← the row saying what the new material is for

docs/
├── testing.md              # ← 25 named manual rows, each carrying its FR number,
│                           #   plus row 5's file count — counted, not incremented
└── workflow.md             # ← Step 1 ordering sentence, Step 2 both jobs, Step 5 the seam

README.md                   # ← the /sources table row names both jobs
```

**Not touched, deliberately**: `bin/lernkarten`, `templates/*.typ`,
`assets/brand/*.typ`, the three rendered PNGs, `scripts/render_brand.py`,
`scripts/build_pdf.py`, `scripts/demo.py`, `scripts/make_testdata.py`,
`.specify/memory/constitution.md`, `CLAUDE.md`, `docs/design.md`,
`docs/index.html`, `tests/test_landing_page.py`, `tests/test_repo_hygiene.py`.

### Structure Decision

**No new module under `scripts/`, and no new option on `scripts/demo.py`.**

`check_docs.py` was the alternative to a new file, and it wins on the rule the
constitution states directly: *"what a skill says to the user, or what its own
`SKILL.md` must contain"* goes in `check_docs.py`. That file already owns
`skills/*/SKILL.md` (`check_skills`, `read_skill`), already has the two shapes
the new checks need — a positive substring gate
(`check_print_skill_relays_setup`, `:363-374`) and a paragraph-scoped negative
gate (`check_print_order`, `:561-572`) — and already has the `read_skill` seam
its tests monkeypatch. Eight small functions beside the thirteen already there
is the established shape; a `check_skill_contracts.py` would be a new import
edge and a second place to look.

`check_project.py` takes the `nature:` work for the mirror-image reason: it is a
key a skill writes **into a user's project**. `NATURES` sits beside
`CONTENT_STATES` (`:47`) and `VISUAL_KINDS` (`:54`) because it is the same kind
of thing, and the experience-only subtopic set travels the road `sparse` already
travels — `check_knowledge` → `check_catalog` → `check_cards` — rather than
inventing a second mechanism for the same shape of fact.

**`scripts/demo.py` gains no `--goal-kind` / `--no-goal` option.** It would exist
to save a human two keystrokes inside a step that is manual anyway, and it would
need its own test. The checklist rows edit one word of the scratch copy instead.
Reasoning in [research.md § R2](research.md#r2--exercising-fr-005s-kinddepth-weighting-on-one-fixture).

### The two halves

**Model-driven work** (`skills/`) — five prompts:

| Skill | What changes | Red artifact, written first |
|---|---|---|
| `sources` | grows from 55 lines to roughly 160: a `## Goal fit` section (piece A), a `## Finding sources` section written **class-neutral** (piece C1) — including the line that makes every candidate name which class of material it is, in words, with no list to choose from — and the practitioner addendum as its own clearly separable sub-section (piece C2, FR-019), the explicit-request rule (piece D), the archive-reach sentence, the `/research-gaps` seam, and a `description` that names both jobs | waves C, D, E in `check_docs.py` |
| `ingest` | writes `nature: experience`, and says when **not** to | wave F |
| `catalog` | reads it; the material-base warning of FR-013's four contents and the rule-versus-case report (FR-014) | wave F |
| `cards` | reads it; attribution through the existing `source:` key (FR-011), keeping the scale (FR-012), and **the same FR-013 material-base warning `/catalog` carries** — the requirement binds both steps | wave F, plus wave B in `check_project.py` |
| `research-gaps` | one paragraph: line 17's exclusivity claim is replaced by the real distinction | wave G |

None of that is verifiable by reading it. The verification is the assertion in
`check_docs.py` written **first**, failing against what today's prompt says.
Where a requirement has no such assertion it is a *reporting* requirement, and
those are named rows in `docs/testing.md` — the plan does not pretend they are
automated.

**Deterministic work** (`scripts/`):

- `check_project.py` — `NATURES`, the `nature:` validation in `check_knowledge`,
  `VERDICT_KEYS` and the FR-007 refusal in `check_sources`, the experience-only
  subtopic derivation, and the FR-011 attribution error. Covered by
  `tests/test_check_project.py` waves A and B.
- `check_docs.py` — eight check functions and eight lines in `main()`. Covered by
  `tests/test_check_docs.py` waves C to G.

**The seam**: **one** of the six formats —
`knowledge/<source-id>/<document>.md` frontmatter, which gains an optional
`nature:` key. `sources.yaml` gains nothing (the negative is a contract file of
its own, so it survives a refactor), `catalog/topics.md` gains nothing,
`cards/*.yaml` gains nothing, `goal.md` gains nothing, `figures/` gains nothing.
That is what keeps `build_pdf.py`, `templates/card.typ` and everything printed
outside this feature.

## Phase 0: Research

Six questions, answered in full in [research.md](research.md). The decisions:

1. **A goal written after the sources are registered** (deferred item 1) —
   **accept the gap explicitly. No back-fill.** Every route to one breaks
   something settled: re-assessing on a listing is FR-008 verbatim; assessing
   only the "not yet assessed" needs a verdict-shaped key that FR-007 refused;
   making `/learning-goal` do it contradicts the spec's own Scope statement that
   `/learning-goal` is untouched. What ships is one **gated** sentence in
   `skills/sources/SKILL.md` saying the assessment happens at registration and a
   later goal does not re-judge the register, plus one ordering sentence in
   `docs/workflow.md` Step 1.
2. **Exercising FR-005's `kind`/`depth` weighting** (deferred item 2) — **two
   named manual rows against a `scripts/demo.py` scratch copy, each changing one
   word of the scratch `goal.md`** (`depth: working` → `awareness` for the
   weigh-down, → `expert` for the weigh-up). The committed fixture keeps its
   single pair, nothing new is committed, and no second corpus exists at any
   point.
3. **How many candidates discovery shows** (deferred item 3) — **at most 3 per
   goal area, at most 10 per run, every area listed including the empty ones.**
   The cap has to be per-area first or FR-027's grouping defeats itself.
4. **The explicit request is spelled `/sources --discover`**, with the
   natural-language equivalents listed as the same entry. The spelling is
   load-bearing: `--discover` appears nowhere in the repository today, so it is
   an exact token for the FR-037 negative gate, where a bare `discover` would
   fire on `skills/catalog/SKILL.md:67` and `scripts/build_pdf.py:745`.
5. **FR-034's negative gate is scoped to the exclusivity claim**, not to the
   words "reaches the network" — which appear innocently at `CONTRIBUTING.md:82`.
   The `check_print_order` paragraph-scoped shape, with an exclusivity regex.
6. **No library and no dependency is needed anywhere.** Recorded above under
   Reuse check.

## Phase 1: Design

Artifacts: [data-model.md](data-model.md), [contracts/](contracts/),
[quickstart.md](quickstart.md).

The design decisions that constrain implementation:

- **Absence is never a finding.** `nature:` absent means nothing was claimed —
  not that the document is *not* an experience report. This single rule is the
  whole of FR-031's compatibility promise, SC-013's middle clause and US2
  scenario 5, and it is written as a regression guard (A3) rather than left to
  fall out of the code.
- **"Experience-only" means *all* references, not *any*.** A subtopic with one
  incident write-up and three handbook chapters may legitimately carry a card
  stating the handbook's general rule, and demanding attribution there would be
  wrong. US3 scenario 3 says *"a subtopic whose only references are experience
  reports"*, and that is the set derived. B3 is the test that pins it.
- **The FR-011 attribution failure is an `error`, not a `warn`.** `check_cards`
  already warns "no source reference" for every card without one (`:1097-1098`),
  so a warning would say nothing new and `--strict` would flatten the
  distinction. The stricter severity is also free: no project on disk carries
  `nature:` yet, so the error cannot fire on anything that exists today.
- **The verdict is derived state and stays out of the file.** No `fit:`, no
  `assessed:`, no timestamp on a `sources.yaml` entry. Written down as a
  contract rather than as an absence, so a future "just a small note on the
  entry" has something to argue with.
- **The advisory never gates.** An off-goal source is registered anyway with the
  warning shown, and the run does not pause to ask. The precedent to copy for
  tone is `skills/catalog/SKILL.md:60-67` — said once, "do not turn it into a
  warning and do not repeat it".
- **The discovery contract is written neutral, and the addendum is a separate
  paragraph and a separate check.** The `## Finding sources` section of
  `skills/sources/SKILL.md` states C1 without naming a class of material; the
  practitioner addendum (FR-019) is its own sub-section, so
  `check_sources_skill_carries_the_discovery_contract()` can assert the neutral
  contract and `check_sources_skill_carries_the_practitioner_addendum()` the addendum,
  and neither has to read the other's text. That is one check function split into
  two, not a new behaviour: the same assertions run, grouped so that issue #43
  adds a third function and edits none of the existing ones (FR-039, SC-016).
  **Nothing of #43 is built here** — no arXiv or OpenAlex backend, no new source
  type, no DOI/author/year/venue/citation frontmatter. #43 inherits FR-023's
  paywall rule from C1 rather than restating it, so the two features do not
  disagree about openly accessible material.
- **The candidate's class of material is a phrase, not a field with a
  vocabulary.** FR-017 makes every candidate say which class of material it is;
  the prompt gives examples — an experience report, research literature, a
  reference work, a standards document, a public dataset, a magazine or trade
  article — and explicitly allows a candidate to name a class the examples do not
  cover. There is **no** `CLASSES` tuple, no validation, no key on disk, and no
  relationship to `NATURES` beyond both being about what a thing is: `nature:` is
  closed, validated and written by `/ingest` onto a *stored* document, whereas
  this is prose about a source that has not been registered at all. Check **D8**
  asserts that the class is named, never which classes exist. **The filter this
  hook is for is not built here** (FR-040): no class-selection argument, no way
  to ask discovery for one class only, and nothing that reads a class back.
- **The landing page's step strip is a label, not a description.**
  `docs/index.html:489-492` gives `/sources` five words naming what it writes.
  US6 scenarios 2 and 4 enumerate the README, `docs/workflow.md` and
  `skills/sources/SKILL.md` as the places that must name both jobs, and the
  spec's Print & Design Impact protects the strip's layout explicitly. So
  `docs/index.html` is **not** edited, and `tests/test_landing_page.py` stays
  green untouched. This is a scoping decision and it is recorded here rather
  than discovered in review.
- **Error messages name the culprit**, matching the existing style. Every new
  message names the file, and the card index or the skill at fault.

### Test plan first

The order the assertions go red in. Each line is one test that must fail **on
its assertion** — not on an ImportError — before the code beside it exists.

Wave G is the natural first commit: G3 is red against the **shipped repository**
the moment it is written, with no fabrication at all.

**Wave G — the stale network claim** *(FR-034, SC-010 — start here)*

| # | Assertion that goes red | Then implement |
|---|---|---|
| G1 | a doc claiming "the only step that reaches the network" is reported, naming the file | `check_network_claim_is_not_exclusive()` over `gated_files()`, paragraph-scoped |
| G2 | *guard*: `CONTRIBUTING.md:82`'s "even reaches the network:" does **not** fire | the exclusivity-scoped regex, not a bare substring |
| G3 | *shipped-repo*: the check passes on this repository | rewriting `skills/research-gaps/SKILL.md:17-19` to the real distinction |

**Wave A — `nature:` on disk, and the verdict that never lands on the entry** *(FR-015, FR-031, SC-013 · FR-007, SC-001)*

| # | Assertion | Then implement |
|---|---|---|
| A1 | a document with `nature: anecdote` is reported, naming the document, the value **and** the allowed set | `NATURES` + the membership test in `check_knowledge` |
| A2 | a document with `nature: experience` produces no finding | |
| A3 | *regression guard*: a project whose documents carry no `nature:` at all exits 0 with **no errors and no warnings** | — (must be green from the start) |
| A4 | *fixture guard*: the shipped demo project still passes `check --strict` | — |
| A5 | a `sources.yaml` entry carrying `fit:` is an **error** naming the entry id and the key — and the same, parametrised one case per name, for `assessed:`, `goal_fit:`, `discovered:` and `proposed_by:` (FR-007) | `VERDICT_KEYS` + the refusal in `check_sources` (`:317-370`), placed before the `type` branch so an unknown type still gets the finding |
| A6 | *no-regression guard*: an entry carrying `login:`, `pattern:`, `pages:`, `depth:` or `note:` is unaffected, and the shipped fixture's `login: true` entry still passes | — (must be green from the start) |

**A5 rejects five key names, never unknown keys in general** — and that is the
whole of the decision. `check_sources` reads `id`, `type` and the type's
required field and ignores every other key today; `login:` relies on that. An
allowlist of permitted keys would invalidate `login:`, would invalidate every
project on disk carrying a key this repo has not thought of, and would be a
behaviour change no requirement asks for. FR-007 forbids a **verdict** on the
entry, not extensibility. The five names are the ones
[contracts/sources-yaml-unchanged.md](contracts/sources-yaml-unchanged.md)
§ *The change* already enumerates. Its "no timestamp" clause is **not** gated,
because a timestamp has no fixed key name; that half stays on row 4g.

**Wave B — the experience-only subtopic and attribution** *(FR-011, SC-009)*

| # | Assertion | Then implement |
|---|---|---|
| B1 | a card under a subtopic **all** of whose references are `nature: experience` documents and which carries no `source:` is an **error**, naming the file, the card index and the subtopic | the `experience` set returned by `check_knowledge`, threaded through `check_catalog` into `check_cards` |
| B2 | the same card **with** `source:` passes | |
| B3 | a subtopic with one experience reference **and** one ordinary reference does not make its cards errors | the "all, not any" rule |
| B4 | *regression guard*: `test_a_minimal_project_is_clean` and the counts are unchanged by the new return values | — |

**Wave C — piece A in the prompt** *(FR-001 – FR-009, FR-029, FR-030)*

| # | Assertion | Then implement |
|---|---|---|
| C1 | a `sources` skill that never names `goal.md` is reported | `check_sources_skill_reads_the_goal()` |
| C2 | one that names `goal.md` but never says the assessment is **advisory** / never blocks is reported | |
| C3 | one that does not say the assessment happens **at registration** and is not re-run on a listing is reported | (FR-008 + [research R1](research.md#r1--a-goal-written-after-the-sources-are-registered)) |
| C4 | one that does not state the archive reach — `depth: 1`, the index page plus same-domain linked posts, capped at 20 — is reported | `check_sources_skill_states_the_archive_reach()` |
| C6 | one that does not say an off-goal warning names the source `id` **and** the `goal.md` line it conflicts with is reported (FR-003) | one more case inside `check_sources_skill_reads_the_goal()` — **no new function** |
| C7 | one that does not say the assessment reasons from `kind`/`depth` **and says which of the two it used** is reported (FR-005) | ditto |
| C8 | one that does not say that with no `goal.md` there is no assessment and **at most one** `/learning-goal` pointer per run is reported (FR-006) | ditto |
| C9 | one that does not say the skill never invents a claim about a source it has not looked at, and says so where it reasons only from the URL, the `note` and the `type`, is reported (FR-009) | ditto |
| C5 | *guard*: the edited shipped skill passes C1–C4 and C6–C9 | the `## Goal fit` section |

**C6–C9 assert that the rule is stated in the prompt, and nothing more.** They
are the answer to the review's W-3: T014 writes all four of those sentences into
`skills/sources/SKILL.md` anyway, and a sentence in a file is assertable by
exactly the substring shape that holds FR-002's "advisory" — so leaving them
ungated was a choice with no argument behind it. What they buy is **drift
detection**: after this feature, an edit that drops one of the four fails a gate
instead of failing nothing. What they do **not** buy is the behaviour. C6 cannot
see a warning, C7 cannot see which of `kind`/`depth` a run reasoned from, C8
cannot count a run's pointers, and C9 cannot see an invention. Each keeps its
named row, and the routing table below says both halves rather than letting the
check column read as coverage.

**Wave D — piece C in the prompt: C1 the neutral contract, C2 the practitioner addendum** *(FR-016 – FR-027, FR-030, FR-033, FR-039, FR-040)*

Two checks, not one, because C1 and C2 have to fail separately (FR-039, SC-016).
D1 – D5 and D8 are the **neutral** contract and none of them may mention a class
of material; D6 is the **practitioner addendum** and is the only check that does.

| # | Assertion | Then implement |
|---|---|---|
| D1 | a `sources` skill with no `--discover` at all is reported | `check_sources_skill_carries_the_discovery_contract()` — **C1, neutral** |
| D1a | one carrying everything **but** the found/shown counts grouped by area, every area listed including the empty ones, is reported (FR-027) | |
| D1b | one missing the caps — ≤ 3 per area, ≤ 10 per run — is reported (R3) | |
| D1c | one missing "one sentence, never a number" for credibility is reported (FR-018) | |
| D1d | one missing the paywalled/login-gated rule is reported (FR-023) | |
| D1e | one missing "never propose a source already in `sources.yaml`" is reported (FR-024) | |
| D1f | one missing "no `goal.md` ⇒ nothing to search for" is reported (FR-025) | |
| D1g | one missing "no network ⇒ report, write nothing, exit clean" is reported (FR-026) | |
| D1h | one missing "picked entries go through the ordinary registration path" is reported (FR-020) | |
| D1i | one missing "the network is reached **only** in discovery mode" is reported (FR-033) | |
| D2 | one missing the "writes nothing until the user picks" rule is reported | |
| D3 | one missing the "never invent" rule is reported | |
| D4 | one missing the refusal to write into `knowledge/`, or the `/research-gaps` seam, is reported | |
| D5 | *neutrality guard*: a **synthetic** skill whose practitioner sub-section has been deleted still passes **every** C1 assertion — D1, D1a–D1i, D2 – D4 and D8 name no material class, no incident, no post-mortem, no company blog | the `## Finding sources` section written class-neutral |
| D5b | *separability*: excising the `### Practitioner material` sub-section **from the shipped `skills/sources/SKILL.md`, by heading** fails exactly one of the checks that read that file — the addendum check — and leaves the others green (SC-016). **Four checks at T018a/T019, five once T020/T021 land**: the fifth, `check_sources_skill_states_the_explicit_request()`, does not exist in wave D, so T018a asserts one-of-four and **T021 widens it to one-of-five** | the addendum as its own sub-section, under a heading the test names verbatim |
| D6 | a `sources` skill missing the practitioner addendum — the primary-and-interested property and the selected-sample property on the credibility sentence — is reported, and **only that check** fails | `check_sources_skill_carries_the_practitioner_addendum()` — **C2** |
| D7 | *guard*: the edited shipped skill passes both checks | the addendum as its own sub-section under `## Finding sources` |
| D8 | a `sources` skill whose candidate shape does not require every candidate to **name which class of material it is** is reported (FR-017) | one more assertion inside `check_sources_skill_carries_the_discovery_contract()` — **C1, neutral**; **no new function**. It asserts that the class is *named*, never *which* classes exist: no list, no vocabulary, no filter (FR-040) |

**One negative case per rule.** D1a–D1i were ten assertions inside the single
case D1, whose synthetic input was a skill missing *everything* — so a check that
forgot to assert, say, FR-024 or the ≤ 10 cap passed anyway. Each case now hands
the check a skill carrying **everything but that one rule**, so a failure names
the rule. FR-035 is no longer among them: **E3** owns it, and asserting a
sentence twice means one dropped sentence fails two checks.

**D5 and D5b are not the same kind of artifact, and the difference is the point.**
D5 runs on **synthetic** text and is a *guard*: it can fail only if the test
author writes a non-neutral C1 check, which is a defect in the test rather than
in the product. **D5b is a red artifact** and runs on the **shipped** file: it
reads `skills/sources/SKILL.md`, cuts from the line `### Practitioner material`
to the next heading of equal or higher level, feeds the remainder through the
`read_skill` seam, and asserts that exactly one of the checks reading that
file reports. It is red until T019 writes the heading. **The set it asserts over
grows once**: at T018a and T019 four checks read that file, so D5b asserts
one-of-four; `check_sources_skill_states_the_explicit_request()` is written at
T020 and T021 widens D5b to one-of-five. Naming the fifth check in wave D would
make D5b raise `AttributeError` at T019 rather than pass. A synthetic D5b — which
is what the plan carried until the 2026-09-08 review remediation — cannot be
false: SC-016 is a claim about the file that ships, the neutral check greps the
whole body, and a token the neutral check demands that happened to be stated
only inside the addendum would break SC-016 with nothing noticing. Cutting **by
heading** rather than by prose is deliberate: rename the heading and the test
fails by name instead of silently excising nothing.

**Wave E — piece D, the silence** *(FR-035 – FR-037, SC-015)*

The silence gates are **C1-level**: they are about the entry condition, which is
the same whatever a candidate turns out to be. No assertion here names a class of
material, and a later addendum does not touch this wave at all (FR-039).

**Two checks, not one**, for the same kind of reason wave D has two: the
assertions have **opposite polarity** and different blast radii. E1/E2/E4 assert
an *absence* across five skills this feature otherwise leaves alone (FR-037's
four, plus `learning-goal` — case E2a);
E3 asserts a *presence* in the one skill this feature rewrites (FR-036). A
single function holding both cannot produce a failure message that says which of
the two rules broke, and the two fail for entirely unrelated reasons.

| # | Assertion | Then implement |
|---|---|---|
| E1 | `--discover` appearing in `skills/catalog/SKILL.md` is reported, naming the file | `check_discovery_is_not_offered_elsewhere()` — the **negative token gate** over `skills/ingest/SKILL.md`, `skills/catalog/SKILL.md`, `skills/cards/SKILL.md`, `skills/print/SKILL.md` and `skills/learning-goal/SKILL.md` (FR-037, plus the `/learning-goal` half of the review's W-7) |
| E2 | the same for `ingest`, `cards` and `print` | |
| E2a | the same for `learning-goal` — the fifth gated file. `--discover` occurs nowhere in it today, so the token is exact there too | |
| E4 | *shipped-repo guard*: the five gated skills carry no `--discover` — green from the start, and the point is that it **stays** green | — |
| E3 | a `sources` skill that does not state that an ordinary run neither enters nor mentions discovery is reported | `check_sources_skill_states_the_explicit_request()` — the **positive substring gate** on `skills/sources/SKILL.md`: discovery is entered only on an explicit request, and an ordinary run neither enters nor mentions it (FR-035, FR-036) |

**`/research-gaps` is not in the gated set and cannot be.** T006 writes
`/sources --discover` into `skills/research-gaps/SKILL.md` on purpose — FR-034
asks for the seam — so a token gate would fire on the sentence the feature
requires. That is the residual risk the review's W-7 names, and it is stated
here rather than left implicit: what holds `/research-gaps` instead is T006's
one-paragraph rewrite (whose content is gated by
`check_network_claim_is_not_exclusive()`), row **12-vi**, which now runs
`/research-gaps` as well, and the spec Assumptions bullet recording the
exclusion. What remains uncovered is a paraphrase inside that one file that row
12-vi's run happens not to emit. **Accepted, and named.**

The rows are grouped by function rather than by number — E4 belongs with E1/E2,
and E3 stands alone. The case **ids are unchanged**, so everything that cites
them (the FR gate table, the `docs/testing.md` rows, `checklists/gates.md`
CHK027) still points where it did.

**Wave F — the experience-report rule in three prompts** *(FR-010 – FR-015, FR-030)*

| # | Assertion | Then implement |
|---|---|---|
| F1 | an `ingest` skill that does not name `nature: experience` is reported | `check_skills_carry_the_experience_rule()` |
| F2 | a `catalog` skill that has lost the experience-report rule, or the FR-013 material-base warning, is reported | |
| F3 | a `cards` skill that has lost the attribution rule, **or the FR-013 material-base warning** (FR-013 binds `/cards` as well as `/catalog` — US3 scenario 5), is reported | |
| F4 | *guard*: the three edited skills pass | the three prompt edits |

**Wave H — the fixture.** Only once A–G are green. One invented archipelago
incident write-up under `raw/field-notes/`, its ingested twin under
`knowledge/field-notes/` carrying `nature: experience`, one subtopic in
`catalog/topics.md` whose only reference is that document, and **exactly one**
card in `cards/signals.yaml` carrying `source:`. Then `DEMO_CARD_COUNT` moves and
`tests/fixtures/demo-project/README.md` gains its row.

**Exactly one card, and this is the only place the reason is written.**
`cards/signals.yaml` holds 7 cards today and is what
`test_three_dividers_share_a_sheet_with_a_short_deck` builds through
`--topic Signals`. At **8** cards the deck fills two A8 rows and the three-divider
block still shares the last sheet (`105 + 8 + 51.5 + 8 = 172.5 <= 210`); at **9**
it fills three, the block opens a further sheet, and that assertion fails. So the
second card is not a matter of taste — it breaks a spec-008 test no task in this
feature owns. If a second card turns out to be genuinely needed, it is a
**stop-and-flag** back to this plan, not a quiet edit to that test. The full
arithmetic, including the two assertions T033 *does* rebuild, is in § Risks; T031
carries the same rule at the point of edit.

**Wave I — the prompts.** Each skill edited until the wave C–F assertions pass
and until running it against the demo project produces a project that passes
`python3 scripts/check_project.py … --strict`. **Two of its three tasks are
human-in-the-loop checkpoints**: driving `/sources` and then
`/ingest` → `/catalog` → `/cards` in a live session, with the network turned off
by hand for one of them, is not something an implementing agent can do, and the
failure mode is that it ticks them from the prompt text it has just written.
T037 and T038 are marked as checkpoints an implementer **stops at**; everything
they verify is also covered by the By-Hand phase, so nothing is lost by
stopping.

**Wave J — docs and the manual checklist.** README, `docs/workflow.md`, and the
25 named rows in `docs/testing.md`. `check_links` is the automated part, and one
**existing** row moves: row 5's "five files under `knowledge/field-notes/`",
which is **already wrong on `main`** — three files joined `raw/field-notes/`
after it was written. T040 **counts** the ingestible files under that folder at
edit time and writes what it counts (eight today, nine after T028) rather than
incrementing a stale number.

**Not automated, and said so plainly.** The whole of piece A's *behaviour*
(FR-001 – FR-009 — the prompt sentences carrying FR-001 – FR-003, FR-005,
FR-006, FR-008 and FR-009 *are* gated, by C1–C3 and C6–C9; what a run says is
not), FR-012, FR-013, FR-014, the run halves of FR-017 – FR-027 and FR-029,
FR-033's behaviour, and FR-036 – FR-038. Nothing on disk records
what a skill *said*. These are the named rows below, and constitution XI's
run-output carve-out is exactly the clause they sit in — this feature uses it as
written rather than extending it.

### Which gate holds which requirement

| Requirement | `check_docs.py` | `check_project.py` | `docs/testing.md` |
|---|---|---|---|
| FR-001 assessment exists, names a goal line | **C1** (the skill must name `goal.md`) | — | **4a** |
| FR-002 advisory, never blocks, no confirmation gate | **C2** (the skill must say it is advisory and never blocks) | — | **4b** |
| FR-003 warning names the id and the goal line | **C6** — *the rule is stated in the prompt; the check cannot see a warning* | — | **4b, 4f** (SC-002 is measured there) |
| FR-004 about this source for this goal, never the subject | — *no case; there is no token whose absence means "says nothing about the subject". Run output only* | — | **4d** |
| FR-005 reasons from `kind`/`depth` and says which | **C7** — *rule stated only; the check cannot see which one a run used* | — | **4a, 4b, 4c** |
| FR-006 no goal ⇒ no assessment, ≤ 1 pointer per run | **C8** — *rule stated only; the check cannot count a run's pointers* | — | **4i** |
| FR-007 never persisted | — | **A5, A6** — `VERDICT_KEYS` refused on an entry. *As strong as the requirement's on-disk half: the obligation **is** an absence and the check sees exactly it. The "no timestamp" clause is ungated — a timestamp has no fixed key name* | **4g** |
| FR-008 a listing does not re-assess | **C3** | — | **4e** |
| FR-009 never invent a claim about an unseen source | **C9** — *rule stated only, and **circular beyond that**: no check and no row can distinguish an invented claim from a real one. See § What no artifact can decide* | — | **4a** |
| FR-010 experience report is evidence, not a rule | **F2, F3** | — | **12-v** |
| FR-011 the card names the case, via `source:` | **F3** | **B1, B2, B3** | **12-v** |
| FR-012 the card carries the scale | **F3** | — | **12-v** |
| FR-013 the material-base warning, in `/catalog` **and** `/cards` | **F2, F3** | — | **9f** (`/catalog`), **12-iv** (`/cards`) |
| FR-014 rule wanted, only cases available | **F2** | — | **9f** |
| FR-015 `/ingest` writes `nature: experience` | **F1** | **A1, A2, A3** | **8m** |
| *C1 — the neutral discovery contract* | | | |
| FR-016 discovery writes nothing until the user picks | **D1, D2** | — | **4k, 4l** |
| FR-017 candidate fields, incl. the class of material | **D1, D8** | *the picked entry, by today's rules* | **4k** |
| FR-018 a sentence, never a number | **D1c** | — | **4k** |
| FR-020 picked entries go through the ordinary path | **D1h** | *ditto* | **4m** |
| FR-021 never propose what it did not retrieve | **D3** | — | **4n-i** *(opportunistic — see § What no artifact can decide)* |
| FR-022 no synthesis, no `type: research`, the seam | **D4** | — | **4m** |
| FR-023 paywalled: say so, never propose, no credentials | **D1d** | — | **4n-i** *(opportunistic)* |
| FR-024 never propose a source already registered | **D1e** | — | **4n** |
| FR-025 no `goal.md` ⇒ nothing to search for | **D1f** | — | **4o** |
| FR-026 no network ⇒ report, write nothing, exit clean | **D1g** | — | **4p** |
| FR-027 found/shown counts, grouped, empty areas visible | **D1a** | — | **4k** *(the shown count and the grouping are decidable; the **found** count is not)* |
| FR-039 C1 is neutral; a class is added as an addendum | **D5** (guard), **D5b** (red, against the shipped file), **D6** | — | **4k** |
| FR-040 no class filter ships; FR-017's class is its hook | **D8** (the hook exists and is neutral) | — | **4k** |
| *C2 — the one addendum this feature ships* | | | |
| FR-019 practitioner addendum: primary-and-interested, selected sample | **D6** | — | **4s** |
| FR-029 the archive reach, stated at registration | **C4** | — | **4h** |
| FR-030 the gate itself | *is* waves C, D, E, F | — | — |
| FR-031 the gate itself | — | *is* waves A, B | — |
| FR-032 the gate itself | — | — | *is* the 25 rows |
| FR-033 network only in discovery mode | **D1i** (the rule) | — | **4r** *(the offline re-run is the observable; a transcript alone is not)* |
| FR-034 the stale claim never reappears | **G1, G2, G3** | — | — |
| FR-035 explicit request only | **E3** (`check_sources_skill_states_the_explicit_request()`) — *and **not** D1; asserting it twice means one dropped sentence fails two checks* | — | **4k** |
| FR-036 an ordinary run neither enters nor mentions it | **E3** — `check_sources_skill_states_the_explicit_request()`, the positive gate | — | **4q** |
| FR-037 no other step enters or mentions it | **E1, E2, E2a, E4** — `check_discovery_is_not_offered_elsewhere()`, the negative gate over five skills. *`/research-gaps` cannot be gated: it must carry the token* | — | **12-vi** (now including a `/learning-goal` and a `/research-gaps` run) |
| FR-038 the whole-pipeline guarantee | — | — | **12-vi** |

**No requirement is left without an artifact.** **Thirty-three** of the
thirty-nine active requirements name an artifact in **two** of the three
columns. The six that name only one are FR-004, FR-030, FR-031, FR-032, FR-034
and FR-038.

**Two have no automated assertion at all: FR-004 and FR-038.** FR-004 — *"about
this source for this goal, never about the subject or the publisher"* — is a
statement about what a warning does **not** say, and there is no token whose
absence carries it. FR-038 is the whole-pipeline guarantee, and no script can
know which sources the user named. Both reach a **named** row instead, 4d and
12-vi, which is constitution XI's run-output carve-out used as written.

FR-032 has no automated assertion either, for a third reason: it **is** the row
set, so nothing can hold it but the rows themselves. FR-040's *"no filter
ships"* half is deliberately ungated for a fourth (§ Risks).

**Five requirements moved out of that list on 2026-09-08**, in the review
remediation, because the review found that a check *could* be written for each
and that leaving them ungated was a choice with no argument behind it (W-3, O-4).
FR-003, FR-005, FR-006 and FR-009 are now held by **C6–C9** inside
`check_sources_skill_reads_the_goal()`; FR-007 by **A5/A6** inside
`check_sources`. **Read both columns, not the check column alone.** C6–C9 assert
that the *rule is stated in the prompt* — they are drift detectors, and the
behaviour they are about stays on rows 4a–4i. A5/A6 are different in kind:
FR-007's obligation *is* an absence on disk, so the check sees exactly the thing
the requirement forbids, and it is as strong as the requirement for every
project the checker is pointed at.

### What no artifact can decide

Four requirements have a gate or a row that looks like verification and is not.
They are recorded here plainly rather than left to read as covered — the review
of 2026-09-08 asked the question and this is the answer.

| Requirement | What *is* decidable | What is not, and why |
|---|---|---|
| **FR-009** — never invent a claim about a source it has not looked at | That the rule is written in the prompt (**C9**) | Everything else. The only evidence a tester has that a run did not look at a source is the run's **own statement** that it did not, which is the thing under test. Row 4a is therefore **circular** and is marked so. Nothing in this feature decides FR-009 |
| **FR-021** — never propose what it did not retrieve | That the rule is in the prompt (**D3**), and a **violation**: open every proposed URL; one that 404s or whose page does not match its description fails row 4n-i | Compliance. A tester cannot make discovery *find* an unretrievable candidate, and the transcript shows what was proposed, not what was fetched and dropped. A run in which nothing is broken is **"not exercised"**, never "pass" |
| **FR-023** — paywalled: say so, never propose | That the rule is in the prompt (**D1d**), and a **violation**: a proposed candidate that turns out to be behind a paywall or a login fails row 4n-i | Compliance, for the same reason. The fixture's own login page (`raw/web/members.html`) is on localhost, which discovery does not search, so the stimulus is not the tester's to produce. Judged **opportunistically** |
| **FR-027** — the *found* count | The **shown** count (it equals the number of candidates listed), the grouping, and that every goal area appears including the empty ones — all countable in the run output | The **found** number. The tester sees what the run printed and has nothing to check it against. Row 4k says "record it as read, not as verified" |

The pattern in all four is the same: the prompt-side gate is real and the
behavioural side is not decidable by anything this feature ships. Saying so is
cheaper than a row a tester has to lie on.

**FR-033's "no network request" was the fifth candidate for this table and is
not in it**, because it turned out to have an observable after all. A session
exposes no request log, so "read the transcript" is not evidence — but *turning
the network off and re-running the three ordinary invocations* is: a
registration, a listing and a removal must behave **exactly** as they did
online (US5 scenario 3 says the registration path is unaffected by the network).
A run that needs the network to register a source the user named fails, visibly.
Row **4r** was rewritten to say that instead of "makes no network request on
discovery's behalf", which nobody could have judged.

### The named rows in `docs/testing.md`

The checklist is a table with columns `| # | Step | Do this | Expect |`, numbered
globally with letter suffixes, and run-output rows already use the
`**run output (FR-0xx):**` prefix (`docs/testing.md:203`). New `/sources` rows go
after line 193; the pipeline rows go beside the existing `/cards` rows; the
no-network row goes beside `9d`.

| # | Step | Covers |
|---|---|---|
| 4a | `/sources` | FR-001, FR-005, FR-009 — the assessment names a required topic or area, and says which of `kind`/`depth` it used |
| 4b | `/sources` | FR-002, FR-003, **SC-002**, FR-005 weigh-down, SC-004 — scratch copy, `depth: awareness`; the warning names the id **and** quotes the goal line, the entry is written, zero confirmation prompts |
| 4c | `/sources` | FR-005 weigh-up — scratch copy, `depth: expert`; the same material is weighed up and the run says so |
| 4d | `/sources` | FR-004 — the warning says nothing about the subject or the publisher in general |
| 4e | `/sources` | FR-008 — a bare listing re-assesses nothing |
| 4f | `/sources` | FR-003, **SC-002** — a source matching an `## Out of scope` line: the warning names the source id and **quotes that line**; zero warnings say only that something looks off-goal |
| 4g | `/sources` | FR-007, SC-001 — after the run `sources.yaml` carries no verdict of any kind |
| 4h | `/sources` | FR-029 — the archive reach is stated at registration |
| 4i | `/sources` | FR-006, SC-003 — `rm goal.md`: no assessment, identical key set, ≤ 1 `/learning-goal` pointer |
| 4j | `/sources` | [research R1](research.md#r1--a-goal-written-after-the-sources-are-registered) — a goal written afterwards produces no assessment for what is already registered, and nothing claims otherwise |
| 4k | `/sources` | FR-016 – FR-018, FR-027, FR-035, FR-039, FR-040, SC-007, SC-017 — the **neutral** proposal shape: the counts (the **shown** count equals the candidates listed and *found* ≥ *shown*; the **found** number itself is recorded as read, not verified), ≤ 3 per area and ≤ 10 per run, every area listed, one credibility sentence per candidate and zero numbers standing in for credibility, whatever class of source the candidate is; **every** candidate names which class of material it is, the non-practitioner ones included, and no candidate is dropped or renamed for naming a class no list contains — there is no list, no class argument and no way to ask for only one class |
| 4s | `/sources` | FR-019, SC-007 — the **practitioner addendum**: a candidate that is practitioner material additionally names primary-and-interested and selected-sample; a candidate that is not — it says so, because FR-017 makes it name its class — is **not** held to those two properties |
| 4l | `/sources` | FR-016, SC-005 — decline everything: zero files created, zero modified |
| 4m | `/sources` | FR-020, FR-022, SC-006 — accept one: the ordinary path, the assessment fires, `--strict` exits 0 |
| 4n | `/sources` | FR-024 — register a source first, then run discovery: it is **not** proposed again. Performable on demand, and the only one of the three exclusions that is |
| 4n-i | `/sources` | FR-021, FR-023 — **opportunistic, and the row says so**. Open every proposed URL: one that 404s, that is paywalled or login-gated, or whose page does not match its description **fails** the row. If none is, the row is **not evidence of conformance** — write "not exercised", not "pass". The prompt-side halves are **D3** and **D1d** |
| 4o | `/sources` | FR-025 — no `goal.md`: nothing to search for, points at `/learning-goal`, writes nothing |
| 4p | `/sources` | FR-026, SC-008 — no network, beside the existing `9d`: reports, writes nothing, exits clean, no traceback |
| 4q | `/sources` | FR-036, SC-015 — a registration, a bare listing and a removal mention discovery nowhere |
| 4r | `/sources` | FR-033 — **the observable is the network, not the transcript.** With the machine offline (row 4p's switch), repeat the registration, the bare listing and the removal: all three must behave exactly as they did online — same entry, same listing, same removal, no error and no "could not reach" line (US5 scenario 3). Read the tool calls too, but the offline run is what decides it |
| 8m | `/ingest` | FR-015 — the incident write-up gets `nature: experience`; the handbook document gets no `nature:` key |
| 9f | `/catalog` | FR-013, FR-014 — the material-base warning carries all four of FR-013's contents in the run's own words, and single-case coverage is not presented as coverage of the rule |
| 12-iv | `/cards` | FR-013 — the **`/cards`** half: a `/cards` run reporting on an experience-only subtopic carries the same four contents. Id verified free: `docs/testing.md`'s 12-series runs `12`, `12-i`, `12-ii`, `12-iii`, and this fills the gap the plan previously skipped |
| 12-v | `/cards` | FR-011, FR-012, SC-009 — every card names its case through `source:`, none states an unattributed general rule, the scale is kept |
| 12-vi | any | FR-037, FR-038, SC-014, SC-015 — a full `/sources` → `/ingest` → `/catalog` → `/cards` run with no `--discover`: zero mentions, zero extra entries. **Plus a `/learning-goal` and a `/research-gaps` run in the same session** — the two skills the token gate does not bound (`/learning-goal`'s paraphrase; `/research-gaps` entirely, since it must carry the token for FR-034's seam). Neither may end with a line offering to go looking |

**Two things about the ids, so a reader does not read them as mistakes.** `4s` is
listed between `4k` and `4l` on purpose: it is `4k`'s addendum companion and is
read beside it, while the id itself is the last one allocated in the 4-series.
And the 12-series is contiguous — `12-iii` already ships in `docs/testing.md`,
and this feature adds `12-iv`, `12-v` and `12-vi` in that order.

Rows 1–14 need a Claude session in the demo folder (`docs/testing.md:293`, which
reads "Steps 1–14"), which
all of these do.

## Risks and things flagged

| Risk | Mitigation |
|---|---|
| **FR-037's automated half is a token check, not a semantic one.** `--discover` in another skill fails `check_discovery_is_not_offered_elsewhere()`; "you could go looking for more material" does not | Accepted, and stated rather than hidden. The token catches the form the drift actually takes — a pointer somebody adds. The paraphrase case is row **12-vi**, and it is named there with its FR number rather than left implicit |
| **The token gate does not bound the two skills whose wrap-ups already point elsewhere.** FR-037 names four skills; `/learning-goal` was never gated, and `/research-gaps` **must carry** `--discover` because T006 writes FR-034's seam into it | Half closed, half named. `skills/learning-goal/SKILL.md` becomes the **fifth** gated file (case **E2a**) — `--discover` occurs nowhere in it today, so the token is exact there too. `/research-gaps` cannot be token-gated at all; what holds it instead is T006's one-paragraph rewrite (content gated by `check_network_claim_is_not_exclusive()`), row **12-vi**, which now runs `/research-gaps` and `/learning-goal` as well, and a spec Assumptions bullet recording the exclusion. **What remains uncovered**: a paraphrase inside `skills/research-gaps/SKILL.md` that row 12-vi's run happens not to emit. Accepted |
| **Four requirements have a gate or a row that reads like verification and is not** — FR-009's "never invent", FR-021's "did not retrieve", FR-023's paywalled find, FR-027's *found* count | Written down in § *What no artifact can decide* rather than counted as covered. Row **4n** is split so a tester is not asked to pass FR-021/FR-023 on a stimulus they cannot produce; row **4n-i** says "not exercised" is the honest outcome; row **4k** says the found count is recorded as read, not verified; FR-009 is recorded as circular. FR-033 was the fifth candidate and was **fixed instead**: row 4r now re-runs the three ordinary invocations **offline**, which is decidable |
| **The new fixture subtopic could disturb `check_project.py --strict` on the demo project** — the catalog carries `Status:`, `Parents:`, `Also covers:`, `Related:` and `Term:` invariants | Wave H runs `python3 scripts/check_project.py tests/fixtures/demo-project --strict` as its own step before the prompts are touched, and the new subtopic is placed under the existing `## Signals, flags and the radio` topic so it serves a required topic already in `goal.md` |
| **`DEMO_CARD_COUNT` and the e2e suite.** `tests/test_e2e.py:27` pins the fixture's card count and skips without an engine, so a wrong count hides until someone sets `LERNKARTEN_E2E=1` | The new card goes in `cards/signals.yaml`, so `TIDES_CARD_COUNT` (`:49`) does not move; `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` is a required step before the PR and is in [quickstart.md](quickstart.md) |
| **Wave H breaks two divider assertions that "derived counts follow automatically" does not cover.** `test_four_dividers_open_a_further_page_on_the_demo_deck` (`tests/test_e2e.py:1285`) asserts `DEMO_A8_PAGES + 2`, and `test_the_run_says_which_paper_case_it_is_in` (`:1325`) asserts `"further sheet"` in stderr. Both hold **only because 32 ≡ 0 (mod 16)**: at 32 cards the last A8 sheet is full, so the four-divider block has to open a fresh one. At **33 or 34** it does not | **Verified against `scripts/build_pdf.py:216-257` (`divider_block`) and `scripts/leitner.py`, not assumed.** A8 is 4 x 4 of 71.75 x 50 mm on 297 x 210 at a 5 mm margin; `GAP_MM = 8`, `GROWTH_MM = 1.5`, `LAYOUT[4] = (2, 2)`, so the block is `2 x 51.5 + 8 = 111` mm and shares the sheet when `filled_to + 8 + 111 + 8 <= 210`. At 32 cards `filled_to = 5 + 4 x 50 = 205` → 332 > 210, a further sheet. At 33 `filled_to = 5 + 1 x 50 = 55` → 182 ≤ 210, **it shares** and both assertions fail. **T033 licenses the edit in writing** and rebuilds both cases on `--topic Tides` (11 cards → 3 rows → `155 + 127 = 282 > 210`, a further sheet), guarded by `assert 5 <= TIDES_CARD_COUNT <= 16`. The companion "shares a sheet" case stays on `--topic Signals`, which is why **T031 adds exactly one card**: at 9 signals cards that block would open a page too (`155 + 8 + 51.5 + 8 = 222.5 > 210`). Invisible to plain `pytest` — it surfaces at T035 |
| **A second literal card count, in a module the plan did not list.** `tests/test_check_project.py:164` hard-codes `counts["cards"] == 32` | Named in **T033** rather than discovered at T044. Plain `pytest` catches it, so it is not silent — but it was a task premise that was wrong |
| **`docs/testing.md` row 5 is stale already, and wave H makes it staler.** It expects "five files under `knowledge/field-notes/`" from `/ingest field-notes`. That was true at `51f0434`; `tide-office-cover.md`, `chart-notes.md` and the generated `harbour-log.txt` have joined `raw/field-notes/` since, so the shipped row is **wrong on `main` today**, before this feature touches anything | **T040** runs `make_testdata.py`, **counts** the ingestible files under `tests/fixtures/demo-project/raw/field-notes/` recursively (excluding `empty.md`, which the row says is reported not invented, and `diagrams/signal-flags.png`, which is a linked figure) and writes the number it counted — **eight today, nine after T028** — rather than incrementing the stale one. It is the only shipped row this feature's fixture work invalidates; the counts in rows 8a–8g are about other sources |
| **`tests/test_testdata.py:265-273` parses `skills/ingest/SKILL.md` literally** for the default-pattern text at line 27-28 | The `nature:` edits go in the frontmatter block (lines 92-111) and the extraction rules, not near line 27. Flagged so nobody reflows that paragraph |
| **`skills/sources/SKILL.md`'s `description` is gated four ways** — folder name, ≥ 20 characters, the word `Triggers`, the domain word `flashcard` | Rewriting it to name both jobs is the first thing wave I does, and `check_skills` catches a miss immediately |
| **`/sources` reaches the network for the first time.** A skill that only wrote to a register now fetches | Accepted deliberately in clarification Q4 and scoped by FR-033: discovery only. The docs stop claiming a clean network line that was never true and state the real one instead (FR-034) |
| **Round 3's C1/C2 split could be read as new work.** It is a regrouping of requirements and of the checks that hold them, not new behaviour | Stated rather than absorbed. Exactly two things grew, and both are test-side: `check_sources_skill_carries_the_discovery_contract()` becomes **two** functions (neutral + practitioner addendum), and wave D gains the neutrality guard **D5** plus the addendum row **D6/D7**, which SC-016 asks for. The prompt gains no new rule — the practitioner addendum moves into its own sub-section of text it was already going to carry. No new requirement of the *user-visible* kind, no new source type, no new frontmatter field, and nothing of issue #43 |
| **"Neutral" gets read as "supports research literature"** | It does not, and three places now say so: spec FR-039's closing note, the spec assumption *The discovery contract is neutral; the coverage is not*, and the addendum section of [contracts/discovery-proposal.md](contracts/discovery-proposal.md). One addendum ships. Issue #43 is a seam recorded, not scope taken |
| **FR-040's "no filter ships" half has no automated gate, deliberately.** A negative check would have to name an argument spelling that does not exist, and inventing one to gate it is the thing FR-040 forbids | Accepted and stated. What *is* gated is the hook: **D8** asserts that every candidate names its class, and asserts nothing about *which* classes exist. Row **4k** carries the rest — no class argument, no vocabulary, nothing dropped for naming a class no list contains. If implementation finds itself writing a class list anywhere, that is a stop-and-flag back to this plan |
| **The FR-017 class field could be read as a new format key.** It looks like `nature:`, and somebody will want to persist it | It is prose in run output and nothing else — spec FR-017 says so, the spec's Format Contracts table carries a deliberate "none" row for it, and [contracts/discovery-proposal.md](contracts/discovery-proposal.md) puts it in the per-candidate field table beside `credibility`, which is also not a key. Nothing in `sources.yaml`, nothing in the knowledge frontmatter, no `NATURES`-style tuple. The two live at different layers and the spec states the relationship rather than leaving a reader to infer it |
| **Round 4's rename could be read as a change of meaning.** The C2 mechanism's name became **addendum** across six artifacts | It is editorial: no requirement gained or lost an obligation, the C1/C2 split is the same split, and the only mechanical consequence is that the check function this plan proposes is named `check_sources_skill_carries_the_practitioner_addendum()`. Recorded in the spec's round-4 clarification so the diff is not mistaken for scope |
| **A dependency turns out to be needed** | Stop and flag back to this plan. The spec states none is needed and [research R6](research.md#r6--is-a-library-or-a-dependency-needed-anywhere-here) confirms it; adding one silently would bypass constitution IV's whole point |

## Post-design re-check

Design changed nothing in the Constitution Check. The three ⚠ rows are the same
three, and all three are work items rather than violations: the format change
and its five-file entourage (I), the fixture extension plus the PR note (VII),
and the skill description that has four assertions on it (X). No gate moved from
pass to fail, and no gate needed a waiver.

Two things are worth recording as *improvements* on the precedent this repo set
in feature 001:

- **The run-output carve-out already exists.** Feature 001 had to add it to the
  constitution mid-flight and said so in its Complexity Tracking. Constitution
  XI now carries it, so the 25 named rows here are the clause being used as
  written, not a plan running ahead of its constitution.
- **Part of a prompt feature became genuinely assertable** — clarification Q1's
  `nature:` key means wave B can check something about the *cards a model wrote*,
  not merely about the text of the prompt that wrote them. That is the first
  time a card-phrasing rule in this repo has had a red assertion at all.

## Complexity Tracking

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| A **second mode** on `/sources`, which also makes it reach the network for the first time | I | Discovery's entire output is proposed `sources.yaml` entries, and `/sources` owns that file. Piece A is putting `goal.md` reading into the same skill anyway | An eighth pipeline step was the alternative and was rejected in clarification Q4: it would move the constitution's Identity sentence, the brand sources, three rendered PNGs, the README banner, `docs/workflow.md` and `docs/index.html` — all of it to house one mode of an existing skill. `/research-gaps` cannot take the job: it needs a catalog with `Status: gap` subtopics, so it cannot run for the user this feature exists for, and it writes synthesised prose rather than handing back URLs |
| **A card-content rule enforced in `check_project.py`** (FR-011), where every card rule so far has been schema or style | XI (placement) | It is the one part of piece B that leaves a trace on disk, and the constitution's own table puts *what a skill writes into a user's project* in this gate | Leaving FR-011 entirely to the manual checklist. Rejected because a check **can** be written here — the spec says so explicitly (spec.md:32) — and constitution XI's carve-out is only for requirements where nothing lands on disk. Using it where an assertion is available is exactly the licence the clause says it is not |

Principle XI has no row here. It is not waivable, and this feature does not ask
it to be.
