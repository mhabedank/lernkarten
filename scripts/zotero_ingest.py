#!/usr/bin/env python3
"""Zotero ingest: PDF attachments of the local Zotero library -> knowledge/<id>/.

Uses the local Zotero API (Zotero 7, port 23119) for metadata and collection
membership, and reads the PDFs straight from ~/Zotero/storage. Text is pulled
out with pdftotext when that happens to be installed; otherwise the item is
written with its metadata and a `pending:` line for the Read tool to fill in.
Works incrementally: existing files are skipped unless the PDF source is newer.

Examples:
    python3 scripts/zotero_ingest.py --source-id zotero-library
    python3 scripts/zotero_ingest.py --source-id zotero-ml --collection "Machine Learning"

Writes into <project>/knowledge/<source-id>/ — the project being the current
folder unless --project says otherwise. Two environment variables exist for
testing against scripts/zotero_stub.py instead of a running Zotero:
ZOTERO_API and ZOTERO_STORAGE.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request
from pathlib import Path

API = os.environ.get("ZOTERO_API", "http://localhost:23119/api/users/0")
STORAGE = Path(os.environ.get("ZOTERO_STORAGE") or Path.home() / "Zotero" / "storage")


def api_get(path):
    with urllib.request.urlopen(f"{API}{path}", timeout=15) as r:
        return json.loads(r.read())


def all_pages(path, sep="?"):
    """Paginates over an API endpoint (limit/start)."""
    start, out = 0, []
    while True:
        batch = api_get(f"{path}{sep}limit=100&start={start}")
        out.extend(batch)
        if len(batch) < 100:
            return out
        start += 100


def slugify(text, maxlen=70):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:maxlen].rstrip("-") or "untitled"


def collection_names():
    """key -> name for every collection."""
    return {c["key"]: c["data"]["name"] for c in all_pages("/collections")}


def _attachment_path(key, data):
    """Local path of an attachment item (imported: storage/<key>/<filename>)."""
    if data.get("contentType") != "application/pdf":
        return None
    path = data.get("path") or ""
    if path.startswith("storage:"):
        candidate = STORAGE / key / path[len("storage:") :]
    elif path:
        candidate = Path(path).expanduser()
    elif data.get("filename"):
        candidate = STORAGE / key / data["filename"]
    else:
        return None
    return candidate if candidate.exists() else None


def find_pdf(item_key):
    """Returns the path of an item's first PDF attachment, or None."""
    try:
        children = api_get(f"/items/{item_key}/children")
    except Exception:
        return None
    for child in children:
        candidate = _attachment_path(child["key"], child.get("data", {}))
        if candidate:
            return candidate
    return None


def extract(pdf):
    """(text, pending) — text when it can be pulled out here, else a to-do."""
    if shutil.which("pdftotext") is None:
        # No extractor installed: leave the item for the Read tool to fill in.
        return None, True
    # Neither side may guess the encoding. `-enc UTF-8` stops pdftotext falling
    # back to the local charset, which cannot represent Greek or Cyrillic at all,
    # and the explicit decode stops Python reading its output through the ANSI
    # code page on Windows — where an em dash would become mojibake and land in
    # the knowledge store unremarked — or raising outright under a C locale.
    r = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", "-layout", str(pdf), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = r.stdout.strip()
    if r.returncode != 0:
        return None, True
    if len(text) < 200:  # no text layer — a scan, which the Read tool can see
        return None, True
    return text, False


def document_key(md):
    """The `zotero_key` a knowledge document records, or None if it has none.

    This is what decides "already ingested" — not the modification time. A
    timestamp cannot tell a re-run from two items that slugify to one name, and
    reading it as a re-run is how documents were lost (BUG-002).
    """
    try:
        with md.open(encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                # Stop at the closing fence, and do not read a whole extracted
                # PDF to find a key that is only ever in the frontmatter.
                if i > 40 or (i and line.rstrip() == "---"):
                    break
                if line.startswith("zotero_key:"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        return None
    return None


def target_for(target, title, key, written, stats):
    """Where this item goes, and whether it had to give way to another one.

    Zotero libraries routinely hold several items with one title — duplicates,
    two editions, a chapter beside its volume. They all slugify to the same
    name, so the name alone cannot identify a document and the item key is
    appended when it is already taken.
    """
    md = target / f"{slugify(title)}.md"
    owner = document_key(md) if md.exists() else None
    # `owner is None` on an existing file means it records no key at all — it
    # was written by hand or by a version older than this rule. Treat it as ours
    # rather than duplicating it; a file this run wrote is never in that state.
    if md in written or (owner is not None and owner != key):
        stats["collisions"] += 1
        return target / f"{slugify(title)}-{key.lower()}.md"
    return md


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--source-id", required=True, help="source id from sources.yaml (target knowledge/<id>/)"
    )
    p.add_argument(
        "--collection", help="only this Zotero collection (name); default: whole library"
    )
    p.add_argument(
        "--project",
        default=".",
        help="project folder to write into (default: the current one)",
    )
    args = p.parse_args()

    try:
        api_get("/collections?limit=1")
    except Exception as e:
        sys.exit(f"Zotero API unreachable ({e}) — is Zotero running with the local API enabled?")

    names = collection_names()
    if args.collection:
        keys = [k for k, n in names.items() if n.lower() == args.collection.lower()]
        if not keys:
            sys.exit(
                f"Collection '{args.collection}' not found. "
                f"Available: {sorted(set(names.values()))}"
            )
        items = all_pages(f"/collections/{keys[0]}/items/top", "?")
    else:
        items = all_pages("/items/top", "?")

    target = Path(args.project).expanduser() / "knowledge" / args.source_id
    target.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    stats = {"new": 0, "skipped": 0, "no_pdf": 0, "pending": 0, "collisions": 0}
    written = set()  # what this run has already put on disk, so a same-run
    # collision can never be mistaken for an incremental skip
    for it in items:
        d = it["data"]
        if d.get("itemType") == "note":
            continue
        title = d.get("title") or "(untitled)"
        if d.get("itemType") == "attachment":
            # Standalone top-level attachment (a PDF without a parent item)
            pdf = _attachment_path(it["key"], d)
        else:
            pdf = find_pdf(it["key"])
        if pdf is None:
            stats["no_pdf"] += 1
            continue
        md = target_for(target, title, it["key"], written, stats)
        if md.exists() and md.stat().st_mtime >= pdf.stat().st_mtime:
            stats["skipped"] += 1
            written.add(md)
            continue

        text, pending = extract(pdf)

        authors = ", ".join(
            " ".join(filter(None, [c.get("firstName"), c.get("lastName")])) or c.get("name", "")
            for c in d.get("creators", [])
        )
        collections = "; ".join(names.get(k, k) for k in d.get("collections", []))
        head = "\n".join(
            filter(
                None,
                [
                    "---",
                    f"source: {args.source_id}",
                    f'document: "{title.replace(chr(34), chr(39))}"',
                    f'path: "{pdf}"',
                    f'authors: "{authors}"' if authors else None,
                    f'year: "{d.get("date", "")[:4]}"' if d.get("date") else None,
                    f'collections: "{collections}"' if collections else None,
                    f"zotero_key: {it['key']}",
                    f'pending: "{pdf}"' if pending else None,
                    f"ingested: {today}",
                    "---",
                ],
            )
        )
        body = text if text else "<!-- read this PDF with the Read tool and replace this line -->"
        md.write_text(f"{head}\n\n{body}\n", encoding="utf-8")
        written.add(md)
        stats["pending" if pending else "new"] += 1
        print(f"OK: {title[:70]}")

    print(
        f"\nDone: {stats['new']} new, {stats['pending']} awaiting the Read tool, "
        f"{stats['skipped']} skipped, {stats['collisions']} collision(s) renamed, "
        f"{stats['no_pdf']} without a PDF"
    )
    # Name the destination. Every wrong one looked exactly like every right one
    # until this line existed, which is how an ingest into the plugin cache went
    # unnoticed (BUG-003).
    print(f"Written to: {target.resolve()}")


if __name__ == "__main__":
    main()
