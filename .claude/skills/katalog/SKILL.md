---
name: katalog
description: >-
  Aus dem erfassten Wissen unter wissen/ einen Themenkatalog mit Themen, Unterthemen und Fundstellen aufbauen oder aktualisieren. Trigger: /katalog, "Themenkatalog erstellen", "welche Themen gibt es".
---

# /katalog — Themenkatalog aufbauen

Verdichtet die Texte unter `wissen/` zu `katalog/themenkatalog.md`: eine
Themenhierarchie, die später als Auswahlmenü für `/karten` dient.

## Ablauf

1. `wissen/` leer → auf `/erfassen` verweisen, fertig.
2. Existiert schon ein Katalog: nur die Dokumente einarbeiten, die neuer sind
   als der Katalog (mtime) oder dort noch nicht als Fundstelle auftauchen —
   bestehende Themen erhalten, nicht neu würfeln.
3. Bei viel Material (> ~15 Dokumente oder > ~200k Wörter): pro Quelle einen
   Lese-Agenten fanouten, der Themen + Unterthemen + 1-Satz-Beschreibungen +
   Fundstellen zurückgibt; danach zusammenführen und deduplizieren. Sonst
   direkt lesen.
4. Katalog schreiben (Format unten), dem Nutzer die Themenübersicht als kurze
   Baumansicht zeigen und auf `/karten` verweisen.

## Format `katalog/themenkatalog.md`

```markdown
# Themenkatalog
Stand: 2026-08-10 · Quellen: <ids>

## <Thema>
Kurzbeschreibung (1–2 Sätze).

### <Unterthema>
Was dieses Unterthema umfasst; die wichtigsten Begriffe/Aussagen in 2–4
Stichpunkten (das ist die Arbeitsgrundlage für die Kartengenerierung).
Fundstellen: [slug](../wissen/<id>/<slug>.md), …
```

## Leitlinien

- Themen nach Inhalt schneiden, nicht nach Quelle — dieselbe Sache aus zwei
  Quellen ist EIN Thema mit zwei Fundstellen.
- 3–10 Themen mit je 2–8 Unterthemen anpeilen; feiner strukturieren statt
  Riesen-Unterthemen anzulegen.
- Die Stichpunkte je Unterthema sollen tragfähig genug sein, dass man daraus
  ohne erneutes Volltextlesen entscheiden kann, was kartenwürdig ist — aber
  die Fundstellen bleiben die Quelle der Wahrheit beim Kartenschreiben.
