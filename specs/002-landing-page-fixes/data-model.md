# Phase 1 data model: three landing page fixes

**No format change.** None of the five file formats that couple the two halves is
touched — `goal.md`, `sources.yaml`, `knowledge/<id>/<doc>.md`,
`catalog/topics.md` and `cards/*.yaml` are all untouched, so there is no contract
to write and no entity to model. A project on a user's disk is unaffected by this
feature in every respect.

What takes the place of a data model here is the **document structure** of
`docs/index.html` — the one arrangement this feature changes, and the one the
structural assertions in `tests/test_landing_page.py` are written against.

## The navigation

**Before** — the link row is a bare container that scrolls sideways:

```text
nav.nav
├── a.nav__home            wordmark
├── div.nav__links         ← overflow-x: auto, scrollbar suppressed
│   ├── a[href="#how"]
│   ├── a[href="#cards"]
│   ├── a[href="#print"]
│   └── a[href="#install"]
└── a.nav__gh              github
```

**After** — the same four links, disclosed by a control that carries a word:

```text
nav.nav
├── a.nav__home            wordmark — unchanged, stays in the bar at every width
├── details.nav__menu
│   ├── summary            "menu" — the control; hidden above 760 px
│   └── div.nav__links     the panel; forced visible above 760 px
│       ├── a[href="#how"]
│       ├── a[href="#cards"]
│       ├── a[href="#print"]
│       └── a[href="#install"]
└── a.nav__gh              github — unchanged, stays in the bar at every width
```

**Invariants** the assertions hold to:

- The four links keep their `href` values and their order. This feature moves
  them; it does not rename, reorder or add one.
- The wordmark and the github block are siblings of the `<details>`, never inside
  it — FR-004's one-line bar depends on it.
- Exactly one `<details>` exists on the page, and its `<summary>` has non-empty
  text content. An empty summary, or one holding only an SVG, fails FR-002.

## The section bands

Three sections share one shape — `01 the pipeline`, `03 print it, cut it` and
`04 install`. A fourth, `02 one card, one idea`, has a button where the others
have a note and is **not** restructured.

**Before** — the note is a flex child, so the longest child sets the row height:

```text
section
├── div.band                 display: flex; align-items: stretch
│   ├── div.band__no         the number
│   ├── h2                   the heading      ~74 px
│   └── p.band__note         the note         81–126 px  ← sets the row height
└── div.<content>            steps / print / install grid
```

**After** — the note is a sibling, so nothing but the heading sizes the row:

```text
section
├── div.band                 display: flex; align-items: stretch
│   ├── div.band__no
│   └── h2                                    ~74 px  ← now the tallest child
├── p.band__note             full width, border-bottom, no border-left
└── div.<content>
```

**Section 02, unchanged** — recorded because the restructure must not reach it:

```text
section#cards
├── div.band
│   ├── div.band__no
│   ├── h2
│   └── button.toggle        flex: none, one short line — never out-measures the h2
└── div.anatomy
```

**Invariants**:

- Reading order is identical before and after: number, heading, note, content.
  The markup already produced that order; only the nesting changes.
- No `p.band__note` is a child of a `div.band`; each is its band's immediate next
  sibling.
- Section 02's band keeps its `button.toggle` as a child. The `flex-wrap` rules
  at the 1080 px breakpoint exist for that button as well as for the notes and
  survive the change.
- The install note stays inside `section.install`, so `.install .band__note`
  keeps matching without a selector rewrite.

## The card toggle

No structural change at all — this is the point of the fix. The markup is already
correct and stays exactly as it is:

```text
section#cards
├── div.band
│   └── button.toggle#flip   hidden in the markup; the script unhides it
└── div.anatomy
    └── div.anatomy__cards
        ├── div.card#card-front    authored without hidden
        └── div.card#card-back     authored without hidden; the script hides it
```

**The invariant that was broken and is being restored**: an element carrying the
`hidden` attribute is not rendered, whatever its class declares. That is a
stylesheet property, not a structural one, which is why this bug has a
one-line fix and no entry in the tree diagrams above.

**Why the no-JS path is unaffected**: both cards are authored *without* `hidden`,
so with the script off both render and the button — authored *with* `hidden` —
does not. Adding the global rule changes neither.
