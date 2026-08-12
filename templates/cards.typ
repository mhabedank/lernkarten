// The press sheet — the build writes cards.json next to this file and calls
// typst. A4 with 2 x 4 cards; front pages and back pages alternate, and the
// backs are column-mirrored so duplex printing with "flip on long edge"
// lines them up.
//
// The card design itself lives in card.typ. Parameters come in via --input:
// margin (mm) and logo (true/false). Layout changes belong here or there,
// never in the generated file.

#import "card.typ": faces, guide

#let cards = json("cards.json")
#let margin = float(sys.inputs.at("margin", default: "5")) * 1mm
#let show-logo = sys.inputs.at("logo", default: "true") == "true"

#let columns = 2
#let rows = 4
#let per-page = columns * rows
#let cw = (210mm - 2 * margin) / columns
#let ch = (297mm - 2 * margin) / rows

#set page(width: 210mm, height: 297mm, margin: 0pt)

#let card = faces(cw, ch, show-logo: show-logo)

// Crop marks reach into the free margin at every cut. With no margin the card
// frames sit on the paper edge and there is nothing left to mark.
#let cropmarks = if margin != 0mm {
  let arm = calc.min(margin * 0.7, 3mm)
  let stroke = 0.3pt + guide
  for i in range(0, columns + 1) {
    let x = margin + i * cw
    place(dx: x, dy: margin - arm, line(end: (0mm, arm), stroke: stroke))
    place(dx: x, dy: 297mm - margin, line(end: (0mm, arm), stroke: stroke))
  }
  for j in range(0, rows + 1) {
    let y = margin + j * ch
    place(dx: margin - arm, dy: y, line(end: (arm, 0mm), stroke: stroke))
    place(dx: 210mm - margin, dy: y, line(end: (arm, 0mm), stroke: stroke))
  }
}

// A sheet of up to 8 cards. `mirror` flips the columns for the back pages.
#let sheet(block-of-cards, render, mirror) = {
  cropmarks
  for (position, one) in block-of-cards.enumerate() {
    let column = calc.rem(position, columns)
    let row = calc.quo(position, columns)
    if mirror { column = columns - 1 - column }
    place(dx: margin + column * cw, dy: margin + row * ch, render(one))
  }
}

#let pages = range(0, calc.ceil(cards.len() / per-page))
#for page-index in pages {
  let block-of-cards = cards.slice(
    page-index * per-page,
    calc.min((page-index + 1) * per-page, cards.len()),
  )
  sheet(block-of-cards, card.front, false)
  pagebreak()
  sheet(block-of-cards, card.back, true)
  if page-index < pages.len() - 1 { pagebreak() }
}
