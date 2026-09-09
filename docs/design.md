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
that cut to a card there is a box for: A7 is a size boxes are sold in, and A8 is
the one this project ships as a printable net (see [The box](#the-box)):

| `--grid` | Alias | Per A4 sheet | Card at `--margin 5` | Card at `--margin 0` |
|---|---|---|---|---|
| `2x4` | `a7` | 8, two columns by four rows | 100 × 71.75 mm | 105 × 74.25 mm (DIN A7) |
| `4x4` | `a8` | 16, four columns by four rows **on a landscape A4** | 71.75 × 50 mm | 74.25 × 52.5 mm (DIN A8) |

**`4x4` is the default.** It was `2x4` until v0.9.0, and the reason it moved is
that `2x4` did not fit the one container this project ships: an A7 card is
100 mm wide against the card box's 73 mm opening, and the Leitner dividers
refuse anything but A8. A default whose output does not fit the box the same
repository hands out is the wrong default.

`2x4` remains fully supported, and remains **the reference size**: the card is
drawn at A7, the 11 pt floor is defined there, and every other grid is a uniform
scale of it. That reference is a separate constant from the default and does not
follow it — one name for both would have re-scaled every A7 card by 39 % the day
the default moved. A card file may name its own with a top-level `grid:`
key, and `--grid` on the command line overrides it. A4 halves into A7 and
halves again into A8, so both grids fill the sheet exactly and every cut line
is shared between two cards.

The backs are mirrored column-wise, so turning a sheet on its long edge lines
them up — at four columns as at two. Whoever does the turning is what `--sides`
picks: at `duplex` each sheet's faces sit on consecutive pages and the printer
turns the paper; at `simplex` every front comes first and the reader turns the
stack between two print jobs. The mirroring is the same either way, because a
stack turned on its long edge is the flip a duplex printer makes.

**"Long edge" is the edge of the *sheet*, not of the page.** The distinction is
invisible at A7 and easy to misread at A8, so it is worth stating: A4 leaves the
tray the same way whatever the grid — 210 mm across, 297 mm along — and the long
edge is that 297 mm side of the paper. The A8 *page* is landscape, so its own
long edge is the other one, and reading the phrase against the page rather than
the sheet gives the opposite flip. Column mirroring is correct at both grids
because the paper never turns; only the layout on it does.

**If your printer disagrees, one sheet tells you.** Print the first two pages
of any deck — at `--sides duplex` the printer turns them, at `--sides simplex`
you do — and look at a single card: the back of the card in the top-left corner
must be the card in the top-*right* corner of the reverse. If it is not, the
turn was the other one; switch the driver's setting, or turn the stack the other
way, and nothing else needs changing. Verified at both grids on real hardware,
but drivers vary and this check costs one sheet.
Default margin 5 mm, which keeps clear of printers with a non-printable edge;
crop marks reach into that margin at every cut. With `--margin 0` the card
frames sit on the paper edge and there are no crop marks to draw.

Everything scales together, the header band included, so a deck written for one
grid prints at the other unchanged. The band holds about 53 characters of
`TOPIC / SUBTOPIC` on one line at either size; past that the label wraps inside
the band and stays readable, and text is only lost around 200 characters, where
a fourth line no longer fits.

## The box

A cut-and-fold box for the cards, on one A4 portrait sheet:
[`assets/card-box.pdf`](../assets/card-box.pdf). Print it on 160–250 gsm card
stock at 100 %, cut the solid lines, fold the dashed ones, glue the tabs.
It holds about 90 cards.

| Property | Value |
|---|---|
| Fits | a deck at `--grid a8`, **default margin** — cards 71.75 × 50 mm |
| Inner box | 73 × 24 × 52 mm |
| Capacity | ≈ 90 cards, depending on stock |
| Paper | 160–250 gsm |
| Sheet | one page, A4 portrait |

**It does not fit an A7 deck:** an A7 card is 100 mm
wide against a 73 mm opening. Nor does an A8 deck printed at `--margin 0`, whose
cards are 74.25 mm. The landing page says so beside the download, because the
sheet cannot be changed to say it — see below.

The three line types are told apart **without colour**, as everything printed
here must be: cut is a solid stroke, fold is dashed, and a glue area is a tint
*plus* the printed word `glue`. A legend on the sheet names all three. Photocopy
it in black and nothing is lost, which is the rule this whole page exists for.

**This artifact has no source in the repository.** It was designed and folded
outside it, and nothing in a checkout can rebuild it — the one exception to
[Principle IX](../.specify/memory/constitution.md) and a named entry in
Principle VIII. So the rules on this page apply to it by *inspection*, not by
construction, and three things it prints about itself are wrong and cannot be
fixed:

- it says `a4 landscape`; the page is A4 **portrait** (MediaBox 595.2 × 841.8 pt)
- it says `cards 70 × 49 mm`, a nominal; the real A8 card is **71.75 × 50 mm**
- it does not name the grid at all

Those three are why the landing page carries the constraint and this table
carries the measurements. `tests/test_repo_hygiene.py` pins the file's SHA-256:
"unchanged" is the only guarantee an artifact without a source can offer, so a
replacement has to be re-folded and the hash updated deliberately.

## The divider

A **compartment divider** for a Leitner box: `lernkarten build --grid a8
--dividers 3` or `--dividers 4` prints them beside the cards, in the same run,
on the same stock. Card width, **1.5 mm taller**, and not a card in any other
sense — no user text, no id, no `TOPIC / SUBTOPIC`, and neither encoding of a
card's side, because a divider has no front and no back.

| Property | Value | Where it comes from |
|---|---|---|
| Size | card width × card height + 1.5 mm | the box is 73 × 52 mm inside against a 71.75 × 50 mm A8 card, so 51.5 mm still slides and still sits below the rim |
| Colour band | 4 mm inward from the cut line | 2 mm registration error under a hand-fed simplex run, plus 1 mm of cut error, gives a floor of 3 mm; the fourth is headroom |
| Bleed | 3 mm outward | the same floor, from the other direction |
| Gap | ≥ 8 mm, **cut line to cut line** | two bleeds facing each other plus the cut tolerance, so the middle 2 mm is unprinted |
| Layout | three in one row; four as two rows of two | `4 × 71.75 = 287.00 mm` is exactly the A8 print width, so four can never share a row |

**A divider is not placed in the card grid**, and that is the whole design.
Two grid cells share one cut line, and two colours cannot both bleed across it
— every divider would carry a strip of its neighbour's colour on the edge they
share. Free-placed, nothing is ever adjacent to a divider, so the bleed's
guarantee is unconditional: **the divider's own colour** reaches every cut edge
on both faces, even with the back displaced 2 mm.

### It carries more ink than a card, on purpose

The rule above — *it never fills the card* — holds for **cards**. A divider is a
different artifact and is allowed a border band, because being findable at a
glance is its entire function and it carries no reading text to compete with.

This is not a loosening for cards. It is the second named exception on this
page, beside `assets/card-box.pdf`'s exception to Principle IX, and it is
written down for the same reason: so the next reader finds a decision rather
than a violation.

Colour still carries no meaning alone. The oversized numeral is what says which
compartment this is, and it survives a black-only photocopy; the colour only
makes one quick to find. On the fourth compartment's `#141414` band the numeral
and the cut line reverse out in paper white.

### The cut line is drawn on the divider

Because the band bleeds 3 mm past the trim, the **visible colour edge is not
the cut line** — cutting there gives a divider 77.75 mm wide, which enters no
box at all. So the divider draws its own trim as a solid stroke, exactly the
rule the card box already follows and `templates/card.typ` has always applied to
a card. Marks in the sheet margin only help someone with a guillotine and a
straight edge; scissors need the line on the piece.

For the same reason the sheet's **grid crop marks are suppressed on a page that
holds no card**: with the block centred at A8 the grid column at x = 76.75 mm
falls 4 mm *inside* the first divider, and a user cutting to the crop marks
would slice it in half.

## The screen surfaces

The readme, the landing page and the documentation site use the same bands, the
same rules and the same three inks. All of them are built from flat colour and
type only — no gradients, no shadows, no rounded corners.

| Surface | Source |
|---|---|
| landing page | [`docs/index.html`](index.html) — one self-contained file, published to GitHub Pages |
| documentation site | [`docsite/`](../docsite/) — Sphinx and MyST, `pydata-sphinx-theme` overridden to the rules on this page |
| readme banner, 1280 × 320 | [`assets/brand/banner.typ`](../assets/brand/banner.typ) |
| pipeline strip | [`assets/brand/pipeline.typ`](../assets/brand/pipeline.typ) |
| social card, 1200 × 630 | [`assets/brand/social-card.typ`](../assets/brand/social-card.typ) |
| example cards | [`assets/brand/example-cards.typ`](../assets/brand/example-cards.typ) |

The documentation site is the one surface that starts from someone else's
design, so it is worth saying what is kept and what is not. **Kept**: the
two-level navigation, the theme's bundled icon font, admonitions that double
their colour with an icon and a rule, and the footer credit. **Overridden**:
the nine inks, the three faces self-hosted from `assets/fonts/`, every radius,
shadow and gradient, and the 15 px reading floor — the theme sets its sidebar
and its small labels at 14.4 px.

The override is written as a rule rather than as a list of selectors, and for
the same reason the type floor is: a list is correct only against the theme
version it was read from, and the next release turns it into a record of
violations instead of a defence against them.
### Two-column sections

Four sections of the landing page are two columns side by side, and each is
drawn to the height of its **heavier** column. That is what makes a light column
a hole rather than a margin: the empty space is not a choice anybody made, it is
the arithmetic of the column beside it.

So a block joins the column whose **kind** it is — pictures with pictures, prose
with prose. The cutting diagram is a drawing of a sheet, so it belongs beside the
two drawings of sheets, not under four hundred pixels of text about printer
settings.

Moving it there is not enough on its own, and the failure is instructive: sent
to the picture column but left to wrap *below* the two sheets, it made that
column the heavy one and the hole simply reappeared on the other side. Three
pictures in one row is what makes both columns end together. Closing a hole and
moving it look identical from the column you were watching — measure both.

A block that belongs to neither kind, or that would make one column outgrow the
other by more than about half, becomes a **full-width block beneath both**. The
card box went that way — it is a different subject from the three printing rules,
what you keep the cards in rather than how you print them — and so did the
section notes before it, for the same reason.

There is no number here on purpose. Nothing in the test suite can measure a
column, so a threshold could not be enforced, and a false precision in this
document would only move the argument from *look at the page* to *what counts as
half*. What the checks do hold is the arrangement that produces the proportion:
`tests/test_landing_page.py` asserts that the card box is not inside the rules
column and that the diagram is inside the sheets column. Those are structure, and
structure is what a file that is never rendered can see.

Two worked examples, both measured before and after:

| Section | Before | After |
|---|---|---|
| `02 one card, one idea` | 269 px of content in a 644 px cell — 46 % empty | 564 px in 644 px |
| `03 print it, cut it` | 327 px in a 1176 px column — 65 % empty | both columns end together at 433 px |

Neither happened at once. `03` accreted over three features, each adding correct,
well-scoped content to the same column, none of them measuring it against the one
beside it. `02` was tipped by a *fix* — making the `hidden` attribute effective
left one card on screen where the column had been proportioned around two. Both
are what this rule exists to catch, because nothing else in this repository has
an opinion about proportion.

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
