#!/usr/bin/env python3
"""Pretends to be the Zotero 7 local API, backed by a JSON file.

The zotero half of /ingest needs a library to talk to. Installing Zotero and
filling it with invented papers is not something a test can do, so this serves
tests/fixtures/zotero/library.json in the shape the real local API returns:

    python3 scripts/zotero_stub.py                 # on the real port, 23119
    python3 scripts/zotero_stub.py --port 0        # any free port, printed

With it running, `/ingest kestrel-zotero` and every curl in the ingest skill
behave as they would with Zotero open — which is what makes that path testable
at all. Endpoints served (the ones the skill and zotero_ingest.py use):

    /api/users/0/collections
    /api/users/0/collections/<KEY>/items/top
    /api/users/0/items/top
    /api/users/0/items/<KEY>/children

Read-only, bound to localhost, and it serves invented data — but it does
occupy Zotero's port, so stop it before starting Zotero for real.
"""

import argparse
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "tests" / "fixtures" / "zotero" / "library.json"
PREFIX = "/api/users/0"


def load_library(path=LIBRARY):
    """(collections, items, storage folder) — storage sits next to the library."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    storage = Path(os.environ.get("ZOTERO_STORAGE") or path.parent / "storage").resolve()
    return data["collections"], data["items"], storage


def item_payload(item):
    """One item in the API's shape: the key outside, everything else in data."""
    data = {
        "itemType": item["itemType"],
        "title": item.get("title", ""),
        "creators": item.get("creators", []),
        "collections": item.get("collections", []),
    }
    if item.get("date"):
        data["date"] = item["date"]
    for field in ("contentType", "path", "filename"):  # top-level attachments
        if item.get(field) is not None and item["itemType"] == "attachment":
            data[field] = item[field]
    return {"key": item["key"], "version": 1, "library": {"type": "user", "id": 0}, "data": data}


def attachment_payload(parent_key, attachment, storage):
    """{STORAGE} in a path becomes the absolute storage folder — Zotero stores
    attachments that were never imported with an absolute path like that."""
    return {
        "key": attachment["key"],
        "version": 1,
        "data": {
            "itemType": "attachment",
            "parentItem": parent_key,
            "title": attachment.get("filename") or "attachment",
            "contentType": attachment.get("contentType", ""),
            "path": attachment.get("path", "").replace("{STORAGE}", str(storage)),
            "filename": attachment.get("filename", ""),
        },
    }


def route(path, collections, items, storage):
    """The response body for an API path, or None for 404."""
    if path == f"{PREFIX}/collections":
        return [
            {"key": c["key"], "version": 1, "data": {"key": c["key"], "name": c["name"]}}
            for c in collections
        ]
    if path in (f"{PREFIX}/items/top", f"{PREFIX}/items"):
        return [item_payload(i) for i in items]

    match = re.fullmatch(rf"{PREFIX}/collections/([^/]+)/items(?:/top)?", path)
    if match:
        key = match.group(1)
        return [item_payload(i) for i in items if key in i.get("collections", [])]

    match = re.fullmatch(rf"{PREFIX}/items/([^/]+)/children", path)
    if match:
        parent = next((i for i in items if i["key"] == match.group(1)), None)
        if parent is None:
            return []
        return [
            attachment_payload(parent["key"], a, storage) for a in parent.get("attachments", [])
        ]
    return None


def make_handler(collections, items, storage, quiet):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):  # noqa: N802 — the base class spells it this way
            body = route(urlparse(self.path).path, collections, items, storage)
            if body is None:
                self.send_error(404, "no such endpoint in the stub")
                return
            payload = json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Total-Results", str(len(body)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):
            if not quiet:
                sys.stderr.write(f"  {self.address_string()} {fmt % args}\n")

    return Handler


def serve(port=23119, library=LIBRARY, quiet=False):
    """Starts the stub. Returns the server — call serve_forever or shutdown."""
    collections, items, storage = load_library(library)
    return ThreadingHTTPServer(
        ("127.0.0.1", port), make_handler(collections, items, storage, quiet)
    )


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--port", type=int, default=23119, help="port to listen on (0 = any free one)")
    p.add_argument("--library", default=str(LIBRARY), help="the JSON library to serve")
    p.add_argument("--quiet", action="store_true", help="do not log requests")
    args = p.parse_args()

    try:
        server = serve(args.port, Path(args.library), args.quiet)
    except OSError as e:
        sys.exit(f"ERROR: cannot listen on port {args.port} ({e}) — is Zotero already running?")

    host, port = server.server_address
    print(f"Fake Zotero library on http://{host}:{port}{PREFIX} — Ctrl-C to stop")
    print(f"  storage: {Path(args.library).parent / 'storage'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
