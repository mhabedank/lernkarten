# Phase 0 Research: the side marker leaves the card

**Feature**: [spec.md](./spec.md) | **Date**: 2026-09-11

Everything below was measured with the pinned engine (Typst 0.15.1, the one
`scripts/engine.py` fetches) against the **real templates** and the **real demo
deck**, not reasoned about. The scratch prototype lived in `/tmp` and touched no
file in the repository.

## R1 — Can a Typst label carry the page it lands on?

**Decision**: yes. `context [#metadata((id: …, side: …, page: here().page()))<face>]`
inside `face()` in `templates/card.typ` gives one entry per laid-out face, with
the page number the face actually printed on.

**Measured**: the prototype patched `face()` to emit the label, compiled the 33-card
demo deck at `a7`, and queried it:

| Build | Entries | Unique `(id, side)` | Pages |
|---|---|---|---|
| `--sides duplex` | 66 | 66 | 1 front, 2 back, 3 front, 4 back … 9 front, 10 back |
| `--sides simplex` | 66 | 66 | 1–5 front, 6–10 back |

33 cards × 2 faces = 66, with no duplicates, and both orders come out exactly as
#48 promises. This is the print-order guarantee read off the document instead of
out of the text layer.

**Alternatives considered**:

- *Keep reading the printed marker* — the thing this feature removes.
- *Infer the face from geometry* (the back is column-mirrored): already ruled out
  in the spec. A deck of one card has two pages with identical grids.
- *PDF page labels via `#set page(numbering:)`* — would need a PDF library to
  read back (a new dev dependency, constitution IV) and shows up in the reader's
  page box. Rejected.

## R2 — Does `measure()` duplicate metadata?

**Decision**: no. Content carrying a label can be measured and then placed; only
the placed copy is introspected.

**Measured**: a document that measures a body containing `<face>` and then emits
that same body queries back exactly one entry. This matters because `card.typ`
measures the prompt and the answer before laying them out, and a doubled entry
would corrupt the map silently.

## R3 — Where does the query have to run, and with which inputs?

**Decision**: inside the `with tempfile.TemporaryDirectory()` block in
`build_pdf.main()`, beside `warn_about_overflow(...)`, and it **must** be given
`sides`.

**Rationale**: the compile workdir is destroyed when the block exits, which is
the whole reason the spec put the map behind the real command. And
`engine_inputs()` has a documented exception — `overflowing()` deliberately omits
`sides`, because what fits on a card does not depend on the page order. The face
map is the one query where the opposite is true: `sides` *is* the answer. Calling
`engine_inputs(margin, logo, grid)` for the face map would return a duplex map
for a simplex build, and every assertion would still look plausible.

This is exactly the failure mode `engine_inputs()`'s docstring was written for,
one argument over. It gets its own comment at the call site.

## R4 — Pages that carry no card face

**Decision**: the build pads the map to the document's page count; the query
alone is not enough.

**Measured**: 16 cards at `a8` with `--dividers 4` puts the dividers on sheet
index 1, so the document is four pages and the query returns faces for two of
them:

| Build | Query returns | Pages that carry no face |
|---|---|---|
| `--sides duplex` | page 1 front (16), page 2 back (16) | 3, 4 |
| `--sides simplex` | page 1 front (16), page 3 back (16) | 2, 4 |

A divider-only page is a real page with no card on it, so the map lists it with
an empty face list rather than skipping the number — otherwise a reader cannot
tell "no cards here" from "page missing". `build_pdf` already computes that total
(`pages(len(cards), grid)`, raised to `2 * (divider_page + 1)` when dividers open
a further sheet); the only change is that the arithmetic has to happen *before*
the workdir closes instead of after.

## R5 — Is the PDF really unchanged when the map is asked for?

**Decision**: yes, and it is testable — but only with `SOURCE_DATE_EPOCH` pinned.

**Measured**: two identical compiles one second apart differ in bytes, because
Typst writes `/CreationDate` and `/ModDate` into the PDF. With
`SOURCE_DATE_EPOCH=1700000000` in the environment, the same two compiles are
byte-identical.

So SC-002a is asserted as: with `SOURCE_DATE_EPOCH` pinned, `lernkarten build`
with and without `--face-map` produce identical bytes. Without that pin the
assertion would be flaky for reasons that have nothing to do with this feature.

## R6 — `typst query` is deprecated in the pinned engine

**Finding**: 0.15.1 prints

> warning: the `typst query` subcommand is deprecated
> hint: use `typst eval 'query(<face>)' --in file.typ` instead

on every invocation. `overflowing()` already lives with this — the warning goes
to stderr and is discarded.

**Decision**: use the same `typst query` call shape as `overflowing()`, and do
**not** migrate to `typst eval` in this feature.

**Rationale**: consistency beats being half-migrated. Two queries in one file
calling the engine two different ways is worse than two calling it the same
deprecated way, and the migration is a change to an existing, tested code path
that this feature has no reason to touch. `typst eval 'query(<face>).map(it =>
it.value)' --in …` was verified to work on 0.15.1 and returns the identical
payload, so the migration is a clean, separable follow-up — it belongs in its own
issue, together with `overflowing()`.

## R7 — A card with no id still has a name in the map

**Finding**: `build_pdf.load_cards()` sets `ref = card_id or f"{path.stem}-{i}"`
(`scripts/build_pdf.py:448`), and `card.ref` is what the `<overflow>` label
already carries.

**Decision**: the face map names `ref`, not the printed id.

**Consequence**: the map keeps working for exactly the decks US3 is about — the
ones with no ids, whose right-hand footer block disappears entirely. The signal
the tests read is therefore independent of the ink this feature removes, which is
the property that makes the swap safe.

## R8 — How to gate the claim in the docs (FR-009)

**Decision**: a new check in `scripts/check_docs.py`, in the shape of the four
that are already there (`check_sheet_capacity`, `check_a7_is_not_the_default`,
`check_cut_count`, `check_print_order`), over a file set widened to include
`docs/*.html`.

**Findings that shape it**:

- `markdown_files()` is root `*.md` + `docs/*.md` + `skills/*/SKILL.md`;
  `gated_files()` adds `scripts/*.py` and `templates/*.typ` and excludes
  `check_docs.py` itself. **Neither covers `docs/index.html`**, where three
  facsimile cards and one paragraph carry the claim. The new gate needs
  `docs/*.html` in its list — nothing else in this repo reaches that file today
  except the Leitner interval check, which hard-codes `docs/leitner.html`.
- `specs/` is in no file set, so this spec's own quotations of `1/2` cannot trip
  the gate. That is by construction, not luck.
- **A naive `\b[12]/2\b` has a false positive in this repo**:
  `scripts/leitner.py:25` documents the compartment spacing as "1/2/5/8/14 cm".
  The token must refuse a digit or a slash on either side —
  `(?<![\d/])[12]\s*/\s*2(?![\d/])` — and that line becomes a test case, because
  it is the exact shape a future author will write again.
- The gate keys on the **literal token only**, never on the words "side marker":
  the header's red circle and yellow disc are still called the side marker in
  `docs/design.md:99`, and they stay.
- Historical statements stay legal. The file already has the idiom
  (`NOT_A_DEFAULT_CLAIM`: `was`, `until`, `since v`, `no longer`), so a release
  note or a design-history sentence can say what the card used to print.

## R9 — Where the diagnostic goes in the CLI

**Decision**: `lernkarten build --face-map PATH`, a visible option with a help
string that says what it is for, off by default.

**Rationale**: `--check`, `--dividers` and `--box` set the house style — an
option with a full sentence of help. The repo has no `argparse.SUPPRESS`
anywhere, and a hidden flag would contradict Principle "no user content, no
surprises" in spirit: an option that exists should be discoverable. The spec's
"not sold to users as a feature" is met by the help text naming it a diagnostic
and by `docs/testing.md` being where it is explained, not `README.md`.

**Alternatives considered**:

- *An environment variable* (`LERNKARTEN_FACE_MAP`) — precedent exists
  (`LERNKARTEN_E2E`, `LERNKARTEN_ENGINE`), but both of those exist because they
  configure something *outside* one command's arguments. A per-build output path
  is an argument.
- *A sibling subcommand* (`lernkarten faces`) — would have to re-do argument
  parsing, settings precedence, grid resolution and the compile, to answer a
  question about a build that just happened. Rejected as duplication
  (constitution III).

## R10 — Does `--face-map` interact with `--check`?

**Decision**: it works with `--check` too, and that is not a special case.

`--check` compiles the document in the workdir and writes no PDF; the face map
describes the document, which exists either way. Refusing the combination would
be an arbitrary rule to explain, implement and test. The `--check` path is where
the e2e tests can get a map without a PDF at all, which is a small bonus.

## Open questions

None. FR-006's clarification was answered before planning (option B), and every
unknown this plan depended on was measured above.
