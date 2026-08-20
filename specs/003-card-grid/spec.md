# Feature Specification: Configurable press-sheet grid

**Feature Branch**: `feat/card-grid`

**Created**: 2026-08-19

**Status**: Clarified · corrected against Phase 0 measurements

**Input**: GitHub issue [#23](https://github.com/mhabedank/lernkarten/issues/23) — "Cards come in one size only, and 8 per A4 sheet is often too big". User description: "there is a ticket about the size of the cards. lets implement it. currently the cards are quite big and thus are a waste of valuable thick paper."

## Clarifications

### Session 2026-08-19

- Q: Which press-sheet grids should `--grid` accept? → A: `2x4` (A7) and `4x4` (A8) only — the two grids on A4 that produce a card you can buy a storage box for. `3x4`, the ticket's suggestion, is dropped.
- Q: How should a deck's target card size reach `/cards`? → A: an optional key in `cards/*.yaml`. The deck declares the size it was written for; `/cards` writes to it, the build reads it as the default, `--grid` overrides it. The model-driven half is in scope.
- Q: Is a real-printer duplex/cutting check on A8 a release gate? → A: yes, a release gate. A8 must be printed duplex on real stock and cut before this merges.
- Q: What vocabulary should the flag and the YAML key use? → A: `--grid COLSxROWS` stays canonical, with `a7` and `a8` accepted as aliases.

### Research that changed the shape of this feature

The ticket recommended 3 × 4 as the first new grid on design grounds, without weighing whether the resulting card fits anything you can buy. Checking that reversed the decision.

Standard flashcard sizes are the ISO A-series in Europe and 3 × 5 inch in the US, and A7 (74 × 105 mm) is the metric equivalent of the 3 × 5 card. Ready-made Lernboxen and Karteikästen are sold in **A7** and **A8** (52 × 74 mm), typically holding 350–400 cards with A–Z registers. Because A4 halves into the A-series, only four grids on an A4 sheet land on a standard size at all:

| Grid | Card at `--margin 0` | A-series | Per sheet | Box you can buy |
|---|---|---|---|---|
| 2 × 2 | 105 × 148.5 mm | A6 portrait | 4 | yes — but larger than today |
| **2 × 4** | 105 × 74.25 mm | **A7 landscape** | 8 | yes — **today's card** |
| 3 × 4 | 70 × 74.25 mm | — | 12 | no snug box; rattles in an A7 |
| 2 × 6 | 105 × 49.5 mm | — | 12 | no |
| **4 × 4** | ~~52.5 × 74.25 mm~~ **74.25 × 52.5 mm** | ~~**A8 portrait**~~ **A8 landscape** | 16 | yes — A8 Lernbox |
| 4 × 8 | 52.5 × 37.1 mm | A9 | 32 | absurdly small |

Two consequences:

1. **The current card is already a standard size.** `docs/design.md` calls it "105 × 74.25 mm, landscape — A7" and that is exact. 2 × 4 on A4 *is* A7. That was a deliberate choice worth keeping.
2. **4 × 4 is exactly A8** — the next standard size down, and the only smaller grid with a purchasable box. At the default 5 mm margin it cuts to 71.75 × 50 mm, which drops into an A8 box with a little slack.

> **Bugfix**: 2026-08-20 — [BUG-007](./bugs/BUG-007.md). The table above originally read "A8 portrait" for 4 × 4 and the row passed anyway, because the selection test was "is there a box you can buy" and a portrait A8 card does fit an A8 box. **Every A-series halving flips the orientation**: A7 landscape is 105 × 74, so A8 landscape is 74 × 52, not 52 × 74. Halving a landscape card's width gives a portrait card. The sheet is turned instead — 4 × 4 on a **landscape** A4 — which tiles exactly and keeps 16 up.

Sources: [Confetti Campus — Karteikarten formats](https://confetticampus.de/lerntipps/kaufhilfe/karteikarten-welches-format/), [Stylex A8 Lern- und Karteikartenbox](https://www.stylex.de/de_DE/p/lern-und-karteikartenbox-din-a8-inkl-350-karteikarten-fsc/601/), [Stylex A7 box](https://www.stylex.de/de_DE/p/lern-und-karteikartenbox-din-a7-mit-6-registern/599/), [HAN A7 quer Karteikarten](https://www.han-fachshop.de/HAN-982-HAN-Karteikarten-DIN-A7-quer-Karteikarton-170-g-m-liniert-weiss-ar210.aspx), [Index card sizes compared](https://www.quill.com/content/index/resource-center/office-supplies/buying-guides/index-card-sizes/).

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/print` and `/cards`, plus build machinery.

**Implementation half**:

- [x] **Both** — and the seam is `cards/*.yaml`. The deterministic half (`scripts/build_pdf.py`, `templates/cards.typ`) gains the grid; the model-driven half (`skills/cards/SKILL.md`, the card-style guidance in `CLAUDE.md`) learns to write for a declared size. They meet at a new optional `grid:` key in the card file, which is a change to one of the five formats named in constitution principle I and is therefore a breaking change with the blast radius set out in Format Contracts below.

**Who runs into this**: both. The user driving Claude in their own project types the flag or lets a deck declare its size; a contributor to this repo has to keep the page-count assertions and the manual print checklist honest across both grids.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Print a deck at A8 and halve the paper (Priority: P1)

A user has a deck of short cards and is spending more thick stock than the content needs. They want the next size down the same standard ladder their current cards already sit on, so the cards still go in a box they can buy.

They run:

```bash
lernkarten build cards/*.yaml -o output/cards.pdf --grid a8
```

and get 16 cards to a sheet at 50 × 71.75 mm — half the sheets for the same deck, and a card that drops into an A8 Lernbox.

**Why this priority**: this is the complaint in the ticket and the only reason the feature exists. Nothing else here is worth building on its own.

**Independent Test**: run `lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/g.pdf --grid a8` over the 29 demo cards and count the pages: `2 × ⌈29 ÷ 16⌉ = 4`, against `2 × ⌈29 ÷ 8⌉ = 8` today.

**Acceptance Scenarios**:

1. **Given** the 29-card demo project, **When** the user runs `lernkarten build … --grid a8`, **Then** the PDF has 4 pages and the reported summary says 4 pages rather than 8.
2. **Given** the same project, **When** the user runs `--grid 4x4`, **Then** the output is identical to `--grid a8` — the alias resolves to the same grid.
3. **Given** the same project, **When** the user runs the build with no `--grid` and no deck declaring a size, **Then** the output is exactly today's behaviour: 2 × 4, 8 per sheet, 8 pages. The default is not merely equal to `2x4` — omitting the flag must change nothing for every project on disk.
4. **Given** `--grid a8`, **When** the sheet is inspected, **Then** front page *n* and back page *n* carry the same 16 cards, the backs column-mirrored across 4 columns (position 0 ↔ 3, 1 ↔ 2, 2 ↔ 1, 3 ↔ 0), so duplex "flip on long edge" lines each back up behind its front.
5. **Given** `--grid a8` at the default 5 mm margin, **When** the sheet is inspected, **Then** crop marks are drawn at 5 vertical and 5 horizontal cut lines — `columns + 1` and `rows + 1` — reaching into the margin at every one.
6. **Given** `--grid a8 --margin 0`, **When** the build runs, **Then** cards are exactly ~~52.5 × 74.25 mm~~ **74.25 × 52.5 mm — DIN A8 landscape, on a landscape A4 sheet (BUG-007)** — and no crop marks are drawn, matching the existing `--margin 0` rule.
7. **Given** `--grid a8`, **When** a card is inspected, **Then** reading text is still 11 pt and the front prompt still 14 pt. The card holds less; it is not set smaller. `scale` stays 1.0.

---

### User Story 2 - A deck declares the size it was written for (Priority: P2)

A8's writing area is **46 % of A7's** — 2218 mm² against 4786 mm², because width drops to 46 % while height is unchanged. A deck written to the A7 guidance and printed at A8 overflows on most cards. So the deck records the size it was written for, and `/cards` writes to that size from the start rather than the author discovering it after the first print.

**Why this priority**: P2 rather than P1 because the flag alone already saves paper for someone with short cards. But without this, every deck `/cards` writes is A7-shaped, and a user who has switched to A8 hand-splits cards after every first print — which makes the feature annoying to live with rather than merely incomplete.

**Independent Test**: per constitution XI, the red artifact for a prompt-half change is a check in `scripts/check_project.py` plus a failing case in `tests/test_check_project.py`. The check validates the new key; the deterministic side is testable to the exit code.

**Acceptance Scenarios**:

1. **Given** a card file carrying `grid: a8`, **When** the user runs `lernkarten build cards/*.yaml` with no `--grid`, **Then** the build uses A8 and reports 16 cards per sheet.
2. **Given** a card file carrying `grid: a8`, **When** the user runs `lernkarten build … --grid a7`, **Then** the flag wins and the build uses A7. An explicit flag always overrides what the file says.
3. **Given** a card file with no `grid:` key at all, **When** the build runs, **Then** it uses A7. Every existing deck on disk keeps working untouched.
4. **Given** two card files declaring *different* grids, **When** they are built together with no `--grid`, **Then** the build exits non-zero and names both files and both values. One PDF is one grid; silently picking one guarantees overflow on the other.
5. **Given** two card files declaring different grids, **When** they are built together *with* `--grid`, **Then** the flag resolves the conflict and the build proceeds.
6. **Given** a card file carrying an unsupported or malformed `grid:` value, **When** `lernkarten check` runs, **Then** it exits non-zero naming the file, the bad value and the supported set.
7. **Given** `/cards` is asked to write a deck for a project whose decks are A8, **When** it writes, **Then** the file carries `grid: a8` and the card text is sized for A8 rather than A7.

---

### User Story 3 - Overflow reporting survives both grids (Priority: P2)

The rule "a card that does not fit is reported, never shrunk" (constitution XIV, `docs/design.md`) must hold at A8 as well as A7. A smaller card means more cards overflow — that is correct and expected — but they must be *named*, not silently clipped.

**Why this priority**: this is the invariant most likely to break quietly. The overflow check runs as a *second* engine invocation (`typst query <overflow>`) which takes its own copy of the `--input` values. If the grid reaches the compile call but not the query call, the build would typeset A8 cards while checking overflow against A7 geometry — every warning wrong, and no existing test failing.

**Independent Test**: run `lernkarten check tests/fixtures/demo-project/broken/overflowing.yaml --grid a8` and assert the deliberately-overlong card is named in a `WARNING:` line, exactly as it is at A7.

**Acceptance Scenarios**:

1. **Given** `tests/fixtures/demo-project/broken/overflowing.yaml`, **When** built at A7 and at A8, **Then** the overlong card is reported by id at both.
2. **Given** the 29 demo cards, **When** built at A7, **Then** none is reported as overflowing — unchanged from today.
3. **Given** any grid, **When** the overflow query runs, **Then** it evaluates the same geometry the PDF was typeset at, so a card reported genuinely does not fit *that* sheet and a card not reported genuinely fits.
4. **Given** a card that does not fit, **When** the build reports it, **Then** the card is still drawn at full 11 pt with its text clipped — never rescaled to fit.
5. **Given** `broken/overflows-only-at-a8.yaml` — a card sized to fit A7 and not A8 — **When** it is built at A7 and at A8, **Then** it is reported **only** at A8. This is the assertion that catches an overflow query running against the wrong geometry; an assertion of absence cannot, because the query returns an empty set under both the correct and the buggy path.
6. **Given** the 29 demo cards built at A8, **When** the build reports overflow, **Then** **none of them is reported** — a regression guard, not the trap-catcher. Measured against the real engine: every demo card fits at A8, whose hard limits are 145 characters on the front and 185 on the back, while the corpus tops out at 66 and 154. This is a fixed expectation, not a golden value to re-measure. It passes under the FR-010 bug as well, so it is explicitly **not** the trap-catcher — scenario 5 is.

---

### User Story 4 - A grid the build cannot honour is refused (Priority: P3)

A user mistypes the flag or asks for a size that has never been printed and looked at. The build refuses before typesetting anything and says what is allowed.

**Why this priority**: P3 because it protects against misuse rather than delivering value. But it is cheap, and without it the failure mode is a silently absurd PDF rather than a message.

**Independent Test**: run the build with each rejected value and assert the exit code and that the message names both the offending value and the supported set.

**Acceptance Scenarios**:

1. **Given** any deck, **When** the user runs `--grid 3X4`, `--grid 3 x 4` or `--grid 3,4`, **Then** the build exits non-zero naming the value received and the expected `COLSxROWS` form.
2. **Given** any deck, **When** the user runs `--grid 0x4`, `--grid 3x0` or `--grid -1x4`, **Then** the build exits non-zero.
3. **Given** any deck, **When** the user runs a well-formed but unsupported grid such as `--grid 3x4` or `--grid 2x6`, **Then** the build exits non-zero and the message lists the supported grids and their A-series names.
4. **Given** any rejected grid, **When** the build refuses, **Then** it has not written or overwritten the output PDF.

---

### Edge Cases

- **Missing optional tooling**: unchanged. The grid rides along on engine invocations that already happen; no new tool is involved.
- **Fresh install on each platform**: unchanged — a CLI flag, an optional YAML key and two template constants. No platform surface.
- **Python floor**: unchanged, 3.12. Parsing `COLSxROWS` and an alias table need nothing beyond the standard library.
- **Encoding and file names**: not touched.
- **Non-Latin card text**: a Greek, Cyrillic or German card at A8 must still set correctly. Worth an explicit check because the head band clips, and clipping bites at widths that differ per script — the demo project already carries `gezeiten-de`, `palirroia-el` and `priliv-ru` for exactly this.
- **Idempotence**: building twice at the same grid gives the same PDF; building at A8 and back at A7 gives the original again. No state carries between runs.
- **Text that does not fit**: covered in full by User Story 3. Reported, never shrunk, at both grids.
- **A card language nothing can hyphenate**: a 43.2 mm-wide field makes bad line breaking far more visible than a 93.2 mm one. Behaviour is unchanged, but A8 is where it would first be noticed.
- **Fewer cards than one sheet holds**: `2 × ⌈n ÷ per-page⌉` must stay correct when *n* < per-page — 1 card at A8 is still 2 pages, not 0.
- **The head band clips, and it already clips today**: the topic/subtopic label sits in a box of `cw − head-h` with `clip: true`. Measured budget for the uppercase `TOPIC / SUBTOPIC` label: **~53 characters at A7, ~22 at A8**. Against the 38 cards shipped in this repo, **11 (29 %) already exceed the A7 budget and clip silently in `main` today**; at A8 all 38 would. This is a pre-existing defect this feature surfaces rather than introduces. It is not fixed here, but it stops being silent: a new grid-aware label-length check in `scripts/check_project.py` turns it into a named warning, and that check is also the red artifact constitution XI requires for the `/cards` prompt change.
- **A deck declaring a grid the build no longer supports**: if the supported set is ever narrowed, an existing file's `grid:` value must fail loudly at `check` time rather than being silently coerced.
- **An output file already exists when the build refuses**: the previous PDF must survive. A user who mistypes `--grid` should not lose the deck they printed yesterday.

## Requirements *(mandatory)*

### Functional Requirements

**The flag**

- **FR-001**: `lernkarten build` and `lernkarten check` MUST accept `--grid COLSxROWS` — for example `--grid 4x4` — setting the card columns and rows on the A4 press sheet.
- **FR-002**: The option MUST also accept the A-series aliases `a7` and `a8`, resolving to `2x4` and `4x4` respectively. `--grid a8` and `--grid 4x4` MUST be indistinguishable in effect.
- **FR-003**: The supported set MUST be exactly `2x4` (A7, 8 per sheet) and `4x4` (A8, 16 per sheet). Any other well-formed grid MUST be refused with a message listing the supported grids and their A-series names.
- **FR-004**: The effective default MUST be `2x4`, and a build with no `--grid` and no deck-declared grid MUST produce exactly the output the build produces today for every existing project.
- **FR-005**: A malformed value MUST be refused with a non-zero exit and a message naming the value received and the `COLSxROWS` form expected. The output PDF MUST NOT be written or overwritten when the build refuses.

**The sheet**

- **FR-006**: The press sheet MUST derive card width from `(sheet width − 2 × margin) ÷ columns` and card height from `(sheet height − 2 × margin) ÷ rows`, so card size, mirroring, crop marks and pagination all follow from the two numbers, as they do today. ~~`(210 mm …)` and `(297 mm …)`~~ — the sheet is A4 but **its orientation follows the grid** (FR-024), so the two numbers are 210 × 297 at `a7` and 297 × 210 at `a8`. *(Corrected by BUG-007.)*
- **FR-007**: Back pages MUST stay column-mirrored across the requested column count, so duplex "flip on long edge" puts each back behind its front at either grid.
- **FR-008**: Crop marks MUST be drawn at `columns + 1` vertical and `rows + 1` horizontal cut lines whenever the margin is non-zero, and MUST NOT be drawn when it is zero.
- **FR-009**: The build MUST report a page count of `2 × ⌈cards ÷ (columns × rows)⌉`, and the PDF MUST have exactly that many pages.
- **FR-010**: The overflow check MUST evaluate the same grid the PDF was typeset at. Both the compile invocation and the `typst query` invocation MUST receive the grid.
- **FR-011**: ~~The card MUST NOT be typeset smaller at a denser grid. Reading text stays 11 pt and the front prompt 14 pt; `scale` stays 1.0.~~ **Superseded by FR-025 (BUG-007).** This was written when A8 was believed to keep A7's height, where holding 11 pt cost nothing. On the corrected card it breaks the design outright — labels wrap out of the band, backs run off the card edge, the note rules stop fitting. What survives verbatim is the rule it was protecting: **a card that does not fit is reported and split by the author, never squeezed to fit.** That is now FR-026.

**The format contract**

- **FR-012**: `cards/*.yaml` MUST gain an optional top-level `grid:` key accepting the same vocabulary as the flag (`2x4`, `4x4`, `a7`, `a8`). Absent, it MUST mean A7, so every existing deck keeps working untouched.
- **FR-013**: An explicit `--grid` MUST override any deck-declared grid.
- **FR-014**: If a single build spans card files declaring *different* grids and no `--grid` is given, the build MUST exit non-zero naming the conflicting files and their values. One PDF is one grid.
- **FR-014a**: **A deck with no `grid:` key counts as declaring A7 for this purpose.** So a build mixing one `grid: a8` deck with decks that declare nothing is a conflict and MUST be refused. The safer reading is deliberate: silently typesetting an A7-written deck at 46 % of its writing area is exactly the drift this feature exists to prevent, and one `--grid` flag resolves it. The error message MUST distinguish a declared value from an absent one so the user can see which files are merely silent. *(Gap found by cross-model review C2.)*
- **FR-015**: `scripts/check_project.py` MUST validate the `grid:` key and report a file whose value is malformed or unsupported, naming the file and the value.
- **FR-016**: `skills/cards/SKILL.md` MUST write the `grid:` key into the decks it produces and MUST size its card text to the declared grid rather than to a single assumed size. Because FR-012 keeps the key optional, presence cannot be asserted on an arbitrary project; the verifiable form is FR-015a below. *(Conflict found by analysis D1.)*
- **FR-015a**: `scripts/check_project.py --strict` MUST warn when a `cards/*.yaml` declares no `grid:` key — "deck does not record the size it was written for". It MUST NOT warn outside `--strict`, so FR-012 holds. This is the red artifact constitution XI requires for the `/cards` prompt change.
- **FR-015b**: Because CI runs `check_project.py tests/fixtures/demo-project --strict` and `--strict` makes every warning fatal, the six demo decks MUST gain an explicit `grid: a7` key so this repo's own gate stays green. FR-015a's guarantee is therefore about *non-strict* runs: an existing project on disk builds and checks unchanged, but a project checked with `--strict` will be told to annotate its decks. *(Collision found by cross-model review C3.)*

**Docs and guidance**

- **FR-017**: The card-style guidance in `CLAUDE.md` MUST stop asserting one card size. The "front ~2 lines, back ~6 lines" advice MUST be stated per grid, with A8's roughly-half writing area made explicit.
- **FR-018**: `skills/print/SKILL.md` MUST document `--grid` alongside `--margin` and `--no-logo`, naming both supported grids and their A-series equivalents.
- **FR-019**: `docs/design.md` MUST describe the press sheet as a configurable grid with A7 (2 × 4) as the default and A8 (4 × 4) as the dense option, rather than as a fixed eight-up sheet.
- **FR-020**: `docs/testing.md` step 15 MUST state the page count as `2 × ⌈cards ÷ (columns × rows)⌉`, and steps 17 and 18 MUST be repeatable per grid rather than assuming 100 × 72 mm cards.

**Gaps closed after the implementation-readiness checklist**

- **FR-021**: `grid:` MUST be a **top-level key only**. A `grid:` key on an individual card MUST be reported as an error naming the file and the card index — one deck is one size, and a per-card grid is meaningless on a sheet that has exactly one geometry. *(Found by CHK015.)*
- **FR-022**: When the build refuses for any reason — malformed grid, unsupported grid, conflicting decks — a file already present at the output path MUST be left untouched: not truncated, not deleted, not partially written. "Writes no PDF" means the user's previous output survives a failed run. *(Found by CHK018.)*
- **FR-023**: ~~The head-band label-length check MUST be a **warning**, not an error, and MUST fire **only for decks resolving to A8**.~~ **Retired by BUG-007.** The check answered an A8-only problem that uniform scaling removes: the label box is now proportionally identical at both grids, so there is nothing A8-specific to warn about. Its stated justification was also false — labels wrap rather than truncate, and loss begins near 200 characters, not 53. Any future label check belongs to the card design at *all* sizes, under constitution XVI, not to this feature. Original text kept below for the record:
  - ~~Both restrictions are forced by the same fact: 11 of the 38 cards shipped in this repo already exceed the ~53-character A7 budget, and because `--strict` makes warnings fatal and CI runs it on the demo project, an A7-scoped check would turn this repo's own gate red on content the feature does not fix. A7 label clipping stays a known defect with its own ticket. Both restrictions are forced by the same fact: 11 of the 38 cards shipped in this repo already exceed the ~53-character A7 budget, and because `--strict` makes warnings fatal and CI runs it on the demo project, an A7-scoped check would turn this repo's own gate red on content the feature does not fix. A7 label clipping stays a known defect with its own ticket. *(Found by CHK033; scoped after cross-model review C3.)*

**Added by BUG-007**

- **FR-024**: **A card MUST be landscape at every supported grid** — wider than it is tall. This was assumed everywhere and asserted nowhere, which is why a portrait A8 passed every gate. Because each A-series halving flips the orientation, the **sheet** turns to satisfy it rather than the card: `a7` tiles a portrait A4 (2 × 4 → 105 × 74.25 mm) and `a8` tiles a **landscape** A4 (4 × 4 → 74.25 × 52.5 mm), both exactly and both 16 up at `a8`. A grid that cannot produce a landscape card MUST be refused rather than supported.
- **FR-025**: The card MUST be typeset at a **uniform scale** derived from the grid — `min(cw ÷ 100 mm, ch ÷ 71.75 mm)` against the A7 reference — so every dimension, band, inset and type size keeps its proportion. At `a8` that is 0.6969, giving 7.67 pt reading text and 6.0 / 4.3 mm bands. This supersedes FR-011. Holding 11 pt on a 50 mm-tall card was measured and does not work: labels wrap out of the band, backs overflow the card, the note rules stop fitting.
- **FR-026**: A card that does not fit MUST be reported and split by the author, **never squeezed to fit its own card**. FR-025 scales the whole card to its grid; it does not shrink text to rescue an overlong card. This is the part of FR-011 that survives, and it is the constitution XVI rule ("never shrinks type to fit") restated where it binds.
- **FR-027**: The overflow thresholds MUST **not** be grid-dependent. Under FR-025 the grids are proportionally identical, and measurement confirms the scaled `a8` card holds slightly *more* than `a7` — first overflow at 520 characters against 500 — because the scale takes the tighter of the two ratios and leaves about 3 % of width slack. One set of limits covers both, and the A7 numbers are the conservative choice. *(Supersedes the split introduced for FR-017.)*

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | **new optional top-level `grid:` key**, values `2x4` \| `4x4` \| `a7` \| `a8`, absent means A7 | `skills/cards`, `scripts/build_pdf.py`, `scripts/check_project.py`, `cards/example.yaml`, `CLAUDE.md`, the demo cards |

**Backwards compatibility**: yes, fully. The key is optional and its absence means today's size, so every project on disk builds unchanged and no deck needs migrating. This is the only shape of the change that does not break existing projects, and it is a hard requirement rather than a preference.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: the press sheet (card count and card size per A4), and the card at a size it has never been printed at. The card *design* — three bands, the inks, the marks — is unchanged; what changes is the rectangle it is drawn into.
- **Black-only laser print still readable**: yes. No colour is added, removed, or made to carry meaning alone. Front/back signals stay doubled by shape and position.
- **Minimum type size respected**: yes, and this is load-bearing. `scale` stays 1.0 at both grids, so reading text stays 11 pt and the floor in `docs/design.md` is never approached. Any proposal passing `scale < 1.0` to fit more on the card is forbidden by that floor and out of scope.
- **The fixed bands**: ~~`head-h` (8.6 mm) and `foot-h` (6.2 mm) are absolute … the bands stay at 20.6 % of card height at A7 and A8 alike. The vertical half of this worry does not arise in the shipped set. What A8 does cost is head-band label width: 91.4 mm → 41.4 mm, 45 % of today, with `clip: true` so the loss is silent.~~ **Wrong on both halves (BUG-007).** The dismissed worry is the one that bites: on the corrected landscape card the absolute bands would take **29.6 %** of card height, not 20.6 %. And the loss is not silent — the label **wraps** inside the band and stays readable to roughly 200 characters, first losing text near four lines, so the "~53-character budget" was measuring one-line capacity rather than truncation. Under FR-025 the bands scale with the card, so both concerns dissolve: at `a8` the bands are 6.0 / 4.3 mm and the proportions are identical to `a7`.
- **Brand PNGs need re-rendering**: no. `assets/brand/*.typ` import `card.typ` and call `faces()` at their own sizes; neither the card design nor the `faces()` signature changes.
- **Duplex alignment unaffected**: not automatically. Mirroring is grid-dependent and must follow the requested column count (FR-007). Correctness can be reasoned about from the PDF; *tolerance* cannot. A 0.5 mm duplex offset is 0.5 % of a 100 mm card and 1.0 % of a 50 mm one, and A8 has 5 vertical cut lines to A7's 3. This needs a real printer — see SC-007.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. Parsing `4x4` is a two-integer split and the alias table is a dict; a library for either would be worse than the code.
- **New runtime dependency**: none.
- **New dev dependency**: none.
- **New external binary**: none.
- **Anything this makes redundant**: the `CARDS_PER_PAGE = 8` module constant in `scripts/build_pdf.py` stops being a constant and becomes derived.
- **Engine version change**: no.
- **Platforms verified**: macOS and Linux via CI and locally. Windows unverified as usual, but the change is a flag, a YAML key and two template constants, with no platform-specific surface.

### Key Entities *(include if the feature involves data)*

- **Grid**: the arrangement of cards on one A4 press sheet. Two positive integers, columns and rows, restricted to `2x4` and `4x4`. Determines card size, cards per sheet, the mirroring axis, the crop-mark cut-line count and the page count. Default `2x4`. Addressable by its A-series alias.
- **Card size**: derived, never given directly. `(210 − 2 × margin) ÷ columns` by `(297 − 2 × margin) ÷ rows`, in mm. The user asks for a grid; the size follows.
- **Deck-declared grid**: the optional `grid:` key on a card file, recording the size the deck's text was written for. Advisory to the build (an explicit `--grid` overrides it) but authoritative for `/cards` when writing.

## Success Criteria *(mandatory)*

**Bugfix**: 2026-08-20 — BUG-007: the A8 card was portrait. SC-003 and SC-007 corrected, SC-010 and SC-011 added.

### Measurable Outcomes

- **SC-001**: Building the 29-card demo project at `--grid a8` produces a 4-page PDF against 8 pages at the default — **half the sheets for the same deck**, which is the paper saving this feature exists to deliver.
- **SC-002**: Building any existing project with no `--grid` flag and no deck-declared grid produces a PDF identical in page count, card size and layout to the one built before this feature existed.
- **SC-003**: At `--margin 0`, `--grid a7` cuts to 105 × 74.25 mm and `--grid a8` to ~~52.5 × 74.25 mm~~ **74.25 × 52.5 mm — landscape, on a landscape A4 sheet (BUG-007)** — the *unrounded* A7 and A8 of the halving series. ISO 216 rounds nominal sizes down to whole millimetres (74 × 105 and 52 × 74), so a card cut at `--margin 0` is up to 0.5 mm over nominal, while at the default 5 mm margin it is comfortably inside at 50 × 71.75 mm. Whether it drops into a bought box is settled physically by SC-007, not by this criterion.
- **SC-004**: `lernkarten build --grid <g>` exits non-zero, names the offending value, lists the supported grids, and writes no output PDF, for every malformed and every unsupported grid tested.
- **SC-005**: A card that **fits A7 but not A8** is reported at A8 and **not** at A7. `tests/fixtures/demo-project/broken/overflows-only-at-a8.yaml` carries exactly such a card — a ~300-character back; measured, it yields no warning at A7 and is reported at A8. This is the **only** assertion that catches an overflow query evaluating the wrong geometry. An assertion that *no* card overflows cannot catch it, because the demo cards overflow at neither grid and the query returns an empty set either way. Additionally: `overflowing-2` is reported at both grids, and no demo card is reported at either.
- **SC-006**: At both grids the reported page count and the actual PDF page count equal `2 × ⌈cards ÷ (columns × rows)⌉`, including when the deck holds fewer cards than one sheet.
- **SC-007**: **Release gate.** An A8 sheet printed duplex on real card stock has every back behind its front, cuts cleanly on the crop marks to **71.75 × 50 mm**, and a cut card drops into a DIN A8 Lernbox. ~~For the head band: a label within the ~22-character A8 budget is complete and legible at 6 pt, and an over-budget label clips cleanly at the band edge. **A short-label card must be printed alongside the demo corpus.**~~ **Rewritten by BUG-007.** The label half is retired with FR-023 — the box is proportionally identical at both grids now. What replaces it is the question uniform scaling raises: **is reading text legible at 7.67 pt on cheap paper?** `docs/design.md` sets the 11 pt floor because Archivo "survives 11 pt on cheap paper", and FR-025 goes below it, so the floor's own claim is what must be checked. Include the Greek and Cyrillic cards: they fall back to New Computer Modern, whose apertures differ, and will fail before the Latin ones. This cannot be judged from a PDF viewer and blocks the merge.

  **This gate has now failed once by being deferred.** BUG-007 shipped in v0.4.0 and v0.4.1 and would not have survived a printed sheet — a portrait card is not something you can hold and still call a flashcard. Walk it before the next release, not after.
- **SC-008**: A deck carrying `grid: a8` builds at A8 with no flag; the same deck with `--grid a7` builds at A7; two decks disagreeing with no flag fail loudly naming both files.
- **SC-010**: A card is landscape at every supported grid — `--grid a7` gives 105 × 74.25 mm and `--grid a8` gives 74.25 × 52.5 mm at `--margin 0`, both wider than tall. Asserted, because assuming it is what produced BUG-007. *(Added by BUG-007.)*
- **SC-011**: A deck that is legal at `a7` prints at `a8` without rewriting a card. Measured: first overflow at 500 characters at `a7` and 520 at `a8`, so the A7 limits are safe at both. This is what SC-001's "half the sheets for the same deck" actually requires. *(Added by BUG-007.)*
- **SC-009**: `docs/design.md`, `docs/testing.md`, `skills/print/SKILL.md` and `CLAUDE.md` contain no statement that the sheet holds eight cards, or that the card is 100 × 72 mm, as a fixed fact. `python3 scripts/check_docs.py` passes.

## Assumptions

- The user has Python 3.12+, a working Claude Code install, and the typesetting engine fetched or fetchable — unchanged from today.
- A4 stays the only paper size. This feature makes the *grid* configurable, not the sheet; Letter, A3 and n-up on other stock are out of scope.
- `--margin` stays a separate, independent option. `--grid` and `--margin` compose, and every card size quoted here is at the default 5 mm unless stated otherwise. Only `--margin 0` yields the exact A-series dimensions.
- `scale` stays 1.0 at both grids. The card holds less; it is never set smaller. Required by the 11 pt floor, not open to revisiting.
- One PDF is one grid. Mixing card sizes within a single output is out of scope — hence the conflict error in FR-014 rather than a per-file grid.
- The demo project carries the material needed: 29 cards across six topics including German, Greek and Russian, plus `tests/fixtures/demo-project/broken/overflowing.yaml`. Per `CLAUDE.md`, a new failure mode belongs in the demo project rather than a fixture of its own — so a deck declaring a `grid:` key, and a pair of decks that disagree, belong there.
- **No demo card overflows at either grid.** This was assumed to go the other way and was measured in Phase 0: despite A8 having 46 % of the writing area, all 29 demo cards fit, because the corpus is short (longest back 154 characters against an A8 hard limit of 185). `overflowing-2` in `broken/overflowing.yaml` is reported at both grids, so detection itself works at A8.
- Existing page-count assertions in `tests/test_e2e.py` (three `== 8`, one `== 2`) are correct for the default grid and stay correct; new assertions are added for A8 rather than the old ones being rewritten.
- **Correction to the ticket**: issue #23 says "the 31 demo cards". The demo project holds **29** (`DEMO_CARD_COUNT = 29`, `tests/test_e2e.py:25`); the "31" came from two stale comments in that same file, at lines 78 and 230. Page counts are unaffected — 29 and 31 give the same `2 × ⌈n ÷ per-page⌉` at every grid considered — so the ticket's measurements stand. The two stale comments are worth correcting while this feature is in the file.
- **Departure from the ticket**: issue #23 recommends 3 × 4 as the first new grid and argues 4 × 4 "should not be first". That reasoning weighed card design only. Once box compatibility is weighed, 3 × 4 fits nothing purchasable and 4 × 4 is exactly A8, so the order is reversed and 3 × 4 is dropped. The ticket's design concern about 4 × 4 is real and survives as the release gate in SC-007 — it is addressed rather than dismissed.
- **Known defect surfaced, not fixed**: 11 of the 38 cards shipped in this repo (29 %) already exceed the ~53-character head-band label budget at A7 and lose their tail silently, in `main`, today. This feature makes the problem visible through a new grid-aware check but does not change the band design to fix it — that is a card-design question under constitution XVI and deserves its own ticket. See [research.md](./research.md) R4 for the measurement.
