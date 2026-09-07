# Data Model: Enumeration tiers

**Feature**: `011-enumeration-tiers` · **Date**: 2026-09-07

No schema changes. `cards/*.yaml` gains no key. What this feature adds is a
**convention inside the existing `back` string** and one derived quantity the
checker computes from it.

## 1. The enumeration

Everything between the brackets of every `#list(` in one card back, as
`_list_items` already extracts it. Unchanged.

| | |
|---|---|
| Source | `back`, a Typst markup string |
| Extraction | `_list_items(back)` — bracket-depth scan (007-deck-anchors, FR-013) |
| `None` | unbalanced markup; every check skips the card and reports nothing |
| `[]` | no enumeration; E-1 and E-3 say nothing, E-2 may |

## 2. The group *(new)*

An item that carries a label and members instead of a single name.

```
[*Discover*: interviews, observation, desk research]
  ^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    label                 members
```

| Field | Rule |
|---|---|
| label | emphasised with single stars, no star inside, non-empty |
| separator | a colon, optional whitespace either side |
| members | the rest of the item, split on commas, each non-empty after stripping |

**I-1**: A member MUST NOT contain a comma. The split is unconditional, the
same limitation `catalog_names()` carries; the workaround is a comma-free
member. Stated in [contracts/check-messages.md](contracts/check-messages.md).

**I-2**: An enumeration is **grouped** only when *every* item is a group. A
mixed list is treated as flat — it has no hierarchy to offer, and "three of
your five items are groups" is not an actionable message.

**I-3**: The label is **structure, not content**. It is exempt from A-2
(FR-011c) and is never counted towards the enumeration size.

## 3. The enumeration size *(new, derived)*

The single number every rule in this family reads.

```
size(back) = number of members   if the enumeration is grouped
             number of items     otherwise
```

**I-4**: E-1, E-3 and the tier rule all read this one helper. They cannot
disagree about "how many" because there is only one definition. This is not
tidiness — it is the fix for R-4, where E-1 counting *items* on a grouped back
made the shipped error fire falsely on the shape this feature recommends.

**I-5**: `size` is undefined (and every check silent) when `_list_items`
returns `None`.

## 4. The tiers

| size | shape | checked? |
|---|---|---|
| 1–2 | a sentence | no — R-8 |
| 3–5 | flat `#list`, exactly *n* items | E-1 (shipped) checks the count |
| 6–8 | one card, grouped | **E-3a** warns if not grouped |
| 9+ | anchor card + one card per group | **E-3b** warns, grouped or not |

**I-6**: E-3b fires at 9 and above **whether or not** the list is grouped. The
top tier is not "group harder", it is "this is more than one card".

**I-7**: The boundaries are two module constants, not literals scattered
through the checks, so the tier table in `skills/cards/SKILL.md` and the code
have exactly two places to disagree rather than six.

## 5. What A-2 sees *(changed)*

| back | today | after |
|---|---|---|
| `[Amber]` | checks `amber` | unchanged |
| `[Amber — the middle stage]` | checks `amber` (head-term cut) | unchanged |
| `[*Discover*: a, b]` | checks `discover` — **measured** | checks `a` and `b`; `discover` exempt |

**I-8**: The change is not purely additive — A-2 stops checking the label. That
is deliberate (FR-011c) and safe today: no card in the repository uses the group
shape, so nothing that passes now begins to fail, and nothing that fails now
begins to pass.

**I-9**: Members reach `_item_key` unchanged, so the maths gate, the head-term
cut and the token-sequence match all apply to a member exactly as they apply to
a flat item.

## 6. The enumeration prompt *(new, E-2 only)*

| Field | Rule |
|---|---|
| cue | a closed per-language set of openings — English `what are`, `name`, `list`, `state`, `give`, `which`; German `was sind`, `nenne`, `liste`, `zähle`, `welche` |
| position | at the very start of the front |
| adjacency | the numeral follows the cue, with at most one article between them |
| numeral | whatever `_announced_count` returned — never re-derived |

**I-10**: A language with no cue set makes E-2 silent, exactly as a language
with no number-word table makes `_announced_count` silent. Quiet beats guessing.

**I-11**: Adjacency is the whole rule (R-2). Without it the check fires on
`F3M2Q`; with a leading-verb-only reading it misses `B7SGP`, the card the issue
was reported for.
