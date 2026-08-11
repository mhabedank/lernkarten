---
name: erfassen
description: >-
  Registrierte Wissensquellen einlesen (scrapen) — PDFs extrahieren, Ordner durchsuchen, Zotero-Sammlungen und Webseiten abrufen — und als Text unter wissen/ ablegen. Trigger: /erfassen, "Quellen einlesen", "scrape meine Quellen".
---

# /erfassen — Quellen einlesen

Extrahiert den Inhalt aller (oder der genannten) Quellen aus `sources.yaml`
nach `wissen/<quellen-id>/<dokument-slug>.md`.

## Ablauf

1. Lies `sources.yaml`. Keine Quellen registriert → auf `/quellen` verweisen, fertig.
2. Argument nennt eine oder mehrere `id`s → nur diese erfassen, sonst alle.
3. **Inkrementell arbeiten**: Existiert `wissen/<id>/<dokument>.md` bereits und
   die Quelldatei ist nicht neuer (mtime vergleichen), überspringen. Bei
   Webseiten: überspringen, wenn jünger als 7 Tage erfasst (Frontmatter
   `erfasst:`), außer der Nutzer sagt „neu erfassen".
4. Pro erfasstem Dokument eine Datei schreiben (Format unten). Bei vielen
   Dokumenten (>10) parallelisierbare Extraktion per Agent-Fanout erledigen.
5. Am Ende: Zusammenfassung (n neu, n übersprungen, n Fehler mit Grund) und
   Hinweis auf den nächsten Schritt `/katalog`.

## Extraktion pro Typ

- **ordner**: Dateien per `muster` (Default: `*.pdf`, `*.md`, `*.txt`, `*.html`,
  `*.docx`) rekursiv sammeln. PDFs → `pdftotext -layout`; DOCX → docx-Skill
  bzw. `textutil -convert txt` (macOS); MD/TXT direkt übernehmen.
- **pdf**: `pdftotext -layout` (mit `-f`/`-l` bei `seiten`-Angabe). Ist das
  Ergebnis fast leer (< 200 Zeichen bei > 3 Seiten), ist es ein Scan → OCR:
  `pdftoppm -r 300 -gray -png <pdf> <prefix>` und dann pro Seite
  `tesseract <png> <out> -l eng` (bzw. `-l deu`), Ergebnis konkatenieren und
  im Frontmatter `ocr: tesseract` vermerken. Erst wenn das scheitert, als
  Fehler ausweisen.
- **zotero (Massenerfassung)**: `python3 scripts/zotero_erfassen.py
  --quellen-id <id> [--sammlung "Name"]` — nutzt die lokale API, extrahiert
  PDF-Anhänge inkl. Metadaten-Frontmatter, arbeitet inkrementell.
- **zotero** (Zotero 7 muss laufen):
  1. Sammlungs-Key auflösen: `curl -s "http://localhost:23119/api/users/0/collections"`
     → Eintrag mit `data.name == sammlung`.
  2. Items holen: `.../collections/<KEY>/items?itemType=-attachment&limit=100`
     (paginieren über `start=`). Ohne `sammlung`: `.../items?...`.
  3. Pro Item die PDF-Anhänge finden (`.../items/<KEY>/children`, `contentType
     == application/pdf`) und den lokalen Pfad nutzen (`data.path`,
     `storage:`-Präfix → `~/Zotero/storage/<attachmentKey>/…`), dann wie
     **pdf** extrahieren. Titel/Autor/Jahr aus den Item-Metadaten ins
     Frontmatter übernehmen.
  4. API nicht erreichbar → abbrechen mit Hinweis, Zotero zu starten.
- **webseite**: Seite per WebFetch abrufen (Prompt: „Gib den vollständigen
  Inhalt als Markdown wieder, ohne Navigation/Boilerplate"). Bei `tiefe: 1`
  zusätzlich die im Inhalt verlinkten Unterseiten derselben Domain (max. 20).
  Liefert WebFetch 403 (Bot-Schutz, z. B. hustlebadger.com): auf die
  Browser-Tools ausweichen (`preview_start` mit der URL, dann `get_page_text`;
  Links über `read_page` einsammeln). Cookie-Banner: ablehnen. Paywall-Inhalte
  nicht umgehen — nur frei zugängliche Seiten erfassen.
- **webseite hinter Login** (`login: true` in `sources.yaml`): Der In-App-Browser
  ist nicht angemeldet. Die Claude-in-Chrome-Tools (`mcp__claude-in-chrome__*`)
  nutzen dagegen die bestehende Sitzung des Nutzers — vorher mit
  `list_connected_browsers` prüfen, ob ein Browser verbunden ist, sonst den
  Nutzer bitten, die Erweiterung zu verbinden. **Niemals selbst einloggen oder
  Zugangsdaten eintippen.** Nur abrufen, wozu der Account berechtigt.
- **bild** (Infografiken, Diagramme, Screenshots): NICHT per OCR verarbeiten —
  mehrspaltige Grafiken liefern damit Buchstabensalat. Stattdessen die Datei
  mit dem Read-Tool ansehen und den Inhalt strukturiert abtippen: Titel, alle
  Kästchen/Spalten in Lesereihenfolge, Achsen- und Pfeilbeschriftungen,
  Fußnoten. Im Frontmatter `typ: infografik` setzen.

## Dateiformat `wissen/<id>/<slug>.md`

```markdown
---
quelle: <quellen-id>
dokument: "Originaltitel oder Dateiname"
pfad: "/absoluter/pfad oder URL"
erfasst: 2026-08-10
---

<extrahierter Text>
```

Slug = Dateiname/Titel in kebab-case, ohne Endung. Text nicht kürzen oder
zusammenfassen — hier zählt Vollständigkeit; aufräumen darf man nur
offensichtlichen Extraktions-Müll (Kopf-/Fußzeilen, Seitenzahlen).
