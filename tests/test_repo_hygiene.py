"""Wacht darüber, dass das Repo themen-agnostisch bleibt.

Versioniert werden nur die Werkzeuge — Quellen, erfasste Texte, Katalog und
generierte Karten gehören dem Nutzer und bleiben lokal.
"""

import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent

# Alles unter diesen Pfaden ist Nutzerinhalt — bis auf die Ausnahmen.
GESPERRT = ("wissen/", "katalog/", "karten/", "output/")
ERLAUBT = {
    "wissen/.gitkeep",
    "katalog/.gitkeep",
    "karten/.gitkeep",
    "karten/beispiel.yaml",
}


def versionierte_dateien():
    ergebnis = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if ergebnis.returncode != 0:
        pytest.skip("kein Git-Repository")
    return ergebnis.stdout.split()


def test_kein_nutzerinhalt_im_repo():
    eindringlinge = [
        d for d in versionierte_dateien() if d.startswith(GESPERRT) and d not in ERLAUBT
    ]
    assert not eindringlinge, (
        "Nutzerinhalt darf nicht versioniert werden (siehe .gitignore und "
        f"CONTRIBUTING.md): {eindringlinge}"
    )


def test_kein_persoenliches_quellenregister_im_repo():
    assert "sources.yaml" not in versionierte_dateien(), (
        "sources.yaml enthält die Quellen des Nutzers — versioniert wird nur sources.example.yaml"
    )


def test_beispiel_quellenregister_ist_gueltig():
    daten = yaml.safe_load((ROOT / "sources.example.yaml").read_text(encoding="utf-8"))
    assert isinstance(daten, dict) and daten.get("quellen"), "Schlüssel 'quellen' fehlt"

    ids = set()
    pflichtfeld = {"ordner": "pfad", "pdf": "pfad", "webseite": "url", "zotero": None}
    for eintrag in daten["quellen"]:
        assert eintrag.get("id"), f"Eintrag ohne id: {eintrag}"
        assert eintrag["id"] not in ids, f"doppelte id: {eintrag['id']}"
        ids.add(eintrag["id"])
        assert eintrag.get("typ") in pflichtfeld, f"unbekannter Typ: {eintrag.get('typ')}"
        feld = pflichtfeld[eintrag["typ"]]
        assert feld is None or eintrag.get(feld), f"{eintrag['id']}: '{feld}' fehlt"


def test_gitignore_deckt_die_nutzerpfade_ab():
    zeilen = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    for muster in ("sources.yaml", "wissen/*", "katalog/*", "karten/*", "output/"):
        assert muster in zeilen, f".gitignore deckt {muster} nicht ab"
