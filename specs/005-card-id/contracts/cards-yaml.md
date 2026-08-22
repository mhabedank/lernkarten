# Contract: `cards/*.yaml` — the `id` key

**Feature**: `specs/005-card-id` · **Status**: proposed · **Date**: 2026-08-21

This is the fifth contract under Constitution Principle I — the file formats are
the entire interface between the model-driven half (`skills/cards`) and the
deterministic half (`scripts/`, `templates/`). A change here is a breaking change
with a known blast radius, so the radius is written down.

## The change

One new **optional** per-card key: `id`.

```yaml
topic: 'Example: Probability'
language: english
grid: a7
cards:
  - id: A45DK                       # NEW — optional, 5 chars, Crockford Base32
    subtopic: 'Basics'
    front: 'What is a sample space $Omega$?'
    back: 'The set of all possible outcomes of a random experiment.'
    source: 'Example source'
```

`id` sits **first** on each card, before `subtopic`. Placement is a convention,
not a parse requirement — a reader must accept `id` anywhere in the mapping. It
is written first so a diff that adds ids stays readable and so a human scanning
the file sees the handle before the content.

## Value rules

| Rule | Value |
|---|---|
| Length | exactly **5** characters |
| Alphabet | Crockford Base32: `0123456789ABCDEFGHJKMNPQRSTVWXYZ` — 32 symbols, `I` `L` `O` `U` excluded |
| Type | a YAML string |
| Case | written upper case; **compared** case-insensitively |
| Confusables | on comparison, `I`→`1`, `L`→`1`, `O`→`0`. `U` is not a mapping — it is excluded so a printed id cannot spell an unfortunate word |
| Uniqueness | within one project (all `cards/*.yaml` together). **Not** global — there is no registry and none is planned |
| Stability | assigned once, never changed by editing, moving or renaming. The single exception is collision reassignment (below) |

## Who writes it

| Writer | Behaviour |
|---|---|
| `/cards` (the skill) | assigns a fresh id to every card it creates; **never** alters an id already present |
| `lernkarten id --backfill` | assigns ids to cards lacking one; leaves existing ids byte-identical; idempotent |
| `lernkarten check` / `check_project.py` | **never writes.** Read-only CI gate — reports and exits non-zero |
| `lernkarten build` | **never writes** to `cards/*.yaml`. It reads ids and renders them; it never assigns, backfills or reassigns |

## The `id` subcommand

`lernkarten id` is the **writing** path. Its surface is fixed here because
`quickstart.md` used two spellings and an implementer would otherwise guess.

| Invocation | Behaviour |
|---|---|
| `lernkarten id --backfill <files>` | assign ids to cards lacking one; leave existing ids untouched; idempotent; all-or-nothing |
| `lernkarten id --reassign <files>` | resolve duplicates across the given files, first-occurrence-wins by argument order |
| `lernkarten id <files>` | **not defined** — exit non-zero with usage. One of the two flags is required, so the destructive act is never the default |

Both flags read every file before writing any, so a failure anywhere leaves the
whole set untouched (FR-007).

## Validation

| Condition | Reported? | Exit |
|---|---|---|
| `id` absent on every card | one advisory line per run, naming the backfill path | **0** |
| `id` absent on some cards | same as above; the deck still builds | **0** |
| Two cards share an id | error naming **both** cards — file and card, not just the id | non-zero |
| `id` not 5 characters | error naming file, card and the length found | non-zero |
| `id` contains `I`, `L`, `O`, `U` or punctuation | error naming file, card and the offending character | non-zero |
| `id` present but not a string (`id:`, `id: 12345`, `id: [a]`) | error naming file and card — not a crash, not treated as absent | non-zero |

## Collision resolution

A collision can only arise when independently-assigned decks are combined —
assignment itself redraws against the project's id set, so it never produces one.

- The **writing** path reassigns automatically. **First occurrence wins**: files
  in command-line order, cards in file order; the first card seen carrying an id
  keeps it, every later one is reassigned.
- The report names the card, the old id and the new one, **and states the
  consequence**: a reassigned id no longer resolves in past conversations, and
  any revision history recorded against it is orphaned.
- The **validating** path never reassigns.

## Backwards compatibility

**Existing projects build unchanged.** `id` is optional; a deck written before
this feature has no `id:` anywhere and must produce the same page count it did
before. Migration is opt-in via backfill, never required.

The one visible change to an old deck is the rendered id itself — from
`topic-3` to a backfilled short id, or to the no-id fallback. That matters only
for cards already printed, and those already carry an id clipped by the
`cw / 3` box, so nothing legible is lost.

## Blast radius — what must change together

| File | Why |
|---|---|
| `skills/cards/SKILL.md` | assigns the id; documents the schema for the model |
| `scripts/build_pdf.py` | reads `card["id"]`; the `f"{path.stem}-{i}"` construction goes |
| `scripts/check_project.py` | the validation table above |
| `scripts/cardid.py` *(new)* | alphabet, generation, normalisation, splice, backfill, reassign |
| `bin/lernkarten` | new `id` subcommand in `COMMANDS` |
| `templates/card.typ` | renders the id at 8 pt; must not break when it is absent |
| `cards/example.yaml` | the versioned schema reference |
| `CLAUDE.md` | the schema block contributors and the model read |
| `tests/fixtures/demo-project/cards/*.yaml` | the shared corpus |
| `tests/fixtures/demo-project/broken/` | the four new failure modes |

## Rendering

The id renders in the footer band's right-hand block as `<id> · 1/2` (front) or
`<id> · 2/2` (back), IBM Plex Mono, muted grey.

- Size **8 pt** (was 4.6 pt), scaled by the template's existing `scale` factor,
  so A8 renders at ≈ 5.66 pt and holds the same proportion of the box.
- Measured 52.80 pt wide against the `cw / 3` cap of 94.49 pt — **55.9 %**, with
  the `clip: true` box never reached.
- A card with **no** id renders the side marker **alone** — `1/2` or `2/2`, with
  no id text and no `·` separator. The block keeps its position and its rule; the
  wordmark and side marker do not move and nothing overlaps (FR-005).

## Explicitly not in this contract

- **No `--card A45DK` selection.** Out of scope (FR-014); the build path does not
  learn to filter by id in this feature.
- **No global namespace or registry.** Uniqueness is per project.
- **No meaning encoded in the id.** It is a handle, not a classification — no
  topic prefix, no language marker, no deck code.
- **No revision or version suffix.** `A45DK@2` addressing belongs to the
  follow-on ticket that depends on this one.
