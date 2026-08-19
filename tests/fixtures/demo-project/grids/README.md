# Decks that declare a grid

Each file here carries a top-level `grid:` key, and that is the whole point of
the folder. It sits **outside** `cards/` on purpose: `tests/test_e2e.py` globs
`cards/*.yaml` into the corpus every unflagged demo build runs over, so a
declaring deck in there would change the page count of tests that have nothing
to do with the grid — or break them.

| File | Declares | Used for |
|---|---|---|
| `tides-a8.yaml` | `a8` | 12 cards — 2 pages at A8, 4 at A7, so a page count tells the two grids apart. Every `TOPIC / SUBTOPIC` label stays inside the ~22-character A8 budget, which also makes it the short-label sample for the manual print gate. |
| `tides-a7.yaml` | `a7` | the partner for the conflict case: two decks declaring *different* grids with no `--grid` flag must fail and name both files. |

Nothing here is copied by `scripts/demo.py` — `demo.copy()` works from an
explicit allowlist, and this folder is not on it.
