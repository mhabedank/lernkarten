---
name: print
description: >-
  Compile flashcard YAML into a print-ready PDF via the LaTeX template (A4, 8 cards per page, fronts/backs for duplex printing). Triggers: /print, "build the PDF", "print my cards".
---

# /print — build the PDF

Compiles the YAML card files into a PDF that is ready to print and cut.

## Steps

1. `cards/` empty → point at `/cards`, done.
2. Determine the selection: arguments name topics (files) or subtopics;
   without arguments, use all of `cards/*.yaml`.
3. Run the build:

   ```bash
   python3 scripts/build_pdf.py cards/*.yaml -o output/cards.pdf
   ```

   Filters: `--topic "Name"` (repeatable), `--subtopic "Name"`.
   Layout: `--margin <mm>` — page margin for printers with a non-printable
   edge (default 5 mm; `--margin 0` = borderless, full A7 cards).
   `--no-logo` prints the cards without the logo mark.
   The language comes from each card file's `language:` key — do NOT pass
   `--language` routinely. Use it only to override, e.g. when a file is
   missing the key (`--language german`, `--language de`).
4. On LaTeX errors: the script names the offending card (topic + index). Fix
   the problem in the YAML file (usually an unescaped special character) and
   rebuild.
5. Check the result: the page count must be even (front/back pairs). Send the
   PDF to the user with SendUserFile and state the printing instructions:
   **duplex, flip on long edge, 100 % scale (not "fit to page")**, then cut
   along the grey lines.

## Notes

- Cards that are too long for the card area are reported by the build as a
  warning ("Overfull"); shorten or split such cards instead of shrinking the
  font.
- The template lives in `templates/cards.tex.in` (Python template syntax,
  `$placeholder`). Make layout changes there, not in the generated `.tex`
  under `output/`.
