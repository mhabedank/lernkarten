# Implementation Plan: The side marker leaves the card and becomes document metadata

**Branch**: `design/side-marker-metadata` | **Date**: 2026-09-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-side-marker-metadata/spec.md`

## Summary

Drop `1/2` / `2/2` from the card footer — a third encoding of one bit, and the
only one made of text — and collapse the right-hand footer block when a card has
no id. The signal it carried moves into a `<face>` label in the document
metadata, which `lernkarten build --face-map PATH` writes out as JSON on request,
so the print-order guarantees from #48 keep being asserted against a real build
by the real command, exactly and without `pdftotext`. Every step was prototyped
against the pinned engine first; see [research.md](./research.md).

## Technical Context

The project's values, unchanged by this feature except where noted.

**Language/Version**: Python `>=3.12`, ruff targeting `py312`.

**Secondary language**: Typst — `templates/card.typ` is where the visible change
happens.

**Runtime dependencies**: `pyyaml==6.0.3`. **Unchanged** — the face map is
`json`, which is stdlib.

**Dev dependencies**: `pytest`, `ruff`, `pillow`, `pyyaml`. **Unchanged.**

**Optional external tools**: `pdftotext`. This feature *reduces* reliance on it:
the print-order tests stop needing a text layer and stop skipping without one.
Other tests still use it and keep their skip.

**Storage**: plain files. The face map is written only where the user points it.

**Testing**: pytest. The engine-dependent assertions go in `tests/test_e2e.py`
(`LERNKARTEN_E2E=1`), the pure arithmetic in `tests/test_build_pdf.py`, the new
documentation gate in `tests/test_check_docs.py`.

**Typesetting engine**: Typst 0.15.1, pinned in `scripts/engine.py`. **Unchanged
— no checksum bump.**

**Target Platform**: Windows, macOS, Linux. Nothing here is platform-specific;
the one path concern is that `--face-map` takes a path from the user, so the
error when it cannot be written must be a plain message, not a traceback.

**Project Type**: CLI tool + Claude Code plugin.

**Performance Goals**: `--face-map` costs one extra engine invocation — the same
shape as the `<overflow>` query that already runs on every build. A build that
does not ask for the map pays nothing.

**Constraints**: the card must survive a black-only laser print. That constraint
is the *reason* for this change rather than a risk to it: the two remaining face
signals are each colour **and** shape **and** position; the one being removed was
the only one that was neither.

**Scale/Scope**: three source files (`templates/card.typ`,
`scripts/build_pdf.py`, `scripts/check_docs.py`), three test modules, four
documents plus the landing page.

## Dependency Decisions

**No dependency change.** Nothing is added, nothing is replaced, and one optional
tool (`pdftotext`) loses a caller. The reuse question (constitution III) has a
concrete answer: the metadata-plus-`typst query` mechanism already exists in this
repository for `<overflow>`, and the new query is the same call with a different
label. Serialising the map is `json.dumps`.

## Constitution Check

*GATE: passed before Phase 0. Re-checked after Phase 1 — see the note below the
table.*

| # | Gate | Pass? |
|---|---|---|
| I | The two halves stay coupled only through the file formats | **yes** — no skill changes, no format changes; `cards.json` (the engine payload) is byte-identical |
| II | **(GATED)** New dependency installs everywhere / new binary self-fetching or optional | **n/a** — none added |
| III | **(GATED)** Nothing hand-rolled that a library does | **yes** — the `<overflow>` mechanism is reused as-is; `json` is stdlib |
| IV | **(GATED)** Vetting table for every new dependency | **n/a** — none added |
| V | Code lands in an existing module | **yes** — `build_pdf.py` and `check_docs.py`; no new `scripts/` file |
| VI | Imports stay acyclic; format reader and engine locator remain leaves | **yes** — no new imports at all |
| VII | **(GATED)** No user content; examples stay subject-agnostic | **yes** — the demo project is the only material touched |
| VIII | No committed binaries | **yes** |
| IX | Typst sources edited, never generated files | **yes** — `templates/card.typ`; nothing in `output/` |
| X | Skill frontmatter valid | **n/a** — no skill changes. Verified: no `SKILL.md` mentions the marker |
| XI | **(NON-WAIVABLE)** Every behaviour tested first | **yes** — the red-first order is in [Phase 1](#test-plan-red-first) and drives the task order |
| XII | The four gates pass; ruff not loosened | **yes** |
| XIII | English throughout | **yes** |
| XIV | Branch `design/side-marker-metadata`; `main` untouched; commit subjects prefixed | **yes** — `design:` for the card and the docs, `test:`/`fix:` where they fit |
| XV | Engine version unchanged, or all six checksums bumped | **yes** — unchanged, 0.15.1 |
| XVI | `docs/design.md` read first; colour doubled by shape; no type shrunk; brand PNGs re-rendered | **yes** — read; nothing is set smaller (text is removed); the mark is untouched so no re-render |
| XVII | Card style and Typst escaping rules respected | **n/a** — no card *content* changes |

**Open-item check**: the constitution's one remaining open item is dependencies
pinned by version rather than by hash. This feature neither closes nor touches
it.

**Post-Phase-1 re-check**: unchanged. The design adds one CLI option, one query
and one documentation gate, all inside existing modules. No gate moved.

## Project Structure

### Documentation (this feature)

```text
specs/013-side-marker-metadata/
├── plan.md              # this file
├── spec.md
├── research.md          # Phase 0 — measured against the pinned engine
├── data-model.md        # Phase 1 — the face map, and why no file format changes
├── quickstart.md        # Phase 1 — how to see it work
├── contracts/
│   └── face-map.md      # Phase 1 — the --face-map option and the JSON it writes
└── checklists/requirements.md
```

### Source Code (files this feature touches)

```text
scripts/
├── build_pdf.py            # --face-map, the <face> query, padding to the page count
└── check_docs.py           # the new gate: no shipped doc claims the printed marker

templates/
└── card.typ                # footer(): the marker goes, the id block collapses,
                            # face(): the <face> label appears

tests/
├── test_build_pdf.py       # unit — the map's arithmetic, no engine
├── test_e2e.py             # the real command: the map, the print order, the ink
└── test_check_docs.py      # the new gate, and its known false positive

docs/
├── design.md               # the band table, the id paragraph, the no-id sentence
├── workflow.md             # the card description
├── testing.md              # the manual footer row, the empty-band row, --face-map
└── index.html              # three facsimile card ids + the footer-band paragraph
```

**Structure Decision**: everything lands in files that already exist. The face
map belongs in `build_pdf.py` because that module already owns the workdir, the
engine call and the `<overflow>` query it is modelled on — a new `scripts/`
module would have to be handed all three (constitution V). The documentation gate
belongs in `check_docs.py` for the same reason: four checks of exactly this shape
already live there.

### The two halves

**Model-driven work** (`skills/`): none. Confirmed by search — no `SKILL.md`
mentions `1/2`, `2/2` or the footer's side marker. `check_project.py` is
untouched.

**Deterministic work**: `templates/card.typ` (the visible change and the label),
`scripts/build_pdf.py` (the option, the query, the map), `scripts/check_docs.py`
(the gate). Covered by `tests/test_e2e.py`, `tests/test_build_pdf.py` and
`tests/test_check_docs.py`.

**The seam**: none — the halves are untouched. The only interface that changes is
a new *diagnostic* output, specified in [contracts/face-map.md](./contracts/face-map.md).

## Phase 0: Research

Complete — [research.md](./research.md). Ten findings, all measured against Typst
0.15.1 and the real templates. The four that change the implementation:

- **`here().page()` works** inside `face()`: 66 entries for 33 cards, no
  duplicates, correct pages in both print orders (R1, R2).
- **The face query must be given `sides`** — unlike `overflowing()`, which
  deliberately omits it. Getting this wrong yields a duplex map for a simplex
  build that looks entirely plausible (R3).
- **Divider-only pages return nothing from the query**, so the build pads the map
  to the document's page count (R4).
- **The PDF is only byte-comparable with `SOURCE_DATE_EPOCH` pinned** — Typst
  writes `/CreationDate` (R5).

And one that shapes the gate: `scripts/leitner.py:25` says "1/2/5/8/14 cm", so a
naive `\b[12]/2\b` has a false positive in this repo on day one (R8).

## Phase 1: Design

### What changes in `templates/card.typ`

1. `face(card, back, body)` emits, as its first act,
   `context [#metadata((ref: card.ref, side: "front"|"back", page: here().page()))<face>]`.
   It sits in `face()` rather than in `front()`/`back()` because `face()` is the
   one place that already knows which side it is laying out, and because a
   divider never goes through it.
2. `footer()` drops `side` entirely. The id block becomes conditional: when
   `card.id == ""`, neither the box nor the vertical rule in front of it is
   placed, and `id-w` is `0mm`, so the wordmark box takes the width. The band
   keeps its height and its top rule in every case, including
   `--no-logo` with no id, where the band is empty apart from that rule.
3. The comment that explained the stranded separator is rewritten to explain the
   collapse — the reasoning it recorded is what makes the collapse necessary.

### What changes in `scripts/build_pdf.py`

1. `--face-map PATH` on `build`, default `None`. Help text names it a diagnostic
   and says what it writes. Works with `--check` too (R10).
2. `face_entries(binary, workdir, margin, logo, grid, sides)` — the query,
   modelled line for line on `overflowing()`, **with `sides` passed through** and
   a comment at the call site saying why (R3).
3. `face_map(entries, page_count)` — pure, unit-testable: groups entries by page
   and pads to `page_count` so a divider-only page appears with no faces (R4).
4. `write_face_map(path, mapping)` — `json.dumps`, and a plain
   `sys.exit(f"ERROR: cannot write the face map to {path}: …")` on `OSError`.
5. The page-count arithmetic (`pages(...)`, raised for dividers) moves above the
   `with tempfile.TemporaryDirectory()` block, since the map is written inside it
   and needs the total. Nothing else about the ordering changes.

### What changes in `scripts/check_docs.py`

`check_printed_side_marker(errors)`, in the shape of the four gates already
there: a narrow token `(?<![\d/])[12]\s*/\s*2(?![\d/])`, over
`gated_files() + sorted((ROOT / "docs").glob("*.html"))`, exempting the
historical idiom the file already defines (`was`, `until`, `since v`, `no longer`).
The error names the file, the line and what the card does now.

### Error messages a user can see

| Situation | Message |
|---|---|
| `--face-map` at an unwritable path | `ERROR: cannot write the face map to <path>: <reason>` — exit 1, before the "OK:" line |
| A doc reintroducing the claim | `docs/x.md:12: '1/2' is given as something the card prints — the face is in the header marker and the footer box, and the machine-readable signal is `--face-map`' |

### Where it is documented

`docs/testing.md` — `--face-map` is a contributor's tool, so it is explained
where contributors read, plus two manual rows (the footer band as a whole, and
the empty band under `--no-logo` with no ids). `docs/design.md` gains the
*reason*: the face was encoded three times, two of them colour-plus-shape, and
the third has moved into the document where the build can read it. Every link
added must resolve — `check_docs.py` fails on a dead one.

### Test plan (red first)

In this order. Each line is an assertion that fails before its implementation
exists, and the order is chosen so `main` would be green at every commit — the
map arrives **before** the ink it replaces is removed.

| # | Test | Where | Red because |
|---|---|---|---|
| 1 | `face_map()` groups entries by page and pads to the page count, empty list included | `test_build_pdf.py` | the function does not exist |
| 2 | `face_map()` keeps a page that carries no face, rather than skipping the number | `test_build_pdf.py` | same |
| 3 | `--face-map` writes a JSON naming every page, ref and side for the demo deck | `test_e2e.py` | the option does not exist |
| 4 | the map for `--sides simplex` differs from the map for `--sides duplex` on the same deck | `test_e2e.py` | catches R3's trap: a map built without `sides` passes every other assertion |
| 5 | a build with no `--face-map` writes the PDF and nothing else | `test_e2e.py` | the option does not exist |
| 6 | `--face-map` at an unwritable path exits non-zero naming the path | `test_e2e.py` | same |
| 7 | with `SOURCE_DATE_EPOCH` pinned, the PDF is byte-identical with and without the map | `test_e2e.py` | same |
| 8 | `--grid a8 --dividers 4` yields a map whose divider-only pages carry no face | `test_e2e.py` | same |
| 9 | the print-order tests read the map instead of the text layer, and no longer skip without `pdftotext` | `test_e2e.py` | `face_marks_per_page` is still the text-layer helper |
| 10 | no page of the demo deck carries a `[12]/2` token, at either grid, with and without `--no-logo` | `test_e2e.py` | the template prints it |
| 11 | a deck with no ids prints neither `·` nor a marker | `test_e2e.py` | it prints the marker today |
| 12 | the template places the id block only when the card has an id | `test_e2e.py` | it is unconditional today |
| 13 | the id measured for the clip cap is the bare id | `test_e2e.py` | `MEASURE` still measures `A45DK · 1/2` |
| 14 | a synthetic doc claiming the card prints `1/2` fails the new gate | `test_check_docs.py` | the gate does not exist |
| 15 | `1/2/5/8/14 cm` does **not** fail the new gate | `test_check_docs.py` | a naive token would fail it (R8) |

Test 12 is the one assertion in this list that reads the template source rather
than an artifact. A drawn rule is not in the text layer and the repository has no
image-comparison machinery, so the observable evidence stops at "nothing is
printed there" (test 11). The precedent is
`test_the_template_sets_the_id_at_the_agreed_size`, which reads the template for
the same reason. The band's *appearance* gets a manual row in `docs/testing.md`
instead of a false claim of coverage.

### Sequencing

1. Tests 1–8, then the `--face-map` implementation. The map exists and is proven.
2. Test 9 — migrate the print-order assertions onto it. The guarantee now rests
   on the new signal while the old one is still printed, so a mistake here shows
   up as a failure, not as a gap.
3. Tests 10–13, then the template change. The ink goes only once nothing depends
   on it.
4. Tests 14–15, then the gate, then the documents and the landing page.

Steps 2 and 3 are the whole reason this is not a one-line deletion.

## Risks

| Risk | Mitigation |
|---|---|
| The face query is called without `sides` and every test still passes | Test 4 exists for exactly this; the call site carries a comment naming the trap (R3) |
| `here().page()` behaves differently inside `place()` on a divider sheet | Measured with dividers at `a8` (R4); the label lives in `face()`, which dividers never enter |
| The new gate fires on innocent text | Its false positive was found before it was written (`leitner.py`, R8) and is test 15 |
| A reader of an old printed deck is confused | Accepted in the spec; both remaining face signals are unchanged, and they are the ones a learner actually reads |

## Release note

By `CONTRIBUTING.md` § Releases this is a **minor**: `--face-map` is a flag a
user can pass that the tool never claimed before. The card losing an element is
not itself a version question — nothing documented promised the marker except
the documents this feature rewrites. The release itself is a separate step and
not part of this branch.

## Complexity Tracking

No Constitution Check row is a "no", so this table is empty.
