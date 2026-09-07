# Contract: the `check_project.py` messages this feature adds and changes

**Feature**: `011-enumeration-tiers`

Continues the contract 007-deck-anchors wrote for A-1 and A-2 and PR #96
followed for E-1. Same house grammar throughout `check_cards`: the file goes in
`where` and the reporter prefixes it; the card is named by its **1-based index
within the file**, never by its `id`; the subject is named first; the reason
follows an em dash.

**Severity**: everything new here is a **warning** (FR-009, FR-012). E-1 stays
the only error in the family, because counting a numeral against a list length
is the only question in it with one answer.

Warnings fail `--strict`, which is what CI runs against
`tests/fixtures/demo-project`. "Green on the fixture" therefore still means no
errors *and* no warnings.

## E-2 — a counted enumeration prompt answered in prose

**Fires when** all of these hold:

1. `_announced_count(front, language)` returns a count of **3 or more**;
2. the front opens with an enumeration cue **adjacent to that numeral**, with
   at most one article between them (data-model §6);
3. `_list_items(back)` is `[]` — no enumeration at all. `None` (unbalanced
   markup) does **not** fire: half a fragment says nothing about the deck.

**Scope**: one finding per card.

**Shape** — normative:

```
WARNING: cards/research.yaml: card 3: the front asks for 'four' and the back
         answers in prose — an enumerated back is graded item by item, and a
         sentence has to be segmented and counted first
```

```python
report.warn(
    where,
    f"card {i}: the front asks for '{word}' and the back answers in prose — "
    "an enumerated back is graded item by item, and a sentence has to be "
    "segmented and counted first",
)
```

**Does not fire on** (each one measured against the shipped fixture):

| front | why silent |
|---|---|
| "Describe how the range is distributed over the six hours of the flood" (`F3M2Q`) | no cue adjacent to the numeral |
| "Which two of the six flags call for help…" (`NKQK0`) | two different counts — `_announced_count` returns nothing |
| "How is a mast with two flags read?" (`1E782`) | count below three, and no cue |
| "Name the inhabited islands" | no numeral, so no count is announced |

## E-3a — an enumeration in the grouped tier that is not grouped

**Fires when** the enumeration size is in the grouped tier (6–8) and the items
are not all groups (data-model I-2).

```
WARNING: cards/process.yaml: card 2: seven items in a flat list — past six,
         group them into two or three labelled groups so recall has a
         hierarchy rather than a queue
```

## E-3b — an enumeration that belongs on more than one card

**Fires when** the enumeration size is 9 or more, **whether or not** it is
grouped (data-model I-6).

```
WARNING: cards/process.yaml: card 5: ten items on one card — write an anchor
         card naming the groups and the total, and one card per group
```

**Only one of E-3a and E-3b ever fires for a card**: the tiers do not overlap.

## E-1 — changed, not new

The message is unchanged. What changes is the number on the right of it: E-1
now compares the announced count against the **enumeration size** (members when
grouped, items when flat) rather than against the raw item count.

Without the change, the shape this feature recommends makes the shipped error
fire falsely — measured:

```
front: 'Name the four steps.'
back:  '#list([*Discover*: alpha, beta], [*Define*: gamma, delta])'
before → ERROR: card 1: the front announces 'four' and the back enumerates 2
after  → silent
```

## A-2 — changed, not new

The message is unchanged. What changes is what it can be about: on a grouped
item A-2 reports an unnamed **member**, never the label.

```
back: '#list([*Discover*: alpha, beta])'   # nothing else names beta
before → ERROR: card 1: 'alpha, beta' … (the head-term cut lands on 'discover')
after  → ERROR: card 1: 'beta' is enumerated and never named — no other card
         in this file mentions it
```

Measured today: `_item_key('*Discover*: alpha, beta')` returns `'discover'`.

## Limitations

- **A member may not contain a comma** (data-model I-1). The split is
  unconditional, the same limitation `catalog_names()` carries in
  `contracts/catalog-topics-md.md` § Limitations. Workaround: write a
  comma-free member, or leave the enumeration flat.
- **A group label may not contain a star.** It is delimited by single stars and
  the pattern refuses a nested one rather than guessing where the label ends.
- **E-2 is silent in a language with no cue set**, exactly as `_announced_count`
  is silent in a language with no number-word table. Quiet beats guessing, and
  the two silences have the same shape on purpose.
