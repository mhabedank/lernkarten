// Shared pieces for the brand graphics. The inks and faces come from the card
// itself, so the readme, the social card and the printed card can never drift
// apart. Rendered to PNG by scripts/render_brand.py.

#import "../../templates/card.typ": (
  blue,
  display,
  ground,
  guide,
  ink,
  mono,
  muted,
  paper,
  reading,
  red,
  yellow,
)

#let sand = rgb("#f2efe6")

// The mark at any size. `style` is "colour", "mono" or "reversed"; below about
// 32 px use small: true, which drops the yellow half and thickens the frame.
#let mark(w, style: "colour", small: false) = {
  let u = w / 104
  let h = 74 * u
  let r = 21 * u
  let line-ink = if style == "reversed" { sand } else { ink }
  let disc = if style == "colour" { blue } else if style == "reversed" { sand } else { none }
  let corner = if style == "colour" or style == "reversed" { red } else { ink }
  let weight = (if small { 9 } else { 5 }) * u

  box(width: w, height: h, {
    if style == "reversed" { place(rect(width: w, height: h, fill: ink)) }
    place(polygon(fill: corner, (0pt, h), (0pt, 0pt), (w / 2, 0pt)))
    if disc == none {
      place(dx: w / 2 - r, dy: h / 2 - r, circle(radius: r, stroke: weight + line-ink))
    } else {
      place(dx: w / 2 - r, dy: h / 2 - r, circle(radius: r, fill: disc))
    }
    if not small {
      // The answer already inside the question: the right half of the circle.
      place(dx: w / 2, dy: h / 2 - r, box(
        width: r,
        height: 2 * r,
        clip: true,
        place(dx: -r, circle(radius: r, fill: if style == "mono" { ink } else { yellow })),
      ))
    }
    place(rect(width: w, height: h, stroke: weight + line-ink))
  })
}

// The wordmark is always lowercase Jost 400, never letterspaced.
#let wordmark(size, fill: ink) = text(font: display, weight: 400, size: size, fill: fill)[
  #lower("lernkarten")
]

#let label(body, size: 10pt, fill: ink, tracking: 0.24em) = text(
  font: display,
  weight: 500,
  size: size,
  fill: fill,
  tracking: tracking,
  upper(body),
)

#let commands = ("/sources", "/ingest", "/catalog", "/cards", "/print")
