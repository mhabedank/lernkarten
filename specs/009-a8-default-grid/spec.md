# Feature Specification: A8 becomes the default grid

**Feature Branch**: `feat/a8-default-grid`

**Created**: 2026-09-07

**Status**: Draft

**Input**: GitHub issue #84 — "A7 is the default only because it was once the only size".

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/print`, and the build machinery under it. Nothing upstream is aware of it.

**Implementation half**:

- [x] **Model-driven** — `skills/cards/SKILL.md` and `skills/print/SKILL.md` mention the default size; the advice `check_project.py` gives about `grid:` changes with it.
- [x] **Deterministic** — one constant in `scripts/build_pdf.py`, one new constant beside it, and the tests and docs that quote the old one.
- [x] **Both** — the seam is `cards/*.yaml`'s `grid:` key. Its *meaning when absent* changes; the key itself does not.

**Who runs into this**: every user with a deck that never stated a grid. That is the whole point and the whole risk.

## Why now

A7 is the default because it was once the only size. Since then three things moved:

- **The box only fits A8.** `assets/card-box.pdf` takes 71.75 × 50 mm cards. An A7 card is 100 mm wide against a 73 mm opening, so **the project's default output does not fit the only container the project ships**.
- **v0.8.0's Leitner dividers refuse anything else.** `--dividers` needs `--grid a8`, so the whole spaced-repetition half of the tool is unreachable from the default.
- **The card budget is size-independent.** `docs/design.md` establishes that a denser grid renders the same card at a uniform scale, so a deck legal at one grid is legal at all of them. Nothing is lost by defaulting to the smaller one, and a user gets twice the cards per sheet.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A new deck prints 16 up (Priority: P1)

Someone writes cards and runs `lernkarten build cards/*.yaml`. They get 16 cards to an A4 sheet, at the size the card box was built for, and `--dividers 4` works without a flag they had to know about.

**Why this priority**: it is the change.

**Independent Test**: build a deck with no `grid:` key and count the pages and the card size.

**Acceptance Scenarios**:

1. **Given** a deck with no `grid:` key, **When** it is built with no `--grid`, **Then** the sheet is landscape A4 and holds 16 cards.
2. **Given** the same deck, **When** `--dividers 4` is passed with no `--grid`, **Then** it is accepted rather than refused.
3. **Given** a deck with no `grid:` key, **When** `lernkarten check` runs, **Then** it says once that the deck relies on the default and names the key that would pin it.

---

### User Story 2 - An existing A7 deck is unharmed (Priority: P1)

Someone who printed an A7 deck last month adds `grid: a7` and reprints one topic. The new cards are indistinguishable from the ones in their hand.

**Why this priority**: **equal first**. A change that silently reprints someone's deck at a different size is not a feature, and the failure mode is invisible until the cards are cut.

**Independent Test**: build a deck carrying `grid: a7` before and after the change and compare card geometry, page count and scale factor.

**Acceptance Scenarios**:

1. **Given** a deck with `grid: a7`, **When** it is built, **Then** the card is 100 × 71.75 mm at the default margin, exactly as before.
2. **Given** the same deck, **When** the rendered card is measured, **Then** its **scale factor is 1.0**, its type is 11 pt and its bands are where they were.
3. **Given** two decks that disagree about `grid:` and no `--grid`, **Then** the build still refuses to guess, with the same error.
4. **Given** any deck, **When** `--grid` is passed, **Then** it still wins over the file.

---

### Edge Cases

- **A deck that says nothing and overflows.** The overflow threshold must not move: a card legal today must stay legal, and one that overflows must still be reported rather than shrunk.
- **`--margin 0`.** The scale reference is margin-dependent; both grids have to be checked at 0, 5 and 10 mm.
- **A mixed build** where one deck says `a7` and another says nothing. After this change the silent one means A8, so the two now disagree where they previously agreed — the refusal is correct, and its message has to be readable.
- **The demo project and `cards/example.yaml`**, neither of which states a grid today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A card file with no `grid:` key MUST build at the 4 × 4 grid (A8, 16 up) on a landscape A4 sheet.
- **FR-002**: **The card scale reference MUST remain the A7 card.** `card_scale()` measures every grid against `card_size(DEFAULT_GRID, margin)`; if that reference follows the default, **A7 cards silently grow by 39 %** — measured: at the default margin the A7 factor goes from 1.000 to 1.394, and at `--margin 0` to 1.414. Type, bands, insets and the note rules all scale with it. The reference is therefore a **separate constant** from the default, and the two are never again the same name.
- **FR-003**: A deck carrying `grid: a7` MUST produce the card it produces today — 100 × 71.75 mm at the default margin, scale factor exactly 1.0, at every permitted margin.
- **FR-004**: `resolve_grid()`'s refusal to guess between two decks that disagree MUST be unchanged, including its message.
- **FR-005**: `--grid` MUST still override whatever the files say.
- **FR-006**: `lernkarten check` MUST report **once per run**, not once per deck, that a deck relies on the default rather than stating its grid, and MUST name the key that pins it. This is what lets a user with a printed A7 deck find out before reprinting.
- **FR-007**: The overflow threshold MUST be measured against the same reference card as today, so a card legal before the change is legal after it.
- **FR-008**: A7 MUST remain a fully supported grid. Only what *absence* means changes.
- **FR-009**: `scripts/check_project.py`'s advice about the `grid:` key MUST name the grid that now needs pinning, not the one that used to.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `goal.md` | none | — |
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` | none | — |
| `catalog/topics.md` | none | — |
| `cards/*.yaml` schema | **the `grid:` key gains no syntax and loses none — but its *absence* changes meaning** | `skills/cards`, `scripts/build_pdf.py`, `scripts/check_project.py`, `cards/example.yaml`, `CLAUDE.md`, the demo cards |

**Backwards compatibility**: **this is the breaking change**, and it is the fifth contract in Principle I that carries it. A deck with no `grid:` key prints at a different size than it did. Adding `grid: a7` restores it exactly; FR-006 exists so a user is told that before they cut.

The blast radius is a deck's *size*, never its content: no card is lost, no key becomes invalid, and nothing needs migrating.

### Print & Design Impact *(mandatory)*

- **Visible surfaces touched**: every deck that never stated a grid. Nothing about the card design itself changes — the same card is rendered at a different scale, which is the mechanism `docs/design.md` already describes.
- **Black-only laser print still readable**: yes for A8 as today; the type-size question at A8 is manual checklist step 20 and is unaffected by which grid is the *default*.
- **Minimum type size respected**: yes — Principle XVI scopes the 11 pt floor to the card at its reference size, and FR-002 keeps that reference where it is.
- **Brand PNGs need re-rendering**: no.
- **Duplex alignment unaffected**: yes — column mirroring is per grid and neither grid changes.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled?** No.
- **New runtime dependency**: none. **New dev dependency**: none. **New external binary**: none.
- **Engine version change**: no.
- **Platforms verified**: unchanged; this is arithmetic, not I/O.

### Key Entities

- **Default grid**: what an absent `grid:` key means. Changes from 2 × 4 to 4 × 4.
- **Reference grid**: what `card_scale()` measures against. **Stays 2 × 4 forever**, because the card design is drawn at that size and 11 pt is defined there. FR-002 is the requirement that these two stop being the same thing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A deck with no `grid:` key builds to a landscape A4 sheet holding 16 cards of 71.75 × 50 mm at the default margin.
- **SC-002**: A deck with `grid: a7` builds to a portrait A4 sheet holding 8 cards of 100 × 71.75 mm, with a scale factor of **exactly 1.0**, at margins 0, 5 and 10 mm.
- **SC-003**: The scale factor for each grid is unchanged from today at every permitted margin — a7 1.000 and a8 0.697 at margin 5, a8 0.707 at margin 0, a8 0.686 at margin 10.
- **SC-004**: Two decks disagreeing about `grid:` are still refused without `--grid`, with the message unchanged.
- **SC-005**: `--grid a7` on a deck that says nothing produces the same PDF as `grid: a7` in the file.
- **SC-006**: `lernkarten check` on a deck with no `grid:` key names the key exactly once per run, whatever the number of decks.
- **SC-007**: A card at the documented budget (~120 characters front, ~400 back) is reported as overflowing neither before nor after the change, at both grids.
- **SC-008**: `--dividers 4` with no `--grid` is accepted.

## Assumptions

- **Nobody has to migrate anything.** A user who wants the old size adds one line; a user who does nothing gets smaller cards on the next print, which is what the release note has to say plainly.
- **Corrected while implementing**: the demo project and `cards/example.yaml` do *not* state no grid — all six demo decks and the example carry `grid: a7` explicitly. So neither moves by itself, and the demo project stays A7 on purpose: it is the corpus that exercises the **non**-default path, which is worth more than having it match the default. `cards/example.yaml` moves to `grid: a8` because it is what a user copies as a starting point, and it should show the size the card box fits.
- **The twelve `broken/` fixtures that stated no grid now state `grid: a7`.** They belong to an A7 project, and after this change their silence would mean A8 and put them in genuine disagreement with the decks beside them — the build was right to refuse, so the fixtures were wrong to be silent.
- **This is a minor, not a major.** Before 1.0.0 a breaking change rides in a minor and the release notes say what breaks (CONTRIBUTING, *Releases*).
- **#67 is untouched.** Its argument against a *settings file* supplying a grid default at build time still stands; this is a built-in constant that moves once, for everyone, in a release, and cannot differ per machine.
