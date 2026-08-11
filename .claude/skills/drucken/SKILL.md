---
name: drucken
description: >-
  Lernkarten-YAML via LaTeX-Template zu einem druckfertigen PDF kompilieren (A4, 8 Karten pro Seite, Vorder-/Rückseiten für Duplexdruck). Trigger: /drucken, "PDF erzeugen", "Karten drucken".
---

# /drucken — PDF bauen

Kompiliert die YAML-Kartendateien zu einem druck- und schneidfertigen PDF.

## Ablauf

1. `karten/` leer → auf `/karten` verweisen, fertig.
2. Auswahl bestimmen: Argumente nennen Themen (Dateien) oder Unterthemen;
   ohne Argumente alle `karten/*.yaml`.
3. Build ausführen:

   ```bash
   python3 scripts/build_pdf.py karten/*.yaml -o output/lernkarten.pdf
   ```

   Filter: `--thema "Name"` (mehrfach möglich), `--unterthema "Name"`.
   Layout: `--rand <mm>` — Seitenrand für Drucker mit nicht bedruckbarem
   Randbereich (Default 5 mm; `--rand 0` = randlos, volle A7-Karten).
4. Bei LaTeX-Fehlern: Das Script nennt die betroffene Karte (Thema + Index).
   Fehler in der YAML-Datei beheben (meist unescapte Sonderzeichen), neu bauen.
5. Ergebnis prüfen: Seitenzahl muss gerade sein (Vorder-/Rückseiten-Paare).
   PDF dem Nutzer mit SendUserFile schicken und die Druckanleitung nennen:
   **Duplex, über lange Kante spiegeln, 100 % Skalierung (nicht „anpassen")**,
   dann entlang der grauen Linien schneiden.

## Hinweise

- Karten, die zu lang für die Kartenfläche sind, meldet der Build als Warnung
  („Overfull"); solche Karten kürzen oder aufteilen statt die Schrift zu
  verkleinern.
- Das Template liegt in `templates/lernkarten.tex.in` (Python-Template-Syntax,
  `$platzhalter`). Layoutänderungen dort, nicht im generierten `.tex` unter
  `output/`.
