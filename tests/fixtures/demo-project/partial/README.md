# Decks part-way through the id migration

Each file here has some cards carrying an `id:` and some not. That is the state
a real project is in the moment a card is added by hand, or a backfill is
interrupted, and it is the case `lernkarten build` and `lernkarten check` both
have to keep working through.

It sits **outside** `cards/` for the same reason as
[`../grids/`](../grids/README.md): `tests/test_e2e.py` globs `cards/*.yaml` into
the corpus every unflagged demo build runs over, so a deck in there would
change the page count of tests that have nothing to do with card ids.

| File | Holds | Used for |
|---|---|---|
| `partial-ids.yaml` | 4 cards, 2 with an `id:` and 2 without | the mixed case — the build must not fail, the two declared ids must survive untouched, and a backfill must fill only the gaps |
