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
  `*.txt`, `*.html`, `*.docx`, `*.png`, `*.jpg`, `*.jpeg`). PDFs as below;
  DOCX → the docx skill or `textutil -convert txt` (macOS); MD/TXT taken as
  they are; images as under **image** below. A folder of photos or screenshots
  is therefore ingested without a `pattern` — say so in the summary, and ask
  before ingesting more than 20 images, since each one is looked at.
- **pdf**: read it with the Read tool, in chunks via `pages` (20 pages per
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
  markdown, without navigation/boilerplate"). With `depth: 1`, also fetch the
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
  reading order, axis and arrow labels, footnotes. Set `type: infographic` in
  the frontmatter.

## File format `knowledge/<id>/<slug>.md`

```markdown
---
source: <source-id>
document: "Original title or file name"
path: "/absolute/path or URL"
ingested: 2026-08-10
---

<extracted text>
```

Slug = file name/title in kebab-case, without the extension. Do not shorten or
summarise the text — completeness is what counts here; only obvious extraction
debris (headers/footers, page numbers) may be cleaned up.
