// The Open Graph image, 1200 x 630 — what a link to the repository shows.
// Rendered at 72 ppi so the pixel size is exactly that.

#import "common.typ": *

#set page(width: 1200pt, height: 630pt, margin: 0pt, fill: ink)
#set text(font: reading, size: 16pt, fill: sand)
#set par(leading: 0.6em)

#place(dx: 68pt, dy: 62pt, mark(104pt, style: "reversed"))

#place(dx: 1200pt - 68pt - 132pt, dy: 62pt, {
  box(width: 44pt, height: 44pt, fill: red)
  box(width: 44pt, height: 44pt, fill: yellow)
  box(width: 44pt, height: 44pt, fill: blue)
})

#place(dx: 68pt, dy: 300pt, stack(
  dir: ttb,
  spacing: 26pt,
  wordmark(92pt, fill: sand),
  box(width: 700pt, text(font: display, weight: 500, size: 38pt, fill: sand)[
    Lecture PDFs in, paper flashcards out. Say what you are learning.
  ]),
))

#place(dy: 630pt - 62pt, line(end: (1200pt, 0pt), stroke: 2pt + sand))
#place(dy: 630pt - 62pt, box(
  width: 1200pt,
  height: 62pt,
  inset: (x: 68pt),
  align(horizon, grid(
    columns: (1fr, auto),
    label("github.com/mhabedank/lernkarten", size: 15pt, fill: sand, tracking: 0.22em),
    label("by mhabedank", size: 15pt, fill: yellow, tracking: 0.22em),
  )),
))
