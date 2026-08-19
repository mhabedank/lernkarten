# Quickstart: verifying the three landing page fixes

Two halves, because the surface is a browser page. The commands settle the
structure; the eye settles the layout. Neither half is optional — constitution XI
allows the split for design work precisely on condition that the visual claims
are named rather than assumed.

## Prerequisites

None beyond a checkout. This feature touches no dependency, needs no typesetting
engine, no `pdftotext`, no network and no Claude session. `docs/index.html` is
self-contained, so a browser opens it straight off disk.

```bash
python3 -m pytest tests/test_landing_page.py -q   # the structural half
open docs/index.html                              # macOS; xdg-open on Linux
```

## The structural half

```bash
python3 -m pytest tests/test_landing_page.py -q
```

Eight assertions, listed with their requirements in
[plan.md](plan.md#test-plan-first). Seven of them fail on the parent commit —
that is the evidence constitution XI asks for, and SC-008 is the criterion:

```bash
git stash                                          # or check out the parent
python3 -m pytest tests/test_landing_page.py -q     # expect 7 failures, on assertions
git stash pop
python3 -m pytest tests/test_landing_page.py -q     # expect all green
```

A failure that reads `ImportError` or `FileNotFoundError` does not count as red.
It has to fail on the assertion.

Then the four gates, which CI runs identically:

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

`check_docs.py` matters more than usual here: this feature adds links to
`docs/testing.md`, and a link that does not resolve fails that gate.

## The visual half

Open `docs/index.html` directly. No server, no build step.

### 1 — Navigation, at 360 px

Set the viewport to 360 px wide (device toolbar, or just narrow the window).

| Check | Expect |
|---|---|
| The bar at rest | one line: wordmark, the control, github |
| The control | reads as a word, not only a glyph |
| Open it | all four links — `how it works`, `the card`, `printing`, `install` |
| Follow `install` | you arrive at the install section |
| Keyboard | the control takes focus and opens with Enter or Space |
| Widen past 760 px | the bar is the row it is today: wordmark, four inline links, github |

Then **disable JavaScript** and repeat the first four rows. All four links must
still be reachable. This is FR-003 and it is the row most likely to be skipped.

### 2 — Section bands, above 1080 px

Widen the window past 1080 px and look at sections `01`, `03` and `04`.

| Check | Expect |
|---|---|
| The three heading rows | the same height as each other, and no taller than the heading needs |
| Each note | a full-width block directly under its band, above that section's content |
| The rules | single everywhere — no 4 px doubled rule where band meets note, none missing |
| Section `04 install` | the note is still `--sand` on `--ink`, and the rule under it is `--sand`, not the default dark |
| Section `02 one card, one idea` | unchanged — its band still holds the toggle button |

Then narrow below 1080 px and check the reading order in all four: number,
heading, note, content. It must be what it is today.

### 3 — The card toggle

Go to `02 one card, one idea`.

| Check | Expect |
|---|---|
| On load | exactly one card visible, button reads "show the back" |
| Click | the other card replaces it, button reads "show the front" |
| Click again | back to the first, label back to "show the back" |

Then **disable JavaScript** and reload: both cards side by side, no button. That
is the fallback the script's own comment describes, and it must survive the fix.

## What is out of scope, and will still look wrong

Naming these so a reviewer does not report them as regressions:

- **The toggle still does not explain itself.** The button sits in the band, away
  from the cards, and neither card is labelled *front* or *back*. That is the
  second half of issue #28, deliberately left open — this feature makes the
  control work, not obvious.
- **The notes are still 14 px**, below the 15 px screen floor `docs/design.md`
  states. That is issue #30, and FR-011 freezes the size here on purpose so the
  two changes do not confound each other's review.
- **The README still buries the landing page.** Issue #26, untouched.
