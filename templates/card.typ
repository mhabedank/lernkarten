// The card itself: one face, three bands — a header rule, the field, a footer
// rule. The bands never move; only what stands in the field changes.
//
// This file is imported by the sheet layout (cards.typ) and by the brand
// assets under assets/brand/, so there is one card design in the repo and not
// two. See docs/design.md for what the parts mean.

// The inks. Red asks, yellow answers, blue structures; the reading is always
// near-black. No colour carries meaning on its own — every one is doubled by
// a shape or a position, so a black-only laser print stays just as sortable.
#let ink = rgb("#141414")
#let paper = rgb("#fbfaf6")
#let ground = rgb("#e9e5da")
#let red = rgb("#c2251b")
#let yellow = rgb("#f0c000")
#let blue = rgb("#0a3f8f")
#let muted = rgb("#3a3733")
#let guide = rgb("#8c8779")
#let note-grey = rgb("#b5b0a2")

// Jost sets the prompts, Archivo the reading text, IBM Plex Mono the ids.
// The engine's own New Computer Modern picks up Greek and Cyrillic, which
// neither of the two shipped faces covers.
#let display = ("Jost", "New Computer Modern")
#let reading = ("Archivo", "New Computer Modern")
#let mono = ("IBM Plex Mono", "DejaVu Sans Mono")

// The mark at footer size: the corner you turn, inside the card. Two shapes
// are all that survive at 3 mm, so the circle is left to the larger versions.
#let mini-mark(colour, scale: 1.0) = box(width: 4.4mm * scale, height: 3.1mm * scale, {
  place(polygon(fill: colour, (0mm, 3.1mm * scale), (0mm, 0mm), (2.2mm * scale, 0mm)))
  place(rect(
    width: 4.4mm * scale,
    height: 3.1mm * scale,
    stroke: 0.4pt * scale + colour,
  ))
})

// Builds the two face renderers for a card of `cw` x `ch`. `scale` sizes the
// rules, insets and type together, so the same card can be drawn at 1:1 for
// the printer and at 2:1 for a screenshot without redrawing anything.
#let faces(cw, ch, show-logo: true, scale: 1.0) = {
  let hairline = 0.9pt * scale + ink
  let pad-x = 3.4mm * scale
  let pad-y = 2.8mm * scale
  let head-h = 8.6mm * scale
  let foot-h = 6.2mm * scale
  let field-h = ch - head-h - foot-h
  let field-w = cw - 2 * pad-x

  // Header band: topic / subtopic, then the side marker — a red circle on the
  // front, a yellow disc on the back. Long labels are clipped rather than
  // allowed to push the band open; the overflow check reports them.
  let header(card, back) = {
    let label = if card.subtopic != "" {
      [#upper(card.topic)#text(fill: guide)[ \/ ]#upper(card.subtopic)]
    } else {
      upper(card.topic)
    }
    place(box(
      width: cw - head-h,
      height: head-h,
      inset: (x: pad-x),
      clip: true,
      align(horizon, text(
        font: display,
        weight: 500,
        size: 6pt * scale,
        tracking: 0.1em,
        label,
      )),
    ))
    place(dx: cw - head-h, box(
      width: head-h,
      height: head-h,
      fill: if back { yellow } else { red },
      align(center + horizon, circle(
        radius: 1.6mm * scale,
        fill: if back { ink } else { paper },
      )),
    ))
    place(dx: cw - head-h, line(end: (0mm, head-h), stroke: hairline))
    place(dy: head-h, line(end: (cw, 0mm), stroke: hairline))
  }

  // Footer band: the mark, the wordmark, the card id and which side you hold.
  // The mark's box is hollow on the front and solid on the back — the one
  // signal you need when eight cards land face-down. `show-logo: false` drops
  // the mark and the wordmark and leaves the id.
  let footer(card, back) = context {
    let top = ch - foot-h
    // A card written before ids existed carries none, and then the block shows
    // the side marker on its own — a separator with nothing in front of it
    // would be a smudge, not information.
    let side = if back { "2/2" } else { "1/2" }
    let id = text(
      font: mono,
      size: 8pt * scale,
      fill: muted,
      if card.id == "" { side } else { card.id + " · " + side },
    )
    // The id block takes exactly the width its text needs, so nothing wraps
    // and the rule in front of it stays put whatever the card file is called.
    let id-w = calc.min(measure(id).width + 5mm * scale, cw / 3)
    place(dy: top, line(end: (cw, 0mm), stroke: hairline))
    place(dy: top, dx: cw - id-w, line(end: (0mm, foot-h), stroke: hairline))
    place(
      dy: top,
      dx: cw - id-w,
      box(width: id-w, height: foot-h, clip: true, align(horizon + center, id)),
    )
    if show-logo {
      place(dy: top, dx: foot-h, line(end: (0mm, foot-h), stroke: hairline))
      place(dy: top, box(
        width: foot-h,
        height: foot-h,
        fill: if back { ink } else { none },
        align(center + horizon, mini-mark(if back { paper } else { ink }, scale: scale)),
      ))
      place(dy: top, dx: foot-h, box(
        width: cw - foot-h - id-w,
        height: foot-h,
        inset: (x: 2.8mm * scale),
        clip: true,
        align(horizon, text(
          font: display,
          weight: 500,
          size: 5pt * scale,
          tracking: 0.2em,
        )[LERNKARTEN BY MHABEDANK]),
      ))
    }
  }

  // One card face. Content that does not fit is reported through the
  // <overflow> label, which the build reads back with `typst query` and turns
  // into a warning — an overlong card gets split in two, never set smaller.
  let face(card, back, body) = box(width: cw, height: ch, {
    set text(font: reading, size: 11pt * scale, fill: ink, lang: card.lang)
    set par(justify: false, leading: 0.62em)
    place(rect(width: cw, height: ch, stroke: hairline))
    header(card, back)
    place(dy: head-h, box(
      width: cw,
      height: field-h,
      inset: (x: pad-x, y: pad-y),
      body,
    ))
    footer(card, back)
  })

  // The smallest picture still worth printing. Overflow is measured against
  // this and not against the room the picture happens to be given: a diagram
  // squeezed into 2 mm would "fit" and teach nothing, which is exactly the
  // silent failure the overflow warning exists to prevent.
  let min-picture = 15mm * scale
  let picture(path) = image(path, fit: "contain", width: 100%, height: 100%)

  let front(card) = face(card, false, context {
    let prompt = text(
      font: display,
      weight: 500,
      size: 14pt * scale,
      eval(card.front, mode: "markup"),
    )
    let room = field-h - 2 * pad-y
    let prompt-h = measure(box(width: field-w, prompt)).height
    // A recognition card — "what does this chart show?" — puts the picture
    // under the prompt. The prompt keeps its size and its place; the picture
    // takes what is left, and never the other way round.
    if card.front_image != "" {
      let gutter = 2.5mm * scale
      if prompt-h + gutter + min-picture > room { [#metadata(card.ref)<overflow>] }
      box(width: field-w, height: room, grid(
        rows: (auto, 1fr),
        row-gutter: gutter,
        box(width: field-w, prompt),
        picture(card.front_image),
      ))
    } else {
      if prompt-h > room { [#metadata(card.ref)<overflow>] }
      align(horizon + left, box(width: field-w, prompt))
    }
  })

  // The back stacks answer, note rules and source. The rules are for what you
  // write the third time you get a card wrong — the one thing paper does that
  // an app cannot — so they appear only where the answer leaves room.
  let back(card) = face(card, true, context {
    let answer = eval(card.back, mode: "markup")
    let source = if card.source != "" {
      text(font: mono, size: 5pt * scale, fill: muted)[
        #box(width: 3.2mm * scale, height: 0.9pt * scale, fill: blue, baseline: -1pt * scale)
        #h(1.6mm * scale)#card.source
      ]
    }
    let gutter = 3mm * scale
    let room = field-h - 2 * pad-y
    let has-picture = card.back_image != ""
    let used = (
      measure(box(width: field-w, answer)).height
        + measure(box(width: field-w, source)).height
        + gutter
        + if has-picture { min-picture + gutter } else { 0mm }
    )
    if used > room { [#metadata(card.ref)<overflow>] }

    let free = room - used
    let note-rule = line(length: 100%, stroke: (
      paint: note-grey,
      thickness: 0.6pt * scale,
      dash: "dotted",
    ))
    let notes = if free >= 16mm * scale {
      stack(dir: ttb, spacing: 6mm * scale, note-rule, note-rule)
    } else if free >= 9mm * scale {
      note-rule
    }

    // The middle row is contested: the note rules fill it when the answer
    // leaves room, and a picture takes it outright when there is one. The
    // picture wins — rules crammed into what a diagram leaves over would be a
    // smudge, not somewhere to write.
    box(width: field-w, height: room, grid(
      rows: (auto, 1fr, auto),
      row-gutter: gutter,
      answer,
      if has-picture { picture(card.back_image) } else { align(bottom, notes) },
      source,
    ))
  })

  (front: front, back: back)
}
