// A finished card, front and back, drawn by the very layout that goes to the
// printer — templates/card.typ, at twice the size. If the card changes, this
// picture changes with it.

#import "common.typ": *
#import "../../templates/card.typ": faces

#let scale = 2.0
#let cw = 100mm * scale
#let ch = 71.75mm * scale
#let gap = 12mm
#let pad = 12mm

#set page(
  width: 2 * cw + gap + 2 * pad,
  height: ch + 2 * pad,
  margin: 0pt,
  fill: ground,
)

#let card = faces(cw, ch, scale: scale)
#let example = (
  id: "probability-3",
  topic: "Probability",
  subtopic: "Bayes theorem",
  front: "How is Bayes' theorem stated?",
  back: "The posterior is the likelihood times the prior, normalised by the evidence: \\ $P(A | B) = (P(B | A) P(A)) / P(B)$",
  source: "Lecture 3, slide 12",
  lang: "en",
)

// The layout never fills the card — that would be a solid block of toner on
// every print. Here the paper is painted in, because a picture has none.
#let on-paper(body) = box(width: cw, height: ch, {
  place(rect(width: cw, height: ch, fill: paper))
  body
})

#place(dx: pad, dy: pad, on-paper((card.front)(example)))
#place(dx: pad + cw + gap, dy: pad, on-paper((card.back)(example)))
