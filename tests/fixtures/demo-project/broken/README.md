# Broken card files — one failure mode each

Every file here must make `lernkarten check` fail (or warn) in a specific,
recognisable way. They are the negative half of the end-to-end tests: a change
that swallows one of these errors breaks a test.

| File | What is wrong | Expected reaction |
|---|---|---|
| `invalid-markup.yaml` | an unescaped `#` in the card text | typeset fails, stderr names the offending card |
| `overflowing.yaml` | far too much text for a 100 x 72 mm card | build succeeds, `WARNING: card … does not fit` |
| `unknown-language.yaml` | `language: klingon` | `ERROR: … unknown language`, exit 1 |
| `missing-fields.yaml` | a card without `back` | `ERROR: … 'front' and 'back' are required`, exit 1 |
| `not-a-mapping.yaml` | a top-level list instead of a mapping | `ERROR: expected a mapping with keys 'topic' and 'cards'` |
| `malformed.yaml` | not readable as YAML | `ERROR: … line N`, exit 1 |
| `overflows-only-at-a7.yaml` | nothing — the 507-character back fits A8 and not A7 | `WARNING: card … does not fit` by default, silent at `--grid a8`. The only fixture that tells the two grids apart, so the only one that catches an overflow query left at the wrong geometry. The direction inverted with BUG-007: the A8 card is now a scaled A7 card and keeps ~3 % more width, so it holds slightly *more* (first overflow at 520 characters against A7's 500) |
| `duplicate-id.yaml` | two cards carrying the same `id` | `ERROR: … card 2: id A45DK is already used by card 1`, exit 1 — the message names **both** cards, because knowing only the id leaves you looking for the other one |
| `bad-alphabet-id.yaml` | ids using `I`, `O` and `-`, none of which are in Crockford Base32 | `ERROR: … 'I' is not in the alphabet`, exit 1 |
| `wrong-length-id.yaml` | ids of four and six characters | `ERROR: … expected 5 characters, found 4`, exit 1 |
| `non-string-id.yaml` | `id:` empty, `id: 12345`, `id: [A45DK]` | `ERROR: … expected a string, found NoneType`, exit 1 — present-but-wrong is never mistaken for absent |
| `escaped-linebreak.yaml` | a line-break `\` directly before a `*`, so the star is escaped rather than the line broken | typeset fails, stderr names the offending card |
| `missing-image.yaml` | `back_image` names a file that is not there | `ERROR: … card M5SS1: back_image '…/gone.png' does not exist`, exit 1 |
| `image-wrong-format.yaml` | a `.tiff`, which the engine does not read — and which is also absent | `ERROR: … is not an image the engine reads (png, jpg, jpeg, gif, svg, webp)`, exit 1. Reported as the wrong *format*, not as missing: the extension is checked first, because it is the first thing wrong with it |
| `image-outside-project.yaml` | a `../../../` path climbing out of the project | `ERROR: … is outside the project`, exit 1 — a deck that only builds on the machine that wrote it is a defect |
| `unreadable-image.yaml` | `not-really-a-picture.png`: a real file, an accepted extension, and plain text inside | typeset fails, stderr names the offending card. The one cause Python cannot answer without decoding the bytes, so the engine answers it and `offending_card()` attributes it |
