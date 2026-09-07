# Implementation Plan: Enumeration tiers

**Branch**: `feat/enumeration-tiers` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-enumeration-tiers/spec.md`

## Summary

Give the enumeration a length rule, and check the two halves of it that can be
checked without judgement. PR #96 deleted the four-item cap and put nothing in
its place; this puts a **tier table** in `skills/cards/SKILL.md` (3–5 flat, 6–8
grouped, 9+ split) and adds three findings to `scripts/check_project.py`, all of
them warnings: **E-2** (a counted enumeration prompt answered in prose), **E-3a**
(grouped tier, not grouped) and **E-3b** (too long for one card).

Two things that shipped already have to move with it, and both were found by
measuring rather than reading:

- **E-1 counts the wrong thing on a grouped back.** It compares the announced
  count with the number of `#list` items; on `[*A*: x, y], [*B*: z, w]` that is
  2, not 4. Adopting this feature's own recommended shape would make the
  previous feature's **error** fire falsely (research R-4).
- **A-2 checks the wrong thing on a grouped back.** `_item_key` cuts at the
  first colon and returns the label, so the members are never checked
  (research R-5).

Everything new is reuse: `_list_items`, `_item_key`, `_mentions` and
`_announced_count` all already do what this needs. What is genuinely new is two
regexes and two closed word lists.

## Technical Context

<!--
  These values are the project's, not placeholders. Change one only if this
  feature genuinely changes it.
-->

**Language/Version**: Python `>=3.12` (`pyproject.toml`), ruff targeting `py312`. CI tests 3.12 and 3.13, and an `oldest-python` job builds cards on the floor. The floor is part of constitution II because it decides which libraries are eligible — it has already been moved twice by that fact, most recently off 3.11 because PyYAML has no cp311 `win_arm64` wheel.

**Secondary language**: Typst — the card (`templates/card.typ`), the press sheet (`templates/cards.typ`), the brand graphics (`assets/brand/*.typ`) and the test-data generators.

**Runtime dependencies**: `pyyaml==6.0.3`, declared in `REQUIREMENTS` in `scripts/deps.py` and read through `scripts/yamlio.py`. They reach the user by installing themselves on first use — `pip install --target` into a cache directory, `--only-binary :all:`, reported by `lernkarten deps --check`. A new one must be pinned exactly and must have a wheel for every supported platform, Windows ARM64 included.

**Dev dependencies**: `pytest>=9.1.1`, `ruff==0.16.2`, `pillow>=11,<13`, plus `pyyaml` so a checkout can run the tests without waiting for the bootstrap (`requirements-dev.txt`). Tools pinned exactly; libraries get a range.

**Optional external tools**: `pdftotext` (poppler-utils) for PDF text. Absent → the path degrades or the test skips, never fails. This is one of the two acceptable shapes for a binary dependency.

**Storage**: plain files on disk — `sources.yaml`, `knowledge/`, `catalog/topics.md`, `cards/*.yaml`, `output/`. No database.

**Testing**: pytest, `testpaths = ["tests"]`, `addopts = "-q"`. Seven levels; see `docs/testing.md`. **Test-first is mandatory** (constitution XI). Two suites are opt-in: `LERNKARTEN_E2E=1` lets the engine be fetched, `LERNKARTEN_DEPS_NET=1` lets one test install from PyPI.

**Lint/format**: ruff — line length 100, `select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]`.

**Typesetting engine**: Typst, one self-contained binary, pinned by version and SHA-256 per platform in `scripts/engine.py` — Darwin arm64/x86_64, Linux x86_64/aarch64, Windows AMD64/ARM64. Fetched once on first build. Override with `LERNKARTEN_ENGINE`. This is the reference pattern for a self-fetching binary.

**Target Platform**: Windows, macOS and Linux, treated as equals (constitution II). `scripts/engine.py` covers all six platform pairs, and CI runs windows-latest legs on the `test`, `cards` and `e2e` jobs. All three platforms block a merge, so a Windows failure is a failure.

**Project Type**: CLI tool + Claude Code plugin (skills). Single module, flat `scripts/`.

**Performance Goals**: cold start matters — a fresh checkout reaches a PDF from one command. No throughput target; the workload is one user, a few hundred cards. A new dependency must not visibly slow a cold invocation (constitution IV).

**Constraints**: frictionless install on all three platforms; works offline once installed and once the engine is cached; output must survive a black-only laser print and a photocopier.

**Scale/Scope**: ~2 000 lines of Python across 11 flat modules, 5 skills, 2 Typst templates, ~1 900 lines of tests, one shared fixture corpus.

## Dependency Decisions

### Reuse check (constitution III)

**Is anything being hand-rolled here?** No — and the question has an unusually
strong answer this time, because the four helpers this feature needs were all
written by the two features before it:

| Need | Reused from |
|---|---|
| pull the items out of a `#list(` | `_list_items` — 007-deck-anchors, bracket-depth scan |
| decide whether a card names a thing | `_item_key` + `_mentions` — 007-deck-anchors |
| read a count off a front | `_announced_count` — PR #96, per-language, maths-gated |

Genuinely new: a regex for the group shape, a regex for the enumeration cue, and
two closed word lists. A natural-language toolkit was considered for "is this an
enumeration prompt" and rejected — a runtime dependency with model data, for a
question a seven-word list answers correctly on all four counted fronts that
exist in this repository (research R-2).

### Vetting (constitution IV)

Not applicable: no new dependency, runtime or dev.

**Removals**: none.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Pass? |
|---|---|---|
| I | The two halves stay coupled only through the four file formats | [x] the seam is the `back` string in `cards/*.yaml`; no new key |
| II | **(GATED)** New dependencies install everywhere with wheels | [x] none added |
| III | **(GATED)** Nothing hand-rolled that a library does | [x] see Reuse check — three of four helpers are reused outright |
| IV | **(GATED)** Vetting table completed | [x] N/A, no dependency |
| V | Code lands in an existing module | [x] all of it in `scripts/check_project.py` beside A-1, A-2 and E-1; no new file |
| VI | Script imports stay acyclic | [x] no new import |
| VII | **(GATED)** No user content; examples stay subject-agnostic | [x] the two real cards in issue #83 stay in the issue; fixture growth is in the Kestrel Islands subject |
| VIII | No binaries committed | [x] text only |
| IX | Typst sources edited, never generated files | [x] no Typst change |
| X | Skill frontmatter valid | [x] unchanged |
| XI | **(NON-WAIVABLE)** Tested first, failing on the assertion | [x] the ordered red list is in Phase 1 below; the prompt change gets a `check_docs.py` check (R-6) |
| XII | The four gates pass; ruff config not loosened | [x] |
| XIII | English throughout | [x] |
| XIV | Branch `<prefix>/<name>`; `main` untouched | [x] `feat/enumeration-tiers` |
| XV | Engine version unchanged | [x] untouched |
| XVI | `docs/design.md` read before a visible change | [x] nothing visible changes — a grouped list is different text in the same box |
| XVII | Card style and Typst escaping respected | [x] the group shape uses single-star emphasis, which is the rule `CLAUDE.md` states |

**Open-item check**: this feature does not touch the constitution's one open
item (dependencies pinned by version rather than by hash). It adds no
dependency, so the question does not arise.

## Project Structure

### Documentation (this feature)

```text
specs/011-enumeration-tiers/
├── plan.md                 # this file
├── spec.md
├── research.md             # Phase 0 — every finding measured against shipped code
├── data-model.md           # Phase 1 — the group, the enumeration size, the tiers
├── contracts/
│   └── check-messages.md   # Phase 1 — E-2, E-3a, E-3b, and the two changed messages
├── quickstart.md           # Phase 1
├── checklists/
│   └── requirements.md
└── tasks.md                # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

<!--
  This is the real layout. Mark the files this feature touches; delete the rows
  it does not. Do not replace it with a generic src/ tree.
-->

```text
bin/
└── lernkarten              # entry point; dispatches build | check | engine

scripts/                    # flat, imported by bare name via sys.path
├── deps.py                 # LEAF — installs the pinned runtime deps on first use
├── engine.py               # LEAF — finds/fetches Typst, pinned by SHA-256, 6 platforms
├── yamlio.py               # → deps. PyYAML plus a one-line error with the line number
├── build_pdf.py            # → engine, yamlio. The PDF build and --check
├── check_project.py        # → build_pdf, yamlio. Gate on model-written artifacts
├── check_docs.py           # → yamlio. Skill frontmatter, doc links, required files
├── make_testdata.py        # → engine. Generates the binary test material
├── demo.py                 # → make_testdata. Scratch copy of the demo project
├── render_brand.py         # → engine. Renders assets/brand/*.typ to PNG
├── zotero_ingest.py        # Zotero local API → knowledge/
├── zotero_stub.py          # Fakes the Zotero 7 API for tests
├── lernkarten              # mirror of bin/lernkarten
└── install-hooks.sh

skills/                     # the model-driven half — one prompt per step
├── sources/SKILL.md
├── ingest/SKILL.md
├── catalog/SKILL.md
├── cards/SKILL.md
└── print/SKILL.md

templates/
├── card.typ                # the card — 105 × 74.25 mm, three fixed bands
└── cards.typ               # the press sheet — A4, 8 up, duplex

assets/
├── brand/*.typ             # graphic sources
└── *.png, *.svg            # rendered marks and graphics (committed)

tests/
├── test_yamlio.py          # unit
├── test_deps.py            # the dependency bootstrap
├── test_engine.py          # unit
├── test_build_pdf.py       # unit
├── test_testdata.py        # the generator; the scan has no text layer
├── test_ingest_sources.py  # web over http.server, zotero over the stub
├── test_e2e.py             # bin/lernkarten as a subprocess, PDF taken apart
├── test_check_project.py   # contracts of the four model-driven steps
├── test_repo_hygiene.py    # no user content, no committed binaries
└── fixtures/
    ├── demo-project/       # THE shared corpus — raw, knowledge, catalog, cards, broken, generators
    └── zotero/             # library.json + generated attachments

docs/
├── workflow.md  design.md  testing.md  index.html

cards/example.yaml          # the only versioned card file of "your own"
sources.example.yaml
```

**Structure Decision**: everything lands in **`scripts/check_project.py`**,
beside `_list_items`, `_item_key`, `_check_orphans` and `_check_counts`. No new
module was considered seriously: constitution V asks which existing module fits,
and this is one — the four helpers it extends are all in that file, and a
separate module would need to import three of them and would put the enumeration
rules in two places. `skills/cards/SKILL.md` and `CLAUDE.md` carry the rule;
`scripts/check_docs.py` gains its first assertion about a skill's own text.

Touched: `scripts/check_project.py`, `scripts/check_docs.py`,
`skills/cards/SKILL.md`, `CLAUDE.md`, `tests/test_check_project.py`,
`tests/test_check_docs.py`, `tests/test_e2e.py` (one constant),
`tests/fixtures/demo-project/cards/*.yaml`,
`tests/fixtures/demo-project/README.md`. Untouched: everything else.

### The two halves

**Model-driven work** (`skills/`): the tier table and the rule that a counted
front's back is enumerated, in `skills/cards/SKILL.md`; the reactions to E-2,
E-3a and E-3b in its step 6, in the shape the three existing reactions use; the
same rule in `CLAUDE.md` § Card style. The check written *first* and seen
failing is **two** checks, because the rule has two audiences: a
`check_project.py` check for what `/cards` writes into a user's project, and a
`check_docs.py` check that `skills/cards/SKILL.md` carries the tier table at all
(research R-6). Without the second, the prompt change is a claim.

**Deterministic work** (`scripts/`): `_enumeration_size` and `_groups` as new
helpers; `_check_counts` changed to read the size rather than the item count;
`_check_orphans` changed to descend into a group item; `_check_shape` added for
E-2, E-3a and E-3b. Covered by `tests/test_check_project.py`.

**The seam**: `cards/*.yaml`, the `back` string. No schema key is added — the
group is a **convention inside markup that already exists**, which is why
Format Contracts records "none" and backwards compatibility is total.

## Phase 0: Research

Complete — [research.md](research.md). Eight findings, three of which change the
design:

- **R-2** corrects FR-008's phrasing. "Opens with an enumeration prompt" read as
  a leading verb misses `B7SGP` — *"What are the four types of work…"* — the card
  the issue was reported for. The rule is a cue **adjacent to the numeral**.
- **R-4** is the sharpest: grouping makes the shipped **E-1 error** fire falsely.
  Measured, not inferred.
- **R-5**: `_item_key('*Discover*: alpha, beta')` returns `'discover'` today, so
  A-2 would check the label and never the members.

R-7 leaves one thing for `/speckit-tasks`: whether the split tier is
demonstrated in the fixture at full size (~6 cards) or in miniature.

## Phase 1: Design

Complete — [data-model.md](data-model.md),
[contracts/check-messages.md](contracts/check-messages.md),
[quickstart.md](quickstart.md).

Three design decisions worth naming here because they are where this could go
wrong:

1. **One definition of "how many".** `_enumeration_size` is read by E-1, E-3a,
   E-3b and the tier table. R-4 exists because two definitions already drifted
   once, silently, between features written four commits apart.
2. **Grouped means *every* item is a group.** A half-grouped list is treated as
   flat: it offers no hierarchy, and "three of your five items are groups" is not
   an actionable message.
3. **The group label is exempt from A-2.** It is structure, not content, and in
   the top tier the anchor card names the groups anyway — so a label that really
   is a taught concept is taught there.

**Test plan first** — the assertions that go red, in this order. Each one fails
on its assertion, not on an import.

| # | Assertion | Red because |
|---|---|---|
| 1 | `_enumeration_size` counts members on a grouped back and items on a flat one | the helper does not exist |
| 2 | `_groups` recognises `[*A*: x, y]` and refuses a mixed list | the helper does not exist |
| 3 | **E-1 is silent** on `'Name the four steps.'` over `#list([*A*: x, y], [*B*: z, w])` | **reported today** — the measured false error of R-4 |
| 4 | **A-2 quotes `w`, not `A`** on a grouped back nothing else names | today it quotes the label, per R-5 |
| 5 | E-2 warns on a cue + numeral ≥ 3 over a prose back | no such check |
| 6 | E-2 is **silent** on `F3M2Q`'s front | guards R-2 against a numeral-anywhere implementation |
| 7 | E-2 is silent on a two-count front and on a front with no cue | inherits `_announced_count`'s guards |
| 8 | E-3a warns on seven flat items, and is silent once grouped | no such check |
| 9 | E-3b warns on ten items whether grouped or not | no such check |
| 10 | `check_docs.py` fails when `skills/cards/SKILL.md` has no tier table | the check does not exist, and the table does not either |
| 11 | the demo project is consistent under `--strict` | red until the fixture grows (R-7), and closed last |

Assertions 3 and 4 are the two that protect shipped behaviour. They are written
**before** any new check, so the regression they describe cannot be introduced
and then noticed.

## Complexity Tracking

No constitution gate answered "no", so this table is empty. One thing is worth
recording anyway, because it looks like a violation and is not:

| Item | Gate | Why it is not a violation |
|---|---|---|
| A-2 stops checking the group label | — | Not a coverage regression in practice: no card in the repository uses the group shape, so nothing that passes today begins to fail and nothing that fails today begins to pass (data-model I-8). It is a deliberate narrowing recorded as FR-011c, not a silent one. |
