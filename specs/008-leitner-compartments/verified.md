# Physical verification

Constitution XI sends four things to a manual checklist, because no assertion
can reach them. This file records what has actually been done, on paper, with
the date — so a later reader finds evidence rather than an intention.

| # | Check | Status |
|---|---|---|
| 1 | A cut divider slides into the folded box (51.5 mm against a 52 mm opening) | **verified 2026-09-07** — printed, cut along the drawn cut line, fits |
| 2 | The 1.5 mm of extra height is visible from above with the box full | **verified 2026-09-07** |
| 3 | The colour band survives a hand-fed simplex run, colour at every edge on both faces | **verified 2026-09-07** |
| 4 | An A8 **duplex** run: divider *n*'s back sits behind divider *n*'s front | **verified 2026-09-07** |
| 5 | `lernkarten setup` asked interactively (pytest has no terminal) | open — the command does not exist yet |

## What check 1 settled

Two things at once, and the second was the one in doubt.

**The size.** 51.5 mm into a 52 mm opening is half a millimetre of clearance,
and paper is not a CAD model — a fold that came out 0.3 mm tight would have
made the whole growth idea unusable. It did not.

**The cut line.** The band bleeds 3 mm past the trim, so before
`eac3f21` there was nothing on the divider saying where it ended, and cutting
at the visible colour edge would have produced a 77.75 mm divider that enters
no box at all. The drawn cut line was added *because* a user pointed this out
while looking at the first render, and check 1 is what confirms it works with
scissors rather than only with a guillotine.

## What checks 2, 3 and 4 settled

**Check 2** — 1.5 mm is enough to see. It was the number most open to the
objection "that is too small to notice", and the box was chosen over 2 mm on
arithmetic alone (52 mm inside against a 50 mm card). It reads.

**Check 3** — the band survives a hand-fed simplex run. This is what the whole
of [research.md R1](./research.md) was derived for: 4 mm inward and 3 mm
outward, from a 2 mm registration error plus a 1 mm cut error. A hand-turned,
re-fed stack is the worst case the feature has, and colour reached every edge
on both faces. The arithmetic held against paper.

**Check 4** — duplex lines up at A8. Divider *n*'s back sits behind divider
*n*'s front, so FR-004a's `sheet_w − x − w` is right in practice and not only
on paper, and the reflection a free-placed object needed matches the one
`cards.typ` performs for a grid cell.

Stated precisely, because it is easy to over-read: this shows that the
**column mirroring agrees with the flip this printer made at this setting**. It
does not by itself prove `docs/design.md`'s wording "flip on long edge" is the
right *instruction* for a landscape A8 sheet — on that sheet the long edge is
horizontal, and the third cross-model review flagged the phrase as possibly
wrong since `feat/card-grid`. What check 4 does establish is that the code is
self-consistent and that a real duplex run produces aligned cards, so any
remaining problem is one of wording rather than of geometry. Worth its own
ticket, not a blocker here.
