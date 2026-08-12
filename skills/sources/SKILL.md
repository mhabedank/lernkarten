---
name: sources
description: >-
  Register, list or remove knowledge sources for the flashcards — folders, PDF collections, Zotero collections, web pages. Triggers: /sources, "add a source", "which sources do I have".
---

# /sources — manage knowledge sources

Maintains the source register `sources.yaml` in the project root.

## Steps

1. Read `sources.yaml`. If the file does not exist (fresh clone — it is
   deliberately not versioned), create it with the comment header from
   `sources.example.yaml` and an empty `sources:` list; do NOT copy the
   example entries.
2. **Without arguments**: show every registered source as a compact table
   (id, type, path/URL/collection, note) and briefly explain how to add one.
   While doing so, check whether each source is still reachable (does the
   folder/file exist?) and flag dead ones.
3. **With arguments** (e.g. `/sources ~/Documents/University/Statistics` or
   "add my Zotero"): create the source(s) — see below. Then show the updated
   list.
4. **Removing** ("remove lecture-notes"): delete the entry from
   `sources.yaml`. Do NOT automatically delete already ingested texts under
   `knowledge/<id>/` — just point them out.

## Creating a source

Determine the type yourself (heuristic: existing folder → `folder`, `.pdf`
file → `pdf`, URL → `web`, the word "Zotero" → `zotero`) and assign a
descriptive kebab-case `id`. Ask only when it is genuinely ambiguous.

Schema per entry (the comment header in `sources.yaml` shows examples):

- `folder`: `path` (required), `pattern` (optional, glob), `note`
- `pdf`: `path` (required), `pages` (optional, e.g. "1-150"), `note`
- `zotero`: `collection` (name of the Zotero collection; omit for the whole library), `note`
- `web`: `url` (required), `depth` (optional: 0 = this page only,
  1 = plus directly linked subpages on the same domain; default 0), `note`

Validate before writing: expand paths (`~`), check that they exist; for
Zotero check whether the local API answers
(`curl -s http://localhost:23119/api/users/0/collections`) — if not, create
the entry anyway and point out that Zotero has to run during `/ingest`.

## Wrap-up

Point at the next step: `/ingest` reads the sources.
