# Phase 0 Research: A short, stable card id

**Feature**: `specs/005-card-id` · **Branch**: `feat/card-id` · **Date**: 2026-08-21

The spec left exactly two questions for the plan. Both are settled below by
measurement rather than argument. Three premises handed to this phase turned out
to be wrong; they are corrected first, because two of the three change the
answer.

---

## Corrections to the brief

### C-1. PyYAML is already a runtime dependency — `ruamel.yaml` would be the second, not the first

`scripts/deps.py` declares:

```python
REQUIREMENTS = [
    ("pyyaml==6.0.3", "yaml"),
]
```

`bin/lernkarten` calls `deps.activate()` before any work, and `scripts/yamlio.py`
imports `yaml` through that bootstrap. So the delivery mechanism for a runtime
dependency is not theoretical — it is in production and carrying a package today.

**Why it matters**: the brief framed a library choice as "this project's first
runtime dependency", implying a high bar. The real bar is lower. It does not
change the outcome below, but it changes the reasoning, and a plan that argued
from the wrong premise would have been overturned at review.

### C-2. CLAUDE.md is out of date, and this is now confirmed twice over

CLAUDE.md says: *"There are none at runtime yet, and there is no mechanism to
deliver one to a plugin user, so a runtime dependency cannot ship today."*

Both halves are false. There is one (`pyyaml==6.0.3`) and there is a mechanism
(`scripts/deps.py`). Constitution Principle II and the plan template's own
Technical Context both record the current state correctly. **Fixing CLAUDE.md is
in scope for this feature** — it is the file the `/cards` skill and every
contributor reads.

### C-3. The 11 pt floor does not bind the card id — `docs/design.md` already says so

The brief stated the id "is currently BELOW the project's own floor" and asked
for a *stated exception* if 11 pt does not fit. No exception is needed, because
`docs/design.md` already carves the id out **by name**:

> Reading text is never smaller than 11 pt printed or 15 px on screen. […]
> **Reading text means Archivo** […] So the floor binds every Archivo paragraph
> […] and **it does not bind a letterspaced label at 11 px or a card id at
> 8.5 px**.

The floor is scoped to Archivo prose. The id is IBM Plex Mono, which the same
document classes as "literals" alongside YAML and commands. The rule is already
machine-enforced for the landing page by `tests/test_landing_page.py`: *"a size
under 15 px is allowed only where the rule that sets it also names one of the
other two faces."* The id qualifies.

**Consequence**: the question is not "may the id be small?" but "how large
should it be, now that it is short enough to grow?" That is a design-balance
question, answered in R-2.

---

## R-1. How backfill writes YAML

**Decision: PyYAML's `compose()` for positions, plus a targeted text splice. No
new dependency.**

### The requirement

FR-006 demands comments, quoting style, key order, encoding and line endings
survive byte-for-byte outside the inserted key. FR-007 demands all-or-nothing
behaviour. `scripts/yamlio.py` is read-only today (`load()` only, no `dump`), and
nothing in this repository writes YAML at all.

### Why not a full round-trip library

`ruamel.yaml` in round-trip mode preserves comments and most quoting, but it
**reserialises the document**. It is not contractually byte-identical: sequence
indentation, line width and some quote styles are normalised on write. For a
requirement whose whole point is "byte-for-byte outside the inserted key", a
reserialiser is the wrong tool — it would force the test to assert something
weaker than the requirement, which is how a requirement quietly stops being true.

### Why this is not hand-rolling YAML (Principle III)

This is the question Principle III exists to ask, and the precedent cuts close:
`scripts/yamlio.py`'s own docstring records that this project *already* deleted a
222-line hand-written parser (`minyaml.py`) in favour of PyYAML, calling it "the
wrong trade". So "we can write it ourselves" is not available as an argument.

But the proposal here does **not** parse YAML. PyYAML does all of it:

- `yaml.compose(src)` returns the node tree **with `start_mark` / `end_mark`
  line and column for every node** — the library locates the cards.
- The only original code is a text splice at a position the library supplied.

Nothing re-implements a parser, a scanner or an emitter. The library does the
reading; we do one `str` insertion. That is using the library, not replacing it.

### Verified, not assumed

`yaml.compose()` marks were checked against the real fixture
`tests/fixtures/demo-project/cards/tides.yaml`:

```
card 1: first key 'subtopic' at line 4  col 4
card 2: first key 'subtopic' at line 8  col 4
...
card 8: first key 'subtopic' at line 32 col 4
```

A working proof of concept was then run against `cards/example.yaml` (11
comments, single-quoted Typst markup) and two demo decks:

| Property | Result |
|---|---|
| Parses after insertion, all cards keep every other key | pass |
| Comments preserved | 11 → 11 |
| Idempotent — a second run is a no-op | pass |
| CRLF preserved, no `\n` leakage | pass |
| Pre-existing ids untouched when only some cards lack one | pass |
| **Round-trip**: `remove(insert(src)) == src`, byte-exact | pass on LF **and** CRLF |
| Same, on a German deck with umlauts (`gezeiten-de.yaml`) | pass |

### The one honest cost: `id` first moves the list dash

The spec assumes `id` sits **first** on each card (before `subtopic`). Making it
first means the `- ` sequence dash moves onto the new line:

```yaml
# before
  - subtopic: 'Basics'
# after
  - id: A45DK
    subtopic: 'Basics'
```

Measured over `cards/example.yaml` (9 cards) and `tides.yaml` (8 cards):

| Placement | Lines added | Original lines altered |
|---|---|---|
| `id` **first** | +9 / +8 | **9 / 8** — one per card, the dash moving |
| `id` **last** | +9 / +8 | **0** |

`id` last is the only placement that touches nothing. `id` first alters exactly
one line per card, and the alteration is the two characters `- ` becoming two
spaces — semantically identical YAML, no reformatting, no content change.

**Recommendation: keep `id` first** (the spec's stated assumption). Readability
in a diff and for a human scanning the file is worth one provably minimal,
semantically neutral edit per card. But FR-006's test must then assert the
*right* property, because the naive one gives a false failure:

> **Assert `remove_ids(insert_ids(src)) == src`, byte-for-byte.**

That round-trip is the honest formalisation of "byte-for-byte outside the
inserted key", and it passed on LF, CRLF and non-ASCII content. A naive
"strip the inserted lines and compare" assertion **fails** here for a reason
that is not a defect — and worse, stripping the id line alone leaves the dash
missing and the file *invalid*, which confirms the dash movement is structural
rather than cosmetic.

### Alternatives considered

| Option | Verdict |
|---|---|
| `ruamel.yaml` round-trip | **Rejected** — reserialises; cannot promise byte-identity, so the test would have to assert less than FR-006 requires. Also a new dependency for a job the existing one already does. |
| PyYAML `compose()` + text splice | **Chosen** — library does the parsing and supplies exact positions; byte-exact round-trip verified on real fixtures. |
| Hand-written line scanner | **Rejected** — this is what Principle III and the `minyaml.py` precedent forbid. Unnecessary: `compose()` already gives marks. |
| Store ids in a sidecar file | **Rejected** — the spec settled on a key in `cards/*.yaml`; a sidecar reintroduces the drift the feature exists to remove. |

**No dependency change. The "Dependency Decisions" section of the plan is a
`No dependency change` entry.**

---

## R-2. What type size the id can reach

**Decision: 8 pt (from 4.6 pt), scaled by the existing `scale` factor.**

Given C-3, the 11 pt floor is not a constraint. The real constraints are the
`cw / 3` clip cap and the footer band's internal balance.

### Measured with the pinned engine (typst 0.15.1, IBM Plex Mono, `A45DK · 1/2`)

`cap = cw / 3 = 94.49 pt` at `cw = 100 mm`; footer band `foot-h = 6.2 mm = 17.57 pt`.

| Size | Width | Height | % of cap | Fits? |
|---|---|---|---|---|
| 4.6 pt *(today)* | 30.36 pt | 3.21 pt | 32.1 % | yes |
| 6 pt | 39.60 pt | 4.19 pt | 41.9 % | yes |
| 7 pt | 46.20 pt | 4.89 pt | 48.9 % | yes |
| **8 pt** | **52.80 pt** | **5.58 pt** | **55.9 %** | **yes** |
| 9 pt | 59.40 pt | 6.28 pt | 62.9 % | yes |
| 10 pt | 66.00 pt | 6.98 pt | 69.9 % | yes |
| 11 pt | 72.60 pt | 7.68 pt | 76.8 % | yes |
| 12 pt | 79.20 pt | 8.38 pt | 83.8 % | yes |

Two things this table settles:

1. **Every candidate size fits.** Width is not the binding constraint once the
   id is 5 characters — even 12 pt uses only 84 % of the cap. The issue's
   complaint that the id is clipped is a fact about the *long* id, not about the
   box.
2. **My 4.6 pt figure (30.36 pt) corroborates the issue's** 27.69 pt for its
   4-character `A45D · 1/2`. One extra character adds ~2.7 pt, as expected for a
   monospaced face. The two measurements are consistent.

### Why 8 pt and not 11 pt

The footer band carries three things: the mark, the wordmark, and the id. The
wordmark is **Jost 500 at 5 pt**, letterspaced. Rendering the band at 4.6, 8 and
11 pt through the real engine shows the hierarchy directly:

- **4.6 pt** — legible only up close; this is the status quo the issue objects to.
- **8 pt** — clearly readable at desk distance, and sits in proportion with the
  5 pt wordmark.
- **11 pt** — the id **dominates the footer**, overpowering the wordmark at more
  than twice its size. Geometrically fine, visually wrong.

8 pt is a **74 % increase** over today, satisfies FR-011 ("larger than 4.6 pt"),
serves US3 (legible without leaning in), and leaves 44 % of the cap unused as
headroom. It is also the size the issue itself proposed.

### The A8 grid holds automatically

`templates/card.typ` sizes everything through one `scale` factor, so at A8
(`74.25 mm` wide, `scale ≈ 0.707`) the id renders at `8 × 0.707 ≈ 5.66 pt` and
`cw / 3` shrinks by the same factor — **the percentage of cap is unchanged at
55.9 %**. The a8 id is still larger than today's a7 id. No separate a8 decision
is needed, which is exactly what the `scale` design is for.

### Alternatives considered

| Option | Verdict |
|---|---|
| Leave at 4.6 pt | **Rejected** — violates FR-011 and leaves US3 unserved. |
| 7 pt | Viable; more conservative. Rejected as under-using clear headroom. |
| **8 pt** | **Chosen** — measured, balanced against the 5 pt wordmark, 44 % headroom. |
| 11 pt (the Archivo floor) | **Rejected** — not required (C-3), and visually unbalances the band. |
| Grow to fill the cap | **Rejected** — `docs/design.md`: the card "never fills"; the footer is a quiet band. |

---

## R-3. Alphabet and generation (no open question — recorded for the implementer)

**Crockford Base32**, 32 symbols, `I` `L` `O` `U` excluded:

```
0123456789ABCDEFGHJKMNPQRSTVWXYZ
```

Decoding is case-insensitive and folds the confusables back, per FR-004:
`I` → `1`, `L` → `1`, `O` → `0`. `U` is excluded from the alphabet but is *not*
a decode mapping — it exists to avoid accidental words on a printed card. Ids
are compared by normalising to upper case and applying those three foldings.

Generation uses **`secrets.choice`** from the standard library — no dependency,
no network, no state outside the project's card files (FR-012). Uniqueness comes
from redraw-against-the-project's-id-set (FR-003a), not from the entropy alone.

---

## R-4. Where the new failure modes live

`tests/fixtures/demo-project/broken/` already carries eight deliberately broken
card files (`malformed.yaml`, `missing-fields.yaml`, `unknown-language.yaml`,
`overflowing.yaml`, …). Per CLAUDE.md and `docs/testing.md`, a new failure mode
belongs **there**, not in a fixture of its own. This feature adds:

- a duplicate id across two cards,
- an id outside the alphabet (`I`/`L`/`O`/`U`),
- an id of the wrong length,
- an id present but not a string (`id:`, `id: 12345`).

All are text files. Nothing here needs `scripts/make_testdata.py`, so **no
binaries are generated or committed** (Principle VIII).

---

## Open questions remaining

**None.** Both questions the spec deferred are settled above with measurements,
and the three incorrect premises are corrected. Phase 1 design can proceed.
