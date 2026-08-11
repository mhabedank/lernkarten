---
name: quellen
description: >-
  Wissensquellen für die Lernkarten registrieren, anzeigen oder entfernen — Ordner, PDF-Sammlungen, Zotero-Sammlungen, Webseiten. Trigger: /quellen, "Quelle hinzufügen", "welche Quellen habe ich".
---

# /quellen — Wissensquellen verwalten

Verwaltet das Quellenregister `sources.yaml` im Projektstamm.

## Ablauf

1. Lies `sources.yaml`. Existiert die Datei nicht (frischer Klon — sie ist
   bewusst nicht versioniert), lege sie mit dem Kommentarkopf aus
   `sources.example.yaml` und einer leeren `quellen:`-Liste an; die
   Beispieleinträge der Vorlage NICHT übernehmen.
2. **Ohne Argumente**: Zeige alle registrierten Quellen als kompakte Tabelle
   (id, Typ, Pfad/URL/Sammlung, Notiz) und erkläre kurz, wie man Quellen
   hinzufügt. Prüfe dabei für jede Quelle, ob sie noch erreichbar ist
   (Ordner/Datei existiert?) und markiere tote Quellen.
3. **Mit Argumenten** (z. B. `/quellen ~/Documents/Uni/Statistik` oder
   „füge mein Zotero hinzu"): Quelle(n) anlegen — siehe unten. Danach die
   aktualisierte Liste zeigen.
4. **Entfernen** („entferne statistik-skript"): Eintrag aus `sources.yaml`
   löschen. Bereits erfasste Texte unter `wissen/<id>/` NICHT automatisch
   löschen — nur darauf hinweisen.

## Quelle anlegen

Bestimme den Typ selbst (Heuristik: existierender Ordner → `ordner`,
`.pdf`-Datei → `pdf`, URL → `webseite`, Stichwort „Zotero" → `zotero`) und
vergib eine sprechende kebab-case `id`. Frage nur nach, wenn wirklich
mehrdeutig.

Schema pro Eintrag (Kommentarkopf in `sources.yaml` zeigt Beispiele):

- `ordner`: `pfad` (Pflicht), `muster` (optional, glob), `notiz`
- `pdf`: `pfad` (Pflicht), `seiten` (optional, z. B. "1-150"), `notiz`
- `zotero`: `sammlung` (Name der Zotero-Sammlung; ohne Angabe = ganze Bibliothek), `notiz`
- `webseite`: `url` (Pflicht), `tiefe` (optional: 0 = nur diese Seite,
  1 = plus direkt verlinkte Unterseiten derselben Domain; Default 0), `notiz`

Validiere vor dem Schreiben: Pfade expandieren (`~`), Existenz prüfen; bei
Zotero prüfen, ob die lokale API antwortet
(`curl -s http://localhost:23119/api/users/0/collections`) — wenn nicht, den
Eintrag trotzdem anlegen und darauf hinweisen, dass Zotero beim `/erfassen`
laufen muss.

## Abschluss

Weise am Ende auf den nächsten Schritt hin: `/erfassen` liest die Quellen ein.
