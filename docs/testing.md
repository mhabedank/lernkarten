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
| `folder` (images) | an infographic as PNG, a photographed notice as JPEG | `make_testdata.py` (JPEG needs `sips`/`magick`) |
| `folder` (office) | a Word document | `make_testdata.py` |
| `web` | a four-page site with links, nav, a cookie banner, a login page and a path that answers 403 | `http.server` |
| `web` (internet) | `https://example.com/`, IANA's reserved example domain | a connection |
| `zotero` | an eight-item library: text PDFs, a scan, a note, a link, an absolute path, a second collection | `zotero_stub.py` |

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

`pytest` covers five levels:

| Module | Level | What it does |
|---|---|---|
| `tests/test_minyaml.py`, `tests/test_engine.py`, `tests/test_build_pdf.py` | unit | the functions, without a typesetter |
| `tests/test_testdata.py` | test data | the generator, and whether the scan really has no text layer |
| `tests/test_ingest_sources.py` | ingest | the web source over a local server, the zotero source over the stub |
| `tests/test_e2e.py` | end-to-end | runs `bin/lernkarten` as a subprocess and takes the PDF apart |
| `tests/test_check_project.py` | contract | the artifacts of the four Claude-driven steps |
| `tests/test_repo_hygiene.py` | repo | no user content, no committed binaries |

`tests/test_e2e.py` and `tests/test_testdata.py` need the typesetting engine.
Without one they skip, so a fresh checkout never downloads 30 MB unasked:

```bash
LERNKARTEN_E2E=1 pytest tests/test_e2e.py   # fetch the engine if it is missing
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
| 8c | `/ingest` | `/ingest island-images` | both images are picked up without a `pattern`; transcribed structurally, `type: infographic` in the frontmatter, no OCR word salad |
| 8d | `/ingest` | `/ingest office-notes` | the DOCX arrives as text |
| 8e | `/ingest` | `/ingest harbour-office` (server running) | three pages under `knowledge/harbour-office/`, nav bar and cookie banner dropped, `depth: 1` followed |
| 8f | `/ingest` | `/ingest harbour-office-members` | the login page is *not* ingested and nothing behind it is invented; no credentials are typed anywhere |
| 8g | `/ingest` | `/ingest kestrel-zotero` (stub running) | three documents, the scan among them flagged `pending:`; the Mainland item is left out |
| 9 | `/catalog` | `/catalog` | `catalog/topics.md` with topics, subtopics and references that resolve |
| 10 | `/catalog` | rename a subtopic by hand, `/catalog` again | your edit survives |
| 11 | `/cards` | `/cards Tides` | `cards/tides.yaml`, 3–8 cards per subtopic, `language:` set |
| 12 | `/cards` | `/cards Tides` again | new cards appended, no duplicated fronts |
| 13 | `/cards` | ask for cards in another language | `language:` follows, umlauts and quotes come out right in the PDF |
| 13b | `/print` | look at the Greek and Cyrillic cards in the PDF | letters, not empty boxes — the engine does not warn when a glyph is missing |
| 14 | any | `python3 scripts/check_project.py .` | no errors |
| 15 | `/print` | `/print` | `output/cards.pdf`, page count = 2 × ⌈cards ÷ 8⌉ |
| 16 | `/print` | `/print only Signals` | only that topic in the PDF |
| 17 | print | duplex, flip on long edge, 100 % scale | back of each card exactly behind its front |
| 18 | print | cut along the grey lines | 100 × 72 mm cards, nothing clipped |
| 19 | print | `lernkarten build … --margin 0` on a borderless printer | full A7 cards, no white edge |

Steps 1–14 need a Claude session in the demo folder; 15–19 only need the
command. If a printer is not at hand, 16–18 can be judged from the PDF: hold
page 1 and page 2 against each other in a viewer at 100 %.

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
