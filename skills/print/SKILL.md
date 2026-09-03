---
name: print
description: >-
  Compile flashcard YAML into a print-ready PDF via the card template (A4, 8 or 16 cards per sheet depending on the grid, fronts and backs ordered for a duplex or a simplex printer). Triggers: /print, "build the PDF", "print my cards", "print at A8", "print smaller cards", "my printer only prints one side", "print all fronts then all backs".
---

# /print — build the PDF

Compiles the YAML card files into a PDF that is ready to print and cut.

## Steps

1. `cards/` empty → point at `/cards`, done.
2. Determine the selection: arguments name topics (files) or subtopics;
   without arguments, use all of `cards/*.yaml`.
2b. **Check the arguments for a card size before treating them as a filter.**
   `a7`, `a8`, `2x4`, `4x4`, "A8", "small", "smaller", "dense", "half the
   paper", "16 up", "fit more on a page" all name a *grid*, not a topic — pass
   the matching `--grid` and do not use the word as a topic filter. `/print a8`
   means the whole deck at A8, not the cards whose topic contains "a8".

   ```
   /print a8                 → lernkarten build cards/*.yaml --grid a8 -o output/cards.pdf
   /print Tides at A8        → lernkarten build cards/*.yaml --topic "Tides" --grid a8 -o output/cards.pdf
   /print smaller cards      → ask which: a7 (8 per sheet) or a8 (16)
   /print                    → no --grid; each deck's own grid: key decides
   ```

   When a size and a topic are both named, apply both. When the request is
   vague ("smaller"), name the two options and ask rather than guessing — a
   deck written for A7 will overflow at A8.
3. Run the build:

   ```bash
   lernkarten build cards/*.yaml -o output/cards.pdf
   ```

   Filters: `--topic "Name"` (repeatable), `--subtopic "Name"`.
   Layout: `--margin <mm>` — page margin for printers with a non-printable
   edge (default 5 mm; `--margin 0` = borderless, full-bleed cards).
   `--grid <COLSxROWS>` — how many cards go on an A4 sheet:

   | Flag | Alias | Per sheet | Card at `--margin 0` |
   |---|---|---|---|
   | `--grid 2x4` | `--grid a7` | 8 | 105 × 74.25 mm — DIN A7 |
   | `--grid 4x4` | `--grid a8` | 16 | 74.25 × 52.5 mm — DIN A8, on a landscape sheet |

   A card file may declare its own size with a top-level `grid:` key, and
   `/cards` writes one. So do **not** pass `--grid` routinely — the deck
   already knows. Pass it to override the deck for one run ("print my A8 deck
   at A7 just this once"), or when the user asks for the denser sheet. Without
   either, the build prints at A7.
   Two files in one build that declare *different* grids are refused, naming
   both; an explicit `--grid` settles it.
   `--no-logo` prints the cards without the mark and the wordmark in the
   footer; the card id stays.
   `--sides <duplex|simplex>` — the order the pages come in:

   | Flag | Page order | For a printer that |
   |---|---|---|
   | `--sides duplex` (default) | front, back, front, back | prints both sides in one pass |
   | `--sides simplex` | every front, then every back | prints one side, so the user turns the stack |

   Pass `--sides simplex` when the user says their printer prints one side
   only, or asks for all the fronts first. Otherwise pass nothing — the
   default is what a duplex printer wants, and the cards are identical either
   way. It is a property of the print run, not of the deck: no card file
   declares it.
   The language comes from each card file's `language:` key — do NOT pass
   `--language` routinely. Use it only to override, e.g. when a file is
   missing the key (`--language german`, `--language de`).
4. On typesetting errors: the script names the offending card (topic + index).
   Fix the problem in the YAML file (usually an unescaped special character)
   and rebuild.
5. Check the result: the page count must be even (front/back pairs), and is
   2 × ⌈cards ÷ (columns × rows)⌉ at either `--sides` value. Send the PDF to
   the user with SendUserFile and state the printing instructions **for the
   order you built** — the build's closing line spells them out, so repeat what
   it says rather than reciting a default:

   - duplex: **flip on long edge, 100 % scale (not "fit to page")**
   - simplex: **print the first page range, turn the stack over on the long
     edge, re-feed it, print the second range — 100 % scale both times.** The
     closing line names both ranges. If their printer stacks face-up, the
     second range goes through in reverse page order, which the print dialog
     offers.

   Then, in both cases: trim the sheet and cut the vertical lines
   before the horizontal ones — one interior vertical cut at `a7` and three at
   `a8`, three interior horizontal cuts at both. Counting the outer trim that
   is five vertical by five horizontal at `a8`, three by five at `a7`. The card
   frames and the crop marks in the margin show where.

## Notes

- Cards that are too long for the card area are reported by the build as a
  warning ("does not fit"); shorten or split such cards instead of shrinking
  the font. The threshold does not depend on the grid: A8 renders the same card
  at a uniform scale, so a deck that fits at A7 fits at A8. Nobody has to
  rewrite cards to print smaller.
- The first build downloads the typesetting engine (about 15 MB) and caches it.
  Nothing else has to be installed. `lernkarten engine --check` says where it
  is; `LERNKARTEN_ENGINE` points the build at one of your own.
- The card layout lives in `templates/card.typ`, the press sheet in
  `templates/cards.typ`. Change it there, never in the generated file, and read
  `docs/design.md` first.
- Once the cards are cut they are a loose stack. Tell the user that
  `assets/card-box.pdf` is a cut-and-fold box on one A4 sheet — 160–250 gsm,
  print at 100 %, holds about 90 cards. Say **which deck it fits**: `--grid a8`
  at the default margin. It does not take an `a7` card, and `a7` is the default,
  so a user who did not pass `--grid` should not print the box.
