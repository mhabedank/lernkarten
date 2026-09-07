# Design references for the Leitner compartments

Two Claude Design exports, kept as **references**, not as shipped artifacts.
Both are self-contained HTML bundles (~400 KB each: base64 fonts plus a JS
template runtime), which is a different kind of file from `docs/index.html` —
44 KB, self-contained, no runtime. Neither can be dropped into `docs/` as-is.

| File | What it shows | What it becomes |
|---|---|---|
| `guide.html` | the method page: the loop, the schedule, setup, house rules | a hand-authored page beside `docs/index.html`, in that page's idiom |
| `dividers.html` | card-sized compartment dividers, solid brand colours | pages in `templates/`, rendered into the card PDF |

## What in them is already superseded

Read them for layout, wording and tone. These parts were decided differently
after they were drawn:

- **Five compartments.** Both exports assume five. The user picks **three or
  four**; five does not fit 24 mm of box depth at any useful proportion.
- **Tabs.** `guide.html` § 03 says to cut dividers "a few millimetres taller
  than the cards, so the numbered tabs stand above the stack", and § 02 says
  "the intervals are printed on the divider tabs". **There are no tabs.** A
  divider is exactly card-sized and is told apart by its colour and its numeral.
- **A solid-colour face.** Both exports fill the whole divider. The decision is
  a **border band** on both faces instead — same colour front and back, numeral
  and interval inside it, running through the cut line so a mis-cut still lands
  in colour.
- **A sheet of its own.** `dividers.html` lays five dividers out on an A4 page
  with its own cut marks and its own `160–250 gsm` footer. The dividers are
  instead **appended to the card PDF as further cards**, so they are cut with
  everything else and cost no extra sheet. The heavier stock applies to the box
  only.
- **The card size printed on it.** `dividers.html` says `70 × 49 mm`, the same
  nominal `assets/card-box.pdf` prints and the same one `docs/design.md`
  corrects: the real A8 card is **71.75 × 50 mm**. Whatever is built has to take
  the size from the card geometry rather than restate it.

## What in them holds

- The palette and the assignment: 1 red `#c2251b`, 2 yellow `#f0c000`,
  3 blue `#0a3f8f`, 4 black `#141414` — the brand colours from
  `docs/design.md`, in that order.
- The oversized numeral as the primary identifier. It is what survives a
  black-only photocopy once the colour is gone, which is the rule that whole
  page exists for.
- The wording of the four house rules, and of the daily loop.

## How big a divider may be, and where it goes

**Rewritten 2026-09-07**, after the cross-model review rejected the layout this
section originally described. What follows is what shipped; the reasoning that
was replaced lives in [research.md](../research.md) R1, in a block marked
superseded.

The box (`docs/design.md` § The divider) is **73 × 52 mm** inside against a
**71.75 × 50 mm** A8 card. So a divider is **1.5 mm taller and never wider**:
51.5 mm still slides and still sits below the rim, and width buys nothing —
cards stand on their long edge and the box is looked into from above, so the
side edges are never seen.

**A divider is not placed in the card grid.** Two grid cells share one cut line,
and two colours cannot both bleed across it: every divider would have carried a
strip of its neighbour's colour on the edge they share, and no band width fixes
that. They are free-placed instead, at least 8 mm cut line to cut line from
anything else — three in one row, four as two rows of two, because
`4 × 71.75 = 287.00 mm` is exactly the A8 print width.

Three ideas this file used to describe are gone with that change: the bottom
row, the downward-only growth, and the `--margin 0` fallback. All three existed
only to work around the grid.

**The block does not always cost a sheet.** It goes in the free height below the
cards where it fits — a two-row block needs 2.44 free card rows, a one-row block
1.25 — and opens a further page where it does not. The run says which case it is
in rather than implying the cheap one.

**And the divider draws its own cut line.** The colour bleeds 3 mm past the trim,
so the visible colour edge is *not* where the divider ends; cutting there gives
77.75 mm, which enters no box at all. The line is drawn on the piece, the way
`templates/card.typ` has always drawn one for a card.
