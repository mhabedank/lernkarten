// The readme banner, 1280 x 320. The mark, the sentence, the five commands —
// and one card, because the card is the product.

#import "common.typ": *

#set page(width: 1280pt, height: 320pt, margin: 0pt, fill: sand)
#set text(font: reading, size: 14pt, fill: ink)
#set par(leading: 0.6em)

#let stripe = box(width: 96pt, height: 100%, {
  place(rect(width: 96pt, height: 320pt * 3 / 9, fill: red))
  place(dy: 320pt * 3 / 9, rect(width: 96pt, height: 320pt * 2 / 9, fill: yellow))
  place(dy: 320pt * 5 / 9, rect(width: 96pt, height: 320pt * 4 / 9, fill: blue))
  place(dx: 96pt, line(end: (0pt, 320pt), stroke: 2pt + ink))
})

#let sample-w = 248pt
#let sample = box(width: sample-w, height: 100pt, {
  place(rect(width: sample-w, height: 100pt, fill: paper, stroke: 2pt + ink))
  place(dy: 24pt, line(end: (sample-w, 0pt), stroke: 2pt + ink))
  place(dx: sample-w - 24pt, rect(width: 24pt, height: 24pt, fill: red))
  place(dx: sample-w - 24pt, line(end: (0pt, 24pt), stroke: 2pt + ink))
  place(dx: sample-w - 16.5pt, dy: 7.5pt, circle(radius: 4.5pt, fill: paper))
  place(dx: 11pt, dy: 8pt, label("probability / bayes theorem", size: 7pt, tracking: 0.12em))
  place(dx: 11pt, dy: 38pt, box(
    width: sample-w - 22pt,
    text(font: display, weight: 500, size: 16pt)[How is Bayes' theorem stated?],
  ))
  place(dy: 80pt, line(end: (sample-w, 0pt), stroke: 2pt + ink))
  place(dx: 11pt, dy: 87pt, label("lernkarten by mhabedank", size: 6.5pt, tracking: 0.2em))
})

#place(rect(width: 1280pt, height: 320pt, stroke: 2pt + ink))
#place(stripe)
#place(dx: 980pt, line(end: (0pt, 320pt), stroke: 2pt + ink))
#place(dx: 980pt, rect(width: 300pt, height: 320pt, fill: paper))

#place(dx: 96pt, box(width: 884pt, height: 320pt, inset: (x: 44pt, y: 40pt), grid(
  rows: (auto, 1fr, auto),
  {
    grid(
      columns: (auto, auto),
      column-gutter: 22pt,
      align: horizon,
      mark(58pt),
      wordmark(58pt),
    )
  },
  align(horizon, box(
    width: 700pt,
    text(font: display, weight: 500, size: 28pt)[
      Turn what you have to learn into flashcards you can hold.
    ],
  )),
  {
    set text(font: mono, size: 13pt, fill: muted)
    grid(columns: 5, column-gutter: 26pt, ..commands)
  },
)))

#place(dx: 980pt, box(width: 300pt, height: 320pt, inset: 26pt, align(bottom, stack(
  dir: ttb,
  spacing: 16pt,
  sample,
  label("print · cut · hold", size: 9pt, fill: muted, tracking: 0.22em),
  label("mit licence", size: 9pt, fill: muted, tracking: 0.22em),
))))
