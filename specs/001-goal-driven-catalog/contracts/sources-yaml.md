# Contract: `sources.yaml` — new type `research`

**Written by**: `/research-gaps` · **Read by**: `/ingest` (skips it — the
documents are already written), `check_sources()` in
`scripts/check_project.py`

## Shape

```yaml
sources:
  - id: governance-research
    type: research
    gap: 'Governance and shadow IT'
    added: 2026-08-18
    note: "Written by /research-gaps — not material the user chose"
```

## Rules

| Rule | Severity |
|---|---|
| `id` kebab-case and unique | error *(unchanged rule)* |
| `gap` present and non-empty | error |
| `path` / `url` neither required nor expected | — |

In `SOURCE_TYPES` this joins `zotero` as a type with no required location field.
The retrieved URLs live in the frontmatter of the documents beneath it.

## Documents

`knowledge/<research-id>/*.md`, using the **existing** frontmatter contract with
no changes:

```markdown
---
source: governance-research
url: https://example.org/governance-primer
ingested: 2026-08-18
---
```

`url` is required here in practice, not by a new rule: `/research-gaps` may not
write a document with no retrieved source behind it, so every file it produces
has one. A researched document with no `url` means the skill invented content,
which the prompt forbids.

## Why a separate type

Provenance. A `web` source is something the user chose; a `research` source is
something the model found. Keeping them apart means:

- the user can always tell their own material from supplied material;
- a card's `source:` reference makes the origin visible on the printed card;
- deleting one register entry and one folder removes all supplied material, and
  the next `/catalog` run returns those subtopics to `Status: gap`.
