# Demo project — test data for the whole pipeline

A complete, miniature lernkarten project: raw material of every kind the
pipeline claims to read, the texts an ingest makes of it, a topic catalog and
card files. It is what the automated end-to-end tests run against, and what you
copy into a scratch folder when you want to try the five skills by hand.

```
raw/          material a user would point /sources at
sources.yaml  the source register /sources writes
knowledge/    the texts /ingest writes
catalog/      the topic catalog /catalog writes
cards/        the card files /cards writes — the input of /print
broken/       card files that must fail, one failure mode each
generators/   typst sources for the binary material (see below)
```

The fake Zotero library that goes with it lives one level up, in
[`../zotero`](../zotero/): a JSON library plus the PDF attachments,
served by `scripts/zotero_stub.py`.

## The raw material

Start here — this is what an ingest actually meets. Everything without a tick
in *versioned* is generated:

| Path | Type | Versioned | What it is there for |
|---|---|:-:|---|
| `raw/field-notes/kestrel-islands.md` | markdown | ✓ | ordinary text with a table |
| `raw/field-notes/tide-cycle.txt` | plain text | ✓ | numbers and rules, no markup |
| `raw/field-notes/signal-code.md` | markdown | ✓ | lists, which become `#list()` cards |
| `raw/field-notes/appendix/wind-log.txt` | plain text | ✓ | a subfolder: the walk has to recurse |
| `raw/field-notes/übersicht-inseln.md` | markdown | ✓ | umlauts in the file name — the slug must survive |
| `raw/field-notes/empty.md` | empty | ✓ | zero bytes: nothing to extract |
| `raw/field-notes/harbour-log.txt` | text, Windows-1252 | | not UTF-8 — a naive read trips over it |
| `raw/web/*.html` | HTML | ✓ | a four-page site with links, a nav bar and a cookie banner; the test server also refuses one path with 403 |
| `raw/handbook/kestrel-handbook.pdf` | PDF | | four pages with a text layer; `pages:` cuts it to two |
| `raw/handbook/tide-tables-scan.pdf` | PDF | | a scan: pixels only, nothing to extract |
| `raw/handbook/tide-almanac.pdf` | PDF | | 61 pages — long enough to need chunking |
| `raw/handbook/damaged.pdf` | PDF | | truncated: every extractor has to give up |
| `raw/images/tide-chart.png` | PNG | | an infographic — transcribe it, never OCR it |
| `raw/images/harbour-noticeboard.jpg` | JPEG | | a photo of a notice |
| `raw/office/mail-boat-timetable.docx` | DOCX | | a Word document |
| `../zotero/storage/*/*.pdf` | PDF | | the attachments of the fake library |

Build the generated half once:

```bash
python3 scripts/make_testdata.py
```

It renders the `generators/*.typ` sources with the typesetting engine the
project ships anyway, and writes the DOCX with nothing but `zipfile`. The JPEG
needs Pillow, since nothing in the standard library writes one; it is a
development dependency, so `pip install -r requirements-dev.txt` covers it. Only
if Pillow is genuinely absent is that job skipped with a `SKIPPED:` line rather
than an error, because no code branches on the image format. Binaries
have no place in a git history, so they are `.gitignore`d and rebuilt from
their text sources instead — which also means you can read and review every
byte of the test data as text.

## Where the content comes from

The subject — the Kestrel Islands, their tide cycle and their flag signals — is
**invented for this repository**. No island, harbour, tide table, paper or
signal code here refers to anything real, and nothing was copied from anywhere.
The content is part of the repository and covered by its
[licence](../../../LICENSE), so it can be shipped, forked and edited without
further questions. The one external address in `sources.yaml`,
`https://example.com/`, is IANA's reserved example domain and exists for
exactly this purpose; the local site under `raw/web` is served from your own
machine and must not be put online.

Keep it that way when you extend the fixture: invent, do not quote. Real
lecture notes, textbook pages, papers or website text belong in your own local
`knowledge/`, never here — see the repo rules in [CLAUDE.md](../../../CLAUDE.md).

## Using it

```bash
# build the binary material, then validate every artifact
python3 scripts/make_testdata.py
python3 scripts/check_project.py tests/fixtures/demo-project

# build the demo cards into a PDF
bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o output/demo.pdf

# copy it into a scratch folder and drive the skills by hand
python3 scripts/demo.py ~/lernkarten-demo --raw

# the two sources that need a server
python3 -m http.server 8137 --directory tests/fixtures/demo-project/raw/web
python3 scripts/zotero_stub.py
```

The manual checklist is in [docs/testing.md](../../../docs/testing.md).
