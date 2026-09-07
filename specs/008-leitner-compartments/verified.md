# Physical verification

Constitution XI sends four things to a manual checklist, because no assertion
can reach them. This file records what has actually been done, on paper, with
the date — so a later reader finds evidence rather than an intention.

| # | Check | Status |
|---|---|---|
| 1 | A cut divider slides into the folded box (51.5 mm against a 52 mm opening) | **verified 2026-09-07** — printed, cut along the drawn cut line, fits |
| 2 | The 1.5 mm of extra height is visible from above with the box full | open |
| 3 | The colour band survives a hand-fed simplex run, colour at every edge on both faces | open |
| 4 | An A8 **duplex** run: divider *n*'s back sits behind divider *n*'s front | open |
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

Checks 2 and 4 need a full deck printed on both sides; check 4 is the one that
also probes whether `docs/design.md`'s "flip on long edge" is right for a
landscape A8 sheet, which the third review flagged as possibly wrong since
`feat/card-grid`.
