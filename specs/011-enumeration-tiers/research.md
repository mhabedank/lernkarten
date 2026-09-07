# Phase 0 Research: Enumeration tiers

**Feature**: `011-enumeration-tiers` · **Date**: 2026-09-07

Every finding below was **measured against the shipped code** before it was
written down. Three of them change the design, and two of those contradict the
spec's own phrasing — which is what Phase 0 is for.

## R-1 — Is there a library for this? (constitution III, asked first)

**Decision**: no library, and no hand-rolling either — the work is almost
entirely *reuse of what 007-deck-anchors and PR #96 already built*.

`_list_items` (bracket-depth scan), `_item_key` (maths gate plus head term),
`_mentions` (token-sequence match), `_announced_count` (per-language number
words, whole tokens, silent on two counts) all exist and all do exactly what
this feature needs. What is genuinely new is two regexes over a Typst fragment
no parser in the wild targets, plus two closed word lists.

**Alternatives considered**: a natural-language toolkit for "is this an
enumeration prompt". Rejected on constitution II and IV — a runtime dependency
with model data, for a question a seven-word closed list answers on the only
four counted fronts that exist in this repository.

## R-2 — How does E-2 recognise an enumeration prompt?

**This corrects FR-008's phrasing.** The spec says the front must "open with an
enumeration prompt". Read as *leading verb only*, that misses the card the
whole issue was reported for:

> `B7SGP` — **"What are the four types of work in the research phase?"**

which opens with "What", not with an imperative. Read as *leading verb
adjacent to the numeral*, it works.

**Decision**: the front matches a **cue at the start followed by the numeral**,
with an optional article between them:

```
^<cue>\s+(the|die|der|das)?\s*<numeral>
```

with `<cue>` a closed per-language set — English `what are`, `name`, `list`,
`state`, `give`, `which`; German `was sind`, `nenne`, `liste`, `zähle`,
`welche`. The numeral is whatever `_announced_count` already found, so the two
checks cannot disagree about what a count is.

**Measured against every counted front in the repository** — all four of them:

| front | cue | E-2 |
|---|---|---|
| `Y4H26` "**Name the five** inhabited islands…" | `name` | would fire if the back were prose — correct |
| `4V946` "**State the three** Kolmogorov axioms." | `state` | same |
| `F3M2Q` "Describe how the range is distributed over the six hours…" | none — `describe` is followed by `how`, not by the numeral | **silent** ✔ |
| `1E782` "How is a mast with two flags read?" | none, and the count is 2 | silent ✔ |

The adjacency is what makes `F3M2Q` silent: its numeral sits in a prepositional
phrase (`over the six hours`) rather than in the asked-for position. A rule
that only looked for a leading verb would also let `Describe the six hours…`
through, and a rule that looked for the numeral anywhere fires on `F3M2Q`, the
false positive the spec was written to avoid.

**Alternatives considered**: (a) numeral anywhere in the front — measured, fires
on `F3M2Q`; (b) leading verb only — misses the issue's own motivating card;
(c) part-of-speech tagging to find the direct object — a runtime dependency for
a four-card corpus.

## R-3 — What shape is a group, and when is an enumeration "grouped"?

**Decision**: an item is a **group** when its text matches

```
^\s*\*([^*]+)\*\s*:\s*(.+)$
```

— an emphasised label, a colon, then the members separated by commas. An
enumeration is *grouped* when **every** item is a group. Mixed lists are not
grouped: a half-grouped list has no hierarchy, and "some items are groups" is
the kind of partial state that produces an unactionable message.

**Alternatives considered**: a nested `#list` — Typst supports it, but it would
have to be checked against the card template first and it gives the label
nowhere to live. Rejected as a bigger change for the same information.

## R-4 — Grouping breaks the shipped E-1 *(measured)*

The sharpest finding in this phase. `_check_counts` compares the announced count
with `len(_list_items(back))`. On a grouped back those are different things:

```
front: 'Name the four steps.'
back:  '#list([*Discover*: alpha, beta], [*Define*: gamma, delta])'
→ ERROR: card 1: the front announces 'four' and the back enumerates 2
```

Reproduced against the shipped checker. So **adopting this feature's own
recommended shape makes the previous feature's error fire falsely.** E-1 is an
error, not a warning, so this would break builds.

**Decision**: the number E-1 compares against is the **enumeration size** — the
member count when the list is grouped, the item count when it is flat — and
E-1, E-3 and the tier rule all read it from **one helper**, so they cannot drift
about what "how many" means. This is a change to code that shipped four commits
ago and it gets its own red test.

## R-5 — What A-2 does with a group item today *(measured)*

```
_item_key('*Discover*: alpha, beta') → 'discover'
```

The head-term cut lands on the colon, so A-2 would demand that another card
name **`Discover`** and would never look at `alpha` or `beta`. Coverage lost
silently, with no failing test to show it — FR-011b exists for this measurement.

**Decision**: `_check_orphans` descends into a group item and checks each
member through the unchanged `_item_key`; the label is exempt (FR-011c).

## R-6 — Where each check belongs

Constitution XI draws the line: a rule about *what a skill writes into a user's
project* goes in `check_project.py`; a rule about *what a `SKILL.md` itself must
contain* goes in `check_docs.py`.

**Decision**: E-2, E-3 and the A-2 change go in `check_project.py`. The
model-driven half's red artifact — SC-006, "a reader can state the tiers" — goes
in `check_docs.py` as an assertion that `skills/cards/SKILL.md` carries the tier
table. That is the first time a rule about a skill's own text gets a check here,
and it is what makes the prompt change verifiable at all rather than a claim.

## R-7 — What the demo project has to grow

The fixture holds **no** enumeration above the flat tier (measured: 4 counted
fronts, 2 lists, both flat, sizes 5 and 3). SC-003 asks for one enumeration per
tier, which costs:

- one **grouped** card (6–8 members), plus enough companion text that A-2 finds
  every member named elsewhere. One companion card can name them all — measured
  against `_check_orphans`, which asks whether *any other card* names the item —
  so this is 2 cards, not 7.
- one **split** set: an anchor card naming the groups and stating the total,
  plus one card per group. At three groups that is 4 cards, and their members
  need naming too.

Both card-count assertions move with it: `DEMO_CARD_COUNT` in
`tests/test_e2e.py` and the bare count in `tests/test_check_project.py`.

**Open for `/speckit-tasks`**: whether the split tier is demonstrated in the
fixture at full size or whether SC-003 is met with the grouped tier plus a
smaller split. The first is honest and costs ~6 cards; the second is cheaper and
leaves the most complex tier undemonstrated. Recommendation: full size — the
tier nobody has ever written is precisely the one that needs shipped material.

## R-8 — The bottom tier is not checked

FR-002 says 1–2 items is a sentence. **Decision**: no check. A one-item `#list`
is absurd but harmless, and a check for it would be a second tier table in code
for a case no deck produces. The rule stays in the skill, where the judgement
lives.
