# Contract — `knowledge/<source-id>/<slug>.md`

**Change**: one optional frontmatter key, `figures:`, holding a list; plus an
inline marker in the body for each kept figure.

## Schema (the addition in context)

```markdown
---
source: handbook
document: "Kestrel Handbook"
path: "/abs/path/raw/handbook/kestrel-handbook.pdf"
ingested: 2026-08-22
figures:                                          # NEW — optional, a list
  - at: 'page 3'
    visual: chart
    path: figures/handbook/tide-curve.png
    caption: 'Semidiurnal tide curve for the Kestrel Deep'
  - at: 'page 1'
    visual: none
    why: 'harbour office logo, repeated in every page header'
---

The tide runs semidiurnal through the Deep, with the second high the weaker.

![Figure: Semidiurnal tide curve for the Kestrel Deep](figures/handbook/tide-curve.png)

Slack water follows roughly two hours after the turn.
```

## Rules

| # | Rule | Severity |
|---|---|---|
| K1 | `figures:` is a list of mappings, or absent. Absent means a document that predates figures, or one with no pictures in it | error if not a list |
| K2 | Every entry carries `at:` (free text) and `visual:` | error |
| K3 | `visual:` is one of `diagram`, `chart`, `map`, `none` — a closed vocabulary, like `content: sparse` | error |
| K4 | `visual: none` requires `why:` and forbids `path:` | error |
| K5 | Any other `visual:` requires `path:` and `caption:` | error |
| K6a | `path:` is project-relative, sits under `figures/<source>/`, and `<source>` matches the folder the document is in | error |
| K6b | The file the path names exists | **warning** |
| K7 | Every kept figure's `path` appears in the body as a markdown image link | error — a figure named and not marked is half an edit |
| K8 | The extension is in the accepted set (`png`, `jpg`, `jpeg`, `gif`, `svg`, `webp`) | error |
| K9 | Two entries in one document may not share a `path` | error |
| K10 | A rejected figure is silent — no warning. Its whole job is to answer "was this looked at?" with yes | — |

K10 follows the reasoning already written into `check_knowledge` for
`content: sparse`: warning about a correctly recorded verdict on every run
replaces a false alarm with a permanent true one.

**Why K6b is a warning where the card rule (C2) is an error.** A missing figure
file stops nothing until a card names it, and `check_sources` already settled
this exact question the same way — `test_a_source_path_that_is_gone_is_only_a_warning`.
It is also load-bearing for the fixture: the demo project's figures are
*generated* and gitignored, so an error here would make `check(DEMO)` fail on
every fresh checkout before `make_testdata.py` has run. A missing picture on a
*card*, by contrast, stops a build and stays an error.

## Error messages

Reported against the **document**, not the source (FR-019):

```text
ERROR: knowledge/handbook/kestrel-handbook.md: figure 1: 'visual: photo' is not one of diagram, chart, map, none
ERROR: knowledge/handbook/kestrel-handbook.md: figure 1: 'path: figures/handbook/tide-curve.png' does not exist
ERROR: knowledge/handbook/kestrel-handbook.md: figure 1: kept, but the body never shows it
ERROR: knowledge/handbook/kestrel-handbook.md: figure 2: 'visual: none' cannot carry a 'path'
```

## Backwards compatibility

The key is optional and new. Every knowledge document on disk today stays valid
and unchanged. `content: sparse`, `pending:` and the existing required keys are
untouched, and a document may carry `figures:` alongside any of them.
