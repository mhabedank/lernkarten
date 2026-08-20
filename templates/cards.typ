// The press sheet — the build writes cards.json next to this file and calls
// typst. A4 with columns x rows cards. The backs are column-mirrored, so
// turning a sheet on its long edge puts each back behind its front; `sides`
// decides only the order the finished pages come in. At `duplex` each sheet's
// two faces sit on consecutive pages and the printer turns the paper; at
// `simplex` every front comes first and the user turns the stack between two
// print jobs.
//
// Two grids are supported, and they are the two that cut to a standard card:
// 2 x 4 is DIN A7 (8 up, the default) and 4 x 4 is DIN A8 (16 up). Card size,
// the mirroring, the crop marks and the pagination all derive from those two
// numbers, so nothing below is written twice.
//
// The card design itself lives in card.typ. Parameters come in via --input:
// margin (mm), logo (true/false), columns and rows. Layout changes belong here
// or there, never in the generated file.

#import "card.typ": faces, guide

#let cards = json("cards.json")
#let margin = float(sys.inputs.at("margin", default: "5")) * 1mm
#let show-logo = sys.inputs.at("logo", default: "true") == "true"

// duplex or simplex. Absent means duplex, so an engine call that forgets the
// pair produces the order this file has always produced.
#let sides = sys.inputs.at("sides", default: "duplex")
#let columns = int(sys.inputs.at("columns", default: "2"))
#let rows = int(sys.inputs.at("rows", default: "4"))
// The sheet is A4 either way round. Which way follows the grid, because a
// flashcard is landscape and every A-series halving flips the orientation:
// 2 x 4 tiles a portrait A4, 4 x 4 a landscape one. scripts/build_pdf.py
// decides and passes both numbers, so this file never has to know the rule.
#let sheet-w = float(sys.inputs.at("sheet-w", default: "210")) * 1mm
#let sheet-h = float(sys.inputs.at("sheet-h", default: "297")) * 1mm
// One factor for the whole card, so every proportion is preserved at a denser
// grid. 1.0 at 2 x 4, so the default sheet is untouched.
#let card-scale = float(sys.inputs.at("scale", default: "1.0"))
#let per-page = columns * rows
#let cw = (sheet-w - 2 * margin) / columns
#let ch = (sheet-h - 2 * margin) / rows

#set page(width: sheet-w, height: sheet-h, margin: 0pt)

#let card = faces(cw, ch, show-logo: show-logo, scale: card-scale)

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

// One sheet, up to columns x rows cards. `mirror` flips the columns for the
// back pages, which is what makes duplex line up at any grid.
#let sheet(block-of-cards, render, mirror) = {
  cropmarks
  for (position, one) in block-of-cards.enumerate() {
    let column = calc.rem(position, columns)
    let row = calc.quo(position, columns)
    if mirror { column = columns - 1 - column }
    place(dx: margin + column * cw, dy: margin + row * ch, render(one))
  }
}

#let sheets = range(0, calc.ceil(cards.len() / per-page))

// The page order as data: one (sheet, back?) pair per face. Both orders are
// the same 2 x sheets faces in a different sequence, so the page count cannot
// depend on which one is asked for. Note that `back?` is also the `mirror`
// argument below — a back page is mirrored by definition, so no ordering can
// pull the two apart.
//
// .flatten() would be wrong for the duplex branch: it flattens deeply and
// would turn ((0, false), (0, true)) into (0, false, 0, true).
#let order = if sides == "simplex" {
  sheets.map(i => (i, false)) + sheets.map(i => (i, true))
} else {
  sheets.map(i => ((i, false), (i, true))).fold((), (a, faces) => a + faces)
}

#for (position, (sheet-index, back)) in order.enumerate() {
  if position > 0 { pagebreak() }
  let block-of-cards = cards.slice(
    sheet-index * per-page,
    calc.min((sheet-index + 1) * per-page, cards.len()),
  )
  sheet(block-of-cards, if back { card.back } else { card.front }, back)
}
