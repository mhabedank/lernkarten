# Contract: file shapes

## The six formats of Principle I: unchanged

| Artifact | Change |
|---|---|
| `goal.md` | none |
| `sources.yaml` | none |
| `knowledge/<id>/<doc>.md` | none |
| `catalog/topics.md` | none |
| `cards/*.yaml` | **none** — a divider is not a card and gains no key |
| `figures/<id>/<file>` | none |

A deck written before this feature builds byte-identically after it, provided no
`lernkarten.yaml` exists. That is SC-005 and it is asserted, not assumed.

## `lernkarten.yaml` (new, user-owned, gitignored)

Three flat keys. Full shape, states and validation rules in
[../data-model.md](../data-model.md#2-lernkartenyaml--the-project-settings-new-user-owned).

The compatibility rule that matters: **absence means the previous behaviour**,
which is the same rule `goal.md` and every optional key in `catalog/topics.md`
already follow.

## `cards.json` (internal, build → engine)

Gains `kind`, absent meaning `"card"`. Shape in
[../data-model.md](../data-model.md#1-cardsjson--a-kind-discriminator-internal-build--engine).

Not a published format: it lives for the duration of one build and no user or
skill reads it. It is documented here only because the divider's whole payload
travels through it, which is what keeps `templates/cards.typ`'s `sys.inputs`
contract unchanged.
