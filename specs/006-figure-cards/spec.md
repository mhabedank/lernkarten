# Feature Specification: Figure cards — pictures from the sources on a card

**Feature Branch**: `feat/figure-cards` — prefix required: `fix/`, `feat/`, `skill/`, `build/`, `docs/`, `ci/`, `test/`, `design/`

**Created**: 2026-08-22

**Status**: Draft

**Bugfix**: 2026-08-25 — [BUG-008](./bugs/BUG-008.md) `fetch` could not reach 28 % of real picture URLs: no `User-Agent`, and the format decided from the URL path instead of the response. Adds FR-026 to FR-028, SC-011, two edge cases.

**Input**: User description: "the lernkarten pipeline should also leveralge images from the sources. its must decide if an image has valiable viaualiztaion and build cards rfrom it. lets say. we have a chart or a flow chart. the pipeline then can create cards which ask for details in the charts or how specific concepüt work, for example "Describe CRISP-DM". You would then have the visualization of the backside."

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/ingest`, `/cards`, `/print` (build machinery). `/sources`, `/catalog`, `/learning-goal` and `/research-gaps` are untouched.

**Implementation half**:

- [ ] **Model-driven** — a prompt change under `skills/<name>/SKILL.md`.
- [ ] **Deterministic** — Python under `scripts/` or `bin/lernkarten`, and/or Typst under `templates/`.
- [x] **Both** — the seam is two file formats, and it is where the judgement stops and the mechanics start:
  - `knowledge/<source-id>/<slug>.md` carries the *judgement* — `/ingest` looks at each picture once, decides whether it is worth showing, and records the decision plus the path of the kept copy. Nothing downstream re-opens a picture to decide again.
  - `cards/<topic-slug>.yaml` carries the *reference* — optional `front_image:` and `back_image:` keys on a card, each a project-relative path. `lernkarten build` resolves them, `lernkarten check` validates them, and neither knows or cares why the model thought the picture was worth printing.

**Who runs into this**: the user driving Claude in their own project (a contributor to this repo runs into the demo fixture and the new build path).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A card carries a picture (Priority: P1)

A user has a card file in which cards name pictures:

```yaml
- id: F3M2Q
  subtopic: 'Tide charts'
  front: 'Describe the shape of the Kestrel Deep tide curve'
  back: 'Two highs and two lows a day, the second high the weaker one.'
  back_image: 'figures/island-images/tide-chart.png'
  source: 'Tide chart, harbour office'

- id: K7WT4
  subtopic: 'Tide charts'
  front: 'What does this chart show?'
  front_image: 'figures/island-images/tide-chart.png'
  back: 'A semidiurnal tide curve — two highs, two lows, unequal.'
```

They run `lernkarten build cards/*.yaml`. A back prints the answer text *and* its picture, above the source line. A front prints the prompt *and* its picture. Turning the sheet still puts each back behind its front.

**Why this priority**: nothing else in this feature is visible without it. It is also the only part that can be built and verified without a single model call, and once it exists a user can hand-write figure cards even if they never run `/ingest` again.

**Independent Test**: add a figure card to the demo deck, run `lernkarten build tests/fixtures/demo-project/cards/*.yaml`, and check the page count is unchanged and each picture lands on the face that named it.

**Acceptance Scenarios**:

1. **Given** the demo project with two cards carrying pictures and six without, **When** `lernkarten build cards/*.yaml` runs, **Then** the PDF has exactly 2 pages (2 × ⌈8 ÷ 8⌉) — a picture never costs a page.
2. **Given** a card carrying `back_image:` only, **When** the build finishes, **Then** the raster appears on the back page and not on the front page; **and** the mirror case holds for `front_image:`.
3. **Given** a card whose picture cannot be resolved or read, **When** `lernkarten build` runs, **Then** it exits non-zero and the message names the path, the card's `id` (or its positional ref, for a deck without ids) *and which face* named it.
4. **Given** a card whose text plus picture do not fit the field, **When** `lernkarten build` runs, **Then** the existing overflow warning names that card — the picture is scaled down to the field but never below the point where the warning would have fired, and the card is never cropped.
5. **Given** a deck in which no card carries a picture, **When** `lernkarten build` runs, **Then** the output is identical to what the same deck produced before this feature existed.
6. **Given** a deck declaring `grid: a8`, **When** it contains a figure card, **Then** it builds — the picture scales with the card like everything else on it, and `check_project.py` says once that pictures are small at this size.

---

### User Story 2 - `/ingest` decides which pictures are worth keeping (Priority: P2)

A user runs `/ingest`. Wherever a picture turns up — a file in a folder source, a figure on a PDF page, an image on a fetched web page, an image linked from a markdown file — the skill looks at it and decides whether *showing* it teaches something the transcription cannot: a chart, a flow chart, a labelled diagram, a decision tree, a map. Against: a photograph, a screenshot of prose, a logo, a running header, a divider, a stock illustration.

A picture worth showing is copied into `figures/<source-id>/<slug>.<ext>`, named in the document's frontmatter, and marked inline in the transcription at the point where it occurred. A picture not worth showing is recorded as rejected — so a second `/ingest` does not look at it again to reach the same conclusion.

**Why this priority**: this is the step the user's request actually asks for — "it must decide if an image has valuable visualization". It is useless without Story 1, which is why it ranks second, not because it matters less.

**Independent Test**: run `/ingest island-images handbook` against the demo project and inspect the knowledge documents — the chart carries a kept figure whose path resolves, the photograph carries a rejection, and the handbook PDF carries one entry per figure on its pages; then run `python3 scripts/check_project.py` and see all of it accepted.

**Acceptance Scenarios**:

1. **Given** the demo source `island-images` (one infographic, one photograph), **When** `/ingest island-images` runs, **Then** `knowledge/island-images/` holds two documents, exactly one figure is kept under `figures/island-images/`, and both documents record a verdict.
2. **Given** a PDF source with a chart on one of its pages, **When** `/ingest` runs, **Then** the chart is kept as a figure, the document's transcription marks where on the page it sat, and the page's running header and logo are not kept.
3. **Given** a markdown file linking a picture beside it (`![...](diagrams/flow.png)`), **When** its folder source is ingested, **Then** the linked picture is judged like any other and, if kept, copied under `figures/` — the link is followed relative to the markdown file.
4. **Given** a web source whose page shows a diagram, **When** `/ingest` runs, **Then** the picture is fetched and judged; a picture that cannot be fetched is reported in the summary and the ingest continues.
5. **Given** a picture that recurs on many pages of one document, **When** `/ingest` runs, **Then** it is kept at most once — a repeated picture is furniture, not a figure.
6. **Given** a project where `/ingest` has already run, **When** it runs again with nothing changed, **Then** no picture is looked at a second time, no file under `figures/` is rewritten, and the summary reports them skipped.
7. **Given** a kept figure whose file has since been deleted, **When** `python3 scripts/check_project.py` runs, **Then** it reports the knowledge document and the missing path.
8. **Given** a source behind a login or a paywall, **When** `/ingest` runs, **Then** no picture is fetched that the page's text would not also have been fetched from — the existing rule is not loosened for images.
9. **Given** a run that would look at more pictures than the existing threshold allows, **When** `/ingest` starts, **Then** it asks first and says how many — pictures found inside PDFs and web pages count towards the same threshold as a folder of images.

---

### User Story 3 - `/cards` writes three kinds of card from one figure (Priority: P3)

The user runs `/cards`. For a subtopic whose references include a document with a kept figure, the skill writes what it could not write before:

- **the description card** — an active-recall prompt on the front ("Describe the CRISP-DM cycle") with the picture on the back, plus a short answer text naming what the picture shows.
- **the recognition card** — the picture on the front ("What does this chart show?") with the answer in text on the back.
- **detail cards** — ordinary text cards asking about parts of the picture ("Which phase does CRISP-DM return to after Evaluation?"), written from the transcription. These carry no picture at all.

All of them go into the subtopic's normal `cards/<topic-slug>.yaml`; nothing about topic selection, merging or ids changes.

**Why this priority**: it is the payoff, but it rests on both stories above. A user who has them can already hand-write a figure card.

**Independent Test**: run `/cards` against a demo catalog whose subtopic references a document with a kept figure, then run `lernkarten check cards/*.yaml` and `python3 scripts/check_project.py` — every picture reference written resolves, and the deck compiles.

**Acceptance Scenarios**:

1. **Given** a subtopic referencing a document with one kept figure, **When** `/cards` runs for it, **Then** at most one card carries it as `back_image:` and at most one as `front_image:` — a picture is not printed onto six cards in a row.
2. **Given** the same subtopic, **When** `/cards` runs, **Then** it also writes text-only cards about the picture's content, so the figure yields recall practice and not only recognition.
3. **Given** a card carrying a picture, **When** it is written, **Then** the text on that same face is non-empty — a face that is only a picture has no prompt to read on the front and no answer to read on the back.
4. **Given** a subtopic marked `Status: gap` or `out of scope`, **When** `/cards` runs with no arguments, **Then** no figure card is written for it — the existing scope rules apply unchanged.
5. **Given** a run that wrote figure cards, **When** the summary is printed, **Then** it says how many cards carry a picture, so the user knows the deck now depends on files outside `cards/`.

---

### User Story 4 - The user finds out before printing, not after (Priority: P4)

Before spending paper, the user runs `lernkarten check cards/*.yaml`. Every picture reference in the deck is checked: the file exists, it is readable, it is a format the typesetting engine accepts, and it lives inside the project. A problem names the file, the card id, the face and what is wrong.

**Why this priority**: a safety net over Stories 1–3. Valuable, but a user who never breaks a path never notices it.

**Independent Test**: point fixture cards at a missing file, an unreadable file, a file of an unsupported type and a path outside the project, and check `lernkarten check` exits non-zero naming each.

**Acceptance Scenarios**:

1. **Given** a card naming a missing picture, **When** `lernkarten check` runs, **Then** it exits non-zero and names the card id, the face and the path.
2. **Given** a card naming a file the engine cannot read as an image, **When** `lernkarten check` runs, **Then** the four causes — missing, unreadable, unsupported type, outside the project — are distinguishable in the message rather than covered by one.
3. **Given** a card naming a picture outside the project directory, **When** `lernkarten check` runs, **Then** it is reported: a deck that only builds on the machine that wrote it is a defect, not a preference.

### Edge Cases

- **Missing optional tooling**: no typesetting engine → fetched as today. No `pdftotext`, no `sips`/`magick` → unchanged. Whatever pulls figures out of a PDF must degrade the way `pdftotext` does — its absence costs PDF figures and nothing else, and never fails an ingest.
- **Fresh install on each platform**: picture paths are project-relative, so a project copied from macOS to Windows still builds. A backslash in a hand-written path is reported, never silently repaired.
- **Python floor**: works on 3.12 with the declared dependencies, and whatever reads PDFs must ship wheels for all three platforms (constitution II).
- **Encoding and file names**: a picture whose file name carries umlauts or spaces; two pictures from one source that slug to the same name; a zero-byte file claiming to be a PNG; an SVG linked from markdown.
- **Non-Latin card text**: unchanged — a picture does not touch the text run.
- **Idempotence**: a second `/ingest` copies nothing and re-judges nothing; deleting one file under `figures/` and re-running brings back exactly that one.
- **Text that does not fit** a 105 × 74.25 mm card: now "text *and picture* that do not fit". Reported through the existing overflow path, never silently shrunk past legibility, never cropped.
- **A card language nothing can hyphenate**: unchanged.
- **A picture that carries its meaning in colour**: on a black-only laser it becomes grey on grey. This project's own graphics obey "colour never carries meaning alone"; a chart from someone else's PDF does not, and no automated check can judge it. It belongs on the manual checklist and in what `/ingest` tells the user.
- **A figure card at `a8`**: legal, and the picture is roughly a third the area it has at `a7`. Said once per run, not once per card.
- **A very large raster** (a 20 MP screenshot) on a 105 mm card: the PDF must not grow unreasonably and the build must not take visibly longer per card.
- **The same picture referenced by cards in two decks**: allowed, stored once.
- **A remote image that 404s, or a markdown link pointing outside the source folder**: reported in the summary, ingest continues.
- **A URL that carries no filename**, or one whose last path segment is a CDN key: fetched and judged from the response; reported as a missing filename if it fails, never as a format problem.
- **A picture in a format the engine cannot print** (AVIF is the common one): downloading it is fine, printing it is not. Refused as a card picture, naming the conversion.
- **A URL ending `.png` that serves an HTML error page**: refused before staging, not at typesetting.
- **A host that blocks a request with no `User-Agent`**: fetched successfully, because the tool says who it is.
- **A "figure" that is the whole page**: a scanned diagram page is a figure; a page of prose is not, however it was rasterised.

## Requirements *(mandatory)*

### Functional Requirements

**The card and the build**

- **FR-001**: `cards/*.yaml` MUST accept optional `front_image:` and `back_image:` keys on a card, each holding a picture path relative to the project root. Absent means a text-only face, exactly as today. A card may carry neither, either, or both.
- **FR-002**: `lernkarten build` MUST render each picture on the face that named it, together with that face's text — under the prompt on the front, and above the `source` line on the back — scaled to fit the field without cropping and without overlapping the header or footer bands.
- **FR-003**: `lernkarten build` MUST report a picture it cannot resolve or read, naming the path, the card and the face, and MUST exit non-zero rather than printing a card with a hole in it.
- **FR-004**: `lernkarten check` MUST validate every picture reference in a deck without typesetting it: exists, readable, an accepted image format, inside the project. Each failure names the card, the face and the path, and the four causes MUST be distinguishable in the message.
- **FR-005**: The existing overflow report MUST account for the picture — a face whose text plus picture exceed the field is reported by the same mechanism that reports overlong text today, naming the same card.
- **FR-006**: A deck containing no picture reference MUST produce exactly the output it produced before this feature. The page-count rule (2 × ⌈cards ÷ per-sheet⌉) MUST hold whether or not cards carry pictures.
- **FR-007**: Figure cards MUST be legal at every grid. The picture scales with the card, as every other element does, so a deck legal at `a7` stays legal at `a8`. `check_project.py` MUST say once per run — not once per card — that pictures are small at `a8`.

**Getting the pictures**

- **FR-008**: `/ingest` MUST find pictures in all four places they occur: image files reachable from a `folder` source; figures embedded in the pages of a PDF source; images on a fetched web page; and images linked from an ingested markdown file, whether the link is relative to that file or a remote URL. A URL does **not** announce its format: it may carry no filename at all (`lh7-us.googleusercontent.com/docsz/AD_4nX…`, which is what WordPress serves for anything pasted out of Google Docs), so what a picture *is* has to be settled from the response — see FR-027.
- **FR-009**: `/ingest` MUST decide, for every picture it looks at, whether the picture itself is worth showing on a card, and MUST record the decision — for both answers, so a rejection is not indistinguishable from a step that never ran.
- **FR-010**: When the answer is yes, `/ingest` MUST place a copy under `figures/<source-id>/<slug>.<ext>` and name that copy in the knowledge document's frontmatter. The original under `raw/` (or wherever the source lives) MUST NOT be moved, renamed or modified.
- **FR-011**: `/ingest` MUST mark, inside the transcription, the place where each kept figure sat, so `/cards` reads the picture in the context that explains it rather than as a loose file.
- **FR-012**: `/ingest` MUST keep transcribing every picture as it does today, whether or not it is kept. The transcription is what `/catalog` and the detail cards read; the copy is only what gets printed.
- **FR-013**: `/ingest` MUST keep a recurring picture at most once per document — a logo or a running header repeated on every page is furniture, not a figure.
- **FR-014**: `/ingest` MUST stay incremental over figures: a picture already judged is not looked at again, and an existing file under `figures/` is not rewritten, unless the source is newer or the user asks for a re-ingest.
- **FR-015**: `/ingest` MUST report a picture it cannot fetch, open or decode in the summary with the reason, and continue — a broken picture never stops an ingest.
- **FR-016**: `/ingest` MUST NOT fetch a picture from anywhere the existing rules forbid fetching text: no paywall circumvention, and nothing behind a login the user's own session is not already entitled to.
- **FR-017**: The count of pictures a run will look at MUST include those found inside PDFs, web pages and markdown links, and MUST be governed by the existing "ask before looking at more than N images" threshold.
- **FR-018**: PDF figure extraction MUST degrade rather than fail where the tool that performs it is unavailable — the rest of the ingest completes and the summary says which documents lost their figures.

**Validation and repository rules**

- **FR-019**: `scripts/check_project.py` MUST validate the new frontmatter: each recorded verdict holds one of the allowed values, each kept figure's path resolves to an existing file inside the project, and a document naming a figure it does not have is reported against the document, not against the source.
- **FR-020**: Figures MUST be treated as user content: `figures/` is gitignored alongside `knowledge/`, `catalog/` and `cards/`, and the repository-hygiene test MUST fail if a figure is committed.
- **FR-021**: The demo project MUST carry test material for every path this feature claims: a standalone picture worth showing, one not worth showing, a figure inside a PDF, a picture linked from a markdown file, and a picture on the local web fixture — all generated from Typst sources, never committed as binaries.

**What `/cards` writes**

- **FR-022**: `/cards` MUST write at most one description card (picture on the back) and at most one recognition card (picture on the front) per figure.
- **FR-023**: A card carrying a picture MUST carry non-empty text on that same face.
- **FR-024**: `/cards` MUST also write text-only detail cards from the figure's transcription. Observably: in the file a figure's cards land in, a subtopic that carries a picture-bearing card MUST also carry at least one card with no picture key — a chart produces recall practice, not only recognition.
- **FR-025**: `/cards` MUST report, in its summary, how many of the cards it wrote carry a picture.

**Reaching the web** *(added 2026-08-25 by [BUG-008](./bugs/BUG-008.md))*

These belong with the fetching rules above and are numbered here instead: a
requirement number is an address, and FR-026 to FR-028 are already cited from
`tasks.md`, the fetch contract and the bug report. Appending keeps the list
readable by number; FR-008 points forward to them.

- **FR-026**: `/ingest` MUST identify itself when fetching a picture, with an honest product token (`lernkarten/<version> (+<repository url>)`) set on the opener so it survives a redirect. It MUST NOT impersonate a browser. This is not a loosening of FR-016: bot protection blocks the *empty* case, and saying who you are is the opposite of pretending to be someone else.
- **FR-027**: The format of a fetched picture MUST be decided from the **response** — its `Content-Type` and its leading bytes — and never from the URL path. A response that is not an image MUST be refused *before* it is staged, so a `.png` URL serving an HTML error page is caught where it happens rather than at typesetting.
- **FR-028**: The formats accepted **from the network** and the formats the **engine can print** are two different sets and MUST be kept apart. A fetched picture that is a real image the engine cannot print MUST be refused *as a card picture*, with a message naming the conversion needed — never with a message claiming it is not an image. A URL that carries no filename MUST likewise be reported as that, and not as a format problem.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | **new**: a `figures:` list, one entry per picture *considered* — its verdict, where in the document it sat, and the project-relative path of the kept copy (present only when kept). A list, not a single key, because one PDF holds several figures. Plus an inline marker in the body at each kept figure's position | `skills/ingest`, `scripts/check_project.py`, the demo project |
| `catalog/topics.md` structure | none — a figure travels with the document that references it, so a subtopic's references need no new syntax | — |
| `cards/*.yaml` schema | **new**: optional `front_image:` and `back_image:` on a card, project-relative paths | `skills/cards`, `scripts/build_pdf.py`, `scripts/check_project.py`, `cards/example.yaml`, `CLAUDE.md`, the demo cards, `templates/card.typ` |
| `figures/<source-id>/<slug>.<ext>` | **new artifact** — the sixth thing the two halves share. Written by `/ingest`, read by the build, gitignored like `knowledge/` | `.gitignore`, `.githooks/pre-commit`, `tests/test_repo_hygiene.py`, `docs/workflow.md` |

**Backwards compatibility**: every existing project on disk still builds unchanged. All new keys are optional and their absence means exactly today's behaviour — a deck without picture keys is a text deck, a knowledge document without `figures:` is a document that predates them. Nothing is renamed and nothing changes meaning. A project that wants figures re-runs `/ingest` for the sources that have them; there is no migration to perform and nothing to hand-edit.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: both card faces — for the first time either can hold something other than type. `docs/design.md` gains a section saying how a picture sits in the field, what it may displace (the note rules) and what it may never displace (the prompt, the answer, the source line, the bands).
- **Black-only laser print still readable**: the layout, yes — a picture's own colours are the source's, not this project's. Nothing about the card's meaning is carried by the picture's colour: the text on the same face says what the picture shows, which is what makes a grey-on-grey print survivable.
- **Minimum type size respected**: yes — a picture never shrinks text to make room. When both do not fit, that is an overflow to report, not a licence to set 8 pt.
- **Brand PNGs need re-rendering**: no, unless the field geometry changes — `assets/brand/*.typ` import the card design but no figure card.
- **Duplex alignment unaffected**: yes — a picture lives inside the field of one face. Card size, mirroring, crop marks and pagination are untouched.
- **The note rules**: today they fill whatever room the answer leaves. A picture competes for the same room, and the picture wins — the rules appear only in what is left, and disappear entirely when nothing is.
- **The front's balance**: the front is a single centred prompt today. With a picture it becomes prompt-over-picture, and the prompt keeps its size and its position; the picture takes the room below.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** Nothing may be. Reading a PDF's pages and pulling a figure out of one is a library's job; so is decoding an image to check it is real (Pillow is already a dev dependency). Placing and scaling the picture is Typst's `image`, not ours. Constitution III makes reuse the default here.
- **New runtime dependency**: **yes — one, for figures inside PDFs.** It must clear Principle II (plain `pip install`, prebuilt wheels for Windows, macOS and Linux, no compiler, works offline) and the full Principle IV vetting table, which goes in `plan.md`. `pypdfium2` is the obvious candidate — permissively licensed, wheels for all six platform/arch pairs the engine already supports — but the vetting decides, not this spec. It ships through `scripts/deps.py` like `pyyaml`, and it is *optional at runtime* per FR-018: a project with no PDF figures never needs it to have worked.
- **New dev dependency**: none — Pillow and Typst already cover generating the demo material.
- **New external binary**: none. Nothing here may require a hand-installed tool for a core path.
- **Anything this makes redundant**: none.
- **Engine version change**: no — the engine already reads PNG, JPEG, GIF and SVG.
- **Network access**: `/ingest` already fetches web pages; it now also fetches the pictures on them and the remote pictures markdown links to. No source type becomes newly network-dependent.
- **Platforms verified**: macOS and Linux in CI; Windows manually — and it matters more than usual here, because this feature puts paths into a file format for the first time.

### Key Entities *(include if the feature involves data)*

- **Figure**: a picture from a source that is worth showing rather than only describing. Attributes: the source it came from, the document and the position it sat at, the path of the stored copy, the original location. Lives under `figures/<source-id>/`.
- **Visual judgement**: `/ingest`'s verdict on one picture — worth showing, or not. Recorded for every picture considered, including the rejections, because the value of writing it down is that nobody has to look again.
- **Figure card**: a card with a picture on one or both faces. Distinguished from every other card by the two optional keys and by nothing else — same id rules, same topic file, same length budget for its text.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A demo deck of 8 cards — one with a picture on the back, one with a picture on the front — builds to exactly 2 pages, with each picture on the face that named it and on no other.
- **SC-002**: `lernkarten check` exits non-zero and names the card id, the face and the path on each of four deliberately broken fixtures — picture missing, unreadable, outside the project, of an unsupported type — and exits 0 on every shipped card file.
- **SC-003**: `/ingest` on the demo project keeps a figure from each of the four paths it claims (a folder image, a PDF page, a markdown link, a web page) and rejects the photograph, the logo and the running header — verified by `scripts/check_project.py` passing on the result and failing when a kept file is deleted.
- **SC-004**: Re-running `/ingest` on an unchanged project rewrites no file under `figures/` and reports every picture skipped; deleting exactly one figure and re-running restores exactly that one.
- **SC-005**: With the PDF-reading dependency uninstalled, a full `/ingest` of the demo project still completes, still writes every transcription, and names in its summary the documents whose figures it could not extract.
- **SC-006**: Every card file shipped in this repo and in the demo project passes `lernkarten check` and `python3 scripts/check_project.py`, with the four existing gates green.
- **SC-007**: A deck with no picture reference produces a PDF identical to the one the same deck produced before this feature — page count, card count and overflow warnings unchanged.
- **SC-008**: A face whose text and picture together exceed the field is named by the overflow warning, and the card is neither cropped nor set below the minimum type size.
- **SC-009**: The same figure deck builds at `a7` and at `a8`, both without error, and the `a8` build says once that pictures are small at that size.
- **SC-010**: A fresh checkout with only Python builds a deck containing figure cards from one command, fetching the engine once and installing only the pinned dependency set.
- **SC-011**: Against a server that imitates the real web, all four shapes behave: an extensionless URL serving `image/png` is fetched and staged with a usable name; a host that 403s a request without a `User-Agent` is fetched with one; a `.png` URL serving `text/html` is refused before staging; and a fetched AVIF is refused as a *card picture* with a message naming the conversion.

## Assumptions

- The user has Python 3.12+, a working Claude Code install, and sources already registered — `/sources` needs no change, because a folder of images is already a `folder` source and the ingest skill already picks up `*.png`, `*.jpg`, `*.jpeg` by default.
- **The judgement is made once, in `/ingest`, and never re-made.** That is where the picture is already being looked at, and re-deciding in `/cards` would mean opening every picture on every run. The cost is that a user who disagrees with a verdict edits one line of frontmatter — the cheapest correction in the pipeline, and the reason the verdict is written down rather than implied.
- **A figure is copied, not linked.** The copy under `figures/` is what makes a project portable, self-contained and buildable after the source folder has been reorganised — and for a figure inside a PDF or on a web page there is no stable original to link at all. The duplicated bytes are the price, and a picture worth printing is small.
- **Figures are user content**, gitignored like `knowledge/` and `cards/`, enforced by the same hook and the same hygiene test. The demo project's pictures stay generated by `scripts/make_testdata.py`, never committed (constitution VII and VIII).
- **The text on a face stays required.** A face that is only a picture has no prompt on the front and no answer on the back, no context for the source line, and nothing for `check_project.py` to measure. The picture supplements the text rather than replacing it.
- **Copyright is the user's call.** Reproducing a figure from someone else's document onto a private study card is the user's decision, exactly as transcribing that document's text already is. `cards/` and `figures/` are gitignored, so this repository never carries it, and no automated check will attempt to judge it.
- ~~**The engine's format set is also the right set to accept from the network.**~~
  Wrong, and the cause of BUG-008. They answer different questions — what typst
  0.15.1 can print, and what a web server may hand back — and AVIF is in the
  second but not the first. Deciding what a fetched picture is needs no
  dependency (`Content-Type` plus a few magic-byte prefixes); *converting* one
  the engine cannot print would need a runtime image library, which is why FR-028
  refuses rather than converts.
- **Only the PDF path needs a new dependency.** Folder images need nothing, web images reuse the fetching that already exists, and markdown links resolve to one or the other.
- The demo project already carries most of the material — `generators/tide-chart.typ` (an infographic worth showing), `generators/noticeboard.typ` (a photograph that is not), `generators/handbook.typ` (a PDF that can gain a figure and a running logo), and the local web fixture under `raw/web`. What is new is a markdown file linking a picture, a figure-bearing demo card, and the four broken fixtures for SC-002.
- This relies on the existing overflow mechanism (`<overflow>` metadata read back with `typst query`) being able to measure a block containing an image, and on `yamlio` reporting the line number of a malformed card file.
