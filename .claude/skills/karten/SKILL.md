---
name: karten
description: >-
  Lernkarten generieren — über den ganzen Themenkatalog oder gefiltert nach Thema/Unterthema. Schreibt YAML-Kartendateien unter karten/. Trigger: /karten, "Lernkarten erstellen", "Karten zu <Thema>".
---

# /karten — Lernkarten generieren

Erzeugt Lernkarten aus dem Themenkatalog und den Fundstellen unter `wissen/`,
als YAML-Dateien unter `karten/<thema-slug>.yaml`.

## Ablauf

1. Kein `katalog/themenkatalog.md` → auf `/katalog` verweisen, fertig.
2. **Auswahl bestimmen**: Argumente nennen Thema/Unterthema (unscharf matchen,
   z. B. „bayes" → Unterthema „Satz von Bayes"). Ohne Argumente: den ganzen
   Katalog abdecken. Bei Mehrdeutigkeit die Treffer nennen und kurz nachfragen.
3. **Pro Unterthema**: Die Fundstellen-Dateien lesen (nicht nur die
   Katalog-Stichpunkte!) und Karten schreiben. Richtwert 3–8 Karten pro
   Unterthema, je nach Stoffdichte. Bei > 5 Unterthemen die Generierung per
   Agent-Fanout parallelisieren (ein Agent pro Thema, Fundstellen-Pfade und
   Stilregeln in den Prompt geben).
4. **Bestehende Dateien mergen**: Existiert `karten/<thema-slug>.yaml`, neue
   Karten anhängen; Karten, deren `vorne` inhaltlich schon existiert, nicht
   duplizieren. Nur bei ausdrücklichem Wunsch („neu generieren") ersetzen.
5. Nach dem Schreiben validieren: `python3 scripts/build_pdf.py --check karten/*.yaml`
   (prüft Schema und kompiliert probehalber). Fehler sofort beheben.
6. Zusammenfassung: Anzahl Karten je Thema/Unterthema, dann auf `/drucken` verweisen.

## Kartenschema

```yaml
thema: "Anzeigename"
karten:
  - unterthema: "Unterthema"
    vorne: "Frage/Begriff"
    hinten: "Antwort"
    quelle: "Kurzbeleg"   # optional, klein auf der Rückseite
```

## Stilregeln (zusätzlich zu CLAUDE.md)

- `vorne`/`hinten` sind LaTeX: `%`, `&`, `_`, `#` escapen; Mathe in `$...$`;
  `\\` für Zeilenumbrüche; Aufzählungen als `\begin{itemize}...` nur auf der
  Rückseite und max. 4 Punkte.
- Kein ASCII-`"` in den YAML-Strings (beendet den String). Deutsche
  Anführungszeichen als `\glqq ...\grqq{}` oder `„...``` schreiben.
- Atomar: eine Karte prüft genau ein Faktum/Konzept. Definitionen, Formeln,
  Abgrenzungen („Unterschied X vs. Y") und Anwendungsfragen mischen.
- Keine Karte, deren Antwort im Katalog-Stichpunkt erschöpfend steht, aber in
  der Fundstelle nicht belegt ist — im Zweifel Fundstelle prüfen.
