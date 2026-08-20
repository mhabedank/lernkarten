---
name: print
description: >-
  Compile flashcard YAML into a print-ready PDF via the card template (A4, 8 cards per page, fronts/backs for duplex printing). Triggers: /print, "build the PDF", "print my cards".
---

# /print — build the PDF

Compiles the YAML card files into a PDF that is ready to print and cut.

## Steps

1. `cards/` empty → point at `/cards`, done.
2. Determine the selection: arguments name topics (files) or subtopics;
   without arguments, use all of `cards/*.yaml`.
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
   | `--grid 4x4` | `--grid a8` | 16 | 52.5 × 74.25 mm — DIN A8 |

   A card file may declare its own size with a top-level `grid:` key, and
   `/cards` writes one. So do **not** pass `--grid` routinely — the deck
   already knows. Pass it to override the deck for one run ("print my A8 deck
   at A7 just this once"), or when the user asks for the denser sheet. Without
   either, the build prints at A7.
   Two files in one build that declare *different* grids are refused, naming
   both; an explicit `--grid` settles it.
   `--no-logo` prints the cards without the mark and the wordmark in the
   footer; the card id stays.
   The language comes from each card file's `language:` key — do NOT pass
   `--language` routinely. Use it only to override, e.g. when a file is
   missing the key (`--language german`, `--language de`).
4. On typesetting errors: the script names the offending card (topic + index).
   Fix the problem in the YAML file (usually an unescaped special character)
   and rebuild.
5. Check the result: the page count must be even (front/back pairs), and is
   2 × ⌈cards ÷ (columns × rows)⌉. Send the PDF to the user with SendUserFile
   and state the printing instructions: **duplex, flip on long edge, 100 %
   scale (not "fit to page")**, then trim the sheet and cut the vertical lines
   before the horizontal ones — one interior vertical cut at `a7` and three at
   `a8`, three interior horizontal cuts at both. Counting the outer trim that
   is five vertical by five horizontal at `a8`, three by five at `a7`. The card
   frames and the crop marks in the margin show where.

## Notes

- Cards that are too long for the card area are reported by the build as a
  warning ("does not fit"); shorten or split such cards instead of shrinking
  the font. The warning follows the grid: an A8 card is half the width, so text
  that fits at A7 can overflow at A8. Rebuilding the same deck at `--grid a8`
  is what surfaces it.
- The head band clips rather than wraps, and holds about 22 characters of
  `TOPIC / SUBTOPIC` at A8 against ~53 at A7. If the user asks for A8 on a deck
  with long topic names, say so before printing — the labels will be cut off
  mid-word, and no build warning fires unless the deck declares `grid: a8`.
- The first build downloads the typesetting engine (about 15 MB) and caches it.
  Nothing else has to be installed. `lernkarten engine --check` says where it
  is; `LERNKARTEN_ENGINE` points the build at one of your own.
- The card layout lives in `templates/card.typ`, the press sheet in
  `templates/cards.typ`. Change it there, never in the generated file, and read
  `docs/design.md` first.
