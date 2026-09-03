# PR description — feat/card-box

*(T020. Two things a reviewer would otherwise have to infer are stated
explicitly: the `.gitignore` negation, and what makes the committed binary
legitimate. Governance requires the first; the second is the whole point of the
Principle VIII amendment.)*

---

## A box to keep the cards in

Closes #45.

`/print` produced a sheet of cards and the project stopped there. The box that
receives them was designed and physically folded some time ago, but it lived in
one working copy and could not be committed at all — `.gitignore` line 43 is
`*.pdf`. This publishes it.

### What changed

| File | Change |
|---|---|
| `.gitignore` | negate `*.pdf` for this one file — **below** line 43, because .gitignore is last-match-wins |
| `assets/card-box.pdf` | tracked, byte-for-byte unchanged |
| `.github/workflows/pages.yml` | copy the PDF into `_site`, and trigger on it |
| `docs/index.html` | the download, in the print section, with the constraint beside it |
| `docs/design.md` | a *The box* section; the press-sheet sentence corrected |
| `README.md`, `skills/print/SKILL.md` | name the box and say which deck it fits |
| `scripts/build_pdf.py` | the grid comment no longer says the box is one you buy |
| `.specify/memory/constitution.md` | **Principle VIII → 2.7.0**, see below |
| `tests/test_repo_hygiene.py`, `tests/test_landing_page.py` | 11 new assertions |

### Two things worth a reviewer's attention

**1. The `.gitignore` change is a deliberate carve-out, not a `git add -f`.**
Constitution VII forbids forcing files past `.gitignore`, and Governance requires
this note. The distinction is that a negation is visible in the diff and a forced
add is not — the rule that keeps build leftovers out is untouched, and exactly one
path is exempted, with the reason in a comment above it.

**2. The committed binary is legitimate because Principle VIII now says so — and
the amendment is honest about what it costs.** VIII forbids committed binaries
with one named exception. Two findings came out of writing it:

- **The exception was already false.** `assets/fonts/*.ttf` had been committed
  and named nowhere, and the brand PNGs were described in prose rather than by
  path. Eight binaries the rule did not admit to carrying. VIII is now a table of
  three globs, and `test_every_committed_binary_under_assets_is_named_in_principle_viii`
  fails on any committed binary under `assets/` that no row matches — so the list
  cannot drift again.
- **The box is not the brand-PNG case, and the amendment says so.** The PNGs have
  Typst sources and a render script: committing them buys convenience and they
  stay regenerable. The box has no source here at all, so the exception gives up
  *regenerability*. That means **Principle IX acquires a standing counterexample**,
  recorded rather than left for someone to find. The alternative was letting a
  future change cite "the brand PNGs precedent" for something that precedent never
  covered.

Its only provenance is that somebody folded it, so a **SHA-256 pin** makes
"unchanged" enforceable rather than aspirational.

### The bug this nearly shipped

The Pages workflow assembles a site out of exactly one file. A relative link to
`assets/card-box.pdf` would have been a **404 on the deployed page while working
perfectly from a local checkout** — the feature's entire deliverable, broken in
the only place it matters, invisible to every local check. The link, the `cp` and
the trigger path are asserted together against `pages.yml` as text, because CI
never executes the workflow.

That also means **a YAML error in this file merges green** and surfaces as a
failed deploy on `main`. Checklist row 34 is the only net; please do not skip it.

### What it fits, and what it does not

An `a8` deck at the **default margin** — cards 71.75 × 50 mm, inner box
73 × 24 × 52 mm, ≈ 90 cards. An `a7` card is 100 mm wide against a 73 mm opening,
and **`a7` is the default grid**, so most users' decks will not fit.

The sheet cannot say this itself. It has no source, and three of its own captions
are wrong: it prints `a4 landscape` on a portrait page (MediaBox 595.2 × 841.8 pt)
and `cards 70 × 49 mm` for a card that is 71.75 × 50. So the constraint lives
beside the download, in the README, and in `docs/design.md`, which carries the
measurements the sheet gets wrong.

### Scope deliberately not taken

Issue #45 asked for a parameterised Typst template deriving the box from the card
geometry. That was specified in full and then **cut** as unnecessary complexity —
the box is finished and does not need to change. The cost is recorded in
`specs/007-card-box/spec.md` under *Accepted Trade-offs*: if the card geometry
ever changes, the box silently becomes wrong, and no test will say so. Issue #45
predicted exactly that, and the trade-off is taken knowingly.

### Gates

```
ruff check . && ruff format --check .     ✅  189 files
pytest                                    ✅  508 passed, 3 skipped
LERNKARTEN_E2E=1 pytest                   ✅  508 passed, 3 skipped
lernkarten check cards/example.yaml       ✅  10 cards valid, 4 pages
python3 scripts/check_docs.py             ✅  7 skills, links fine
```

**Manual checklist rows 34–39** (`docs/testing.md`) are **not yet done** — they
need a printer, a photocopier and the deployed site. Row 37 in particular (a
black-only photocopy, handed to someone who has not seen the colour version) is
the direct test of the rule `docs/design.md` closes with.
