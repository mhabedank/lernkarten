# Contract — `cards/<topic-slug>.yaml`

**Change**: two optional keys on a card, `front_image:` and `back_image:`.
Everything else is untouched.

## Schema (the addition in context)

```yaml
topic: 'Tides'
language: english
grid: a7
cards:
  - id: F3M2Q
    subtopic: 'Tide charts'
    front: 'Describe the shape of the Kestrel Deep tide curve'
    back: 'Two highs and two lows a day, the second high the weaker one.'
    back_image: 'figures/island-images/tide-chart.png'   # NEW — optional
    source: 'Tide chart, harbour office'

  - id: K7WT4
    subtopic: 'Tide charts'
    front: 'What does this chart show?'
    front_image: 'figures/island-images/tide-chart.png'  # NEW — optional
    back: 'A semidiurnal tide curve — two highs, two lows, unequal.'
```

## Rules

| # | Rule | Enforced by | Severity |
|---|---|---|---|
| C1 | The value is a path relative to the **project root** — the parent of the directory holding the card file | `build_pdf.load_cards`, `check_project.check_cards` | error |
| C2 | The file exists | both | error |
| C3 | The resolved path does not escape the project root | both | error |
| C4 | The extension is one of `png`, `jpg`, `jpeg`, `gif`, `svg`, `webp` | both | error |
| C5 | The file is decodable as that format | the engine, attributed by `offending_card()` | error |
| C6 | A face carrying a picture carries non-empty text on the same face | `check_project` | error |
| C7 | At most one card per project uses a given figure as `back_image`, and at most one as `front_image` | `check_project` | warning |
| C8 | Neither key may appear at the top level of the file — a picture belongs to a card, not a deck | `check_project` | error |
| C9 | A deck declaring `grid: a8` that contains any picture gets one note per run, not one per card | `check_project` | note, once |
| C10 | A subtopic with any picture-bearing card in a file has at least one card there with no picture key | `check_project` | warning |

C10 is FR-024 made observable: a figure must yield recall practice, not only
recognition. A warning rather than an error, because a hand-written single card
is legitimate — the rule describes what `/cards` should produce, not what a
human may not write.

## Error messages

Each names the card, the face and the path, and the four causes stay
distinguishable (FR-004):

```text
ERROR: cards/tides.yaml: card F3M2Q: back_image 'figures/island-images/tide-chart.png' does not exist
ERROR: cards/tides.yaml: card F3M2Q: back_image 'figures/x.tiff' is not an image the engine reads (png, jpg, jpeg, gif, svg, webp)
ERROR: cards/tides.yaml: card F3M2Q: back_image '../../elsewhere/chart.png' is outside the project
ERROR: cards/tides.yaml: card F3M2Q: front_image 'figures/a/b.png' could not be read by the typesetter: unknown image format
```

For a deck written before ids existed, the positional ref (`tides-4`) stands in
for the id, exactly as the overflow warning already does.

## What the engine receives

`payload()` emits `front_image` and `back_image` as **staged file names**, not
project paths — `fig-<sha256[:12]>.<ext>`, or `""` for a face without a
picture. `templates/card.typ` reads both fields unconditionally, as it already
reads `id`.

## Backwards compatibility

Both keys optional; absent means today's behaviour exactly. No existing key
changes meaning. A deck with no picture produces a byte-identical PDF (SC-007).
