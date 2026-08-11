# Mitmachen

Danke für dein Interesse. Fehlerberichte, Verbesserungen an den Skills, am
LaTeX-Layout oder an der Doku sind willkommen.

## Grundregel: kein Inhalt ins Repo

Das Repo ist themen-agnostisch — es enthält Werkzeuge, kein Wissen.
`sources.yaml`, `wissen/`, `katalog/`, `karten/` (außer `beispiel.yaml`) und
`output/` sind bewusst in `.gitignore`. Bitte heble das nicht mit `git add -f`
aus: eigene Quellen sind für andere unbrauchbar, und erfasste Fremdtexte
gehören urheberrechtlich nicht hierher.

Beispielkarten sollen ein Format zeigen, kein Fachgebiet. `karten/beispiel.yaml`
ist die einzige eingecheckte Kartendatei.

## Entwicklungssetup

```bash
git clone https://github.com/mhabedank/lernkarten.git
cd lernkarten
python3 -m pip install --user -r requirements-dev.txt
```

Systemseitig brauchst du dasselbe wie für die normale Nutzung: `pdflatex`,
`pdftotext`, Python ≥ 3.9 (siehe [README](README.md#voraussetzungen)).

## Vor dem Pull Request

Genau das, was auch die CI prüft:

```bash
ruff check .                                                # Lint
ruff format --check .                                       # Formatierung
pytest                                                      # Tests
python3 scripts/build_pdf.py --check karten/beispiel.yaml   # Kartenschema + LaTeX-Build
python3 scripts/check_docs.py                               # Skill-Frontmatter + Doku-Links
```

Alle müssen grün sein — die CI blockt den Merge sonst.

## Branch-Modell

`main` ist geschützt: **direkte Pushes sind serverseitig gesperrt.** Jede
Änderung läuft über einen Pull Request mit grüner CI.

```bash
git switch -c fix/kartenrand
# … ändern, committen …
git push -u origin fix/kartenrand
gh pr create
```

Installiere einmalig den lokalen Hook, dann fällt ein versehentlicher Push
auf `main` schon vor dem Netzwerkzugriff auf:

```bash
scripts/install-hooks.sh
```

## Commits

Kurze, sprechende Betreffzeile im Imperativ, gern mit Präfix
(`skill:`, `build:`, `docs:`, `ci:`), Fließtext auf Deutsch oder Englisch.

```
build: Seitenrand konfigurierbar machen
```

## Woran man sich orientiert

- **Skills** (`.claude/skills/*/SKILL.md`): knapp und handlungsorientiert.
  Ein Skill beschreibt einen Ablauf, keine Theorie. Neue Skills brauchen
  Frontmatter mit `name` und `description` inklusive Trigger-Formulierungen.
- **Python**: Standardbibliothek plus PyYAML, keine weiteren Laufzeit-Abhängig-
  keiten. Deutsche Funktions- und Variablennamen wie im Bestand, Docstrings
  auf Deutsch.
- **LaTeX**: Layoutänderungen ausschließlich in `templates/lernkarten.tex.in`,
  nie im generierten `.tex`.
- **Karten-Konventionen** (Schema, Escaping, Stil) stehen in
  [CLAUDE.md](CLAUDE.md) und gelten auch für Beiträge.

## Fehler melden

Bitte mit: Betriebssystem, Python- und TeX-Version, ausgeführtem Befehl,
vollständiger Fehlermeldung — und, wenn es um eine Karte geht, dem
betroffenen YAML-Ausschnitt (ohne dein privates Material, wenn es sich
vermeiden lässt).
