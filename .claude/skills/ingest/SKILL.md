---
name: ingest
description: >-
  Read (scrape) the registered knowledge sources — extract PDFs, walk folders, fetch Zotero collections and web pages — and store them as text under knowledge/. Triggers: /ingest, "read my sources", "scrape my sources".
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
  `*.txt`, `*.html`, `*.docx`). PDFs → `pdftotext -layout`; DOCX → the docx
  skill or `textutil -convert txt` (macOS); MD/TXT taken as they are.
- **pdf**: `pdftotext -layout` (with `-f`/`-l` when `pages` is given). If the
  result is nearly empty (< 200 characters over > 3 pages) it is a scan → OCR:
  `pdftoppm -r 300 -gray -png <pdf> <prefix>` and then, per page,
  `tesseract <png> <out> -l eng` (or another language), concatenate the result
  and record `ocr: tesseract` in the frontmatter. Only report a failure once
  that fails too.
- **zotero (bulk)**: `python3 scripts/zotero_ingest.py --source-id <id>
  [--collection "Name"]` — uses the local API, extracts PDF attachments
  including metadata frontmatter, works incrementally.
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
