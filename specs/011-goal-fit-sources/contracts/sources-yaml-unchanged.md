# Contract: `sources.yaml` — unchanged, and that is the contract

**Written by**: `/sources` · **Read by**: `/ingest`, `/catalog`,
`check_project.py`

This file exists because the interesting thing about `sources.yaml` in this
feature is a **negative**, and a negative that is written down survives a
refactor while a negative that is merely absent does not.

## The change

**None.** After this feature a source entry has exactly the keys it has today:

| `type` | Required | Optional |
|---|---|---|
| `folder` | `path` | `pattern`, `note` |
| `pdf` | `path` | `pages`, `note` |
| `web` | `url` | `depth`, `login`, `note` |
| `zotero` | — | `collection`, `note` |
| `research` | `gap` | `note` |

No sixth type. No `fit:`. No `assessed:`. No `discovered:`, no `proposed_by:`,
no timestamp. `SOURCE_TYPES` in `scripts/check_project.py:32-38` does not move.

## Why the goal-fit verdict is not here

Clarification Q2, and it is worth keeping the reason next to the format it
governs. A stored verdict is **derived state about a criterion that moves
underneath it**: edit `goal.md` and every stored `fit:` is stale, with nothing
to re-derive it, because FR-008 forbids re-assessment on a listing. That is
issue #33's FR-002 objection unchanged.

So the assessment is reported in the run and nowhere else, and this file is what
a future reader consults before adding "just a small note on the entry".

## What a discovery run may write

Exactly one thing: an **ordinary entry**, and only for a candidate the user
picked (FR-016, FR-020).

- Same schema as an entry the user named. A reader of `sources.yaml` cannot tell
  the two apart, and nothing in this feature adds a way to — the difference is
  in *how the user got there*, and the user was there either way.
- It goes through the ordinary registration path, so the goal-fit assessment of
  FR-001 applies to it exactly as it applies to a source the user named.
- It is validated by today's `check_project.py` with no change: known type,
  unique kebab-case `id`, the required field for its type present (SC-006).

## What a discovery run may never write

- No entry for a candidate the user did not pick (FR-016, SC-005).
- No `type: research` entry, and nothing into `knowledge/` — that is
  `/research-gaps`'s output, not discovery's (FR-022).
- Nothing at all into `catalog/`.

## The whole-pipeline guarantee (FR-038)

Across a whole run — `/sources` register, `/ingest`, `/catalog`, `/cards`,
`/print`, with or without `goal.md` — the **only** path by which a source the
user did not name reaches this file is a discovery run the user explicitly asked
for and a candidate the user picked. Every other path writes only what the user
named.

This is the property `/research-gaps` was built to protect: the user can always
tell their own material from what the model brought in. This feature preserves
it and does not weaken it.
