#!/usr/bin/env python3
"""Doku-Gate: prüft Skill-Frontmatter und die internen Links der Dokumentation.

Läuft ohne Argumente über das ganze Repo und ist als CI-Schritt gedacht:

    python3 scripts/check_docs.py

Geprüft wird:
  * jeder Skill unter .claude/skills/<name>/SKILL.md hat ein YAML-Frontmatter
    mit 'name' (= Ordnername) und 'description' (mit Trigger-Hinweis),
  * jeder relative Markdown-Link in den Doku-Dateien zeigt auf eine
    existierende Datei,
  * die Pflichtdateien eines Open-Source-Repos sind vorhanden.
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
PFLICHTDATEIEN = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CLAUDE.md",
    "sources.example.yaml",
    "docs/nutzungsflow.md",
    ".github/workflows/ci.yml",
]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CODEBLOCK = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def pruefe_pflichtdateien(fehler):
    for name in PFLICHTDATEIEN:
        if not (ROOT / name).exists():
            fehler.append(f"Pflichtdatei fehlt: {name}")


def pruefe_skills(fehler):
    ordner = sorted(p for p in SKILLS.iterdir() if p.is_dir()) if SKILLS.is_dir() else []
    if not ordner:
        fehler.append(f"keine Skills unter {SKILLS.relative_to(ROOT)} gefunden")
        return

    for verzeichnis in ordner:
        datei = verzeichnis / "SKILL.md"
        if not datei.exists():
            fehler.append(f"{verzeichnis.relative_to(ROOT)}: SKILL.md fehlt")
            continue

        text = datei.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            fehler.append(f"{datei.relative_to(ROOT)}: kein YAML-Frontmatter")
            continue

        rohdaten = text.split("---\n", 2)[1]
        try:
            kopf = yaml.safe_load(rohdaten) or {}
        except yaml.YAMLError as e:
            fehler.append(f"{datei.relative_to(ROOT)}: Frontmatter ist kein gültiges YAML: {e}")
            continue

        if kopf.get("name") != verzeichnis.name:
            fehler.append(
                f"{datei.relative_to(ROOT)}: 'name: {kopf.get('name')}' "
                f"passt nicht zum Ordner '{verzeichnis.name}'"
            )
        beschreibung = str(kopf.get("description") or "")
        if len(beschreibung) < 20:
            fehler.append(f"{datei.relative_to(ROOT)}: 'description' fehlt oder ist zu knapp")
        elif "Trigger" not in beschreibung:
            fehler.append(
                f"{datei.relative_to(ROOT)}: 'description' nennt keine Trigger — "
                "ohne sie findet Claude Code den Skill schlechter"
            )


def markdown_dateien():
    dateien = sorted(ROOT.glob("*.md"))
    dateien += sorted((ROOT / "docs").glob("*.md"))
    dateien += sorted(SKILLS.glob("*/SKILL.md"))
    return dateien


def pruefe_links(fehler):
    for datei in markdown_dateien():
        # Codeblöcke zeigen Formatbeispiele mit Platzhalter-Pfaden — nicht prüfen
        text = CODEBLOCK.sub("", datei.read_text(encoding="utf-8"))
        for ziel in LINK.findall(text):
            if ziel.startswith(("http://", "https://", "mailto:", "#")):
                continue
            pfad = (datei.parent / ziel.split("#", 1)[0]).resolve()
            if not pfad.exists():
                fehler.append(f"{datei.relative_to(ROOT)}: toter Link -> {ziel}")


def main():
    fehler = []
    pruefe_pflichtdateien(fehler)
    pruefe_skills(fehler)
    pruefe_links(fehler)

    for f in fehler:
        print(f"FEHLER: {f}", file=sys.stderr)
    if fehler:
        sys.exit(1)

    anzahl = len(list(SKILLS.glob("*/SKILL.md")))
    print(f"OK: {anzahl} Skills, Doku-Links und Pflichtdateien in Ordnung.")


if __name__ == "__main__":
    main()
