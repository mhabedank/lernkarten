#!/usr/bin/env python3
"""Zotero-Erfassung: PDF-Anhänge der lokalen Zotero-Bibliothek -> wissen/<id>/.

Nutzt die lokale Zotero-API (Zotero 7, Port 23119) für Metadaten und
Sammlungszuordnung, extrahiert die PDFs mit pdftotext direkt aus
~/Zotero/storage. Arbeitet inkrementell: existierende Dateien werden
übersprungen, wenn die PDF-Quelle nicht neuer ist.

Beispiele:
    python3 scripts/zotero_erfassen.py --quellen-id zotero-bibliothek
    python3 scripts/zotero_erfassen.py --quellen-id zotero-ml --sammlung "Machine Learning"
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
import unicodedata
import urllib.request
from pathlib import Path

API = "http://localhost:23119/api/users/0"
ROOT = Path(__file__).resolve().parent.parent
STORAGE = Path.home() / "Zotero" / "storage"


def api_get(pfad):
    with urllib.request.urlopen(f"{API}{pfad}", timeout=15) as r:
        return json.loads(r.read())


def alle_seiten(pfad, sep="?"):
    """Paginiert über einen API-Endpunkt (limit/start)."""
    start, out = 0, []
    while True:
        batch = api_get(f"{pfad}{sep}limit=100&start={start}")
        out.extend(batch)
        if len(batch) < 100:
            return out
        start += 100


def slugify(text, maxlen=70):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:maxlen].rstrip("-") or "ohne-titel"


def sammlungs_namen():
    """key -> Name aller Sammlungen."""
    return {c["key"]: c["data"]["name"] for c in alle_seiten("/collections")}


def _attachment_pfad(key, daten):
    """Lokaler Pfad eines Anhang-Items (imported: storage/<key>/<filename>)."""
    if daten.get("contentType") != "application/pdf":
        return None
    pfad = daten.get("path") or ""
    if pfad.startswith("storage:"):
        kandidat = STORAGE / key / pfad[len("storage:") :]
    elif pfad:
        kandidat = Path(pfad).expanduser()
    elif daten.get("filename"):
        kandidat = STORAGE / key / daten["filename"]
    else:
        return None
    return kandidat if kandidat.exists() else None


def finde_pdf(item_key):
    """Liefert den Pfad des ersten PDF-Anhangs eines Items oder None."""
    try:
        kinder = api_get(f"/items/{item_key}/children")
    except Exception:
        return None
    for k in kinder:
        kandidat = _attachment_pfad(k["key"], k.get("data", {}))
        if kandidat:
            return kandidat
    return None


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--quellen-id", required=True, help="Quellen-id aus sources.yaml (Zielordner wissen/<id>/)"
    )
    p.add_argument("--sammlung", help="Nur diese Zotero-Sammlung (Name); Default: ganze Bibliothek")
    args = p.parse_args()

    try:
        api_get("/collections?limit=1")
    except Exception as e:
        sys.exit(
            f"Zotero-API nicht erreichbar ({e}) — läuft Zotero und ist die lokale API aktiviert?"
        )

    namen = sammlungs_namen()
    if args.sammlung:
        keys = [k for k, n in namen.items() if n.lower() == args.sammlung.lower()]
        if not keys:
            sys.exit(
                f"Sammlung '{args.sammlung}' nicht gefunden. "
                f"Vorhanden: {sorted(set(namen.values()))}"
            )
        items = alle_seiten(f"/collections/{keys[0]}/items/top", "?")
    else:
        items = alle_seiten("/items/top", "?")

    ziel = ROOT / "wissen" / args.quellen_id
    ziel.mkdir(parents=True, exist_ok=True)
    heute = datetime.date.today().isoformat()

    stat = {"neu": 0, "uebersprungen": 0, "ohne_pdf": 0, "fehler": 0, "leer": 0}
    for it in items:
        d = it["data"]
        if d.get("itemType") == "note":
            continue
        titel = d.get("title") or "(ohne Titel)"
        if d.get("itemType") == "attachment":
            # Eigenständiger Anhang auf oberster Ebene (PDF ohne Eltern-Eintrag)
            pdf = _attachment_pfad(it["key"], d)
        else:
            pdf = finde_pdf(it["key"])
        if pdf is None:
            stat["ohne_pdf"] += 1
            continue
        md = ziel / f"{slugify(titel)}.md"
        if md.exists() and md.stat().st_mtime >= pdf.stat().st_mtime:
            stat["uebersprungen"] += 1
            continue

        r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True)
        text = r.stdout.strip()
        if r.returncode != 0 or len(text) < 200:
            stat["leer" if r.returncode == 0 else "fehler"] += 1
            print(
                f"WARN {'leer' if r.returncode == 0 else 'fehler'}: {titel} ({pdf.name})",
                file=sys.stderr,
            )
            if r.returncode != 0:
                continue  # leere (vermutlich gescannte) PDFs trotzdem nicht schreiben
            continue

        autoren = ", ".join(
            " ".join(filter(None, [c.get("firstName"), c.get("lastName")])) or c.get("name", "")
            for c in d.get("creators", [])
        )
        koll = "; ".join(namen.get(k, k) for k in d.get("collections", []))
        kopf = "\n".join(
            filter(
                None,
                [
                    "---",
                    f"quelle: {args.quellen_id}",
                    f'dokument: "{titel.replace(chr(34), chr(39))}"',
                    f'pfad: "{pdf}"',
                    f'autoren: "{autoren}"' if autoren else None,
                    f'jahr: "{d.get("date", "")[:4]}"' if d.get("date") else None,
                    f'sammlungen: "{koll}"' if koll else None,
                    f"zotero_key: {it['key']}",
                    f"erfasst: {heute}",
                    "---",
                ],
            )
        )
        md.write_text(f"{kopf}\n\n{text}\n", encoding="utf-8")
        stat["neu"] += 1
        print(f"OK: {titel[:70]}")

    print(
        f"\nFertig: {stat['neu']} neu, {stat['uebersprungen']} übersprungen, "
        f"{stat['ohne_pdf']} ohne PDF, {stat['leer']} leer (Scan?), {stat['fehler']} Fehler"
    )


if __name__ == "__main__":
    main()
