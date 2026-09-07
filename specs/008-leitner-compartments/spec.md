# Feature Specification: Leitner compartments

**Feature Branch**: `feat/leitner-compartments`

**Created**: 2026-09-05

**Status**: Draft

**Input**: GitHub issue #46 — "The box holds the cards but not the method: no Leitner compartments", as rewritten on 2026-09-05, plus the decisions recorded in `design/README.md`.

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/print`, and the build machinery under it. Nothing upstream of `/cards` is aware this feature exists.

**Implementation half**:

- [x] **Model-driven** — `skills/print/SKILL.md` gains the paper-stock advisory and the sentence about which sheet case a run is in.
- [x] **Deterministic** — divider rendering in `templates/`, placement and page arithmetic in `scripts/build_pdf.py`, the settings read in `bin/lernkarten`, plus tests.
- [x] **Both** — the seam is the project settings file `lernkarten.yaml` (#67). The deterministic half reads it and decides what to render; the model-driven half only reports what happened. **No new key touches any of the six file formats in Principle I.**

**Who runs into this**: the user. They print a deck, and now the deck comes with the dividers that turn it into a review system. Contributors touch the divider template and the placement rule; nobody has to learn a new artifact format.

## Why this is not a software scheduler

Worth stating in the spec, because it bounds the whole feature: **the card's position is its state.** The compartment a card sits in is how far along it is, and moving it is the write. There is no scheduling logic, no per-card review history, no `next_review` field and no state file. What this feature produces is *paper* — coloured divider cards and a page of instructions — plus the three questions needed to decide whether to print them.

Issue #25 Option C rejected exporting into a digital spaced-repetition system on the grounds that it is "a different product with a different loop". This is the inverse: the same product, the loop it already implies, in the material it is already made of.

## Clarifications

### Session 2026-09-07 — after the cross-model review

- Q: Two adjacent dividers share a vertical cut line and both bleed across it, so each carries a strip of its neighbour's colour. How is that resolved? (FR-006, [review finding 1](./reviews/2026-09-07-not-ready.md)) → A: **Dividers leave the card grid entirely.** They are free-placed as a block with a gap between them, on the same sheet below the cards where the block fits, otherwise on a further page. No two dividers share a cut line, so the bleed premise holds again.
- Q: Four dividers at card width total 287 mm, exactly the A8 print width, so no gap fits. How are they arranged? (FR-004) → A: **Two per row, stacked, at full card width.** Three fit one row of three; four take two rows of two. Full width is kept so a divider spans the box the way a card does.

### Session 2026-09-05

- Q: May dividers take free cells in a partly occupied bottom row, or must they always start a fresh sheet? (FR-004) → A: They must occupy a bottom row that holds no cards at all. *(Superseded on 2026-09-07: dividers left the grid entirely — see the session above. The reasoning survives, the mechanism does not.)*
- Q: What does the back of a divider carry — the same as the front, or something different? (FR-005) → A: Identical to the front: same colour, same numeral, same interval, same rule line. A divider has no wrong way round.
- Q: How are the settings shaped in `lernkarten.yaml`? (FR-019) → A: Three flat keys — `compartments` (`3` | `4` | `none`), `dividers_printed` (bool), `box_printed` (bool). No nesting, so validation is a set-membership test and #67's precedence resolves per key.
- Q: At three compartments, what are the three intervals? (FR-017) → A: daily · every 3 days · every 2 weeks. Both sets end at the same longest rest, so choosing three compartments buys fewer sessions rather than shorter gaps.
- Q: What does a divider's rule line say? (FR-005) → A: What enters and what leaves — compartment 1 "new + wrong cards", middles "moved up from N-1", the last "right → retire". Not a weekday rhythm: the interval already says when, and a printed weekday would freeze a start day the user never chose.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dividers come out of the same print run (Priority: P1)

A user has a deck and runs `lernkarten build cards/*.yaml --grid a8 --dividers 4`. The PDF they get holds their cards *and* four coloured divider cards, on the same stock, cut from the same sheets. They cut everything at once, drop the dividers into the box, and have compartments.

**Why this priority**: it is the artifact. Everything else in this feature exists to decide whether this happens and to explain what to do with it.

**Independent Test**: `lernkarten build tests/fixtures/demo-project/cards/*.yaml --grid a8 --dividers 4 -o /tmp/out.pdf` and take the PDF apart — page count, card count, the position of the four dividers.

**Acceptance Scenarios**:

1. **Given** the 31-card demo project at `--grid a8`, **When** built with `--dividers 4`, **Then** the PDF contains 31 cards plus 4 dividers, arranged two per row in a free-placed block that shares no cut line with any card or with each other.
2. **Given** the same deck, **When** built with `--dividers 3`, **Then** exactly three dividers are rendered, numbered 1–3, in **one row of three**.
3. **Given** any deck, **When** built with `--dividers 5` or `--dividers 2`, **Then** the build refuses with an error naming the accepted values, and writes no PDF.
4. **Given** a deck built with `--dividers 4`, **When** the divider cells are measured, **Then** each divider is **1.5 mm taller** than the run's card and **identical in width**, with at least 8 mm between its cut lines and any neighbour's, and at least 8 mm from every outer cut line to the paper edge.
5. **Given** a deck built with `--dividers 4 --margin 0`, **Then** each divider is still card width by card height + 1.5 mm with its full band and bleed — the block's internal gaps carry the bleed, so no margin is borrowed and **no fallback message is emitted**.
6. **Given** a deck built with `--dividers 4 --grid a7`, **Then** the build refuses per FR-009, and the error says which grid is required.

---

### User Story 2 - Asked once, then never again (Priority: P2)

A user runs `lernkarten build cards/*.yaml` for the first time in a project and is told, once, that the Leitner setup is unanswered and that `lernkarten setup` answers it. They run it, are asked how many compartments they want and whether the dividers and the box are already printed, and the three answers are written to `lernkarten.yaml` in the project root. Every later build in that project uses them without asking, and `/print` never has to mention it again.

**Why this priority**: without it the feature is a flag nobody discovers. With it, printing a deck offers the method. Principle II calls friction the thing this project does not accept, and retyping `--dividers 4` forever is friction.

**Independent Test**: run `lernkarten setup` against a scratch project with a scripted stdin; assert `lernkarten.yaml` appears with the three keys, and that a following build reads them and says nothing about setup.

**Acceptance Scenarios**:

1. **Given** a project with no `lernkarten.yaml`, **When** `lernkarten setup` runs on a terminal, **Then** the three questions are asked and the answers are written to `lernkarten.yaml`.
1a. **Given** the same project, **When** `lernkarten build` runs, **Then** it builds the deck unchanged and reports the unanswered setup exactly once, naming `lernkarten setup`.
1b. **Given** the same project, **When** `lernkarten setup` runs without a terminal, **Then** it refuses rather than guessing, and the error names the flags that set the same values non-interactively.
2. **Given** a project whose `lernkarten.yaml` records `compartments: 4` and `dividers_printed: true`, **When** `lernkarten build` runs, **Then** nothing is asked and **no dividers are added** — they exist already.
3. **Given** the same project, **When** `lernkarten build --dividers 4` is run explicitly, **Then** the dividers are rendered anyway: an explicit flag always beats the remembered answer.
4. **Given** a project whose `lernkarten.yaml` records `compartments: none`, **When** any build runs, **Then** no dividers are rendered and **no advisory line appears** — declined is not the same as unanswered.
5. **Given** an existing project with no `lernkarten.yaml`, **When** a build runs, **Then** the output matches today per SC-005 — absence of the file means the behaviour this repo had before the feature existed, and the advisory line goes to the run output, never into the PDF.
6. **Given** an unknown key in `lernkarten.yaml`, **When** any command reads it, **Then** a warning names the file, the key and the known keys, and the run continues.
7. **Given** an invalid value on a known key, **Then** the run fails with an error naming the key and the accepted values.
8. **Given** a `lernkarten.yaml` that exists but is **empty**, **Then** it is treated exactly as an absent file — never asked, so the advisory line appears. An empty file is not a declined answer.

---

### User Story 3 - The box is offered, with the warning that matters (Priority: P2)

The same first run asks whether the card box has been printed. If not, `output/box.pdf` is written beside `output/cards.pdf`, and the run says plainly that the box wants 160–250 gsm while the cards do not — a paper change in the middle of a print job.

**Why this priority**: `assets/card-box.pdf` shipped in 0.7.2 as a download on the landing page, which nobody sees at the moment they are printing. This puts it where it is needed.

**Independent Test**: build with `--box`; assert `output/box.pdf` exists, is byte-identical to `assets/card-box.pdf`, and that the run's output names the stock and the grid constraint.

**Acceptance Scenarios**:

1. **Given** any build, **When** `--box` is passed, **Then** `output/box.pdf` is written as an exact copy of `assets/card-box.pdf` and is **not** merged into `output/cards.pdf`.
2. **Given** a run that writes the box, **Then** the run states the stock (160–250 gsm), that it applies to the box only, and that the cards print on ordinary card stock.
3. **Given** a run at `--grid a7`, **When** `--box` is passed, **Then** the run refuses per FR-009.

---

### User Story 4 - The method, on a page (Priority: P3)

A user who has cut dividers wants to know what to do with them. `docs/leitner.html` explains the loop: which compartment is due, what a right answer does, what a wrong answer does, and where the intervals come from. It is linked from `docs/index.html` beside the box download.

**Why this priority**: a box with four slots and no instructions is a box with four slots. But the paper works without the page, so it ranks after the paper.

**Independent Test**: `python3 scripts/check_docs.py` resolves the new page and its links; the page is one self-contained file.

**Acceptance Scenarios**:

1. **Given** the repository, **When** `scripts/check_docs.py` runs, **Then** `docs/leitner.html` is present, linked from `docs/index.html`, and every link in it resolves.
2. **Given** the page, **When** its intervals are compared to the rendered dividers, **Then** every string matches exactly, for both the three- and the four-compartment set — a compartment cannot say "weekly" on paper and "every 5 days" on screen.
3. **Given** the page, **Then** it names Sebastian Leitner's 1972 original *and* says that its own schedule is a calendar simplification, not his capacity rule.

---

### Edge Cases

- **Missing optional tooling**: unchanged. Dividers are typeset by the pinned engine like everything else; no new binary and no new optional tool.
- **Fresh install on each platform**: `lernkarten.yaml` is read and written with the existing `scripts/yamlio.py`. No new path handling, so Windows, macOS and Linux stay equal.
- **Python floor**: no new dependency, so 3.12 is unaffected.
- **Encoding and file names**: `lernkarten.yaml` is UTF-8 like every other file this project writes.
- **Non-Latin card text**: unaffected — a divider carries a numeral and an English interval word, no user text.
- **Idempotence**: running a build twice with the same settings produces the same PDF. Answering the questions once does not re-ask; deleting `lernkarten.yaml` asks again and restores the same answers.
- **Text that does not fit**: a divider's text is generated and fixed, so it cannot overflow the way a user's card can. The interval strings are short by construction and are asserted to fit.
- **A card language nothing can hyphenate**: unaffected — dividers carry no prose.
- **The last sheet has no room for the block.** The common case, and the demo project sits in it: 31 cards at `--grid a8` fill three-and-a-bit rows of sheet 2, far less than the 2.44 free card rows a two-row block needs, so the dividers open a further page — which under `--sides simplex` goes through the printer twice. This is not a failure; it is the case the run has to *name* rather than implying the cheap one.
- **A deck that exactly fills its last sheet.** Same outcome, arrived at differently: no free cells at all, so the dividers begin a new sheet where every neighbour is empty and the bleed is unobstructed.
- **`--margin 0`.** Once dividers left the grid this stopped being a special case: the block reserves its own room and the bleed lives in the gaps between dividers, not in the page margin. The block is simply placed 8 mm clear of the paper edge instead of 5 mm clear of the print area. *(Superseded on 2026-09-07; the old fallback requirement is gone.)*
- **A non-interactive invocation.** `/print` runs `lernkarten build` without a terminal, so nothing can be asked. See FR-014.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `lernkarten build` MUST accept `--dividers <n>` where `n` is `3` or `4`, and MUST refuse any other value with an error naming the accepted set. It MUST also accept `--box`.
- **FR-002**: With `--dividers <n>`, the build MUST render exactly `n` divider faces into `output/cards.pdf`, numbered `1` to `n`, in the brand colour order: 1 `#c2251b`, 2 `#f0c000`, 3 `#0a3f8f`, 4 `#141414`.
- **FR-003**: A divider MUST be **1.5 mm taller** than the run's card and **identical in width**. The 1.5 mm comes from the box: 52 mm inside against a 50 mm card, so 51.5 mm still slides and still sits below the rim. Because FR-004 places dividers outside the grid, the extra height needs no direction and no borrowed margin — the block simply reserves the room. **`--margin 0` therefore no longer forces a fallback**: the gaps inside the block are the bleed's home, and only the block's outermost edges depend on the page margin, which the placement keeps clear of.
- **FR-004**: Dividers are **not laid out in the card grid**. They are free-placed as one block, so that no two dividers and no divider and card ever share a cut line — which is what makes the bleed in FR-006 safe. The block rules:
  - **Full card width.** A divider spans the box the way a card does.
  - **The layout is a table, not a maximum**: three dividers in **one row of three**; four as **two rows of two**. Four in one row is impossible — `4 × 71.75 = 287.00 mm` is the entire A8 print width, so any gap at all overflows it. Three in a row measure `3 × 71.75 + 2 × 8 = 231.25 mm`; two rows measure `2 × 51.5 + 8 = 111 mm`.
  - **8 mm is a cut-line-to-cut-line distance**, not clear paper: 3 mm of bleed from each neighbour plus 2 mm of cut tolerance, so the **middle 2 mm** is unprinted. Every outer cut line sits **at least 8 mm from the paper edge**, at every margin — measured from the paper, not from the print area, so `--margin 0` needs no special case.
  - The block sits in the **free area below the cards** on the last sheet when that area is tall enough, and otherwise **opens a further page**. At A8 a two-row block needs 2.44 free card rows, so it shares a sheet only when the last sheet holds at most one row of cards; a one-row block of three needs 1.25 rows and shares whenever at most two rows are used.
  - The block is **always placeable**, because a fresh page offers the full 200 mm.
- **FR-004a**: On a **back** page a divider MUST be placed at `sheet_w − x − w`; `y` is unchanged. `templates/cards.typ:65-72` mirrors a *card* by recomputing its column, and a free-placed divider has no column — so without this the back of divider 1 prints where the front of divider 2 sits, and one piece of paper reads `1` on one side and `2` on the other. FR-005's "identical faces" test would stay green through it, because both faces really are rendered from one definition; what differs is *which* definition lands on which piece of paper. The assertion that catches it compares the position of numeral `n` on the back against the mirrored position of numeral `n` on the front.
- **FR-005**: The two faces of one divider MUST be **identical** — same colour band, same numeral, same interval, same rule line. A divider is dropped into the box whichever way round it is held, so a face that differs is invisible half the time. This also makes the assertion trivial: the two faces render from one definition, and the test is that they match.
- **FR-006**: The colour band MUST extend past **every** cut line of the divider and MUST still reach every cut edge on **all four sides of both faces** when the back is offset by **2 mm** in any direction. Since FR-004 removes dividers from the grid, what lies past a divider's cut line is always empty paper — never a card and never another divider — so the guarantee is unconditional and a test may assert **the divider's own colour**, not merely that some colour is present.
- **FR-006a**: A divider MUST NOT carry either encoding of a card's side: not the header marker (`docs/design.md`: "a red circle on the front, a yellow disc on the back") and not the footer's `1/2` · `2/2`. It has no front and no back, so a marker claiming otherwise would be false. It also carries no card id and no `TOPIC / SUBTOPIC` label, because it belongs to no deck. (Related: #75 proposes dropping the footer marker from cards too; this requirement holds either way.)
- **FR-006b**: The divider block MUST carry **its own cut marks**, because it sits outside the grid the sheet's crop marks describe. **And on a page that holds the block, the sheet's grid marks MUST be drawn only for cut lines that bound a card** — none at all on a divider-only page. Otherwise the two mark sets contradict each other on one sheet: with the block centred at A8, the grid column at x = 76.75 mm runs 4 mm *inside* divider 1 and the one at 220.25 mm 4 mm inside divider 2, so a user cutting along the crop marks with a guillotine slices every divider. `sheet()` already knows which slice a page holds, so it can decide this. They MUST be drawn so the band cannot bury them — the band is dark and the existing marks are drawn first, in `guide` grey, which would be invisible under `#141414`. A divider whose cut line is unmarked can only be cut by measuring, which is the defect the crop-mark prerequisite exists to prevent.
- **FR-007**: A divider MUST be legible with all colour removed: the numeral and the interval carry the meaning, colour only speeds up finding it. (Principle XVI — colour never carries meaning alone.)
- **FR-008**: Dividers MUST NOT be cards. They MUST NOT appear in `cards/*.yaml`, MUST NOT be assigned a card id, and `scripts/check_project.py` MUST NOT count them in any card total.
- **FR-009a**: `--dividers` at `--margin 0` MUST **advise, not refuse**. The A8 card is then 74.25 × 52.5 mm and the divider 74.25 × 54 mm, which `docs/design.md` § The box already says will not enter a 73 × 52 mm opening. The asymmetry with FR-009 is deliberate and worth stating: an A7 card is **27 mm** over the opening and can never be made to fit, while a margin-0 A8 divider is **1.25 mm** over — and the *cards* it accompanies are already 1.25 mm over and are not refused. A divider that matches its deck is the correct artifact; refusing would hand a `--margin 0` user a deck with no dividers, when they may well trim or own a different box.
- **FR-009**: The build MUST refuse `--dividers` and `--box` at any grid other than A8, with an error naming the required grid. **This is the single statement of the A8 constraint**; its ground is `docs/design.md` § The box (73 × 24 × 52 mm inside against a 100 mm-wide A7 card), and everywhere else in this spec refers to FR-009 rather than restating the measurement.
- **FR-010**: `--box` MUST write `box.pdf` **beside the `-o` target** — `output/box.pdf` for the default target, `<dir>/box.pdf` for any other — as an exact copy of `assets/card-box.pdf`. It MUST NOT be merged into the card PDF. Naming a fixed `output/` path would put it somewhere the user did not ask for whenever `-o` points elsewhere.
- **FR-011**: Whenever the box is part of a run, the run MUST state that the box needs 160–250 gsm and that this applies to the box alone.
- **FR-012**: Whenever dividers are part of a run, the run MUST state whether they fitted into an existing sheet or added one, and — under `--sides simplex` — that an added sheet is fed twice.
- **FR-012c**: Advisories go to **stderr**, where every existing `NOTE`/`WARNING` in `scripts/build_pdf.py:412-416, 599-603` already goes. Only the closing summary line stays on stdout, so a caller redirecting one does not lose the other.
- **FR-012b**: Advisory lines are **independent and cumulative**. A run that adds a page, writes the box and skips file-driven dividers at a non-A8 grid emits all three, each once, in a stable order. None suppresses another, and none is merged into a summary sentence that would have to be parsed.
- **FR-012a**: The run MUST report dividers and cards as **separate counts**. `lernkarten check` already prints "`<n>` cards valid" and `tests/test_e2e.py` asserts on it, so a divider silently inflating that number would break an existing assertion and misstate what the user wrote.
- **FR-013**: `lernkarten setup`, run on a terminal, MUST ask three things — how many compartments (`3`, `4` or `none`), whether the dividers are already printed, and whether the box is already printed — and MUST write the answers to `lernkarten.yaml`. No other command asks, and none of the three is asked twice.
- **FR-014**: On a **non-interactive** run with no `lernkarten.yaml`, the build MUST NOT block and MUST NOT guess. It MUST build the deck exactly as it does today and report, **once**, that the Leitner setup is unanswered and that `lernkarten setup` answers it.
- **FR-014a**: `skills/print/SKILL.md` MUST relay that line to the user and offer to run `lernkarten setup`. The skill never invents the answers and never writes `lernkarten.yaml` itself — it only makes the question reachable from the pipeline. This keeps the file deterministic and testable under pytest while leaving the feature discoverable to a user who only ever types `/print`.
- **FR-014b**: `lernkarten setup` MUST be the one place the questions are asked. It takes `--project <dir>` (default: the working directory) so that what it **writes** and what a build **reads** are the same file — FR-021 derives the read root from the card files, and `setup` is given none. It MUST refuse to run without a terminal rather than guessing, and its error MUST name the three flags that set the same values non-interactively: `--compartments 3|4|none`, `--dividers-printed yes|no` and `--box-printed yes|no`. Those flags are the only pytest-reachable path, so they are the ones the tests use; a piped stdin is *not* a terminal and is refused like any other non-interactive run.
- **FR-015**: An explicit `--dividers` or `--box` flag MUST override whatever `lernkarten.yaml` records.
- **FR-015a**: A **file-driven** compartment count at a grid other than A8 MUST NOT fail the build. The dividers are skipped and the run says so once, naming FR-009's constraint. A **flag-driven** one still refuses per FR-009. The asymmetry is deliberate: a flag is a request the user just made and can correct; a file is an answer given once, possibly months ago, and must not make an unrelated A7 build impossible.
- **FR-016**: An absent `lernkarten.yaml` MUST produce the output SC-005 defines — `cards.json` byte-identical, and the PDF matched on page count, page size and card placement against post-prerequisite `main`. *(It said "byte-identical output" until 2026-09-07, which [research.md R8](./research.md) shows is impossible while the engine stamps a `CreationDate`. A requirement its own success criterion refuses is worse than a weaker one.)*
- **FR-016a**: An **unknown key** MUST be reported as a warning naming the file, the key and the keys this version knows, and the run MUST continue. It is never silently ignored, and it is never fatal. The reason is forward compatibility: #67 adds keys to this same file, and a hard error would make a project written by a newer version unbuildable by an older one — defeating FR-019's promise that #67 stays additive. A typo (`compartment` for `compartments`) is caught just as reliably, because the warning appears on every run.
- **FR-016b**: An **invalid value on a known key** MUST be a hard error naming the key and the accepted values, in the style `parse_grid` already uses. Unlike an unknown key, an unusable value cannot be carried forward: there is no safe interpretation of `compartments: 5`.
- **FR-017**: `docs/leitner.html` MUST exist, MUST be linked from `docs/index.html`, and MUST take its interval wording from the same source the divider template uses, so a compartment cannot say "weekly" on paper and something else on screen.
- **FR-017a**: The interval sets are fixed and are **not** truncations of one another:

  | Compartments | 1 | 2 | 3 | 4 |
  |---|---|---|---|---|
  | **3** | daily | every 3 days | every 2 weeks | — |
  | **4** | daily | every 2 days | weekly | every 2 weeks |

  Both end at the same longest rest, because what the far end of the box is for does not change with the number of compartments: choosing three buys **fewer sessions**, not shorter gaps for material already known. A build MUST refuse any compartment count other than 3 or 4 rather than deriving a set for it.
- **FR-017b**: Each divider MUST carry a **rule line** saying what enters that compartment and what leaves it — compartment 1 `new + wrong cards`, each middle compartment `moved up from <n-1>`, the last `right -> retire`. It MUST NOT name a weekday or a date: the interval already says *when*, and a printed weekday would fix a start day the user never chose and cannot change after cutting. This is the same reasoning that forbids printing a compartment number on a card.
- **FR-018**: `docs/design.md` MUST gain a section describing the divider — its geometry, its colour band and why it is allowed more ink than a card.
- **FR-020**: A successful **build** that renders dividers MUST set `dividers_printed: true`, and one that writes the box MUST set `box_printed: true` — otherwise a project answering `4 / no / no` reprints dividers forever. Three limits make that safe:
  - it writes back **only into a `lernkarten.yaml` that already exists and whose `compartments` is 3 or 4**. It never creates the file. A file carrying `dividers_printed: true` with no `compartments` would be a fourth state, and the three-state table does not have one;
  - it never writes back on `lernkarten check`. Check test-typesets the dividers, which "renders" them, but nothing was printed — and `/print` runs check before build, so a write there would mark the dividers printed and make the real build skip them;
  - it writes to the same project root FR-021 reads from, never to the working directory.
- **FR-021**: `lernkarten.yaml` is looked up in the **project root derived from the card files**, not in the current working directory — the same root `scripts/build_pdf.py` already derives for `figures/`. A settings file in whatever directory a command happens to run from would make the repository's own e2e runs depend on a developer's private file.
- **FR-019**: This feature MUST create `lernkarten.yaml` itself, carrying **only** its own three keys — `compartments` (`3` | `4` | `none`), `dividers_printed` (boolean) and `box_printed` (boolean), all at the top level with no nesting — and MUST do so in the shape #67 specifies for the project scope: the same filename in the project root, the same precedence (an explicit flag beats the file), and the same "an unknown key is reported, not ignored" rule. #67 then becomes purely **additive** — it adds keys and the user scope to a file that already exists, rather than replacing one. Creating a differently-named or differently-shaped file here is exactly the second artifact #67 exists to prevent, and is forbidden.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | **none** — dividers are not cards and get no key | — |

A **seventh** artifact enters the project, and it is deliberately outside the six of Principle I: `lernkarten.yaml`, the project settings file specified by #67. It holds choices, never content (Principle VII), and it is gitignored like everything else a user owns. This feature adds three flat keys to it — `compartments`, `dividers_printed` and `box_printed` — and answers #67's open "eager or lazy asking?" with **lazy**: the question is asked at the first print, when it is answerable.

**Backwards compatibility**: complete. Every existing project builds unchanged, because absence of `lernkarten.yaml` means today's behaviour and no card file gains or loses a key. The one behaviour that changes for existing projects is the first interactive build in a project, which asks three questions and accepts "none" as an answer.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: a new printed artifact (the divider) and its own cut marks, the free area of the press sheet below the cards, the landing page (one link), and a new documentation page. **The card grid itself is untouched** — dividers are placed outside it.
- **Black-only laser print still readable**: **yes** — FR-007. The numeral and the interval carry the meaning; the four colours become four greys and lose nothing but speed.
- **Minimum type size respected**: **yes** — the interval and the numeral are display sizes, well above the floor. The divider carries no reading text in the sense of Principle XVI.
- **Brand PNGs need re-rendering**: no. `assets/brand/*.typ` is untouched.
- **Duplex alignment**: **cards unaffected; dividers need explicit work.** `templates/cards.typ:65-72` mirrors *columns* for back pages (`if mirror { column = columns - 1 - column }`), which is a mechanism only a grid cell has. A free-placed divider is positioned in millimetres and therefore gets no mirroring for free — FR-004a supplies it. *(The earlier wording here argued that the 1.5 mm of growth needed no mirrored counterpart. That was true of the superseded downward-growth design and says nothing about `x`; leaving it in place would have been a stale justification standing beside a live defect.)*
- **Physical check required**: an A8 **duplex** run, because the mirroring above is verified against code and not against paper.

**The ink rule needs an explicit amendment.** `docs/design.md` says a card "never fills the card … only the two markers and the footer box on the back carry ink area". A border band is more ink than that. It is allowed here because a divider is **not a card** — it carries no user text, it never moves between compartments, and being findable at a glance is its entire function. This goes on that page as an addition for a new artifact, not as a loosening of the rule for cards.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. The dividers are typeset by the pinned engine like every other page, and the settings file is read through the existing `scripts/yamlio.py`.
- **New runtime dependency**: **none.** Copying `assets/card-box.pdf` to `output/box.pdf` is a file copy, deliberately chosen over merging it into the card PDF precisely so that no PDF library is needed.
- **New dev dependency**: none.
- **New external binary**: none.
- **Anything this makes redundant**: no.
- **Engine version change**: no.
- **Platforms verified**: macOS and Linux directly; Windows through the existing CI legs. Nothing platform-specific is introduced.

### Key Entities

- **Divider**: a printed card-sized sheet that separates compartments. Attributes: number (1…n), colour, interval text, rule text. It has no identity in any data file — it is generated from one integer and is not addressable, editable or countable as a card.
- **Compartment**: a position in the box, not a record. Its entire representation is physical.
- **Project settings (`lernkarten.yaml`)**: the choices a user answers once per project, as flat top-level keys. This feature contributes `compartments` (`3` | `4` | `none`), `dividers_printed` and `box_printed`. `none` is a real answer, not an absence: it means the user was asked and declined, and it stops the advisory line.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `lernkarten build tests/fixtures/demo-project/cards/*.yaml --grid a8 --dividers 4` produces a PDF containing 31 cards and 4 dividers. The 31 cards fill sheet 1 and three-and-a-bit rows of sheet 2, leaving far less than the 2.44 free rows a two-row block needs, so the dividers open sheet 3: the PDF is **6 pages**, against 4 without `--dividers`. No divider shares a cut line with a card or with another divider.
- **SC-002**: Every divider measures exactly the run's card width and card height + 1.5 mm, at every margin including `--margin 0`, with at least 8 mm cut-line-to-cut-line to any neighbour and to the paper edge.
- **SC-002a**: `--dividers` at `--margin 0` emits the box-fit advisory FR-009a requires.
- **SC-002b**: On a back page every divider's numeral sits at the mirrored `x` of the same numeral on the front (FR-004a).
- **SC-003**: With the back face displaced by 2 mm in any direction, **the divider's own colour** still reaches all four cut edges on both faces — not merely some colour, since nothing else is ever adjacent.
- **SC-003a**: The two faces of every divider are identical: same colour, numeral, interval and rule line, and neither carries a side marker.
- **SC-004**: `lernkarten check` reports the same card total with and without `--dividers` — 31 for the demo project either way — and dividers appear on their own line. *(The earlier wording also named `scripts/check_project.py`. That half was vacuous: it reads `cards/*.yaml` and a divider exists only in the build's in-memory record list, so it can never see one. FR-008 is asserted where a divider actually reaches — the six call sites in `scripts/build_pdf.py`.)*
- **SC-005**: A project with no `lernkarten.yaml` — or with an empty one — produces output **indistinguishable from `main` after the crop-mark prerequisite**, for every deck in the demo project, at **both grids** (`a7`, `a8`), **both `--sides` values** and at `--margin 0` as well as the default.
  *"Indistinguishable", not "byte-identical".* `tests/test_e2e.py` already records that the engine stamps a `CreationDate`, so two builds of identical input differ in bytes today and no byte comparison is possible without first making the timestamp reproducible. The comparison is therefore: the `cards.json` handed to the engine is **byte-identical** (which is assertable now, and is what the absent-means-`card` rule in `kind` buys), and the PDF matches on page count, page size and card placement. The baseline is post-prerequisite `main`, not "the previous release" — the prerequisite deliberately moves the A8 crop marks.
- **SC-006**: `lernkarten setup` writes `lernkarten.yaml`; a later build in the same project asks nothing and honours it.
- **SC-006a**: A non-interactive build with no `lernkarten.yaml` reports the unanswered setup exactly once, exits 0, and produces the same PDF it produces today.
- **SC-007**: Every run that includes the box states the 160–250 gsm stock and that it applies to the box only; every run that includes dividers states whether a sheet was added.
- **SC-008**: `python3 scripts/check_docs.py` passes with `docs/leitner.html` present and linked, and every interval string on that page matches the rendered dividers exactly, for the three- and the four-compartment set alike.
- **SC-008a**: `--dividers 3` renders "daily", "every 3 days", "every 2 weeks"; `--dividers 4` renders "daily", "every 2 days", "weekly", "every 2 weeks". Neither set is produced by truncating the other.
- **SC-008b**: Every rendered divider carries a rule line; the first says `new + wrong cards`, the last says `right -> retire`, and no rule line anywhere contains a weekday or a date.
- **SC-009**: `--dividers` or `--box` **as a flag** at `--grid a7` exits non-zero naming A8 and writes no PDF; the same values **from `lernkarten.yaml`** build normally, skip the dividers and say so once (FR-015a).

## Testability note on run output *(Principle XI)*

FR-011, FR-012 and FR-014 are satisfied by what a run *says*, and Principle XI
carves those out of test-first — "leaves nothing on disk, so no
`check_project.py` check can be written".

**That carve-out does not apply here.** It is written for the model-driven half.
These requirements belong to `bin/lernkarten`, which `tests/test_e2e.py` already
drives as a subprocess and asserts against its standard output
(`assert f"{DEMO_CARD_COUNT} cards valid" in result.stdout`, `test_e2e.py:69`).
Every advisory line in this spec is therefore a normal failing-test-first
requirement, not a manual checklist item, and none of them may be deferred to
`docs/testing.md`.

What *does* go on the manual checklist is the physical half, and only that:
that a cut divider slides into the folded box, that 1.5 mm is visible above the
cards in the box, and that the colour band survives a real hand-fed simplex run.
No assertion can reach those.

## Assumptions

- **#67 does not block this feature.** `lernkarten.yaml` is created here with three flat keys, in the shape #67 specifies for the project scope (FR-019), so #67 later adds to it rather than replacing it. What this feature deliberately does *not* build is #67's user scope, its full precedence chain (`flag → deck → project → user → default`) or its other keys — those stay #67's work.
- **#84 is independent.** A8 becoming the project-wide default makes `--grid a8` unnecessary at the command line, but nothing here depends on it: this feature refuses non-A8 explicitly, which is correct before and after that change.
- **The interval wording is fixed by FR-017a**, not derived. `design/guide.html` proposes a five-compartment set (daily, every 2 days, weekly, every 2 weeks, monthly); neither shipped set is a prefix of it, and the design README already records that five compartments are superseded. The last compartment in use carries the retire rule on its rule line.
- **The single source for the interval strings is a plan-level decision**, deliberately left open here. What the spec fixes is the *property* FR-017 has to satisfy — one definition, two renders — because that is what becomes an assertion. Whether it lives as a constant passed to the engine, a small data file read by both, or a check in `scripts/check_docs.py` comparing the two, is for plan.md.
- **The demo project is the test corpus.** Its 31 cards at `--grid a8` leave no room for a two-row block on the last sheet, which is exactly the "dividers add a page" case worth asserting. No new fixture is needed (Principle XI: extend the demo project, never start a second corpus).
- **The method page is hand-authored.** `design/guide.html` is a ~400 KB Claude Design export with embedded fonts and a JS template runtime; `docs/index.html` is 44 KB and self-contained. The export is a template for the page, not the page, and `design/README.md` records which of its assumptions are already superseded.
- **`assets/card-box.pdf` is the only geometry contract.** #45 shipped it without a Typst source (Principle VIII's named exception), so the box measurements in `docs/design.md` are what the *divider geometry* is checked against, by inspection rather than by construction. This is a different claim from FR-009, which owns the *grid refusal*; neither restates the other.
- **The user prints on a home printer**, mostly simplex, and cuts by hand. That assumption is what sets the colour band's width: it is a registration tolerance, not a matter of taste.
