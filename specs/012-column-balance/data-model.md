# Phase 1 Data Model: The landing page's two-column sections carry their weight

**Feature**: 012-column-balance | **Date**: 2026-09-08

**No format change.** None of the four file formats is read or written by this
feature — `sources.yaml`, `knowledge/<id>/<doc>.md`, `catalog/topics.md` and
`cards/*.yaml` are untouched, so there is nothing under `contracts/` either.

What this feature *does* have a model of is the **DOM of two sections**, in the
idiom feature 002's data-model used for the navigation. The trees below are the
contract the assertions hold to.

---

## Section 02 — `one card, one idea`

**Before** — a control in the band hides one of the two cards whenever a script
runs:

```text
section#cards
├── div.band
│   ├── div.band__no                     02
│   ├── h2                               one card, one idea
│   └── button.toggle#flip               ← "show the back", [hidden] until JS un-hides it
├── div.anatomy
│   ├── div.anatomy__cards
│   │   ├── div.card#card-front
│   │   └── div.card#card-back           ← given [hidden] by the script on load
│   └── div.anatomy__list                4 × div.anatomy__item
└── div.yaml
```

**After** — the band holds a number and a heading, and both cards stand:

```text
section#cards
├── div.band
│   ├── div.band__no                     02
│   └── h2                               one card, one idea
├── div.anatomy
│   ├── div.anatomy__cards
│   │   ├── div.card#card-front          both visible, at every width,
│   │   └── div.card#card-back           with and without JavaScript
│   └── div.anatomy__list                4 × div.anatomy__item — unchanged
└── div.yaml                             unchanged
```

**Invariants** the assertions hold to:

- Neither card carries `hidden`, in the markup or after load.
- No `.toggle` element exists anywhere on the page.
- The `id` attributes `card-front` and `card-back` may go with the script that
  used them, but if either is kept it must still name the same card — nothing
  else on the page references them.
- The four `.anatomy__item` blocks keep their text, their order and their
  `.anatomy__key` letters A–D. This feature does not edit the prose.

---

## Section 03 — `print it, cut it`

**Before** — one column holds two pictures, the other holds everything else:

```text
section#print
├── div.band                             03 / print it, cut it
├── p.band__note
└── div.print
    ├── div.print__sheets                327 px of content
    │   ├── div.sheet                    page 1 · fronts
    │   └── div.sheet                    page 2 · backs, mirrored
    └── div.print__rules                 1174 px of content
        ├── div.rule-item                1 · duplex, flip on long edge
        ├── div.rule-item                2 · 100 % scale
        ├── div.rule-item                3 · three cuts down, three across
        ├── div.print__cut               ← the diagram rule 3 is about
        └── div.print__box               ← a different subject entirely
```

**After** — pictures on the left, prose on the right, the box across the bottom:

```text
section#print
├── div.band                             unchanged
├── p.band__note                         unchanged
├── div.print
│   ├── div.print__sheets                closes level with the rules column, 433 px
│   │   ├── div.sheet                    page 1 · fronts
│   │   ├── div.sheet                    page 2 · backs, mirrored
│   │   └── div.print__cut               ← beside them, not below: three in one row
│   └── div.print__rules                 the three numbered rules only — 433 px
│       ├── div.rule-item                1
│       ├── div.rule-item                2
│       └── div.rule-item                3
└── div.print__box                       ← full width, beneath both columns
```

**Invariants** the assertions hold to:

- `.print__box` is not a descendant of `.print__rules`, and follows `.print`.
- `.print__cut` is a descendant of `.print__sheets`, and sits **beside** the two
  sheets rather than wrapping below them. The assertion reaches only the first
  half; the second is what makes both columns end together, and it is checked by
  hand ([BUG-012](bugs/BUG-012.md)).
- The box moves as one unit: its heading, its `card-box.pdf` download link, the
  `--dividers 4` paragraph with its `leitner.html` link, and the
  `.print__box-note` sizing caption. The href stays relative — it resolves only
  on the deployed site, where `pages.yml` puts the two files side by side, and
  the HTML comment recording that moves with it.
- The three `.rule-item` blocks keep their numbers, their colours and their
  order. Rule 3 still introduces the diagram; the diagram is now beside the
  sheets rather than beneath the rule, which is a layout change and not a
  reading-order one.

---

## The rules between the blocks

The one thing a tree cannot show, and the detail R1 flags as most likely to be
got wrong (FR-006):

| Boundary | Rule | Owner |
|---|---|---|
| `.print__sheets` \| `.print__rules` | `border-right` on the sheets column | unchanged |
| `.print` above `.print__box` | `border-top` on the box | already declared |
| `.print__box` below | none — `#print` carries `border-bottom` inline | must **not** gain one |
| last `.rule-item` | `border-bottom` | unchanged; it is no longer the last child of its column, it is the third of three |

A doubled 4 px rule and a missing one look equally deliberate at a glance, which
is why feature 002 gave this its own requirement rather than trusting the eye.
