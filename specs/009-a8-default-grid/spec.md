# Feature Specification: A8 becomes the default grid

**Feature Branch**: `feat/a8-default-grid`

**Created**: 2026-09-07

**Status**: Draft

**Input**: GitHub issue #84 — "A7 is the default only because it was once the only size".

**Bugfix**: 2026-09-07 — [BUG-010](./bugs/BUG-010.md) The constant moved and its *description* did not, in fourteen places across nine files — **seventeen once the gate was written and looked for itself**. Two of them are not prose: `skills/cards/SKILL.md:173` writes a literal `grid: a7` into every deck `/cards` produces, pinning it to the size that fits neither the card box nor the Leitner dividers; and `scripts/check_project.py:990` resolves an absent grid with the literal `"a7"`, so the A8 picture advisory is skipped for exactly the decks that now print at A8. Adds FR-010 to FR-014 and SC-009 to SC-012, corrects FR-009, annotates the Format Contracts row, adds two edge cases and two assumptions.

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
- **A deck `/cards` already wrote.** *(Added by BUG-010.)* It carries `grid: a7`, prints at the size the card box does not fit, and is invisible to FR-006's report because it is not silent. Fixing the generator does not reach it; only the release note does (FR-014).
- **A grid-less deck carrying a picture.** *(Added by BUG-010.)* It prints at A8 and must be told that a picture there is a third of the area, exactly as a deck saying `grid: a8` is told. The advisory keying off a literal `"a7"` is what makes the two differ (FR-013).

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

  **Corrected by BUG-010.** "Advice about the `grid:` key" was read as one place and there are **two**. The `--strict` advice at `:930-935` was updated and is correct. The **picture advisory** at `:990` was not: it decides which decks are dense by `parse_grid(data.get("grid") or "a7")`, so a grid-less deck — the common case after this feature — is treated as A7 and never gets the warning, while an identical deck saying `grid: a8` does. Reproduced, and no test covers that advisory at all. The behavioural half is now **FR-013**.

**Added by BUG-010** *(2026-09-07)*

- **FR-010**: **`/cards` MUST write the default grid into a new deck, and it MUST be the grid `DEFAULT_GRID` names.** The schema block in `skills/cards/SKILL.md` currently hands the model a literal `grid: a7`, which is not a stale fallback a future move of the constant would correct — it is a *value written into the user's file*, and `--grid` at print time is then the only way past it. That deck does not fit `assets/card-box.pdf` and `--dividers` refuses it: the two problems this feature exists to solve, reintroduced by the feature's own generator. The value written is **`a8`**, not an omitted key: FR-006's report and the `--strict` advice both ask a silent deck to state its grid, so a generator that stays silent would fight the checker this feature shipped.
- **FR-011**: **No file outside `specs/` may describe A7 as what a default build produces** — neither by calling it the default in so many words, nor by giving the A7 card's dimensions, sheet capacity or cut count as the default output. The second half is the one that was missed: `README.md:155` still says to make four cuts, `:181-183` still gives the default card as 100 × 71.75 mm, and the landing page's hero band still opens with `8 cards / A4 page · 105 × 74.25 mm`. Historical statements inside `specs/` are correct as written and MUST NOT be swept; `docs/design.md`'s explanation of why the *reference* stays A7 is also correct and MUST survive.
- **FR-012**: **FR-011 MUST be enforced by a check that runs on every PR, not by a sweep.** This repository has made the same mistake three times — `check_sheet_capacity()` and `check_print_order()` in `scripts/check_docs.py` both exist because a `--grid` sweep was enforced by a hand-written grep and shipped the lines it missed, and `check_print_order`'s own comment says so. The check is **split by file type, each owner reading files it already reads**: `scripts/check_docs.py` widens beyond `markdown_files()` to cover `scripts/*.py` and `templates/*.typ`; `tests/test_landing_page.py`, which already parses `docs/index.html` and owns every other claim on that page, covers the landing page. Between them they MUST cover every site.

  **Implemented 2026-09-07.** Four checks, not one: `check_cards_skill_writes_the_default_grid` (FR-010, read from `DEFAULT_GRID` so the next move carries it), `check_a7_is_not_the_default`, `check_cut_count` and `check_borderless_size`, plus two assertions in `tests/test_landing_page.py`. Written **before** the sweep, and they found three sites this bug report had missed — including `build_pdf.py`'s `--grid` help string, which is the default as `--help` states it. Sixteen of the seventeen are gated; the seventeenth is an assertion *message* in a test, which no gate should read. The exemptions are four real distinctions and each is asserted: the default *margin*, the scale *reference*, explicit history, and the mixed-build refusal.
- **FR-013**: **`scripts/check_project.py` MUST resolve an absent `grid:` key through the same constant the build resolves it through, never a literal.** This is the arrangement FR-002 already forced on the *scale reference*: the two ideas of "which grid" are each named once and never retyped. A grid-less deck carrying a picture MUST therefore produce the dense-with-pictures advisory, identically to the same deck stating `grid: a8`.
- **FR-014**: **The release that carries this fix MUST tell users that decks `/cards` wrote since v0.9.0 are pinned to `grid: a7`.** Fixing the generator does not fix files already on disk, and **FR-006's report cannot find them** — it fires on decks that are *silent* about the grid, and these decks state one. Nothing in the tool will ever mention them, so the release note is the only place the user can learn it. No new check: reporting every `grid: a7` deck would nag every deliberate A7 deck, the demo corpus included.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `goal.md` | none | — |
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` | none | — |
| `catalog/topics.md` | none | — |
| `cards/*.yaml` schema | **the `grid:` key gains no syntax and loses none — but its *absence* changes meaning** | `skills/cards`, `scripts/build_pdf.py`, `scripts/check_project.py`, `cards/example.yaml`, `CLAUDE.md`, the demo cards |

> **Bugfix**: 2026-09-07 — [BUG-010](./bugs/BUG-010.md). The "Also needs updating" column above lists six artifacts and **understates the real set by more than half**. Everything it names was done except the first, `skills/cards` — which is the one that writes a value into user data (FR-010). The full set is seventeen sites in nine files: the six listed, plus `templates/cards.typ`, `docs/index.html`, `docs/workflow.md`, `docs/testing.md` and `README.md`. A contract row is not a requirement, nothing derives a task from it, and nothing checked it — which is why the column's first entry is the only one that shipped stale. FR-011 and FR-012 turn the column into something enforced.

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

**Added by BUG-010** *(2026-09-07)*

- **SC-009**: A deck written by `/cards` states `grid: a8`, builds 16 up with no flag, is accepted by `--dividers 4`, and draws no grid remark from `lernkarten check --strict`.
- **SC-010**: A grid-less deck carrying a picture produces the same dense-with-pictures advisory as the identical deck stating `grid: a8`. Asserted both ways, because absence of a warning is what shipped.
- **SC-011**: No file outside `specs/` calls A7 the default or gives the A7 card's dimensions, sheet capacity or cut count as a default build's output — and reintroducing one **fails a check**, in `scripts/check_docs.py` for markdown, `scripts/*.py` and `templates/*.typ`, and in `tests/test_landing_page.py` for `docs/index.html`. Verified by sabotage: put the sentence back and watch the gate go red.
- **SC-012**: The release notes for the version carrying this fix name decks `/cards` wrote since v0.9.0 and say they carry `grid: a7`.

## Assumptions

- **Nobody has to migrate anything.** A user who wants the old size adds one line; a user who does nothing gets smaller cards on the next print, which is what the release note has to say plainly.
- **Corrected while implementing**: the demo project and `cards/example.yaml` do *not* state no grid — all six demo decks and the example carry `grid: a7` explicitly. So neither moves by itself, and the demo project stays A7 on purpose: it is the corpus that exercises the **non**-default path, which is worth more than having it match the default. `cards/example.yaml` moves to `grid: a8` because it is what a user copies as a starting point, and it should show the size the card box fits.
- **The twelve `broken/` fixtures that stated no grid now state `grid: a7`.** They belong to an A7 project, and after this change their silence would mean A8 and put them in genuine disagreement with the decks beside them — the build was right to refuse, so the fixtures were wrong to be silent.
- **This is a minor, not a major.** Before 1.0.0 a breaking change rides in a minor and the release notes say what breaks (CONTRIBUTING, *Releases*).
- **Corrected by BUG-010**: "the blast radius is a deck's *size*, never its content" held for the build and not for the generator. `/cards` writing a literal `grid: a7` puts the default's *value* into user content, where no later change to the constant can reach it. A default that a prompt can pin is not one constant — it is one constant and every description of it, and the descriptions are the half that goes stale.
- **This feature shipped with no `plan.md` and no `tasks.md`** — `spec.md` and `checklists/` and nothing else, where every neighbouring feature carries the full set. That is the mechanical cause of BUG-010: the phase that enumerates the blast radius of a moved constant is the phase that was skipped. 003-card-grid, which *introduced* the `grid:` key, spent a whole task (T026) on "update the now-stale header comments in `templates/cards.typ` and the module docstring in `scripts/build_pdf.py`" — the same two sites, stale again. 009 is not retrofitted with a plan after the fact; `tasks.md` is created for the **fix**, carrying the site list, so the enumeration exists somewhere durable. *(Added 2026-09-07.)*
- **#67 is untouched.** Its argument against a *settings file* supplying a grid default at build time still stands; this is a built-in constant that moves once, for everyone, in a release, and cannot differ per machine.
