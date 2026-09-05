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

## How big a divider may be

Recorded because the arithmetic is what settled it, and it is easy to redo
wrong.

The box (`docs/design.md` § The box) is **73 × 52 mm** inside against a
**71.75 × 50 mm** A8 card: 1.25 mm of clearance across, 2 mm up. So 2 mm larger
on both axes does not go in at all, and width has nothing to gain anyway —
cards stand on their long edge and the box is looked into from above.

**1.5 mm of extra height** reaches 51.5 mm against a 52 mm opening, which still
slides and still sits below the rim.

The sheet permits exactly that and nothing more. `card_size()` in
`scripts/build_pdf.py:169` is `(sheet - 2 * margin) / grid`: cards tile the
print area with **no gutter**, so a wider divider collides with the card beside
it, while a taller one collides only with the row above or below — and below the
bottom row there is already a gutter, the page margin. Hence: bottom row, growing
down, no second grid.

At `--margin 0` there is no margin to grow or bleed into, and dividers fall back
to exact card size.

## What simplex costs

`templates/cards.typ:63-70` mirrors **columns** for the back pages, never rows,
so "down" is the same paper edge on both faces at either `--sides` value.

What changes under `--sides simplex` is registration: the stack is turned by
hand and re-fed, which is routinely 1–2 mm off and may be skewed. The colour
band has to stay at every cut edge under a 2 mm back-face offset — that is a
floor under its width — and the bleed runs as far as the page margin allows
rather than only as far as the 1.5 mm of growth.
