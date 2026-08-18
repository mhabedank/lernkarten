// The seven commands as one strip: what you type, what it does, what it writes.
// Replaces the flowchart in the readme.
//
// Seven columns, not five, so the measure had to be re-derived rather than
// inherited: `/learning-goal` is 14 characters and would not fit the old 19pt
// mono, so the command drops to 15pt and the caption to 12pt, both still above
// the floor in docs/design.md. The two optional steps carry a literal OPTIONAL
// label — colour alone never carries meaning (constitution XVI).

#import "common.typ": *

#set page(width: 1280pt, height: 300pt, margin: 0pt, fill: sand)
#set text(font: reading, size: 13pt, fill: ink)
#set par(leading: 0.62em)

#let w = 1280pt - 88pt
#let col = w / 7

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
// The goal is a target you aim at; the gap is literally something missing.
#let diamond = polygon(fill: paper, (22pt, 0pt), (44pt, 22pt), (22pt, 44pt), (0pt, 22pt))
#let notch = box(width: 48pt, height: 44pt, {
  place(rect(width: 19pt, height: 44pt, fill: paper))
  place(dx: 29pt, rect(width: 19pt, height: 44pt, fill: paper))
})
#let sheet = box(width: 40pt, height: 48pt, {
  place(rect(width: 40pt, height: 48pt, fill: paper))
  place(dx: 8pt, dy: 10pt, rect(width: 24pt, height: 3pt, fill: ink))
  place(dx: 8pt, dy: 18pt, rect(width: 24pt, height: 3pt, fill: ink))
  place(dx: 8pt, dy: 26pt, rect(width: 14pt, height: 3pt, fill: red))
})

#let steps = (
  (blue, diamond, "/learning-goal", true, "Name what you are learning.", "goal.md"),
  (red, square, "/sources", false, "Say where your material lives.", "sources.yaml"),
  (yellow, triangle, "/ingest", false, "Read it and store it as text.", "knowledge/"),
  (blue, ring, "/catalog", false, "Derive the topics — from your goal.", "catalog/topics.md"),
  (yellow, notch, "/research-gaps", true, "Research what nothing covers.", "knowledge/<id>/"),
  (red, pair, "/cards", false, "Write the cards. Appends, never overwrites.", "cards/*.yaml"),
  (ink, sheet, "/print", false, "Compile a print-ready A4 PDF.", "output/cards.pdf"),
)

#place(dx: 44pt, dy: 34pt, box(width: w, height: 232pt, {
  place(rect(width: w, height: 232pt, stroke: 2pt + ink))
  for (i, step) in steps.enumerate() {
    let (colour, shape, command, optional, what, writes) = step
    let x = i * col
    place(dx: x, dy: 0pt, rect(width: col, height: 84pt, fill: colour))
    place(dx: x, dy: 0pt, box(width: col, height: 84pt, align(center + horizon, shape)))
    if optional {
      place(dx: x + 10pt, dy: 8pt, label("optional", size: 9pt, fill: ink, tracking: 0.18em))
    }
    place(dx: x, dy: 84pt, line(end: (col, 0pt), stroke: 2pt + ink))
    place(dx: x, dy: 84pt, box(width: col, height: 108pt, inset: (x: 14pt, y: 14pt), stack(
      dir: ttb,
      spacing: 9pt,
      text(font: mono, weight: 500, size: 15pt, command),
      text(size: 12pt, fill: muted, what),
    )))
    place(dx: x, dy: 192pt, line(end: (col, 0pt), stroke: 2pt + ink))
    place(dx: x, dy: 192pt, box(
      width: col,
      height: 40pt,
      inset: (x: 14pt),
      align(horizon, text(font: mono, size: 11pt, writes)),
    ))
    if i > 0 { place(dx: x, dy: 0pt, line(end: (0pt, 232pt), stroke: 2pt + ink)) }
  }
}))
