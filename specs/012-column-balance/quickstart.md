# Quickstart: validating 012-column-balance

**Feature**: 012-column-balance | **Date**: 2026-09-08

Two halves, because this feature's central requirement is one the test suite
cannot see. The assertions check the arrangement; a browser checks the
proportion the arrangement produces. Both are required — see
[research.md](research.md#r3--what-can-be-asserted-given-the-module-never-renders-the-page).

## Prerequisites

- Python 3.12+ and the dev requirements (`pip install -r requirements-dev.txt`)
- A browser, for the by-hand half. No repository dependency on one is added.

## 1. The assertions

```bash
python3 -m pytest tests/test_landing_page.py -q
```

Expected: green, including the four new assertions. Before the implementation
tasks they are red — that is the point, and constitution XI requires seeing it.

To confirm each one bites rather than merely passing, revert one move at a time
and re-run. Each should fail and name its section (SC-006):

| Revert this | Expect this to fail |
|---|---|
| put `.print__box` back inside `.print__rules` | the box-placement assertion |
| put `.print__cut` back in the rules column | the diagram-placement assertion |
| add `hidden` to `#card-back` | the both-cards assertion |
| add a second `<script>` block | the self-contained-file assertion |

## 2. The four gates

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

`check_docs.py` matters more than usual here: this feature adds a link from
constitution XVI to `docs/design.md`, and a link that does not resolve fails
that gate.

## 3. The proportion, by hand

Open `docs/index.html` straight off disk — no server, no build.

| # | At | Do this | Expect |
|---|---|---|---|
| 1 | above 1080 px | look at section `02` | two cards **one above the other**, filling the column beside the four explanations. No button in the band. They never sit side by side: the column offers ~618 px of usable width and two 380 px cards need 786 px |
| 2 | above 1080 px | check each of the four explanations against the cards | the header band, the field, the footer band and the note space are all *visible* — three of the four differ front to back, which is why one card was not enough |
| 3 | **from 1280 px up** | look at section `03` | two sheets and the cutting diagram on the left, three numbered rules on the right, the card box across the full width beneath both. No hole under **either** column — both close at 433 px |
| 3b | 1120 px | look at section `03` again | the diagram wraps below the sheets and roughly 160 px is left under the three rules. **This is the accepted fallback of SC-003, not a failure of row 3.** The caption has a minimum width and reading text is never shrunk to fit (constitution XVI) |
| 4 | above 1080 px | look at every boundary in `03` | every rule is single — none doubled where the box meets the columns, none missing |
| 5 | **JavaScript off**, reload | both sections | identical to rows 1 and 3. There is no script left, so there is nothing to differ |
| 6 | 360 px | scroll both sections | one column each; reading order unchanged; nothing holds the page open sideways |
| 7 | the box download | follow `card-box.pdf` from the moved block | dead when opened off disk, correct on the deployed site — unchanged by the move, and the HTML comment beside it says so |

Rows 1–4 are the ones that would have caught this bug. Row 5 is cheap now and
was not before.

**Row 3 said "under either column" from the start**, while SC-002 named only the
sheets column — so the by-hand row was better specified than the criterion it
stood behind, and walking it is what caught [BUG-012](bugs/BUG-012.md). Keep
these rows written as questions about the *section*, not about one box in it.

### Measuring instead of eyeballing

If a number is wanted rather than an impression, append a probe to a copy of the
page and read it back. Note the trap: `.sheet` is stretched by
`align-items: stretch` and is **not** ink — walking all descendants reports the
printing column as full when it is 65 % empty. Measure the visible elements by
name:

```js
// against .sheet__page and .sheet .label, never against .sheet
```

Targets from [spec.md](spec.md#measurable-outcomes): section 02 goes from 269 px
of content in a 644 px cell to 564 px, at 1120, 1280, 1440 and 1800 px.

Section 03 is the one to measure carefully, and **both** its columns:
`.print__sheets` held 327 px in a 1176 px column, and both columns now close at
433 px from 1280 px up. Measuring only the sheets column is how the first fix
passed while leaving 161 px under the rules — see
[BUG-012](bugs/BUG-012.md). Between 1080 px and about 1180 px the row wraps and
roughly 160 px is left under the rules; that is the accepted fallback in SC-003,
not a failure of this check.

The page caps its content at 1280 px, so those widths settle it above the
breakpoint.

## 4. What "done" looks like

- Four new assertions green, and red when their move is reverted
- Four gates green
- Rows 1–7 above walked once, in three engines for the layout rows
- `docs/design.md` carries the two-column rule; constitution XVI points at it
- `docs/index.html` holds zero `<script>` blocks
