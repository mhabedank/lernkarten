# Implementation Plan: A short, stable card id

**Branch**: `feat/card-id` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-card-id/spec.md`

## Summary

Replace the position-derived card id (`f"{path.stem}-{i}"`, which silently
changes when a card is inserted, deleted or the file renamed) with a **5-character
Crockford Base32 id stored as a per-card `id:` key** in `cards/*.yaml`, assigned
by `/cards` on write and backfillable by a new `lernkarten id` subcommand.

The approach needs **no new dependency**: PyYAML — already a runtime dependency —
exposes `compose()`, which returns exact line/column marks for every card, so
backfill is a text splice at a library-supplied position rather than a
reserialisation. The id also **grows from 4.6 pt to 8 pt** on the printed card,
measured against the footer's `cw / 3` cap and balanced against the 5 pt
wordmark beside it.

See [research.md](./research.md) for both decisions and for three corrections to
the premises this plan was handed.

## Technical Context

**Language/Version**: Python `>=3.12` (`pyproject.toml`), ruff targeting `py312`. CI tests 3.12 and 3.13, and an `oldest-python` job builds cards on the floor. Unchanged by this feature.

**Secondary language**: Typst — this feature touches `templates/card.typ` only (the footer band's id size and the `id-w` calculation).

**Runtime dependencies**: `pyyaml==6.0.3`, declared in `REQUIREMENTS` in `scripts/deps.py`. **Unchanged** — see the Dependency Decisions section. This feature deliberately uses PyYAML's existing `compose()` API rather than adding a round-trip library.

**Dev dependencies**: `pytest>=9.1.1`, `ruff==0.16.2`, `pillow>=11,<13`, `pyyaml`. Unchanged.

**Optional external tools**: `pdftotext`. Not touched — id generation and validation never shell out.

**Storage**: plain files on disk. The change is confined to `cards/*.yaml`.

**Testing**: pytest, seven levels per `docs/testing.md`. **Test-first is mandatory** (constitution XI). This feature adds cases at four levels: unit (`test_build_pdf.py`), a new id module's unit tests, contract (`test_check_project.py`), and end-to-end (`test_e2e.py`, opt-in via `LERNKARTEN_E2E=1`).

**Lint/format**: ruff — line length 100, `select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]`. Unchanged.

**Typesetting engine**: Typst 0.15.1, pinned by SHA-256 per platform. **Version unchanged — no checksum bump** (Principle XV).

**Target Platform**: Windows, macOS and Linux as equals. This feature **writes files**, which makes line endings a genuine cross-platform concern; CRLF preservation is verified in research and is an explicit test.

**Project Type**: CLI tool + Claude Code plugin. Single module, flat `scripts/`.

**Performance Goals**: unchanged. Id generation is `secrets.choice` over a 32-symbol alphabet; the cost is invisible next to a Typst compile.

**Constraints**: frictionless install (nothing new to install here); output survives black-only laser print — the id is muted grey monospace on paper and gets *larger*, so print legibility improves.

**Scale/Scope**: ~2 000 lines of Python across 11 flat modules. This feature adds one module (`scripts/cardid.py`) and edits five.

## Dependency Decisions

**No dependency change.**

### Reuse check (constitution III)

**Is anything being hand-rolled here?** **No** — and this was the plan's main
open question, so the reasoning is recorded rather than asserted.

Backfill must insert a key into a YAML file while preserving comments, quoting,
key order, encoding and line endings byte-for-byte (FR-006). The obvious
candidate library is `ruamel.yaml` in round-trip mode.

**It was considered and rejected on the requirement, not on cost**:
`ruamel.yaml` *reserialises* the document. It preserves comments and most
quoting, but normalises sequence indentation, line width and some quote styles.
It cannot promise byte-identity, so adopting it would force FR-006's test to
assert something weaker than FR-006 states — which is how a requirement quietly
stops being true.

**The chosen approach does not replace a library, it uses one.**
`yaml.compose()` — PyYAML, already a runtime dependency — returns a node tree
carrying `start_mark`/`end_mark` line and column for every node. The library
parses; the library locates each card; the only original code is a `str`
insertion at a position the library supplied. No scanner, no parser, no emitter
is re-implemented.

The `minyaml.py` precedent (222 lines of hand-written YAML parsing, deleted in
favour of PyYAML) is the thing Principle III exists to prevent, and this is not
it. `yamlio.py`'s docstring makes that precedent explicit, which is why the
distinction is drawn here in full rather than waved at.

Verified against real fixtures — byte-exact `remove(insert(src)) == src` on LF,
CRLF and a German deck with umlauts. Evidence table in
[research.md § R-1](./research.md).

### Vetting (constitution IV)

Not applicable — no new package, dev tool or binary.

**Removals**: none. The `f"{path.stem}-{i}"` expression in
`scripts/build_pdf.py` is replaced, but it is an expression, not a dependency.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Pass? |
|---|---|---|
| I | The model-driven and deterministic halves stay coupled only through the four file formats | [x] The seam is `cards/*.yaml` and only that. `/cards` writes `id:`; the deterministic half reads, validates, renders and backfills it. Neither half calls the other. |
| II | **(GATED)** Any new dependency installs with a plain `pip install`…; any new binary is self-fetching + checksum-pinned, or genuinely optional | [x] **No new dependency and no new binary.** Vacuously satisfied — see Dependency Decisions. |
| III | **(GATED)** Nothing is hand-rolled that a vetted library already does — or the Reuse check above says why | [x] The Reuse check above says why, at length. PyYAML does the parsing and supplies the positions; only the text splice is ours. |
| IV | **(GATED)** Every new dependency has a completed vetting table above, and a reviewer read it | [x] No new dependency, so no table is owed. |
| V | Code lands in an existing module where one fits; any new `scripts/` file has a reason and a docstring | [x] One new module, `scripts/cardid.py`. Justification in Structure Decision below; it is a **leaf** so `build_pdf`, `check_project` and the new CLI path can all import it without a cycle. |
| VI | Script imports stay acyclic; the format reader and the engine locator remain leaves | [x] `cardid.py` imports only `yamlio` (and stdlib `secrets`/`re`). `yamlio` and `engine` stay leaves. No cycle: `build_pdf → cardid → yamlio`. |
| VII | **(GATED)** No user content committed; nothing forced past `.gitignore`; examples stay subject-agnostic | [x] New fixtures go in `tests/fixtures/demo-project/`, which is invented material versioned on purpose. `cards/example.yaml` gains ids but stays a probability example. **Needs an explicit note in the PR description.** |
| VIII | No binaries committed; new test material is generated from a text source | [x] Every new fixture is a text `.yaml`. `make_testdata.py` is not involved. |
| IX | Typst sources edited, never generated files; nothing in `output/` hand-edited | [x] `templates/card.typ` is a source. Nothing in `output/` is touched. |
| X | Skill frontmatter valid — `name` == folder, `description` names its triggers | [x] `skills/cards/SKILL.md` body changes; frontmatter untouched. `check_docs.py` covers it. |
| XI | **(NON-WAIVABLE)** Every behaviour was tested first… Prompt changes have a failing `check_project.py` check | [x] The full red-first ordering is in Phase 1 below. The `skills/cards` change is gated by a new `check_project.py` check plus a `test_check_project.py` case, per the constitution's rule for the model-driven half. |
| XII | The four gates pass; ruff config not loosened without a stated reason | [x] No ruff config change. All four gates run before the PR, plus `LERNKARTEN_E2E=1` once. |
| XIII | English throughout | [x] |
| XIV | Branch is `<prefix>/<short-kebab-name>`; `main` untouched directly; commit subjects prefixed | [x] `feat/card-id`, already checked out. Commits prefixed `feat:`, `test:`, `docs:`, `skill:`. |
| XV | Engine version unchanged, or every platform checksum bumped with it | [x] Typst stays 0.15.1. No checksum change. |
| XVI | `docs/design.md` read before any visible change; colour doubled by shape; no type shrunk to fit; brand PNGs re-rendered | [x] Read — and it changed the answer (see C-3 in research). The id **grows**, never shrinks. No colour change. Mark and wordmark untouched, so **no PNG re-render**. |
| XVII | Card style and Typst escaping rules from `CLAUDE.md` respected | [x] The id is a plain literal — no Typst markup, no escaping concerns. Card text is untouched. |

**Open-item check**: this feature does **not** touch the constitution's one
still-open item (dependencies pinned by version rather than by hash). It adds no
dependency, so it neither closes nor works around it.

## Project Structure

### Documentation (this feature)

```text
specs/005-card-id/
├── plan.md              # This file
├── research.md          # Phase 0 — the two decisions, three corrections
├── data-model.md        # Phase 1 — the format change
├── quickstart.md        # Phase 1 — how to validate it end to end
├── contracts/
│   └── cards-yaml.md    # Phase 1 — the `cards/*.yaml` contract, versioned
├── checklists/
│   └── requirements.md  # from /speckit-specify + /speckit-clarify
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

Rows this feature touches, marked. Untouched rows deleted.

```text
bin/
└── lernkarten              # EDIT — add "id" to COMMANDS, dispatch to cardid

scripts/
├── deps.py                 # untouched (leaf)
├── engine.py               # untouched (leaf)
├── yamlio.py               # untouched — compose() is used via PyYAML directly
├── cardid.py               # NEW (leaf+) — alphabet, generate, normalise,
│                           #   validate, locate, insert, backfill, reassign
├── build_pdf.py            # EDIT — read card["id"], drop f"{stem}-{i}"
├── check_project.py        # EDIT — duplicate / alphabet / length / type checks
└── check_docs.py           # untouched

skills/
└── cards/SKILL.md          # EDIT — assign an id on write; never change one

templates/
└── card.typ                # EDIT — id size 4.6pt → 8pt; handle a missing id

tests/
├── test_cardid.py          # NEW — unit: alphabet, generation, round-trip
├── test_build_pdf.py       # EDIT — id read from the file, stability cases
├── test_check_project.py   # EDIT — the four new failure modes (contract)
├── test_e2e.py             # EDIT — backfill through the real command
└── fixtures/demo-project/
    ├── cards/*.yaml        # EDIT — ids added to the demo decks
    └── broken/             # NEW files — duplicate, bad alphabet, bad length,
                            #   non-string id

cards/example.yaml          # EDIT — ids added; it is the schema reference
CLAUDE.md                   # EDIT — schema + correct the stale dependency claim
docs/design.md              # EDIT — record the id's new size
docs/testing.md             # EDIT — the manual-checklist items (SC-007, advisory wording)
```

**Structure Decision**: one new module, `scripts/cardid.py`.

Three existing modules were considered first, as Principle V requires:

- **`yamlio.py`** — rejected. It is deliberately "a thin layer over PyYAML" that
  *reads* the YAML this project owns, and it is a **leaf** that `build_pdf`,
  `check_project` and `check_docs` all depend on. Putting id semantics (an
  alphabet, a generator, a collision policy) inside it would make the format
  reader carry card-domain knowledge and would widen a leaf everything imports.
- **`build_pdf.py`** — rejected. It already owns the build and `--check`;
  `check_project.py` would then have to import id logic *through* the build
  module, which is the wrong direction and drags the engine locator into a code
  path that must work without an engine (FR-012).
- **`check_project.py`** — rejected. It imports `build_pdf`, so id logic living
  there could not be used by `build_pdf` without a cycle (Principle VI).

`cardid.py` is a leaf that imports only `yamlio` and stdlib, so all three callers
plus `bin/lernkarten` reach it without a cycle. It gets a docstring saying what
it is for and why it is not in `yamlio`.

### The two halves

**Model-driven work** (`skills/`): `skills/cards/SKILL.md` gains the rule that
every card it writes carries a fresh `id:`, that an id already present is never
altered, and that ids are drawn from the 32-symbol alphabet at length 5.

The red artifact — the only way a prompt change is verifiable at all — is a new
check in `scripts/check_project.py` that reports a card file whose cards lack
ids, plus a case in `tests/test_check_project.py` that **fails against what the
current prompt produces**. Written and seen failing before `SKILL.md` is edited.

**Deterministic work** (`scripts/`, `bin/`, `templates/`):

| Change | Test module | Level |
|---|---|---|
| `cardid.py`: alphabet, generate, normalise, validate | `tests/test_cardid.py` | unit |
| `cardid.py`: locate/insert/remove round-trip, CRLF, idempotence | `tests/test_cardid.py` | unit |
| `cardid.py`: collision reassignment, first-occurrence-wins | `tests/test_cardid.py` | unit |
| `build_pdf.py`: id read from file; absent id tolerated | `tests/test_build_pdf.py` | unit |
| `check_project.py`: duplicate / alphabet / length / type | `tests/test_check_project.py` | contract |
| `bin/lernkarten id --backfill` end to end | `tests/test_e2e.py` | e2e (opt-in) |
| `card.typ` id at 8 pt, fits the cap | `tests/test_e2e.py` | e2e (opt-in) |

**The seam**: `cards/*.yaml` — one new optional per-card key, `id`. This is the
fifth contract under Principle I and the only thing crossing between the halves.
Contract in [contracts/cards-yaml.md](./contracts/cards-yaml.md).

## Phase 0: Research

Complete — [research.md](./research.md). Summary:

- **Is there a library for this?** Yes, `ruamel.yaml`, and it was **rejected on
  the requirement**: it reserialises, so it cannot promise the byte-identity
  FR-006 demands. PyYAML's `compose()` — already present — supplies exact
  positions, making the write a text splice. **No dependency change.**
- **Does Typst support the layout this needs?** Yes, unchanged. Measured: the id
  fits the `cw / 3` cap at every size from 4.6 pt to 12 pt once it is 5
  characters. **8 pt chosen**, balanced against the 5 pt wordmark; 11 pt fits
  geometrically but unbalances the band.
- **Does the demo project already carry material?** Partly. The decks exist; the
  four new failure modes are added to `tests/fixtures/demo-project/broken/`,
  all as text files, no generator involved.
- **Degraded path**: id work never needs the engine, the network or `pdftotext`
  (FR-012). Only the two rendering assertions need the engine, and they skip
  without it exactly as the e2e suite already does.
- **Three premises in the brief were wrong** and are corrected in research:
  PyYAML is already a runtime dependency; CLAUDE.md's dependency claim is stale;
  and `docs/design.md` already exempts the card id from the 11 pt floor by name.

## Phase 1: Design

### Format change

One new **optional** per-card key, `id`, in `cards/*.yaml`. Optional is
load-bearing: a deck written before this feature has no `id:` and must still
build to the same page count (US2, SC-003). Full contract, including the
validation table and the backwards-compatibility rule, is in
[contracts/cards-yaml.md](./contracts/cards-yaml.md); entity detail in
[data-model.md](./data-model.md).

### Module placement

`scripts/cardid.py`, a leaf. Public surface:

| Function | Purpose |
|---|---|
| `ALPHABET` | `"0123456789ABCDEFGHJKMNPQRSTVWXYZ"` |
| `generate(taken)` | a fresh 5-char id not in `taken` (`secrets.choice`, redraw on clash) |
| `normalise(text)` | upper-case and fold `I`/`L` → `1`, `O` → `0` (FR-004) |
| `validate(text)` | `None` if valid, else why — length, alphabet, or type |
| `cards_in(src)` | each card's marks, via `yaml.compose` |
| `insert_ids(src, gen)` | splice `id:` as the first key of every card lacking one |
| `remove_ids(src)` | the inverse — exists so the round-trip is *assertable* |
| `backfill(paths)` | all-or-nothing across the invocation (FR-007) |
| `reassign(paths)` | first-occurrence-wins collision resolution (FR-013b) |

`remove_ids` is public on purpose: FR-006's honest test is
`remove_ids(insert_ids(src)) == src`, and a test cannot assert that against a
private helper.

### The errors a user will see

| Situation | Message shape | Exit |
|---|---|---|
| Duplicate id | names **both** cards, file and card, plus the id (FR-008) | non-zero |
| Id outside the alphabet | names file, card, and the offending character (FR-009) | non-zero |
| Id wrong length | names file, card, and the length found | non-zero |
| Id present but not a string | names file and card; not a crash, not "absent" | non-zero |
| No ids anywhere | **one** advisory line per run naming the backfill path | **0** |
| Backfill on an unparseable/unwritable file | names the file and the reason; **nothing written anywhere** | non-zero |
| Reassignment | names the card, the old id and the new one, **and the consequence** (FR-013c) | 0 |

### Documentation

- `CLAUDE.md` — the `cards/*.yaml` schema block gains `id`, **and** the stale
  "a runtime dependency cannot ship today" claim is corrected (research C-2).
- `docs/design.md` — the id's size recorded as 8 pt. No exception clause is
  needed; the document already exempts the card id from the 11 pt floor by name
  (research C-3), and that sentence stays as it is.
- `docs/testing.md` — the two Principle XI manual-checklist items are **named**
  there rather than left implicit: SC-007 (a user reads an id off paper and it
  still resolves after an edit) and the wording of the missing-id advisory.
- Every doc link must resolve or `check_docs.py` fails.

### Test plan first

The order the assertions go red, before any implementation task exists.
**Each must fail on its assertion, not on an ImportError** (Principle XI).

| # | Assertion that goes red | Module | Covers |
|---|---|---|---|
| 1 | `validate("A45DK")` is None; `validate("A45DI")` names `I`; `validate("A45D")` names the length; `validate(12345)` names the type | `test_cardid.py` | FR-003, FR-009 |
| 2 | `normalise("a45dk") == "A45DK"`; `normalise("A45DO") == "A45D0"` | `test_cardid.py` | FR-004 |
| 3 | 10 000 generated ids are all length 5, all in the alphabet, all distinct | `test_cardid.py` | SC-001 |
| 4 | `remove_ids(insert_ids(src)) == src` byte-for-byte, on LF, CRLF and a deck with umlauts | `test_cardid.py` | **FR-006a**, SC-006 |
| 5 | `insert_ids` twice == `insert_ids` once | `test_cardid.py` | SC-006 |
| 6 | `insert_ids` leaves a pre-existing id byte-identical | `test_cardid.py` | FR-006 |
| 7 | backfill over a set where one file is unwritable leaves **every** file unmodified | `test_cardid.py` | FR-007 |
| 8 | two decks sharing an id: the **later by argument order** is reassigned; swapping the arguments reassigns the other | `test_cardid.py` | FR-013b, SC-008 |
| 9 | a card's id survives insert-before, delete-before, file rename, text edit, and `--subtopic` | `test_build_pdf.py` | SC-002 |
| 10 | `load_cards` returns the file's `id`, and no longer any `stem-N` string | `test_build_pdf.py` | FR-001 |
| 11 | a deck with no `id:` still loads and builds | `test_build_pdf.py` | US2, SC-003 |
| 11a | a card with no id renders the side marker **alone** — no id text, no `·` | `test_build_pdf.py` | **FR-005** |
| 11b | assignment gives up after a bounded number of redraws, naming the count and the bound, and writes nothing | `test_cardid.py` | **FR-003b** |
| 11c | a replacement id that itself clashes is redrawn; one pass leaves zero duplicates | `test_cardid.py` | **FR-013d** |
| 12 | checker reports a duplicate naming **both** cards | `test_check_project.py` | FR-008, SC-004 |
| 13 | checker reports bad alphabet / bad length / non-string id | `test_check_project.py` | FR-009 |
| 14 | checker leaves input files **byte-identical** (hash before/after) | `test_check_project.py` | FR-013a, SC-009 |
| 15 | checker reports a deck whose cards have no ids — **this is the red artifact gating the `skills/cards` prompt change** | `test_check_project.py` | FR-002, XI |
| 16 | `lernkarten id --backfill` through the real subprocess assigns ids and preserves comments | `test_e2e.py` | US4 |
| 17 | rendered id width at 8 pt < `cw / 3`, and the size **is 8 pt** | `test_e2e.py` | FR-010, **FR-011**, SC-005 |

Assertions 16 and 17 need the engine and skip without it, as `test_e2e.py`
already does. Everything else runs in the default suite.

**Revised after the Phase 4 checklist review** — assertions 11a, 11b and 11c were
added when `checklists/format-contract.md` found three requirements that had no
assertable form: the no-id fallback *value* (CHK001), redraw termination
(CHK003), and the recursive collision case (CHK004). Assertion 4 now cites
FR-006a, the round-trip formulation that removes FR-006's self-contradiction
(CHK007), and assertion 17 pins 8 pt rather than accepting anything above the old
floor (CHK020). **20 assertions total.**

**Nothing in this table depends on a `--card` flag** — `/print` selection by id
is out of scope (FR-014), and no assertion smuggles it back in.

## Complexity Tracking

Every Constitution Check row passed, so this table is empty by the template's own
rule. Two items are recorded not as violations but because a reviewer will ask:

| Item | Gate | Why it is not a violation |
|---|---|---|
| New module `scripts/cardid.py` | V | Three existing modules were evaluated and each rejected for a stated structural reason (see Structure Decision). It is a leaf, so it introduces no cycle. |
| Backfill writes YAML, a thing this repo has never done | III | The write is a text splice at a position **PyYAML** supplied, not a re-implementation of YAML. The alternative library was rejected on the requirement, not on cost. Full argument in Dependency Decisions. |

Principle XI has no row here. It is not waivable.

## Post-Design Constitution Re-check

Re-evaluated after Phase 1. **No row changed from pass to fail.** The design
added one module (V, VI — justified and acyclic), one optional format key
(I — the seam is stated and contracted), and one visible size change
(XVI — `docs/design.md` read first, and it corrected the premise). Test-first
ordering (XI) is enumerated above with 17 assertions, each tied to a requirement.
