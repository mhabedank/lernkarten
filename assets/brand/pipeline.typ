// The five commands as one strip: what you type, what it does, what it writes.
// Replaces the flowchart in the readme.

#import "common.typ": *

#set page(width: 1280pt, height: 300pt, margin: 0pt, fill: sand)
#set text(font: reading, size: 13pt, fill: ink)
#set par(leading: 0.62em)

#let w = 1280pt - 88pt
#let col = w / 5

// Each step gets a shape, not just a colour: square, triangle, ring, two
// cards, a sheet of lines.
#let square = box(width: 44pt, height: 44pt, fill: paper)
#let triangle = polygon(fill: ink, (0pt, 44pt), (44pt, 44pt), (44pt, 0pt))
#let ring = box(width: 44pt, height: 44pt, {
  place(circle(radius: 22pt, fill: paper))
  place(dx: 13pt, dy: 13pt, circle(radius: 9pt, fill: blue))
})
#let pair = box(width: 52pt, height: 44pt, {
  place(dy: 2pt, rect(width: 34pt, height: 24pt, fill: paper))
  place(dx: 16pt, dy: 16pt, rect(width: 34pt, height: 24pt, fill: yellow, stroke: 2pt + ink))
})
#let sheet = box(width: 40pt, height: 48pt, {
  place(rect(width: 40pt, height: 48pt, fill: paper))
  place(dx: 8pt, dy: 10pt, rect(width: 24pt, height: 3pt, fill: ink))
  place(dx: 8pt, dy: 18pt, rect(width: 24pt, height: 3pt, fill: ink))
  place(dx: 8pt, dy: 26pt, rect(width: 14pt, height: 3pt, fill: red))
})

#let steps = (
  (red, square, "/sources", "Say where your material lives — folders, PDFs, Zotero, web pages.", "sources.yaml"),
  (yellow, triangle, "/ingest", "Read it all and store it as text. Skips what has not changed.", "knowledge/"),
  (blue, ring, "/catalog", "Derive topics and subtopics. Extends the catalog you already have.", "catalog/topics.md"),
  (red, pair, "/cards", "Write the cards — everything, or one topic. Appends, never overwrites.", "cards/*.yaml"),
  (ink, sheet, "/print", "Compile a print-ready A4 PDF, eight cards to the page.", "output/cards.pdf"),
)

#place(dx: 44pt, dy: 34pt, box(width: w, height: 232pt, {
  place(rect(width: w, height: 232pt, stroke: 2pt + ink))
  for (i, step) in steps.enumerate() {
    let (colour, shape, command, what, writes) = step
    let x = i * col
    place(dx: x, dy: 0pt, rect(width: col, height: 84pt, fill: colour))
    place(dx: x, dy: 0pt, box(width: col, height: 84pt, align(center + horizon, shape)))
    place(dx: x, dy: 84pt, line(end: (col, 0pt), stroke: 2pt + ink))
    place(dx: x, dy: 84pt, box(width: col, height: 108pt, inset: (x: 20pt, y: 18pt), stack(
      dir: ttb,
      spacing: 10pt,
      text(font: mono, weight: 500, size: 19pt, command),
      text(size: 13pt, fill: muted, what),
    )))
    place(dx: x, dy: 192pt, line(end: (col, 0pt), stroke: 2pt + ink))
    place(dx: x, dy: 192pt, box(
      width: col,
      height: 40pt,
      inset: (x: 20pt),
      align(horizon, text(font: mono, size: 12pt, writes)),
    ))
    if i > 0 { place(dx: x, dy: 0pt, line(end: (0pt, 232pt), stroke: 2pt + ink)) }
  }
}))
