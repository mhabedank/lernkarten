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

## Why the dividers are not larger than a card

Worth recording, because "make them 1–2 mm bigger so you can feel them" is the
obvious first idea and it fails on two independent counts.

The box (`docs/design.md` § The box) is **73 × 52 mm** inside against a
**71.75 × 50 mm** A8 card: 1.25 mm of clearance across, 2 mm up. A divider 2 mm
larger does not go in on either axis, and one grown only in height reaches
51.5 mm against a 52 mm opening — a jam, for a protrusion too small to feel.

And `card_size()` in `scripts/build_pdf.py:169` is `(sheet - 2 * margin) / grid`.
Cards tile the print area with **no gutter**: a card's edge is its neighbour's
edge, one cut line serves both, and there is no spare millimetre to grow into.
