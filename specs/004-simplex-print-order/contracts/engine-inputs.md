# Contract: `scripts/build_pdf.py` → `templates/cards.typ`

**Feature**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

Not one of the five file formats — this is the internal seam between the Python
that decides and the Typst that draws. It is written down because it has
already caused one bug class: `engine_inputs()` exists precisely because the
compile call and the overflow query used to build their arguments separately,
and a grid that reached one but not the other typeset at one size while
reporting overflow against another (`scripts/build_pdf.py:290`).

`sides` joins that list under the same rule.

## The pairs

| `--input` | Type | Default in `cards.typ` | Set by |
|---|---|---|---|
| `margin` | mm, float | `5` | `--margin` |
| `logo` | `true` \| `false` | `true` | `--no-logo` |
| `columns` | int | `2` | the resolved grid |
| `rows` | int | `4` | the resolved grid |
| `sheet-w` | mm, float | `210` | the resolved grid |
| `sheet-h` | mm, float | `297` | the resolved grid |
| `scale` | float | `1.0` | the resolved grid |
| **`sides`** | **`duplex` \| `simplex`** | **`duplex`** | **`--sides`** |

## Rules

1. **One builder.** Every engine invocation gets its arguments from
   `engine_inputs(margin, logo, grid, sides)`. Three call sites use it today —
   `typeset()`, `offending_card()` and `overflowing()` — and all three keep
   using it. A caller that assembles `--input` pairs by hand is the bug this
   function was written to prevent.

2. **`sides` is passed even where it cannot matter.** `overflowing()` asks the
   engine which cards run off their card area, which depends on the grid and
   the scale but not on page order; `offending_card()` typesets one card at a
   time to find a culprit. Both still receive `sides`, because "pass everything
   everywhere" is checkable and "pass the subset each call needs" is a rule
   somebody has to remember.

3. **Absent means duplex.** `cards.typ` reads
   `sys.inputs.at("sides", default: "duplex")`, so an engine call that omits
   the pair produces today's output rather than an error or a surprise. This is
   how every other parameter in the table already behaves.

4. **Typst validates nothing.** An unrecognised value would silently take the
   duplex branch. That is acceptable only because the value can never be
   unrecognised: `argparse` restricts it to the two members of `SIDES` and
   exits 2 otherwise (FR-005), so the Python side is the single validation
   point. If a third order is ever added, it is added to `SIDES` and to the
   `cards.typ` branch in the same change.

5. **No new Typst feature.** The branch uses `sys.inputs`, `range`, `.map`,
   `.fold` and `.enumerate`, all long-standing, so `scripts/engine.py` keeps
   its pinned version and all six platform checksums (constitution XV).

## What `cards.typ` does with it

```typst
#let sides = sys.inputs.at("sides", default: "duplex")
#let sheets = range(0, calc.ceil(cards.len() / per-page))
#let order = if sides == "simplex" {
  sheets.map(i => (i, false)) + sheets.map(i => (i, true))
} else {
  sheets.map(i => ((i, false), (i, true))).fold((), (a, p) => a + p)
}
```

Then one loop over `order`, placing a `pagebreak()` before every face but the
first, and passing the face's `is_back` as both the renderer selector and the
`mirror` argument to `sheet()`.

**`.flatten()` is not usable here**: it flattens deeply and would turn
`((0, false), (0, true))` into `(0, false, 0, true)`, destroying the pairs.
`.fold((), (a, p) => a + p)` concatenates one level, which is what is wanted.
