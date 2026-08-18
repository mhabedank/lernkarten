# Contract: `catalog/topics.md` (extended)

**Written by**: `/catalog`, updated by `/research-gaps` · **Read by**: `/cards` ·
**Validated by**: `parse_catalog()` + `check_catalog()` in
`scripts/check_project.py`

All additions are **optional lines**. A catalog written before this feature is
valid unchanged, and a project with no `goal.md` still produces one.

## Shape

```markdown
# Topic catalog
Updated: 2026-08-18 · Goal: [goal.md](../goal.md) · Sources: <ids>

## Platform fundamentals
What a low-code platform is and what it costs to run one.
Also covers: Access control (cards in cards/security.yaml)

### What low-code is
- Abstraction over hand-written code; the no-code boundary
Related: Make-or-buy
References: [primer](../knowledge/lc/primer.md)

### Governance and shadow IT
- Who may build what, and how it is reviewed
Status: gap
References: none

## Security
Controls and their failure modes.

### Access control
- Roles, least privilege, review cadence
Parents: Security, Platform fundamentals
References: [rbac](../knowledge/lc/rbac.md)

### Research methodology
- How the papers in the reading list were conducted
Status: out of scope
References: [paper-a](../knowledge/lc/paper-a.md)
```

## The new lines

| Line | On | Meaning |
|---|---|---|
| `Goal:` | header | link to `goal.md`; presence marks a goal-driven catalog |
| `Status:` | subtopic | `gap` or `out of scope`. Absent ⇒ in scope and covered |
| `Parents:` | subtopic | every topic it belongs under, **primary first**. Absent ⇒ the containing heading is the only parent |
| `Related:` | subtopic | undirected associations to other subtopics |
| `Also covers:` | topic | subtopics parented here but written elsewhere, naming where their cards live |
| `References: none` | subtopic | valid **only** with `Status: gap` |

## Invariants

| # | Rule | Severity |
|---|---|---|
| C-1 | every `Parents:` name is a topic in this catalog | error |
| C-2 | the primary parent equals the heading the subtopic sits under | error |
| C-3 | every non-primary parent carries a reciprocal `Also covers:` entry | error |
| C-4 | every `Also covers:` name is a subtopic whose `Parents:` includes that topic | error |
| C-5 | every `Related:` name is an existing subtopic | error |
| C-6 | a subtopic has references, or `Status: gap` | error |
| C-7 | `Status:` is `gap` or `out of scope` | error |
| C-8 | every reference link resolves | error *(unchanged)* |
| C-9 | a multi-parent subtopic is counted **once** and appears once in the set passed to `check_cards()` | error |

There is no acyclicity rule. The catalog is two levels deep and edges run only
topic → subtopic, so the graph is bipartite and cycles cannot form.

## Consumption by `/cards`

- `Status: out of scope` → skipped unless named; reported as a **count only**
- `Status: gap` → skipped; reported as a **warning naming every gap**, since a
  gap means the deck is incomplete and a number is not actionable
- `Parents:` → cards written **once**, into the primary parent's file, with the
  primary topic as `topic:`
- `Related:` → connection and distinction cards for the pair, written once; never
  for a target that is a gap or out of scope

## Structural note

`Also covers:` is deliberately a line on the topic, **not** a second `###`
heading. A borrowed subtopic must not create a heading, or the existing heading
scan would count it twice and `check_cards()` would see a duplicate name.
