---
name: catalog
description: >-
  Build or update a topic catalog with topics, subtopics and references from the ingested knowledge under knowledge/. Triggers: /catalog, "build the topic catalog", "which topics are there".
---

# /catalog — build the topic catalog

Condenses the texts under `knowledge/` into `catalog/topics.md`: a topic
hierarchy that later serves as the selection menu for `/cards`.

## Steps

1. `knowledge/` empty → point at `/ingest`, done.
2. If a catalog already exists: only work in the documents that are newer than
   the catalog (mtime) or do not appear there as a reference yet — keep the
   existing topics instead of re-rolling them.
3. With a lot of material (> ~15 documents or > ~200k words): fan out one
   reading agent per source that returns topics + subtopics + one-sentence
   descriptions + references, then merge and deduplicate. Otherwise read
   directly.
4. Write the catalog (format below), show the user a short tree view of the
   topics and point at `/cards`.

## Format `catalog/topics.md`

```markdown
# Topic catalog
Updated: 2026-08-10 · Sources: <ids>

## <Topic>
Short description (1–2 sentences).

### <Subtopic>
What this subtopic covers; the most important terms/statements in 2–4 bullet
points (this is the working basis for card generation).
References: [slug](../knowledge/<id>/<slug>.md), …
```

## Guidelines

- Cut topics by content, not by source — the same thing from two sources is
  ONE topic with two references.
- Aim for 3–10 topics with 2–8 subtopics each; structure more finely rather
  than creating giant subtopics.
- The bullet points per subtopic should carry enough weight to decide what is
  card-worthy without re-reading the full text — but the references stay the
  source of truth when the cards are written.
