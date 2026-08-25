# Testing — automatically and by hand

The pipeline has two halves. `/print` and everything below it is a script: it
can be tested to the last exit code. `/sources`, `/ingest`, `/catalog` and
`/cards` are done by Claude, so what a test can pin down there is the *shape*
of what they write, not the wording. Both halves have their tool here.

Everything runs against one body of test data: the **demo project** in
[`tests/fixtures/demo-project`](../tests/fixtures/demo-project/README.md) — a
miniature project about an invented archipelago, with raw material, ingested
texts, a topic catalog, card files in four languages, and six card files that
are broken on purpose. The subject is invented for this repository, so the
fixture can be shipped and edited without a licence question. Keep it that way:
invent, do not quote.

## Write the test first

The rest of this page says *where* a test goes. This section says *when*: before
the code, always.

Write the test, run it, watch it fail, then make it pass. A test written
afterwards tells you what the code does; only a test you have seen fail tells
you it does what was asked. "Fails with `ImportError`" is not a red test — make
it fail on the assertion.

For the deterministic half that is an ordinary pytest case at whichever level
the [table below](#automated) prescribes. For the model-driven half it needs one
more step, because a prompt has no unit test: the red artifact is **a check in
`scripts/check_project.py` plus a case in `tests/test_check_project.py` that
fails against what the current prompt produces.** Then change the prompt until
it passes. If you cannot write a check that fails, the requirement is not yet
sharp enough to implement — that is a signal to go back and pin down what the
skill should write, not a licence to skip the test.

Bug fixes reproduce first: the failing test names the culprit and stays in the
suite for good.

Design work is the one place this thins out. Page count, card count, an
overflowing card *reported* rather than shrunk, an exit code — all of that is
assertable and comes first. Whether the card actually looks right is not a
pytest question and belongs on the [checklist](#the-checklist) below.

Spikes are fine. Explore in a scratch branch, learn the answer, throw it away,
then build it test-first. A spike does not go straight into a pull request.

## The test data

A test that starts at `knowledge/` never touches `/ingest`, so the fixture
starts one step earlier: at the raw material a user would point `/sources` at.

```bash
python3 scripts/make_testdata.py     # build the binary half, once
```

| Source type | What the fixture offers | Needs |
|---|---|---|
| `folder` | markdown, plain text, HTML, a subfolder, an umlaut file name, an empty file, a Windows-1252 file | — |
| `pdf` | a four-page handbook with a text layer, a scan with none, a 61-page almanac and a truncated file | `make_testdata.py` |
| `folder` (images) | an infographic as PNG, a photographed notice as JPEG | `make_testdata.py` |
| `folder` (office) | a Word document | `make_testdata.py` |
| `web` | a four-page site with links, nav, a cookie banner, a login page and a path that answers 403 | `http.server` |
| `web` (internet) | `https://example.com/`, IANA's reserved example domain | a connection |
| `zotero` | an eight-item library: text PDFs, a scan, a note, a link, an absolute path, a second collection | `zotero_stub.py` |
| `research` | one source written the way `/research-gaps` writes them: a `gap:` instead of a path, and a document naming the URL it was built from | — |

The fixture also carries a `goal.md` with three areas, and a catalog holding
all three subtopic states at once: one `Status: gap` (nothing covers it), one
`Status: out of scope` (ingested but off-goal), one closed by the `research`
source, plus a two-parent subtopic with its reciprocal `Also covers:` line and
a `Related:` pair.

The binaries — PDFs, the scan, the image, the DOCX, the Zotero attachments —
are **generated, not versioned**: `make_testdata.py` renders them from the
typst sources in `tests/fixtures/demo-project/generators/`. So the whole test
corpus is reviewable as text, a git history stays free of binary blobs, and the
scan is genuinely a scan: pixels rendered into a PDF, with nothing for
`pdftotext` to find. That last one matters — a "scan" with a text layer would
test nothing.

The two sources that need something to talk to are served locally:

```bash
python3 -m http.server 8137 --directory tests/fixtures/demo-project/raw/web
python3 scripts/zotero_stub.py     # fakes the Zotero 7 local API on port 23119
```

With the stub running, `/ingest kestrel-zotero` and every `curl` in the ingest
skill work with no Zotero installed. Details in the
[fixture README](../tests/fixtures/zotero/README.md).

## Automated

```bash
ruff check . && ruff format --check .      # style
pytest                                     # unit and end-to-end tests
lernkarten check cards/example.yaml        # the shipped example still typesets
python3 scripts/check_docs.py              # skills, links, required files
```

These four are the gates before every pull request, and CI runs the same.

CI runs the suite on Linux, macOS and Windows, and all three block a merge.
Windows was advisory for exactly as long as it took to fix what it found — git
quoting paths it should not have, and nobody stating the encoding of extracted
PDF text — and it counts like the others now. A Windows failure is a failure.

`pytest` covers eight levels:

| Module | Level | What it does |
|---|---|---|
| `tests/test_yamlio.py`, `tests/test_engine.py`, `tests/test_build_pdf.py` | unit | the functions, without a typesetter |
| `tests/test_deps.py` | dependencies | the bootstrap: what happens with no package, no pip, a failing pip |
| `tests/test_testdata.py` | test data | the generator, and whether the scan really has no text layer |
| `tests/test_ingest_sources.py` | ingest | the web source over a local server, the zotero source over the stub |
| `tests/test_e2e.py` | end-to-end | runs `bin/lernkarten` as a subprocess and takes the PDF apart |
| `tests/test_check_project.py` | contract | the artifacts of the four Claude-driven steps |
| `tests/test_repo_hygiene.py` | repo | no user content, no committed binaries, and what a release must and must not say in its docs |
| `tests/test_landing_page.py` | page | the structure of `docs/index.html` — never its geometry |

`tests/test_e2e.py` and `tests/test_testdata.py` need the typesetting engine.
Without one they skip, so a fresh checkout never downloads 30 MB unasked:

```bash
LERNKARTEN_E2E=1 pytest tests/test_e2e.py   # fetch the engine if it is missing
```

One test in `tests/test_deps.py` really installs a package from PyPI, and is
skipped unless you ask for it — the same bargain, so a plain `pytest` reaches the
network for nothing:

```bash
LERNKARTEN_DEPS_NET=1 pytest tests/test_deps.py
```

Text extraction from the generated PDFs needs `pdftotext` (poppler-utils).
Where it is missing, those tests skip rather than fail — the code path they
cover is exactly the one that treats an unreadable PDF as a job for the Read
tool.

### Checking a project that Claude wrote

`scripts/check_project.py` reads a whole project folder and reports what the
next step would trip over — a source without an `id`, an ingested file whose
frontmatter is missing, a catalog reference pointing nowhere, two cards with
the same front, a language nothing can hyphenate:

```bash
python3 scripts/check_project.py                        # the current folder
python3 scripts/check_project.py ~/flashcards --strict   # warnings count too
```

Errors mean the pipeline breaks and exit with 1. Warnings are style questions —
a card back of 600 characters, a subtopic that is in no catalog — and only fail
with `--strict`. Run it after `/ingest`, `/catalog` and `/cards`; it is the
closest thing to a test the model-driven half has.

## By hand

Some things only a person can judge: whether the cards are worth learning, and
whether front and back land on top of each other after printing.

### Setting up a scratch project

```bash
python3 scripts/demo.py ~/lernkarten-demo --raw   # sources only, work to do
python3 scripts/demo.py ~/lernkarten-demo         # the finished project
cd ~/lernkarten-demo && claude
```

`--raw` copies the raw material and the source register and leaves
`knowledge/`, `catalog/` and `cards/` empty — that is the version for testing
the skills. Without it you get the finished project, which is the version for
testing `/print` and the build script. `--force` overwrites an earlier copy,
and refuses any folder that is not a demo project. The binary material is built
on the way in, so the copy is complete.

Two of the nine sources want a server. Start both in their own terminal before
step 5, and stop the Zotero stub again before you open the real Zotero:

```bash
python3 -m http.server 8137 --directory ~/lernkarten-demo/raw/web
python3 scripts/zotero_stub.py
```

### The checklist

| # | Step | Do this | Expect |
|---|---|---|---|
| 1 | `/sources` | `/sources ~/lernkarten-demo/raw/field-notes` in a fresh folder | `sources.yaml` with one `type: folder` entry and a kebab-case id |
| 2 | `/sources` | `/sources https://example.com/` | a second entry, `type: web`, `depth: 0` |
| 3 | `/sources` | `/sources` with no argument | every source listed, unreachable ones flagged |
| 4 | `/sources` | "remove the web source" | the entry is gone, the rest untouched |
| 5 | `/ingest` | `/ingest field-notes` on the raw demo copy | five files under `knowledge/field-notes/` — including the one from `appendix/`; the umlaut file name becomes a clean slug; the empty file is reported, not invented |
| 6 | `/ingest` | `/ingest` a second time | everything skipped as unchanged, nothing rewritten |
| 7 | `/ingest` | delete one knowledge file, `/ingest` again | exactly that one comes back |
| 8a | `/ingest` | `/ingest handbook` | text of the first two pages only — `pages: "1-2"` is respected |
| 8b | `/ingest` | `/ingest tide-tables` | the scan is read as images; the tide figures are there and not garbled |
| 8c | `/ingest` | `/ingest island-images` | both images are picked up without a `pattern`; transcribed structurally, no OCR word salad. The chart is kept — `visual: chart`, a `path:` under `figures/island-images/`, a caption, and a markdown image link in the body where it sat. The photograph is **rejected**, `visual: none` with a `why:`, and nothing is copied for it |
| 8c-i | `/ingest` | `/ingest handbook` | the figure on page 3 is offered and kept; the office mark in the running header is offered **once** with `repeated_on: 4` and rejected as furniture |
| 8c-ii | `/ingest` | `/ingest` a second time | **run output, nothing on disk (FR-014):** every picture reported as skipped, no file under `figures/` rewritten. Delete exactly one figure and exactly that one comes back |
| 8c-iii | `/ingest` | uninstall `pypdfium2`, `/ingest handbook` | **run output (FR-018):** the transcription is still written in full, and the summary names the document whose figures could not be extracted. Exit 3 from `figures.py`, no traceback |
| 8c-iv | `/ingest` | point a source at an unreadable image | **run output (FR-015):** the summary names the file and the reason, and the ingest carries on |
| 8c-v | `/ingest` | a source with more than 20 pictures across PDFs, pages and links | **run output (FR-017):** you are asked first, and told how many — pictures found inside documents count towards the same threshold as a folder of images |
| 8d | `/ingest` | `/ingest office-notes` | the DOCX arrives as text |
| 8e | `/ingest` | `/ingest harbour-office` (server running) | three pages under `knowledge/harbour-office/`, nav bar and cookie banner dropped, `depth: 1` followed |
| 8f | `/ingest` | `/ingest harbour-office-members` | the login page is *not* ingested and nothing behind it is invented; no credentials are typed anywhere |
| 8g | `/ingest` | `/ingest kestrel-zotero` (stub running) | three documents, the scan among them flagged `pending:`; the Mainland item is left out |
| 8g-i | `/ingest` | the same, over the whole stub library | the two items titled *Notes on the Ashwind approach* **both** land, the second as `<slug>-<key>.md`; the summary counts one collision and names the absolute directory it wrote into. Neither is called "skipped" |
| 8g-ii | `/ingest` | the same run, the *Tide office of Fenmouth* item | the cover sheet keeps the little text it has and is marked `content: sparse` with a character count — **not** `pending:`, because there is nothing for the Read tool to come back for |
| 8h | `/learning-goal` | `/learning-goal` with a short brief | `goal.md` with frontmatter, at least one area, at least one topic |
| 8i | `/learning-goal` | run it again with a brief that only **adds** | merges without a single question, `updated` moves to today |
| 8j | `/learning-goal` | run it again with a **contradictory** brief | every contradiction listed and put to you; nothing written until answered |
| 8k | `/learning-goal` | make a required topic out-of-scope on a re-run | names the catalog subtopics and card files that would be affected |
| 9 | `/catalog` | `/catalog` | `catalog/topics.md` with topics, subtopics and references that resolve |
| 9-i | `/catalog` | a topic whose name contains a comma, named from `Parents:`, `Related:` and `Also covers:` | validates clean, and the name comes back as it was written — `/catalog` has been seen renaming the topic to get past the splitter and telling the user afterwards |
| 9-ii | `/catalog` | a subtopic whose only reference is a `content: sparse` document | it is reported, and the honest outcome is `Status: gap` rather than coverage built on a cover sheet |
| 9a | `/catalog` | `/catalog` with a `goal.md` present | the tree follows the goal's areas; uncovered topics are `Status: gap`, off-goal material `Status: out of scope` |
| 9b | `/catalog` | delete `goal.md`, `/catalog` again | no `Status:` lines at all, plus one line saying the catalog covers the material rather than the topic |
| 9c | `/catalog` | read the closing report | covered / gap / out-of-scope counts, and `/research-gaps` named when there is a gap |
| 9d | `/research-gaps` | `/research-gaps` with no network | reports which gaps stayed open, writes nothing, never invents a document |
| 10a | `/cards` | `/cards` over a subtopic with a kept figure | three kinds of card: one description card (picture on the back), one recognition card (picture on the front), and at least one text-only detail card |
| 10b | `/cards` | read the closing report | **run output (FR-025):** how many of the cards written carry a picture |
| 10c | `/cards` | look at the recognition card | the picture does not answer its own question — a chart with its title printed inside it tests reading, not recall |
| 9e | `/research-gaps` | delete a `research` source and its folder, `/catalog` | the subtopic goes back to `Status: gap` |
| 10 | `/catalog` | rename a subtopic by hand, `/catalog` again | your edit survives |
| 11 | `/cards` | `/cards Tides` | `cards/tides.yaml`, 3–8 cards per subtopic, `language:` set |
| 11a | `/cards` | `/cards` with gaps in the catalog | out-of-scope reported as a bare count; gaps as a warning naming each one |
| 11b | `/cards` | `/cards` naming an out-of-scope subtopic | generated anyway — the mark is a default, not a lock |
| 11c | `/cards` | `/cards` naming a **secondary** parent | generated once, and the file its cards went into is reported |
| 12 | `/cards` | `/cards Tides` again | new cards appended, no duplicated fronts |
| 12-i | `/cards` | ask for a card that emphasises a word | `*bold*`, never `**bold**` — the second typesets and prints flat, so only `check_project.py` can tell you |
| 12-ii | `/cards` | ask for a card with a line break followed by emphasis | `'... \\ *bold* ...'` with the space. Without it the backslash escapes the star and the build fails on "unclosed delimiter", which does not say so |
| 13 | `/cards` | ask for cards in another language | `language:` follows, umlauts and quotes come out right in the PDF |
| 13b | `/print` | look at the Greek and Cyrillic cards in the PDF | letters, not empty boxes — the engine does not warn when a glyph is missing |
| 14 | any | `python3 scripts/check_project.py .` | no errors |
| 15 | `/print` | `/print` | `output/cards.pdf`, page count = 2 × ⌈cards ÷ (columns × rows)⌉ — so ⌈cards ÷ 8⌉ sheets at `a7` and ⌈cards ÷ 16⌉ at `a8` |
| 15b | `/print` | `/print` on a deck declaring `grid: a8` | the same count at 16 up, with no flag given — the deck was believed |
| 15c | `/print` | `/print` over two decks declaring *different* grids | refused, naming both files and both values; no PDF written |
| 16 | `/print` | `/print only Signals` | only that topic in the PDF. (In the demo project the catalog topic is now *Signals, flags and the radio* — the comma is deliberate, see row 9-i; the card file's `topic:` is unchanged) |
| 17a | print | duplex, flip on long edge, 100 % scale | back of each card exactly behind its front |
| 17b | print | `--sides simplex`: print the first page range, turn the stack over on the long edge, re-feed, print the second — 100 % scale both times | back of each card exactly behind its front. Note whether your printer stacks face-up: if it does, the second range needs reverse page order from the print dialog |
| 18 | print | cut along the crop marks | cards of the size the grid promises, nothing clipped |
| 19 | print | `lernkarten build … --margin 0` on a borderless printer | full-bleed cards, no white edge |
| 20 | print | read the card id off a printed sheet at arm's length | the five characters are legible without leaning in — this is the whole point of setting it at 8 pt, and no test can judge it |
| 21 | `/cards` | **SC-007**: read an id off a printed card, name it in a Claude session (*"A45DK uses a word it never defines"*), let the session edit that card, then look again | the id is unchanged and still names the same card. This is the feature's reason for existing and it leaves nothing on disk, so per constitution XI it is named here rather than left implicit |
| 22 | `/print` | `lernkarten check` on a deck written before ids existed | exit 0, and **one** advisory line naming `--backfill` — not one line per card. The exit code is asserted by a test; the wording is a judgement and lives here |
| 23 | `/print` | photocopy a sheet | the id still reads in black only |
| 23a | `/print` | photocopy a sheet holding a **figure card** | the diagram still reads. This is the one thing no check can judge: our own graphics never let colour carry meaning alone, but a chart from someone else's PDF does, and a red-versus-green series goes grey on grey. If it does not survive, the card's text still has to say what the picture showed |
| 23b | `/print` | print a figure deck at `--grid a8` | the picture scales with the card and is still legible at sixteen up; `check_project.py` said so once, not once per card |
| 23a | `/print` | look at the footer band as a whole, at both grids | **FR-011a**: the id does not overpower `LERNKARTEN BY MHABEDANK` beside it. This, not the clip cap, is what bounds the id's size from above — every size up to 12 pt fits the box, and 11 pt still looks wrong. Measured support: at 8 pt the id is 52.80 pt against a 92.85 pt wordmark, so it stays the smaller of the two. Whether the band still reads as quiet is a judgement, which is why it is named here rather than asserted |

**Steps 17–19 are per grid, and both grids have to be walked.** Registration is
the thing that breaks when the column count changes: A8 has five vertical cut
lines to A7's three (counting the two outer trim lines, which the crop marks
also draw), and a 0.5 mm offset costs 1.0 % of a 50 mm card against 0.5 % of a
100 mm one. Run each of them twice:

| | `--grid a7` (the default) | `--grid a8` |
|---|---|---|
| 17 registration | 3 vertical, 5 horizontal cut lines | 5 vertical, 5 horizontal cut lines |
| 18 cut card | 100 × 71.75 mm (105 × 74.25 at `--margin 0`) | 71.75 × 50 mm (74.25 × 52.5 at `--margin 0`) |
| 19 borderless | drops into a DIN A7 box | drops into a DIN A8 box |

| 20 | print | at `--grid a8`, read the card at arm's length | **the type-size question**: A8 renders the whole card at ~0.70, so reading text is 7.67 pt against A7's 11 pt. `docs/design.md` sets the floor because Archivo "survives 11 pt on cheap paper"; this asks whether it survives 7.67. Include the Greek and Cyrillic cards — they fall back to New Computer Modern, whose apertures differ, and will fail first |

Steps 1–14 need a Claude session in the demo folder; 15–20 only need the
command. If a printer is not at hand, 16–18 can be judged from the PDF: hold
page 1 and page 2 against each other in a viewer at 100 %. Step 20 can be read
off the PDF too — clipping is visible on screen. Steps 17–19 at A8 cannot: the
cut is the point.

### The landing page

`tests/test_landing_page.py` reads `docs/index.html`; it never renders it. So it
can tell you a control exists and cannot tell you anybody would find it, and it
can tell you the note is no longer a child of the band and cannot tell you the
heading row got shorter. These three rows are the other half of that pair, and
they are named here rather than left to a reviewer's eye because that is the
condition constitution XI attaches to splitting a layout requirement.

Open `docs/index.html` straight off disk. No server, no build.

| # | At | Do this | Expect |
|---|---|---|---|
| 20 | 360 px wide | look at the bar, then open the menu | one line at rest; the control reads as a word, not a glyph; all four links behind it; `install` among them |
| 21 | 360 px wide | tap `install` | you land on the install section |
| 22 | 360 px wide | keyboard only: tab to the control, press Enter | it opens; the links take focus in order |
| 23 | 360 px, **JavaScript off** | repeat rows 20 and 21 | unchanged — the disclosure is CSS and markup, and nothing here needs script |
| 24 | above 760 px | widen | the bar is one line: wordmark, four inline links, github. No control, no menu |
| 25 | above 1080 px | sections `01`, `03`, `04` | the three heading rows are the same height, none taller than its heading needs; each note is a full-width block under its band |
| 26 | above 1080 px | the rules around each note | single everywhere — no doubled 4 px rule where band meets note, none missing |
| 27 | above 1080 px | section `04 install` | the note is still light on ink, and the rule under it is `--sand`, not the default dark |
| 28 | below 1080 px | all four sections | reading order unchanged: number, heading, note, content. Section `02` still has its toggle in the band |
| 29 | any width | `02 one card, one idea`: click **show the back**, then again | exactly one card at a time, and the label follows it |
| 30 | any width, **JavaScript off** | reload and look at `02` | both cards side by side, no button — the fallback the script's own comment describes |
| 31 | Chromium, Firefox, Safari | repeat rows 20, 23 and 25 in each | the same in all three. CI has no browser leg, so this is the only place the claim is checked |
| 32 | above 1080 px and at 360 px | the section notes, the anatomy list, the printing descriptions, the rules list and the three principles, after the type floor was raised to 15 px | nothing reflows into a heading row, no column loses its measure, and the three heading rows of row 25 are still equal. The size itself is asserted by `test_reading_text_is_never_below_the_screen_floor`; what a test cannot see is whether the extra line a paragraph gained landed somewhere ugly |
| 33 | github.com, an ordinary laptop window | the `README.md` opening block, rendered — then follow the link | the link to the live page is visible without scrolling past the intro paragraph; it reads as an invitation to *look*, not one more thing to read; and `https://mhabedank.github.io/lernkarten/` loads. `test_the_readme_points_a_newcomer_at_the_landing_page` asserts that the link is in the opening block and where in it — it cannot tell you whether anybody sees it, whether the wording invites, or whether the page is still there |

Row 33 is the odd one out. It is read on github.com rather than off disk, and
its subject is `README.md`, not the page. It sits here because what it checks
is whether a reader ever reaches the landing page at all.

Row 31 is the one that cannot be delegated to a machine here. The `<details>`
disclosure needs two user-agent behaviours overridden at once — older engines
hid the closed panel with `display: none`, current Chrome wraps it in
`::details-content` and hides that — and overriding only the panel's own
`display` renders nothing while reporting `flex` to devtools.

One thing is known and is not a regression: the card toggle still does not
explain itself (the open half of the issue that produced it).

### When the engine is the suspect

```bash
lernkarten engine --check          # which binary, which version, where from
LERNKARTEN_ENGINE=/path/to/typst lernkarten check cards/*.yaml
```

The failure table in [workflow.md](workflow.md#when-something-goes-wrong)
covers the errors you are likely to meet.

## Adding to the test data

Extend the demo project rather than inventing a second one — one body of test
data that every test shares is the point of it.

- A new **feature** of the build gets a case in `tests/test_e2e.py`.
- A new **failure mode** gets a file in
  `tests/fixtures/demo-project/broken/`, a row in that folder's README and a
  case that proves the error message names the culprit.
- A new **rule** about what the skills write gets a check in
  `scripts/check_project.py` and a test in `tests/test_check_project.py`.
- Card counts are asserted in the tests (`DEMO_CARD_COUNT`); adding cards means
  updating that number.
