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
| `raw/images/harbour-noticeboard.jpg` | JPEG | | a photo of a notice — the picture /ingest is meant to *reject* |
| `raw/images/office-mark.png` | PNG | | a logo, embedded in every page header of the handbook: offered once, as furniture rather than a figure |
| `raw/field-notes/diagrams/signal-flags.png` | PNG | | a picture `chart-notes.md` *links* to, relative to itself — the link has to be followed to be judged |
| `raw/web/harbour-plan.png` | PNG | | a picture the local web fixture shows with `<img>`: fetched, then judged |
| `raw/office/mail-boat-timetable.docx` | DOCX | | a Word document |
| `../zotero/storage/*/*.pdf` | PDF | | the attachments of the fake library |

`figures/island-images/tide-chart.svg` is the one picture that is **committed**
rather than generated: the demo cards print it, a missing picture on a card is
an error, and a fresh checkout has to pass `pytest` before
`scripts/make_testdata.py` has ever run. SVG is text, so the no-binaries rule is
satisfied by the same stroke.

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

## The deck-level checks

`scripts/check_project.py` asks four questions of the deck that no schema can
ask, and the fixture is written so that all of them pass — and so that the
interesting borderline cases are visible in the material rather than hidden in
a test.

**A-1, the anchor.** A subtopic whose catalog entry carries a `Term:` line has
to be named by at least one card in every card file that holds its cards.
`catalog/topics.md` carries **seven** such lines. What satisfies each of them:

- `Rhythm of the tide` is anchored in `cards/tides.yaml` by card `R7XQ4`, the
  one card this fixture gained for the check, and in `cards/palirroia-el.yaml`
  by the Greek alias `παλίρροια`.
- `Tidenrhythmus` and `Tidenhub` are anchored in `cards/gezeiten-de.yaml`, and
  `The six flags` in `cards/signals.yaml`, by cards that were **reworded** to
  name the concept they were already about. Anchoring costs a card only when no
  card is close enough to reword.
- Card `P1H4B` is deliberately left alone. Its `Nipptidenhub` and
  `Springtidenhub` contain `Tidenhub` as a substring, and they do **not**
  anchor it: matching is by token sequence, and the shipped fixture is where
  you can see that.
- The aliases are written in the inflected form the cards actually use —
  `нуля глубин`, not `нуль глубин`; `εύρος`. There is no stemming.
- `Settlements` and `Rules of use` carry **no** `Term:` line, on purpose. They
  are descriptions of a group of facts rather than named concepts, so there is
  nothing to anchor and A-1 stays silent about them.
- The three subtopics with no cards — `Relief and the crater`, `Storm surge and
  the Ashwind warning stages` and `Right of way in the Kestrel Deep` — carry
  none either. The line is inert without cards, and it is written when the
  cards arrive.

**A-2, the orphan.** Every item enumerated in a `#list(...)` back has to be
named by some other card in the same file. Card `Y4H26` in
`cards/geography.yaml` lists all five islands, and `Skarn` and `Bellhorn` used
to appear nowhere else in that file. Card `ZRKBA`'s back was reworded to say
where the mail boat takes the goods, which names both — again without adding a
card.

**E-1, the counted front.** A front that announces a count — "name the five
islands" — promises a back with five items, and a `#list(...)` back that
enumerates another number is an error. Card `Y4H26` in `cards/geography.yaml`
is the passing case: five announced, five enumerated. Two cards sit on the
borderline and are silent on purpose:

- `NKQK0` in `cards/signals.yaml` announces **two** counts — *"which two of the
  six flags"* — so no rule can say which number a back would answer to. Its
  back is prose anyway. A front like this has a different problem, and it is
  the double question rather than the count.
- `F3M2Q` in `cards/tides.yaml` says *"the six hours of the flood"* and answers
  in prose that itself counts (*"One twelfth, two, three, three, two, one"*).
  With no `#list(...)` there is no second number to compare, and whether that
  back should have been an enumeration is a judgement this check does not make.

**The enumeration tiers.** How long a `#list(...)` may be before its shape has
to change: 3–5 flat, 6–8 grouped, 9 or more split across cards. Card `V6TQ8` in
`cards/signals.yaml` is the grouped tier, and it is the only card here written
to demonstrate a rule rather than to teach the subject:

```yaml
back: '#list([*Traffic*: grey, blue], [*Help*: white, yellow], [*Closure*: red, black])'
```

It carries three checks at once, which is why one card was enough where six
looked necessary:

- **E-1 counts members, not items.** Six announced, six enumerated — in *three*
  `#list` items. Against the checker as it shipped in v0.9.0 this card reported
  `the front announces 'six' and the back enumerates 3`, an **error** produced by
  writing the card the way this project recommends.
- **A-2 descends into a group.** It checks `grey`, `blue`, `white`, `yellow`,
  `red` and `black`, never `Traffic`, `Help` or `Closure`. Before that change
  the head-term cut landed on the colon, and the result was not merely wrong but
  arbitrary: `*Help*` passed because `NKQK0`'s front happens to say "call for
  help", while `*Traffic*` and `*Closure*` failed.
- **Grouping cost one card, not seven.** A-2 asks whether *any other card* in
  the file names an item, and all six flag names were already there — `grey` and
  `blue` on `BS1M5`, `red` on `W9238`, `white` and `yellow` on `NKQK0`, `black`
  on `A7BSD`. No companion card was written for it.

**The 9+ tier is deliberately not here.** After you split a long enumeration you
have ordinary cards: an anchor card naming the groups is just a flat three-item
card, and nothing in the material marks it as the product of a split. Fixture
cards would demonstrate nothing a reader could check. E-3b's finding is a
failing case, so it lives in `tmp_path` with the others.

**All four failing cases live in `tmp_path`, not in `broken/`.**
`check_project.py` reads `<project>/cards/*.yaml` and
`<project>/catalog/topics.md` and nothing else, so it never looks inside
`broken/`; a card file placed there would not be checked at all. The red cases
are therefore built in temporary projects by `tests/test_check_project.py`, and
`broken/README.md` gains no row for any of them — that file documents how
`lernkarten check` and the build react, which is a different question.

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
