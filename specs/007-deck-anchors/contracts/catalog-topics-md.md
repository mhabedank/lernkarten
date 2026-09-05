# Contract: `catalog/topics.md` — the `Term:` line

**Feature**: `007-deck-anchors` | **Status**: additive, backwards compatible

`catalog/topics.md` is one of the six formats that couple the model-driven half
to the deterministic half (constitution I). This feature adds **one optional
attribute line** and changes nothing else.

## Grammar

A subtopic body may carry, in any order among the other attribute lines:

```
Term: <alias>[, <alias>]*
```

- **Written by**: `/catalog` (`skills/catalog/SKILL.md`) — and not merely on
  request: the skill's writing guidance instructs producing the line for a
  subtopic whose heading names a concept, at latest when its cards exist
  (FR-027 as amended in review W1). A format the prompts never write is a dead
  format; the line is inert on a subtopic without cards, so writing it early
  costs nothing.
- **Read by**: `scripts/check_project.py` — check A-1 only.
- **Optional.** Absent means the pre-feature behaviour: A-1 says nothing about
  that subtopic, neither error nor warning. This is the same "absent means the
  old behaviour" shape `Status:`, `Parents:`, `Related:` and `Also covers:`
  already have.

## Example

```markdown
## Tides
The Ashwind tide cycle as the tide office in Fenmouth teaches it.

### Rhythm of the tide
Semidiurnal tide, the length of the tidal day and the daily shift of high water.
Term: Rhythm of the tide, Tidenrhythmus, παλίρροια
References: [tide-cycle](../knowledge/field-notes/tide-cycle.md)

### Settlements
Where people live, which harbours are reachable how, and where the tide office sits.
References: [kestrel-islands](../knowledge/field-notes/kestrel-islands.md)
```

`Rhythm of the tide` is a term and carries the line. `Settlements` is a
description of a group of facts rather than a single named concept, so it
carries none and A-1 ignores it. No rule can tell the two apart — that is the
whole reason the line exists rather than the heading being matched (FR-011).

## What the aliases are for

**Every language the deck is written in needs its own alias**, because A-1 binds
per card file (FR-010): an English anchor in `cards/tides.yaml` does not satisfy
the Greek cards in `cards/palirroia-el.yaml`. One subtopic, one `Term:` line,
one alias per language the deck actually uses.

When A-1 fires on a file whose cards already name the concept in their own
language, the missing piece is the **alias**, not a card: add that language's
alias to the line. The checker step in `skills/cards/SKILL.md` names that
remedy (review W5).

## Matching rules

| Rule | Detail |
|---|---|
| Separator | a comma |
| Trailing parenthetical | stripped — `Term: Chart datum (LAT)` yields `Chart datum` |
| Normalisation | `topic_key()`: lower-cased, non-`\w`/non-space replaced by a space, whitespace collapsed. Unicode-aware |
| Match | the normalised alias occurs as a **space-padded token sequence** in the normalised `front + " " + back` of the cards in one file under that subtopic |
| Any alias suffices | a file is anchored as soon as **one** alias matches in it |
| Substrings are not matches | `Nipptidenhub` does not anchor `Tidenhub`; `settlement` does not anchor `Settlements` |
| No stemming | an inflecting language needs the form the cards actually use — `нуля глубин`, not `нуль глубин` |

## Limitations

- **An alias may not contain a comma.** The line is split by the existing
  `catalog_names()` helper with no `known` set to match against first, so
  `Term: Governance, risk & compliance` becomes two aliases. Write a comma-free
  alias instead. (A topic *name* may contain a comma — that case is handled,
  and is unaffected.)
- **A `Term:` line on a topic (`##`) is ignored**, not reported. This matches
  how a `Parents:` line on a topic is treated today.

## Validation

| Condition | Reaction |
|---|---|
| absent | nothing |
| one or more aliases | nothing (the normal case) |
| present but empty (`Term:`), or parses to zero aliases | **error**: `catalog/topics.md: subtopic 'X': 'Term:' is empty — name the term, or leave the line out` |
| written **twice** under one subtopic | nothing — **the first line wins**, the second is discarded silently |

**A repeated `Term:` line is not an error.** `parse_catalog` stores attributes
with `setdefault`, so the first occurrence of a key is the one that survives.
That is not a rule invented here: it is what already lets a `References:` line
wrap onto a second line without the continuation being read as a new attribute,
and `Term:` inherits it unchanged. A subtopic that wants more aliases adds them
to the one line, comma-separated.

## Backwards compatibility

Every `catalog/topics.md` on disk today parses identically and gains no finding,
because none of them carries the line. No migration, no re-run of `/catalog`
required. A user who never adds a `Term:` line gets exactly the checker they had
before.
