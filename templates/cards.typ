// Flashcard layout — the build writes cards.json next to this file and calls
// typst. A4 with 2 x 4 cards; front pages and back pages alternate, and the
// backs are column-mirrored so duplex printing with "flip on long edge"
// lines them up.
//
// Parameters come in via --input: margin (mm) and logo (true/false).
// Layout changes belong here, never in the generated file.

#let cards = json("cards.json")
#let margin = float(sys.inputs.at("margin", default: "5")) * 1mm
#let show-logo = sys.inputs.at("logo", default: "true") == "true"

#let columns = 2
#let rows = 4
#let per-page = columns * rows
#let cw = (210mm - 2 * margin) / columns
#let ch = (297mm - 2 * margin) / rows

#set page(width: 210mm, height: 297mm, margin: 0pt)
#set text(font: "New Computer Modern", size: 10pt)
#set par(justify: false, leading: 0.65em)

// Brand mark: two stacked cards, drawn here so the build needs no image file.
#let logomark = box(width: 4.8mm, height: 2.9mm, {
  place(dx: 0.15mm, dy: 0.3mm, rotate(-14deg, rect(
    width: 3.1mm, height: 2.2mm, radius: 0.4mm,
    stroke: 0.2mm + luma(150),
  )))
  place(dx: 1.45mm, dy: 0.55mm, rect(
    width: 3.1mm, height: 2.3mm, radius: 0.4mm,
    fill: white, stroke: 0.2mm + luma(110),
    align(center + horizon, text(size: 4pt, weight: "bold", fill: luma(110))[?]),
  ))
})

// Grey guides to cut along. With no margin the outer edges are paper edges.
#let cutlines = {
  let xs = range(0, columns + 1).map(i => margin + i * cw)
  let ys = range(0, rows + 1).map(j => margin + j * ch)
  if margin == 0mm {
    xs = xs.slice(1, -1)
    ys = ys.slice(1, -1)
  }
  for x in xs {
    place(dx: x, dy: 0mm, line(end: (0mm, 297mm), stroke: 0.1pt + luma(160)))
  }
  for y in ys {
    place(dx: 0mm, dy: y, line(end: (210mm, 0mm), stroke: 0.1pt + luma(160)))
  }
}

#let subdued = luma(120)

#let inset = 3.5mm

// One card face. `head` sits above the content, `foot` below it. Content that
// does not fit is reported through the <overflow> label, which the build reads
// back with `typst query` and turns into a warning.
#let face(head, body, foot, lang, id) = box(width: cw, height: ch, inset: inset, {
  set text(lang: lang)
  let headline = align(center, text(size: 7pt, fill: subdued, head))
  let middle = box(width: 100% - 6mm, align(center, body))
  context {
    let room = ch - 2 * inset
    let used = (
      measure(box(width: cw - 2 * inset, headline)).height +
      measure(box(width: cw - 2 * inset - 6mm, body)).height +
      measure(box(width: cw - 2 * inset, foot)).height
    )
    if used > room { [#metadata(id)<overflow>] }
  }
  grid(
    rows: (auto, 1fr, auto),
    row-gutter: 0pt,
    headline,
    align(center + horizon, middle),
    foot,
  )
})

#let front(card) = face(
  if card.subtopic != "" [#card.topic #h(0.4em) · #h(0.4em) #card.subtopic] else [#card.topic],
  eval(card.front, mode: "markup"),
  grid(
    columns: (1fr, auto),
    align(left + bottom, if show-logo { logomark }),
    align(right + bottom, text(size: 5pt, fill: luma(150), card.id)),
  ),
  card.lang,
  card.id,
)

#let back(card) = face(
  [],
  eval(card.back, mode: "markup"),
  grid(
    columns: (1fr, auto),
    align(left + bottom, text(size: 7pt, fill: subdued, card.source)),
    align(right + bottom, text(size: 5pt, fill: luma(150), card.id)),
  ),
  card.lang,
  card.id,
)

// A sheet of up to 8 cards. `mirror` flips the columns for the back pages.
#let sheet(block-of-cards, render, mirror) = {
  cutlines
  for (position, card) in block-of-cards.enumerate() {
    let column = calc.rem(position, columns)
    let row = calc.quo(position, columns)
    if mirror { column = columns - 1 - column }
    place(dx: margin + column * cw, dy: margin + row * ch, render(card))
  }
}

#let pages = range(0, calc.ceil(cards.len() / per-page))
#for page-index in pages {
  let block-of-cards = cards.slice(
    page-index * per-page,
    calc.min((page-index + 1) * per-page, cards.len()),
  )
  sheet(block-of-cards, front, false)
  pagebreak()
  sheet(block-of-cards, back, true)
  if page-index < pages.len() - 1 { pagebreak() }
}
