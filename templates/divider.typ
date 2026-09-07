// A compartment divider. Card-width, 1.5 mm taller, and deliberately not a card:
// it carries no user text, no id, no topic label and neither encoding of a
// card's side — it has no front and no back, so a side marker would be false.
//
// What it does carry is a colour band running out past its own cut line, an
// oversized numeral, the interval and one rule line. The numeral is what
// survives a black-only photocopy; colour only makes a compartment quick to
// find. See docs/design.md and specs/008-leitner-compartments/research.md R1.
//
// Every dimension arrives in the record from scripts/leitner.py by way of
// scripts/build_pdf.py, so nothing here is a second opinion about a millimetre.

#import "card.typ": display, ink, mono, paper

#let divider(d, scale: 1.0) = {
  let w = float(d.w) * 1mm
  let h = float(d.h) * 1mm
  let band = float(d.band) * 1mm
  let bleed = float(d.bleed) * 1mm
  let colour = rgb(d.colour)
  // Black is the one compartment colour the numeral cannot sit on.
  let on-band = if d.colour == "#141414" { paper } else { ink }

  box(width: w, height: h, {
    // The band runs from `bleed` outside the cut line to `band` inside it, on
    // all four edges. Nothing is ever adjacent to a divider, so it can bleed
    // freely: that is the whole reason the block left the card grid.
    place(dx: -bleed, dy: -bleed, rect(
      width: w + 2 * bleed,
      height: h + 2 * bleed,
      fill: colour,
    ))
    place(dx: band, dy: band, rect(width: w - 2 * band, height: h - 2 * band, fill: paper))

    // The cut line, drawn *on* the divider at its own boundary.
    //
    // Without it there is nothing to cut to. The band bleeds `bleed` past the
    // trim, so the visible colour edge is 3 mm too far out on every side — cut
    // there and the divider comes out 6 mm too wide, which no longer enters a
    // 73 mm box. Marks in the sheet margin only help someone with a guillotine
    // and a straight edge; scissors need the line on the piece.
    //
    // This is the rule `assets/card-box.pdf` already follows and docs/design.md
    // already states: cut is a solid stroke. You cut *on* the line, so what is
    // left of it afterwards is a hairline at the very edge.
    place(rect(width: w, height: h, stroke: 0.4pt * scale + on-band, fill: none))

    // The numeral, and the count it belongs to.
    place(dx: band + 3mm * scale, dy: band + 2mm * scale, text(
      font: display,
      weight: 400,
      size: 16mm * scale,
      fill: ink,
      str(d.number),
    ))
    place(dx: band + 3mm * scale, dy: band + 20mm * scale, text(
      font: display,
      weight: 500,
      size: 2.4mm * scale,
      tracking: 0.16em,
      fill: ink,
      upper("compartment " + str(d.number) + " / " + str(d.of)),
    ))

    // The interval — what the compartment is *for* — then the rule line: what
    // enters it and what leaves. Never a weekday: the interval already says
    // when, and a printed weekday would fix a start day nobody chose.
    place(dx: band + 3mm * scale, dy: h - band - 12mm * scale, text(
      font: display,
      weight: 500,
      size: 6mm * scale,
      fill: ink,
      lower(d.interval),
    ))
    place(dx: band + 3mm * scale, dy: h - band - 5mm * scale, text(
      font: mono,
      size: 2.6mm * scale,
      fill: ink,
      d.rule,
    ))

    // The number again, reversed out of the band, so the compartment is legible
    // edge-on in the box — which is the one view a divider is actually used in.
    place(dx: w - band - 1mm * scale, dy: h - band, box(
      width: band,
      height: band,
      align(center + horizon, text(
        font: mono,
        size: 2.4mm * scale,
        fill: on-band,
        str(d.number),
      )),
    ))
  })
}
