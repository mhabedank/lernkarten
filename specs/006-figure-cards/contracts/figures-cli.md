# Contract — `scripts/figures.py`, the command the `/ingest` skill calls

The one piece of this feature that needs code on the ingest side. It exists
because three jobs cannot be done by a prompt: rasterising a region of a PDF
page, downloading a picture from a URL, and applying the slug-and-dedup rule
that `check_project.py` later validates.

Called the way `zotero_ingest.py` already is — by the skill, with an explicit
`--project`, so an ingest never lands wherever the working directory happens to
point.

## `figures.py extract`

```bash
python3 scripts/figures.py extract <pdf> --project <root> --source-id <id> [--pages 1-4]
```

Pulls figure candidates off the pages into a staging directory and prints a
JSON manifest on stdout for the model to look at and judge:

```json
{
  "candidates": [
    {"at": "page 3", "file": ".figures-staging/handbook/p3-1.png", "width": 1240, "height": 700},
    {"at": "page 1", "file": ".figures-staging/handbook/p1-1.png", "width": 180, "height": 60,
     "repeated_on": 4}
  ],
  "skipped": [{"at": "page 2", "why": "smaller than the minimum"}]
}
```

| Rule | Behaviour |
|---|---|
| A candidate repeated on several pages is offered **once**, with `repeated_on` saying how many (FR-013) — a page header is furniture, not a figure | |
| A candidate below a minimum pixel size is skipped, and the skip is reported | |
| The staging directory is temporary; nothing enters `figures/` until `place` says so | |
| **`pypdfium2` unavailable** → exit code 3, one line on stderr naming the document, no traceback (FR-018) | |

Exit 3 is the degrade contract: the skill reports the document as "figures not
extracted" and carries on with the rest of the ingest.

## `figures.py fetch`

```bash
python3 scripts/figures.py fetch <url> --project <root> --source-id <id>
```

Downloads one picture with `urllib` — standard library, no dependency, every
platform. Same staging output. A fetch that fails prints the reason and exits
non-zero for that URL alone (FR-015).

Never follows a redirect off the source's host, never sends credentials, and
never fetches from a page the ingest rules already refuse (FR-016).

## `figures.py place`

```bash
python3 scripts/figures.py place <staged-file> --project <root> --source-id <id> --slug <slug>
```

Moves a judged-keeper into `figures/<source-id>/<slug>.<ext>` and prints the
project-relative path the frontmatter must carry.

| Rule | Behaviour |
|---|---|
| Slug is kebab-case and unique within the source | a collision gets `-2`, and the manifest says so |
| The extension is preserved and must be in the accepted set | otherwise refused by name |
| The same bytes placed twice under the same source return the existing path | no duplicate copy (FR-014 idempotence) |
| An existing destination is left alone unless `--force` | re-running `/ingest` rewrites nothing |

## Why one module and not three

Constitution V asks which existing module was considered first.
`zotero_ingest.py` is Zotero-specific, `build_pdf.py` owns the *output* PDF and
must not learn to read input PDFs, and `make_testdata.py` is a generator. What
these three verbs share is one subject — getting a picture out of a source and
into `figures/` — and one optional dependency, which is exactly the boundary a
module should have. It imports `deps` only, so it sits beside `yamlio` in the
graph and adds no cycle (constitution VI).
