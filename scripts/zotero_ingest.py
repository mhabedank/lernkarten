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
    r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True)
    text = r.stdout.strip()
    if r.returncode != 0:
        return None, True
    if len(text) < 200:  # no text layer — a scan, which the Read tool can see
        return None, True
    return text, False


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

    stats = {"new": 0, "skipped": 0, "no_pdf": 0, "pending": 0}
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
        md = target / f"{slugify(title)}.md"
        if md.exists() and md.stat().st_mtime >= pdf.stat().st_mtime:
            stats["skipped"] += 1
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
        stats["pending" if pending else "new"] += 1
        print(f"OK: {title[:70]}")

    print(
        f"\nDone: {stats['new']} new, {stats['pending']} awaiting the Read tool, "
        f"{stats['skipped']} skipped, {stats['no_pdf']} without a PDF"
    )


if __name__ == "__main__":
    main()
