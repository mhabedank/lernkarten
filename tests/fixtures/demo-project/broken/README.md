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
| `overflows-only-at-a8.yaml` | nothing — the back fits A7 and not A8 | silent by default, `WARNING: card … does not fit` at `--grid a8`. The only fixture that tells the two grids apart, so the only one that catches an overflow query left at the wrong geometry |
| `escaped-linebreak.yaml` | a line-break `\` directly before a `*`, so the star is escaped rather than the line broken | typeset fails, stderr names the offending card |
