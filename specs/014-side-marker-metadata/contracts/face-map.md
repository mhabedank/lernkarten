# Contract: `lernkarten build --face-map`

**Feature**: [../spec.md](../spec.md) | **Status**: proposed | **Date**: 2026-09-11

The only interface this feature adds. It is a **diagnostic**: it exists so the
front/back identity of every page can be read back from a real build without
reading printed text, which is what the print-order guarantees from #48 are
asserted against once the `1/2` / `2/2` marker is gone.

## The option

```
--face-map PATH
```

| Property | Value |
|---|---|
| Command | `lernkarten build` |
| Default | absent — nothing is written, and the build behaves exactly as it did before this feature |
| Argument | a file path. Relative paths resolve against the working directory, like `-o` |
| Works with `--check` | yes — the document is compiled either way, so the map describes it either way |
| Effect on the PDF | none. With `SOURCE_DATE_EPOCH` pinned, the bytes are identical with and without the option |
| Cost when unused | none — no extra engine call, no extra file |
| Where it is documented | `docs/testing.md` and the `--help` text. Not `README.md`: it answers a contributor's question, not a learner's |

**Help text** (the sentence a user meets in `--help`):

> write a JSON map of which face each page carries — a diagnostic for checking
> the print order, not something a printed deck needs

## The file it writes

UTF-8 JSON, one object.

```json
{
  "sides": "duplex",
  "grid": "2x4",
  "pages": [
    { "page": 1, "faces": [ { "ref": "A45DK", "side": "front" } ] },
    { "page": 2, "faces": [ { "ref": "A45DK", "side": "back" } ] }
  ]
}
```

| Key | Type | Contract |
|---|---|---|
| `sides` | `"duplex"` \| `"simplex"` | the order this document was built in — the same value `--sides` resolved to |
| `grid` | string | the canonical `COLSxROWS` spelling, from `grid_name()` |
| `pages` | array | one entry per page of the built document, in page order, **none skipped** |
| `pages[].page` | integer ≥ 1 | contiguous from 1 |
| `pages[].faces` | array | the card faces printed on that page, in layout order. Empty for a page that carries only Leitner dividers |
| `pages[].faces[].ref` | string | the card's `ref`: its `id`, or `<file-stem>-<index>` when it has none |
| `pages[].faces[].side` | `"front"` \| `"back"` | which face |

`sides` and `grid` are in the file so it is self-describing. They also make the
one mistake this feature can silently make visible to a human: a map produced
without telling the query which print order it was (see
[research.md](../research.md) R3) would carry `"sides": "simplex"` over pages
laid out for duplex.

## Guarantees

1. **Every page is listed.** A page with no cards on it appears with
   `"faces": []`. "No cards here" and "page missing" never look the same.
2. **One side per page.** Every face on a page has the same `side` — a sheet is
   printed one face at a time.
3. **The deck is complete.** Every card appears exactly once as `front` and once
   as `back`, however many pages the document has.
4. **It reflects the print order.** For `duplex` the sides alternate page by
   page; for `simplex` every front page precedes every back page.
5. **Writing it changes nothing else.** Same PDF, same stdout, same exit code.

## Failure

| Situation | Behaviour |
|---|---|
| The path cannot be written (missing directory, no permission) | exit 1 with `ERROR: cannot write the face map to <path>: <reason>`. Never a traceback, never a silently skipped diagnostic |
| The engine query fails | the build already failed, or the failure is reported the way the `<overflow>` query's is — the map is not written, and the exit code says so |

## Stability

No compatibility promise beyond this repository's own test suite. It is a
diagnostic, and the keys may grow. What may **not** change silently is guarantee
1 — padding the page list is the part a reader cannot reconstruct from anything
else.
