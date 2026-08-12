# The design — ink, type, and the card

Everything the project shows anyone is one system: the printed card, the mark,
the readme and the landing page. Three inks, three faces, one grid. This page
is what to read before changing how any of it looks.

The short version: the card is built from squares, circles and triangles;
colour never carries meaning on its own; and a black-only laser print has to be
exactly as usable as a colour one.

![A finished card, front and back](../assets/example-cards.png)

## Ink and paper

| Role | Hex | Where it appears |
|---|---|---|
| ink | `#141414` | every rule, every letter you read |
| paper | `#fbfaf6` | the card ground in pictures — never printed |
| sand | `#f2efe6` | the page ground on screen |
| ground | `#e9e5da` | the surface a card lies on in pictures |
| red — the prompt | `#c2251b` | the front marker, section 01 chips, the vertical cut |
| yellow — the answer | `#f0c000` | the back marker, highlights, the mirrored sheet |
| blue — structure | `#0a3f8f` | sources, dividers, the horizontal cuts |
| muted | `#3a3733` | secondary reading text |
| guide | `#8c8779` | the `/` between topic and subtopic, crop marks |

Near-black on warm paper rather than black on white: a contrast ratio around
14:1, high but not the 21:1 that tires the eyes under a desk lamp. The three
primaries never carry reading text. They label, divide and mark.

**The rule that matters:** every colour is doubled by a shape or a position.
The front marker is red *and* a hollow circle *and* in the header's right
square; the footer mark's box is hollow on the front *and* solid on the back.
Photocopy the stack and nothing is lost.

## Type

| Face | Weight | Job |
|---|---|---|
| Jost | 400 | the wordmark, display sizes |
| Jost | 500 | card prompts, headings, all uppercase labels |
| Archivo | 400 | reading text — the back of a card, a paragraph in a readme |
| IBM Plex Mono | 400 | card ids, YAML, commands, anything literal |

Jost is geometric and carries the Bauhaus line; Archivo has wider apertures
than a true geometric sans, so it survives 11 pt on cheap paper. Maths is set
in New Computer Modern Math, which the typesetter carries itself.

All three faces are shipped in [assets/fonts/](../assets/fonts/) under the SIL
Open Font License, and the build passes that folder to the typesetter while
ignoring system fonts — a card prints the same everywhere. Greek and Cyrillic
fall back to New Computer Modern, so Russian, Greek and Ukrainian cards still
set correctly.

Reading text is never smaller than 11 pt printed or 15 px on screen. Uppercase
labels are letterspaced between 0.1 em and 0.24 em; the wordmark never is.

## The mark

A card holding the three solids: the triangle is the corner you turn, the
circle is the question, the yellow half is the answer already inside it.
Constructed on a 12-unit grid, no curve that is not a true circle.

| File | Use |
|---|---|
| [`assets/logo.svg`](../assets/logo.svg) | the default, four inks |
| [`assets/logo-mono.svg`](../assets/logo-mono.svg) | one ink — laser, stamps, print |
| [`assets/logo-reversed.svg`](../assets/logo-reversed.svg) | on black or a photograph's dark quarter |
| [`assets/logo-small.svg`](../assets/logo-small.svg) | 32 px and below: the yellow half drops out, the frame thickens |

Clear space on all four sides equals the circle's radius. The wordmark is
always lowercase Jost 400, never letterspaced, never italic. The mark never
sits on red, yellow or blue — only on paper, on black, or on the dark quarter
of a photograph.

## The card

105 × 74.25 mm, landscape — A7. Three bands that never move:

| Band | Height | Holds |
|---|---|---|
| header | 8.6 mm | topic `/` subtopic, then the side marker: a red circle on the front, a yellow disc on the back |
| field | the rest | one prompt on the front, the answer on the back |
| footer | 6.2 mm | the mark, `LERNKARTEN BY MHABEDANK`, the card id and `1/2` or `2/2` |

The frame and the band rules are 0.9 pt; the field is inset 3.4 mm across and
2.8 mm down. The front prompt is Jost 500 at 14 pt and sits centred in the
field; the back is Archivo at 11 pt and starts at the top. Above the footer,
wherever the answer leaves room, are one or two dotted rules — the note you
write the third time you get the card wrong, and the one thing paper does that
an app cannot. The source, if the card names one, sits on the bottom line
behind a short blue dash.

Two things the layout deliberately does *not* do:

- **It never fills the card.** `#fbfaf6` is what a card looks like in a
  picture; on paper that would be a solid block of toner on every card. Only
  the two markers and the footer box on the back carry ink area.
- **It never shrinks type to fit.** A card whose text does not fit is reported
  through the `<overflow>` label, the build turns that into a warning, and the
  card gets split in two.

The layout lives in [`templates/card.typ`](../templates/card.typ) and nowhere
else. The sheet that arranges eight of them is
[`templates/cards.typ`](../templates/cards.typ).

## The press sheet

Eight cards to an A4 page, two columns by four rows. Fronts and backs on
consecutive pages, the backs mirrored column-wise so duplex printing with
"flip on long edge" lines them up. Default margin 5 mm, which leaves the cards
at 100 × 71.75 mm and keeps clear of printers with a non-printable edge; crop
marks reach into that margin at every cut. With `--margin 0` the card frames
sit on the paper edge and there are no crop marks to draw.

## The screen surfaces

The readme and the landing page use the same bands, the same rules and the same
three inks. Both are built from flat colour and type only — no gradients, no
shadows, no rounded corners.

| Surface | Source |
|---|---|
| landing page | [`docs/index.html`](index.html) — one self-contained file, published to GitHub Pages |
| readme banner, 1280 × 320 | [`assets/brand/banner.typ`](../assets/brand/banner.typ) |
| pipeline strip | [`assets/brand/pipeline.typ`](../assets/brand/pipeline.typ) |
| social card, 1200 × 630 | [`assets/brand/social-card.typ`](../assets/brand/social-card.typ) |
| example cards | [`assets/brand/example-cards.typ`](../assets/brand/example-cards.typ) |

The graphics are drawn in Typst, not by hand, so they take their inks and faces
from the card itself — and the example-cards picture is drawn by the very
layout that goes to the printer. Re-render after changing any of them:

```bash
python3 scripts/render_brand.py            # all of them
python3 scripts/render_brand.py banner     # just one
```

The PNGs it writes are committed. Nobody needs to run it to use the pipeline.

## Changing something

1. Card, sheet or brand graphic: edit the Typst source, never a generated file.
2. Re-render the brand PNGs if you touched the card or anything under
   `assets/brand/`.
3. Check what a printer would get:

   ```bash
   lernkarten build cards/example.yaml -o output/cards.pdf
   lernkarten build cards/example.yaml --margin 0 --no-logo -o output/borderless.pdf
   ```

4. Run the gates in [CONTRIBUTING.md](../CONTRIBUTING.md).

If a change makes the card prettier on screen and worse on a photocopier, it is
the wrong change.
