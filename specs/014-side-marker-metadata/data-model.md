# Phase 1 Data Model: the face signal

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-09-11

## No file format changes

The six formats that couple the two halves (constitution I) are untouched:

| Artifact | Change |
|---|---|
| `goal.md` | none |
| `sources.yaml` | none |
| `knowledge/<id>/<doc>.md` | none |
| `catalog/topics.md` | none |
| `cards/*.yaml` | none |
| `figures/<id>/<file>` | none |

`cards.json`, the payload `build_pdf.payload()` hands the engine, is byte-identical
too: the `<face>` label is built by the template out of fields the card already
carries (`ref`) and out of where the template is laying it out (`back`,
`here().page()`). No deck on any disk needs migrating, and a deck written before
ids existed keeps building — it is the one US3 is about.

## Entities

### Face signal

One card face, as the laid-out document knows it. It exists only inside the
compiled document; it is not stored anywhere and is not part of any format a
user writes.

| Field | Type | Meaning |
|---|---|---|
| `ref` | string | the card's `ref` — its `id`, or `<file-stem>-<index>` when it has none (`scripts/build_pdf.py:448`) |
| `side` | `"front"` \| `"back"` | which face this is |
| `page` | integer, 1-based | the page of the built document it printed on |

**Why `ref` and not `id`**: the map has to keep working for a deck with no ids,
which is exactly the deck whose footer block this feature removes. Naming the
printed id would make the signal depend on the ink being deleted. `ref` is
already what the `<overflow>` label carries, so this is the established handle
rather than a new one.

**Invariants** (measured in [research.md](./research.md) R1/R2):

- Exactly one signal per card face. 33 cards yield 66 signals, never 132 — a
  measured body carrying the label does not duplicate it.
- Every signal's `page` is a real page of the document.
- The set of `(ref, side)` pairs is the deck itself: every card appears once as
  `front` and once as `back`.

### Face map

Every face signal of one built document, grouped by page and padded to the
document's page count. This is the artifact `--face-map` writes; its wire format
is specified in [contracts/face-map.md](./contracts/face-map.md).

| Field | Type | Meaning |
|---|---|---|
| `sides` | `"duplex"` \| `"simplex"` | the print order this document was built in |
| `grid` | string | the grid alias, e.g. `2x4` |
| `pages` | list | one entry per page of the document, in order, none skipped |
| `pages[].page` | integer | the page number, 1-based and contiguous |
| `pages[].faces` | list of face signals without their `page` | the faces on that page, in layout order |

**Invariants**:

- `len(pages)` equals the document's page count, so a page carrying only Leitner
  dividers appears with `faces: []` rather than being absent (R4). "No cards
  here" and "page missing" must not look the same.
- A page's faces are all the same `side`. A sheet is printed one face at a time —
  this is the property the print-order tests assert, and the map is what makes it
  assertable.
- The map describes the document that was just compiled. Asking for it does not
  change that document: with `SOURCE_DATE_EPOCH` pinned, the PDF is byte-identical
  with and without `--face-map` (R5).

### What the map is not

- **Not a card format.** Nothing reads it back into a build; nothing in `cards/`
  refers to it.
- **Not written by default.** A build that does not ask for it produces exactly
  the files it produced before this feature.
- **Not a substitute for the printed id.** The id stays on the card — it is the
  handle a learner reads off paper and says out loud. The map is for the machine.

## State transitions

None. The face map is derived, written once, and owned by whoever asked for it.
