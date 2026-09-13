# Contract: `knowledge/<source-id>/<document>.md` frontmatter — the `nature:` key

**Written by**: `/ingest` · **Read by**: `/catalog`, `/cards` · **Validated by**:
`check_knowledge()` in `scripts/check_project.py`

**Change**: one **new, optional, additive** key with a **closed vocabulary**.
Nothing existing moves. This is the third of the six formats in constitution
Principle I, and it is the only format this feature touches.

## Shape

```markdown
---
source: field-notes
document: "Ovray Cove, 14 March — what the harbour office wrote down"
path: "raw/field-notes/ovray-grounding.md"
content: sparse          # optional, unchanged
characters: 68           # optional, unchanged
nature: experience       # NEW — optional, closed vocabulary
ingested: 2026-09-07
figures:                 # optional, unchanged
  - at: 'page 3'
    visual: chart
    path: figures/field-notes/tide-curve.png
    caption: 'What the picture shows, in one line'
---

<extracted text>
```

## Vocabulary

| Value | Means |
|---|---|
| `experience` | the document's **subject is a reported case** — an incident post-mortem, a case study, a fuck-up report, an application scenario, a company or engineering blog post about something that happened |

`experience` is the only value today. The set is closed for the reason
`CONTENT_STATES` and `VISUAL_KINDS` are closed: a marker nothing downstream can
act on is worse than no marker.

## Rules

| Rule | Severity | Message names |
|---|---|---|
| the key is absent | **never a finding** | — |
| `nature:` ∈ `NATURES` | none | — |
| `nature:` ∉ `NATURES` | error | the document, the value, and the allowed set |

Message shape, matching `content:` and `visual:` exactly:

```
knowledge/field-notes/ovray-grounding.md: 'nature: anecdote' is not one of experience
```

## When `/ingest` writes it

- A document whose subject is a reported case → `nature: experience`.
- Everything else → **no `nature:` key at all.** Not `nature: reference`, not
  `nature: none`. The vocabulary has one value and absence is the other state.
- A document that is mostly a reference work with one anecdote in it is **not**
  marked. `nature:` is one value about the whole document, never a per-paragraph
  judgement.

## What reads it

| Reader | What it does |
|---|---|
| `/catalog` | places the document normally; reports a required topic covered **only** by experience reports rather than presenting single-case coverage as coverage of the rule (FR-014), and warns about the material base of a subtopic that rests only on such reports — FR-013's four contents, in its own words (see [spec.md § FR-013](../spec.md) for the worked example, written once and not restated here) |
| `/cards` | phrases cards from it about the reported case, names the case in the existing optional `source:` key, and carries the scale or circumstances the fact depends on (FR-011, FR-012); and when it reports on a subtopic that rests only on such reports it carries **the same** FR-013 warning `/catalog` does — the requirement binds both steps |
| `check_project.py` | validates the key, and derives the experience-only subtopic set that carries the FR-011 attribution rule |

None of them re-judges the document. That is the point of putting the
recognition on disk instead of re-deriving it on every run.

## Backwards compatibility

**Total, in both directions.**

- Every project on disk today carries no `nature:` key and stays valid — the
  absence rule above is what guarantees it, and it is asserted as a regression
  guard rather than assumed.
- No migration. No re-ingest. A document ingested before this feature simply has
  no marker, and nothing treats a missing marker as a claim that the document is
  *not* an experience report.
- An older reader that does not know the key ignores it, the way it ignores
  `content:` on a build that predates BUG-004.

## Also needs updating when this contract changes

`skills/ingest/SKILL.md` (the format block at lines 92-111 and the rule for when
to write it), `skills/catalog/SKILL.md`, `skills/cards/SKILL.md`,
`scripts/check_project.py` (`NATURES` + `check_knowledge`),
`tests/fixtures/demo-project/knowledge/`, and `docs/workflow.md` where the
knowledge frontmatter is described.
