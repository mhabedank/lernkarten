# PR description — fix/a8-default-description

*(T022. The release note is the only place a user with an already-pinned deck
can learn what happened, so it is drafted here rather than left to the release.)*

---

## The A8 default moved the constant and left its description behind

Closes #95. Bug report: [BUG-010](./bugs/BUG-010.md).

v0.9.0 made A8 the default grid. `DEFAULT_GRID` moved and four descriptions of
it moved too. **Seventeen did not**, across ten files — and two of them were not
prose:

- **`/cards` wrote a literal `grid: a7` into every new deck.** Not a stale
  fallback a later change to the constant would correct: a *value in the user's
  file*, pinning the deck to a card the box does not fit and `--dividers`
  refuses — the two problems the default was moved to solve.
- **`lernkarten build --help` said `(default: what they say, else 2x4)`**, which
  is what a user reads at the moment they care. Not in the bug report; the gate
  found it.
- **The A8 picture advisory never fired for a grid-less deck**, because it
  resolved an absent key with a literal `"a7"`. A deck saying `grid: a8` was
  warned; the identical silent deck, printing identically, was not.

### For anyone upgrading

**Decks written by `/cards` since v0.9.0 carry `grid: a7`.** They print at the
older, larger card and will not fit `assets/card-box.pdf`. Nothing in the tool
will ever tell you: `lernkarten check`'s once-per-run report finds decks that are
*silent* about the grid, and these state one.

```bash
grep -l '^grid: a7' cards/*.yaml
```

Delete the line to take the default, or change it to `a8`. If you deliberately
print A7, keep it — A7 stays fully supported and nothing about it changed.

### What changed

| File | Change |
|---|---|
| `skills/cards/SKILL.md` | the schema block writes `grid: a8`; the prose inverts, and stops contradicting the budget rule two sections below it |
| `scripts/check_project.py` | `_deck_grid()` resolves an absent key through `DEFAULT_GRID`, never a literal; the comment that said "absent means A7" eight lines above a warning that said A8 |
| `scripts/build_pdf.py` | module docstring, and the `--grid` help string |
| `scripts/check_docs.py` | **four new gates** — see below |
| `templates/cards.typ` | the press-sheet header; and `card-scale`'s comment, which called the *reference* the default |
| `README.md` | cut count, card dimensions, borderless dimensions, and the line that said A7 was the default 51 lines after the line that said A8 was |
| `docs/index.html` | the hero band, the cut sentence, the cutting **diagram and its `aria-label`**, the margin paragraph |
| `docs/workflow.md`, `docs/testing.md` | the cutting instruction, the borderless comment, the manual matrix (A8 column first) |
| `.specify/memory/constitution.md` | Principle VI's import graph — `check_docs` now reads `build_pdf` |

### The gates, which are the point

A sweep by hand is what shipped this, and it is the third time
(`check_sheet_capacity`, `check_print_order`). So the gate was written **while
the repository was still wrong** and its red state was the real sites — a gate
authored against a corpus it was just made to pass proves nothing.

| Gate | Catches |
|---|---|
| `check_cards_skill_writes_the_default_grid` | the schema block handing the model a grid that is not the default — read from `DEFAULT_GRID`, so the next move carries it |
| `check_a7_is_not_the_default` | A7, `2x4`, 8-up or the A7 dimensions asserted as the default |
| `check_cut_count` | one-down-three-across given as a fixed fact |
| `check_borderless_size` | `--margin 0` promised as an A7 card |

`gated_files()` reaches `scripts/*.py` and `templates/*.typ` as well as
markdown — six sites were outside `markdown_files()`, and a gate that cannot see
the file is no better than the grep it replaces. `docs/index.html` is covered in
`tests/test_landing_page.py`, which already parses it.

**Exemptions are real distinctions, not holes**: the *margin* has a default too;
the scale *reference* stays A7 forever and FR-002 exists to keep it separate;
history may say what the default used to be; and the mixed-build refusal is
about decks disagreeing. All four are asserted.

### Version

**Patch.** The documentation promised A8 was the default and the tool did not
deliver it — CONTRIBUTING § Releases, the `0.7.3` case. No key gains or loses
meaning; nothing a user could already do stops working.
