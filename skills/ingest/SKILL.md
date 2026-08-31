---
name: ingest
description: >-
  Read (scrape) the registered knowledge sources the flashcards are built from — extract PDFs, walk folders, fetch Zotero collections and web pages — and store them as text under knowledge/. Triggers: /ingest, "read my sources", "scrape my sources".
---

# /ingest — read the sources

Extracts the content of all (or the named) sources from `sources.yaml` into
`knowledge/<source-id>/<document-slug>.md`.

## Steps

1. Read `sources.yaml`. No sources registered → point at `/sources`, done.
2. If the argument names one or more `id`s → ingest only those, otherwise all.
3. **Work incrementally**: if `knowledge/<id>/<document>.md` already exists and
   the source file is not newer (compare mtime), skip it. For web pages: skip
   if ingested less than 7 days ago (frontmatter `ingested:`), unless the user
   says "re-ingest".
4. Write one file per ingested document (format below). With many documents
   (>10), do the parallelisable extraction via an agent fan-out.
5. At the end: a summary (n new, n skipped, n failed with reason) and a
   pointer to the next step, `/catalog`.

## Extraction per type

- **folder**: collect files recursively by `pattern` (default: `*.pdf`, `*.md`,
  `*.txt`, `*.html`, `*.docx`, `*.png`, `*.jpg`, `*.jpeg`). A markdown or HTML
  file may *link* pictures (`![…](diagrams/flow.png)`, `<img src=…>`): follow
  those links relative to the file and judge what they point at, the same way.
  A remote link is fetched with `figures.py fetch`. PDFs as below;
  DOCX → the docx skill or `textutil -convert txt` (macOS); MD/TXT taken as
  they are; images as under **image** below. A folder of photos or screenshots
  is therefore ingested without a `pattern` — say so in the summary, and ask
  before ingesting more than 20 images, since each one is looked at.
- **pdf**: pull the figures off the pages first —
  `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py extract <pdf> --project <project root>
  --source-id <id>` — then judge the candidates it lists. **Exit code 3 means no
  PDF renderer**: say which document lost its figures, and carry on; the text is
  unaffected. Then read it with the Read tool, in chunks via `pages` (20 pages per
  call). Nothing has to be installed for this. If `pdftotext` happens to be
  available, prefer it for documents over ~40 pages — `pdftotext -layout`
  (with `-f`/`-l` when `pages` is given) is far cheaper — and fall back to the
  Read tool when it is missing or returns nearly nothing. A PDF whose text
  layer is empty is a scan: the Read tool handles those, since it sees the
  pages as images.
- **zotero (bulk)**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/zotero_ingest.py --source-id <id>
  --project <project root> [--collection "Name"]` — uses the local API, extracts
  PDF attachments including metadata frontmatter, works incrementally. **Pass
  `--project` explicitly**: the script itself lives in the plugin cache, and
  leaving the destination to whatever the working directory happens to be is
  how an ingest ends up somewhere the user never looks. The summary names the
  absolute directory it wrote into — read it back. Without `pdftotext` it
  still writes one file per item with the metadata and `pending: <pdf path>`;
  fill those in with the Read tool and drop the `pending:` line. Items sharing a
  title get their Zotero key appended (`<slug>-<key>.md`) and are counted as
  collisions in the summary, so none of them is lost.
- **zotero** (Zotero 7 must be running):
  1. Resolve the collection key: `curl -s "http://localhost:23119/api/users/0/collections"`
     → the entry whose `data.name` matches the collection.
  2. Fetch items: `.../collections/<KEY>/items?itemType=-attachment&limit=100`
     (paginate via `start=`). Without a collection: `.../items?...`.
  3. Per item, find the PDF attachments (`.../items/<KEY>/children`,
     `contentType == application/pdf`) and use the local path (`data.path`,
     a `storage:` prefix → `~/Zotero/storage/<attachmentKey>/…`), then extract
     as for **pdf**. Carry title/author/year from the item metadata into the
     frontmatter.
  4. API unreachable → stop and ask the user to start Zotero.
- **web**: fetch the page with WebFetch (prompt: "return the full content as
  markdown, without navigation/boilerplate"). Pictures on the page are fetched
  with `figures.py fetch` and judged like any other; one that will not download
  is reported in the summary and the ingest continues. With `depth: 1`, also fetch the
  subpages of the same domain linked from the content (max. 20). If WebFetch
  returns 403 (bot protection): fall back to the browser tools
  (`preview_start` with the URL, then `get_page_text`; collect links via
  `read_page`). Cookie banners: decline. Do not work around paywalls — ingest
  freely accessible pages only.
- **web behind a login** (`login: true` in `sources.yaml`): the in-app browser
  is not signed in. The Claude-in-Chrome tools (`mcp__claude-in-chrome__*`)
  do use the user's existing session — check with `list_connected_browsers`
  whether a browser is connected, otherwise ask the user to connect the
  extension. **Never sign in yourself or type credentials.** Only fetch what
  the account is entitled to.
- **image** (infographics, diagrams, screenshots): do NOT run OCR — multi-column
  graphics come out as word salad. Instead look at the file with the Read tool
  and transcribe the content in a structured way: title, every box/column in
  reading order, axis and arrow labels, footnotes. Then **judge it** — see
  *Pictures worth showing* below.

## File format `knowledge/<id>/<slug>.md`

```markdown
---
source: <source-id>
document: "Original title or file name"
path: "/absolute/path or URL"
content: sparse          # optional — see below
characters: 68           # with `content: sparse`, how much text there was
ingested: 2026-08-10
figures:                 # optional — one entry per picture you looked at
  - at: 'page 3'
    visual: chart
    path: figures/<source-id>/tide-curve.png
    caption: 'What the picture shows, in one line'
  - at: 'page 1'
    visual: none
    why: 'a logo in every page header'
---

<extracted text>
```

Slug = file name/title in kebab-case, without the extension. Do not shorten or
summarise the text — completeness is what counts here; only obvious extraction
debris (headers/footers, page numbers) may be cleaned up.

**Three outcomes, not two.** A document is either extracted, or waiting for the
Read tool, or *thin*:

- Text came out → write it, no marker.
- **No text layer at all** — a scan → `pending: <path>`, and the Read tool sees
  the pages as images.
- **Text came out and there is barely any of it** — a cover sheet standing in
  for a book, an empty form template → write what there is and add
  `content: sparse` with the character count. Do **not** mark it `pending:`:
  the extraction is complete and a second pass has nothing to find. Leaving the
  two indistinguishable is what made `/catalog` guess whether a near-empty
  document was broken or real.

## Pictures worth showing

Some pictures teach something a transcription cannot: a chart, a flow chart, a
labelled diagram, a decision tree, a map. Most do not: a photograph, a
screenshot of prose, a logo, a divider, a stock illustration. **Decide once,
here**, and write the verdict down — `/cards` reads it and never opens the
picture again.

1. **Transcribe it either way.** The text is what `/catalog` and the detail
   cards read. Keeping a picture is in addition, never instead.
2. **Judge it.** Ask what a card would show. If the answer is "the words I just
   transcribed", the picture is not worth keeping.
3. **Keep it** by placing a copy:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py place <staged file>
   --project <project root> --source-id <id> --slug <kebab-case>`. It prints
   the path to write into `path:`. Never move or rename the original.
4. **Mark it in the body** at the point the picture sat, as ordinary markdown:
   `![Figure: <caption>](figures/<id>/<slug>.png)`. A figure named in the
   frontmatter and absent from the text is half an edit, and
   `check_project.py` says so.
5. **Record the rejections too**, with `visual: none` and a one-line `why:`.
   That is what stops the next run looking at the same picture to reach the
   same conclusion.

`visual:` is one of `diagram`, `chart`, `map`, or `none`. Anything but `none`
needs a `path:` and a `caption:`; `none` needs a `why:` and must not carry a
`path:`.

**A picture repeated across pages is furniture.** `figures.py extract` reports
it once with `repeated_on: <n>` — a mark in a running header, not a figure.
Keep it only if it genuinely is one.

**Count pictures towards the same threshold as images**: ask before looking at
more than 20 in one run, whether they came from a folder, a PDF, a web page or
a markdown link. Each one is looked at, and that is what costs.

**Fetch nothing the text rules would not fetch.** No paywall, no login the user
is not already entitled to, and no redirect off the source's own host —
`figures.py fetch` refuses that last one for you. It identifies itself as
`lernkarten` and never as a browser; a host that blocks the tool by name is a
host that has said no, and that answer stands.

**A URL does not tell you what it is.** Many carry no file name at all — this is
what a CDN serves for anything pasted out of Google Docs — so do not skip one
because it "looks like it is not an image". `fetch` decides from the response
and tells you which of three things went wrong: it is not a picture, the URL
names no file, or it is a real picture the typesetter cannot print.

**That last case is AVIF, mostly.** The web serves it constantly and the
typesetter cannot read it. `fetch` will download it; `place` will refuse it and
say what to convert. Convert it and place the result, or record the picture as
`visual: none` with that as the `why:` — either is honest, and inventing a
transcription for a picture you never kept is not.

**Say what happened.** The summary names every picture that could not be
fetched, opened or decoded, with the reason, and every document whose figures
were skipped because no PDF renderer was available. A broken picture never
stops an ingest.
