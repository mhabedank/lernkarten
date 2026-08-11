# Lernkarten-Werkstatt — Projektanweisungen

Pipeline: `/quellen` → `/erfassen` → `/katalog` → `/karten` → `/drucken`.
Die Skills liegen unter `.claude/skills/`. Antworte auf Deutsch.

## Konventionen

- **Quellenregister**: `sources.yaml` ist die einzige Wahrheit über registrierte
  Quellen. Jede Quelle hat eine eindeutige `id` (kebab-case).
- **Wissensablage**: `wissen/<quellen-id>/<dokument>.md` — reiner Text/Markdown
  mit einem Frontmatter-Block (`quelle`, `datei`/`url`, `erfasst`).
- **Themenkatalog**: `katalog/themenkatalog.md` — Hierarchie aus Themen (`##`)
  und Unterthemen (`###`), je mit Kurzbeschreibung und Fundstellen
  (Verweise auf Dateien unter `wissen/`).
- **Karten**: `karten/<thema-slug>.yaml` mit dem Schema:

  ```yaml
  thema: "Anzeigename des Themas"
  karten:
    - unterthema: "Unterthema"
      vorne: "Frage oder Begriff"
      hinten: "Antwort oder Definition"
      quelle: "Kurzbeleg (optional)"
    - ...
  ```

  `vorne`/`hinten` sind **LaTeX-Quelltext**: Sonderzeichen (`%`, `&`, `_`, `#`)
  müssen escaped sein; Mathematik in `$...$` ist erlaubt; `\\` erzeugt einen
  Zeilenumbruch. Das Build-Script escaped NICHT selbst.
  Kein ASCII-`"` innerhalb der YAML-Strings (beendet den String!) —
  Anführungszeichen als ``\glqq ...\grqq{}`` bzw. `„...``` setzen.
- **PDF-Build**: `python3 scripts/build_pdf.py` (siehe `--help`). Ausgabe nach
  `output/`. Niemals LaTeX von Hand in `output/` editieren — immer über die
  YAML-Dateien gehen.

## Kartenstil

- Eine Karte = ein Fakt/Konzept. Keine Doppelfragen.
- Vorderseite kurz (max. ~2 Zeilen), Rückseite max. ~6 Zeilen — die Karte ist
  nur ca. 100 × 72 mm groß. Lieber zwei Karten als eine überfüllte.
- Aktive Abfrage formulieren („Was …?", „Warum …?", „Nenne …"), keine
  Ja/Nein-Fragen.
- Sprache der Karten = Sprache der Quelle, sofern der Nutzer nichts anderes sagt.

## Repo-Regeln

Dies ist ein öffentliches Open-Source-Repo — es enthält die Werkzeuge, nicht
das Wissen.

- **Nichts Eigenes einchecken**: `sources.yaml`, `wissen/`, `katalog/`,
  `karten/` (außer `beispiel.yaml`) und `output/` stehen in `.gitignore`.
  Niemals mit `git add -f` erzwingen — auch nicht „nur kurz".
- **Themen-agnostisch bleiben**: Beispiele und Doku zeigen das Format, nicht
  ein Fachgebiet. Keine fachspezifischen Inhalte in README, Skills oder Code.
- **`main` ist gesperrt**: Änderungen laufen über einen Branch und einen Pull
  Request. Direkte Pushes lehnt der Server ab, der `pre-push`-Hook ebenso.
- **Vor jedem PR** müssen diese vier Gates grün sein (dasselbe prüft die CI):

  ```bash
  ruff check . && ruff format --check .
  pytest
  python3 scripts/build_pdf.py --check karten/beispiel.yaml
  python3 scripts/check_docs.py
  ```
