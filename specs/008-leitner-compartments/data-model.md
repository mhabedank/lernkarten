# Phase 1 Data Model: Leitner compartments

Two shapes change and one is new. **None of the six formats in Principle I is
touched** — no card file gains a key, and a project that never runs
`lernkarten setup` builds exactly as it does today.

---

## 1. `cards.json` — a `kind` discriminator *(internal, build → engine)*

`cards.json` is written by `build_pdf.py` next to `templates/cards.typ` and read
by the engine. It is internal: not a user file, not one of the six formats, and
nothing outside a single build run ever sees it.

Today every entry is a card. It gains one field.

| Field | Type | Applies to | Notes |
|---|---|---|---|
| `kind` | `"card"` \| `"divider"` \| `"blank"` | every entry | **Absent means `"card"`**, so a build that renders no dividers writes exactly the JSON it writes today — which is the half of SC-005 that is genuinely assertable ([research.md R8](./research.md): the PDF itself cannot be byte-compared while the engine stamps a `CreationDate`) |
| `number` | integer | divider | 1…n. Its identity, and the thing that survives a black-only photocopy |
| `of` | integer | divider | 3 or 4. Renders as `compartment 2 / 4` |
| `interval` | string | divider | from `leitner.INTERVALS`, never composed at the call site |
| `rule` | string | divider | from `leitner.RULES` |
| `colour` | string | divider | `#rrggbb`, from `leitner.COLOURS` |
| `x`, `y` | float (mm) | divider | where `divider_block()` placed it; a divider is not located by its index. On a **back** page the writer emits `sheet_w − x − w` (FR-004a) |
| `w`, `h` | float (mm) | divider | `card_w` and `card_h + 1.5` at the run's grid and margin |
| `band`, `bleed` | float (mm) | divider | 4.0 and 3.0, scaled with the card |

**`blank`** is a padding entry that occupies a grid cell and renders nothing —
no frame, no ink, no crop-mark contribution. It exists so the sheet count and
`pages()` keep working off list length when a divider page carries no cards at
all. *(Revised 2026-09-07: it no longer pushes dividers into a particular cell.
Under FR-004 a divider is not a grid cell — `divider_block()` locates it in
millimetres. See [research.md R6](./research.md).)*

**A `divider` entry therefore carries its own position**, in `x` and `y` above.
That is the whole difference between a grid cell, which is located by its index,
and a free-placed object, which is not — and it is why nothing is ever adjacent
to a divider, which is what makes FR-006's guarantee unconditional.

### Validation

- A `divider` entry MUST carry all eleven of its fields. `w`, `h`, `band` and `bleed` travel in the record rather than as template constants, so `templates/divider.typ` reads numbers and defines none — which is what closes the "how does the template get the geometry" question the first review raised and the first two remediations did not answer. A partial one is a build
  error naming the field, never a half-drawn card.
- `number` is in `1..of`; `of` is 3 or 4. Any other value is refused before the
  engine is invoked (FR-001).
- No `divider` entry is ever assigned a card id, and none is written into any
  `cards/*.yaml` (FR-008).

### What reads it

`templates/cards.typ` dispatches on `kind` and calls `divider.typ` or `card.typ`
accordingly. `card.typ` is untouched — a divider is not a card with extra
properties, it is a different thing that happens to be the same size.

---

## 2. `lernkarten.yaml` — the project settings *(new, user-owned)*

A new artifact in the project root, deliberately **outside** Principle I's six.
It holds choices, never content (Principle VII), and it is gitignored in the
same commit that first writes it.

```yaml
compartments: 4          # 3 | 4 | none
dividers_printed: true
box_printed: false
```

| Key | Type | Values | Meaning |
|---|---|---|---|
| `compartments` | integer or `none` | `3`, `4`, `none` | How many compartments the user wants. `none` is a real answer, not an absence: it means asked and declined, and it stops the advisory |
| `dividers_printed` | boolean | | Whether the dividers already exist on paper. `true` means a build adds none unless `--dividers` says so |
| `box_printed` | boolean | | Same, for `assets/card-box.pdf` |

All three are **flat, top level, no nesting** — so "unknown key" is a set
membership test and #67's precedence chain resolves per key rather than per
container.

### Three states, not two

The distinction that makes the advisory line work exactly once:

| State | Meaning | Build behaviour |
|---|---|---|
| file absent **or empty** | never asked | build unchanged + advisory naming `lernkarten setup` |
| `compartments: none` | asked, declined | build unchanged, **no advisory** |
| `compartments: 3` \| `4` | asked, answered | dividers rendered unless `dividers_printed` |

Collapsing "absent" and "none" would either nag a user who has said no, or
silently swallow the one chance to mention the feature.

### Validation

- An **unknown key** is a *warning* naming the file, the key and the keys this
  version knows; the run continues (FR-016a). Never silently ignored, never
  fatal — because #67 adds keys to this same file, and an older version must not
  refuse a project a newer one wrote.
- An **invalid value on a known key** is a hard error naming the key and the
  accepted values, in the style `parse_grid` already uses (FR-016b). There is no
  safe reading of `compartments: 5`, so it cannot be carried forward.
- A malformed file is an error with the line number, which is what
  `scripts/yamlio.py` exists to provide.
- **Absence is not an error**, and an **empty file is absence**. Both are the
  pre-feature behaviour; asserting byte-identical output for them across both
  grids, both `--sides` values and `--margin 0` is SC-005.

### Precedence

`explicit flag → lernkarten.yaml → built-in default`

This is the project-scope slice of the chain #67 designs
(`flag → deck → project → user → default`). The two levels this feature does not
build — deck and user — are left to #67, and nothing here forecloses them: a
later reader inserted between `flag` and `project` changes no call site because
resolution happens in `settings.py`, not at the flags.

---

## 3. Entities that deliberately do **not** exist

Worth stating, because their absence is the design:

- **No review record.** No `next_review`, no per-card history, no state file.
  The card's position in the box is its state (FR: *Why this is not a software
  scheduler*).
- **No compartment entity.** A compartment is a position in a physical box. It
  has no identity in any file; the divider that marks it is generated from one
  integer.
- **No divider identity.** A divider has no card id, no `cards/*.yaml` entry and
  no addressable existence between runs. Rebuilding produces the same four
  dividers because the same integer produces them, not because anything was
  stored.
