# Contract: `goal.md` (new — the fifth format)

**Written by**: `/learning-goal` · **Read by**: `/catalog`, `/cards`,
`/research-gaps` · **Validated by**: `check_goal()` in `scripts/check_project.py`

**Location**: project root, beside `sources.yaml`. Absent is valid.

## Shape

```markdown
---
goal: 'Pass the September low-code exam'
kind: exam            # exam | meeting | interview | self-study
depth: working        # awareness | working | expert
updated: 2026-08-18
---

# Learning goal

One to three sentences on what being ready actually looks like.

## Required topics

### Platform fundamentals
- What low-code is, and where the boundary to no-code runs
- Governance and shadow IT

### Make-or-buy
- Total cost over a five-year horizon
- Vendor lock-in

## Out of scope

- Research methodology of the papers in the reading list
- Vendor market history before 2015
```

## Rules

| Rule | Severity | Message names |
|---|---|---|
| `goal`, `kind`, `depth`, `updated` all present and non-empty | error | the missing key |
| `kind` ∈ {`exam`, `meeting`, `interview`, `self-study`} | error | the bad value and the set |
| `depth` ∈ {`awareness`, `working`, `expert`} | error | the bad value and the set |
| `updated` matches `YYYY-MM-DD` | error | the bad value |
| `## Required topics` holds ≥ 1 area (`###`) | error | the file |
| every area holds ≥ 1 topic | error | the area |
| every required topic appears in `catalog/topics.md` | **warning** | the topic |

## Areas are independent

Areas exist so a goal can hold strands with nothing in common — an interview's
technical round and its behavioural round. Nothing downstream may merge them or
infer a relation between them. Each area becomes its own top-level topic in the
catalog.

## Reconciliation on re-run

`/learning-goal` never silently overwrites. On a second run:

- **additive change** (new area, new topic) → merge, move `updated`, no questions
- **contradiction** (`kind` or `depth` changed; a topic crossing between required
  and out-of-scope; an area or topic dropped) → list every one, ask, write only
  what the user chose
- a contradiction that **narrows** scope must also name what depends on it: the
  catalog subtopics and card files that would become out of scope

## Not in this contract

`goal.md` is user content: gitignored, blocked by `.githooks/pre-commit`,
asserted by `tests/test_repo_hygiene.py`. The one committed copy is the demo
fixture, let back in by `!tests/fixtures/**/goal.md` — required because `goal.md`
has no slash and so matches at every directory level, exactly like
`sources.yaml`.
