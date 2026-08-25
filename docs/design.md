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

**Reading text means Archivo**, and the table above is what says so: Jost 500
carries uppercase labels and IBM Plex Mono carries literals, and neither is
prose. So the floor binds every Archivo paragraph — including a note beside a
heading, a caption under a code sample and a description in a list, all of which
are prose in a muted colour rather than a different category of text — and it
does not bind a letterspaced label at 11 px or a card id at 8.5 px.

The rule is scoped here rather than left to judgement because it had been read
three incompatible ways in one specification, and the landing page sat below it
in six places while a document in this repository certified that it did not.
`tests/test_landing_page.py` now asserts it: a size under 15 px is allowed only
where the rule that sets it also names one of the other two faces.

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

105 × 74.25 mm at A7, or 74.25 × 52.5 mm at A8 — landscape either way, and the
whole card rendered at one scale, so every proportion holds. It is *not* the A7
card cut down the middle: that would be portrait, because every A-series halving
flips the orientation. The sheet turns instead. Three bands that never move, at
either size:

| Band | Height | Holds |
|---|---|---|
| header | 8.6 mm | topic `/` subtopic, then the side marker: a red circle on the front, a yellow disc on the back |
| field | the rest | one prompt on the front, the answer on the back |
| footer | 6.2 mm | the mark, `LERNKARTEN BY MHABEDANK`, the card id at 8 pt and `1/2` or `2/2` |

The frame and the band rules are 0.9 pt; the field is inset 3.4 mm across and
2.8 mm down. The front prompt is Jost 500 at 14 pt and sits centred in the
field; the back is Archivo at 11 pt and starts at the top. Above the footer,
wherever the answer leaves room, are one or two dotted rules — the note you
write the third time you get the card wrong, and the one thing paper does that
an app cannot. The source, if the card names one, sits on the bottom line
behind a short blue dash.

The card id sits in the right-hand block of the footer, IBM Plex Mono at 8 pt,
followed by `·` and the side marker. It is five characters of Crockford Base32,
and the size follows from that: the old id was the file name and the card's
position — `genai-foundation-and-model-landscape-32` — which measured 124.62 pt
against a block capped at `cw / 3`, 94.49 pt, with `clip: true`. It was cut off
on the printed card. Five characters measure 52.80 pt, 56 % of the cap, which is
what makes room to set it large enough to read across a desk.

**8 pt and not larger**, though 11 pt would still fit the box. The wordmark
beside it is 5 pt, and at 11 pt the id dominates a band that is meant to be
quiet. The clip cap is not the binding constraint here; the balance of the
footer is. A card with no id — a deck written before ids existed — shows the
side marker on its own, with no separator in front of nothing.

Two things the layout deliberately does *not* do:

- **It never fills the card.** `#fbfaf6` is what a card looks like in a
  picture; on paper that would be a solid block of toner on every card. Only
  the two markers and the footer box on the back carry ink area.
- **It never shrinks type to fit.** A card whose text does not fit is reported
  through the `<overflow>` label, the build turns that into a warning, and the
  card gets split in two.

Everything above holds at both sizes, and the third rule is why: the bands are
fixed, so A8 takes its width out of the *field*, not out of the header or the
footer. What changes with the size is how much text fits, not where anything
sits.

### A picture in the field

A card may carry a picture on either face — `front_image` for "what does this
show?", `back_image` for "describe X". It sits **inside the field**, so the
three bands do not move and nothing about the sheet changes.

| Face | Where it goes | What it may displace |
|---|---|---|
| front | under the prompt, which keeps its 14 pt and its place | the vertical centring; the prompt moves to the top |
| back | the row the note rules live in, between answer and source | the note rules, entirely |

The picture wins that middle row outright. Rules crammed into what a diagram
leaves over would be a smudge, not somewhere to write, so a face with a picture
has none.

It is `fit: "contain"`, so it is never cropped and never wider than the field.
And it is measured for overflow at a **minimum useful height** rather than at
the room it happens to be given — otherwise an answer long enough to squeeze a
diagram to two millimetres would report "fits" and print something nobody can
read. Past that, the card is reported and split in two, exactly as an overlong
text card is. The type is never shrunk to make room; that rule has no exception
for pictures.

**One limit is real and cannot be designed away.** This project's own graphics
obey *colour never carries meaning alone*, but a chart lifted from someone
else's PDF does not: a red-versus-green series becomes grey on grey on a
black-only laser, and no check can judge that. What the layout guarantees
instead is that the card still works without the picture — the text on the same
face says what the picture shows, which is why that text is required rather
than optional. Whether the figure itself survived the toner is a question for
the printed sheet, and it is on the manual checklist in
[testing.md](testing.md).

The layout lives in [`templates/card.typ`](../templates/card.typ) and nowhere
else. The sheet that arranges them is
[`templates/cards.typ`](../templates/cards.typ).

## The press sheet

A configurable grid, `--grid`, with two settings — because those are the two
that cut to a card you can buy a box for:

| `--grid` | Alias | Per A4 sheet | Card at `--margin 5` | Card at `--margin 0` |
|---|---|---|---|---|
| `2x4` | `a7` | 8, two columns by four rows | 100 × 71.75 mm | 105 × 74.25 mm (DIN A7) |
| `4x4` | `a8` | 16, four columns by four rows **on a landscape A4** | 71.75 × 50 mm | 74.25 × 52.5 mm (DIN A8) |

`2x4` is the default and stays the default: it is the size the cards in this
repo are written for. A card file may name its own with a top-level `grid:`
key, and `--grid` on the command line overrides it. A4 halves into A7 and
halves again into A8, so both grids fill the sheet exactly and every cut line
is shared between two cards.

The backs are mirrored column-wise, so turning a sheet on its long edge lines
them up — at four columns as at two. Whoever does the turning is what `--sides`
picks: at `duplex` each sheet's faces sit on consecutive pages and the printer
turns the paper; at `simplex` every front comes first and the reader turns the
stack between two print jobs. The mirroring is the same either way, because a
stack turned on its long edge is the flip a duplex printer makes.
Default margin 5 mm, which keeps clear of printers with a non-printable edge;
crop marks reach into that margin at every cut. With `--margin 0` the card
frames sit on the paper edge and there are no crop marks to draw.

Everything scales together, the header band included, so a deck written for one
grid prints at the other unchanged. The band holds about 53 characters of
`TOPIC / SUBTOPIC` on one line at either size; past that the label wraps inside
the band and stays readable, and text is only lost around 200 characters, where
a fourth line no longer fits.

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

### The step strip

The pipeline strip — on the landing page and as `pipeline.png` — carries seven
cells, two of which are optional. Two rules hold there:

- **Optional is a word, not a colour.** Each optional cell carries a literal
  `OPTIONAL` label. Colour never carries meaning on its own, and a muted fill
  alone would say nothing on a black-and-white screenshot.
- **The measure is set by the longest command, not by the caption.**
  `/learning-goal` is fourteen characters of mono, so it decides the column
  width; the caption then gets whatever is left. That is why the landing page
  sets the command at 16 px rather than 18 px — it buys the room that keeps the
  caption at 15 px, the floor above. Narrower cells for the optional steps were
  considered and rejected: they hold the two longest names.

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
