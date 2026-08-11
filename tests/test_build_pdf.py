"""Tests für scripts/build_pdf.py — Raster, YAML-Einlesen, Seitenaufbau.

Kompiliert bewusst kein LaTeX: der Probelauf mit pdflatex ist ein eigener
CI-Schritt (`build_pdf.py --check`), diese Tests laufen ohne TeX-Installation.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_pdf  # noqa: E402


def schreibe(tmp_path, name, inhalt):
    pfad = tmp_path / name
    pfad.write_text(inhalt, encoding="utf-8")
    return str(pfad)


# --- raster ---------------------------------------------------------------


def test_raster_teilt_a4_in_acht_karten():
    kb, kh, _ = build_pdf.raster(rand=0)
    assert (kb, kh) == pytest.approx((105.0, 74.25))
    assert kb * build_pdf.SPALTEN == pytest.approx(build_pdf.A4_BREITE)
    assert kh * build_pdf.REIHEN == pytest.approx(build_pdf.A4_HOEHE)
    assert build_pdf.SPALTEN * build_pdf.REIHEN == build_pdf.KARTEN_PRO_SEITE


def test_raster_zieht_rand_ab():
    kb, kh, _ = build_pdf.raster(rand=5)
    assert (kb, kh) == pytest.approx((100.0, 71.75))


def test_raster_ohne_rand_zeichnet_keine_aussenkanten():
    _, _, randlos = build_pdf.raster(rand=0)
    _, _, mit_rand = build_pdf.raster(rand=5)
    # 3 Spalten- und 5 Reihenlinien mit Rand, ohne Rand fallen je 2 Außenkanten weg
    assert len(mit_rand.splitlines()) == 8
    assert len(randlos.splitlines()) == 4


# --- lade_karten ----------------------------------------------------------

MINIMAL = """
thema: "Statistik"
karten:
  - unterthema: "Bayes"
    vorne: "Frage"
    hinten: "Antwort"
    quelle: "VL 3"
"""


def test_lade_karten_liest_felder(tmp_path):
    karten, fehler = build_pdf.lade_karten([schreibe(tmp_path, "a.yaml", MINIMAL)], [], [])
    assert fehler == []
    assert karten == [
        {
            "id": "a-1",
            "thema": "Statistik",
            "unterthema": "Bayes",
            "vorne": "Frage",
            "hinten": "Antwort",
            "quelle": "VL 3",
        }
    ]


def test_lade_karten_meldet_kaputtes_yaml(tmp_path):
    datei = schreibe(tmp_path, "kaputt.yaml", "thema: 'offen\nkarten: [")
    karten, fehler = build_pdf.lade_karten([datei], [], [])
    assert karten == []
    assert len(fehler) == 1 and "YAML-Fehler" in fehler[0]


def test_lade_karten_meldet_fehlende_pflichtfelder(tmp_path):
    datei = schreibe(tmp_path, "b.yaml", 'thema: "T"\nkarten:\n  - vorne: "nur vorne"\n')
    karten, fehler = build_pdf.lade_karten([datei], [], [])
    assert karten == []
    assert "'vorne' und 'hinten' sind Pflicht" in fehler[0]


def test_lade_karten_meldet_falsche_struktur(tmp_path):
    datei = schreibe(tmp_path, "c.yaml", "- eine\n- liste\n")
    _, fehler = build_pdf.lade_karten([datei], [], [])
    assert "erwartet Mapping" in fehler[0]


def test_lade_karten_faellt_auf_dateinamen_als_thema_zurueck(tmp_path):
    datei = schreibe(tmp_path, "ohne-thema.yaml", 'karten:\n  - vorne: "v"\n    hinten: "h"\n')
    karten, fehler = build_pdf.lade_karten([datei], [], [])
    assert fehler == []
    assert karten[0]["thema"] == "ohne-thema"
    assert karten[0]["quelle"] == ""


def test_filter_matcht_teilstring_ohne_gross_kleinschreibung(tmp_path):
    datei = schreibe(tmp_path, "a.yaml", MINIMAL)
    assert build_pdf.lade_karten([datei], ["statis"], [])[0]
    assert build_pdf.lade_karten([datei], ["Analysis"], [])[0] == []
    assert build_pdf.lade_karten([datei], [], ["BAYES"])[0]
    assert build_pdf.lade_karten([datei], [], ["Markov"])[0] == []


# --- erzeuge_inhalt -------------------------------------------------------


def karte(i):
    return {
        "id": f"k-{i}",
        "thema": "T",
        "unterthema": "U",
        "vorne": f"V{i}",
        "hinten": f"H{i}",
        "quelle": "",
    }


def test_erzeuge_inhalt_paart_vorder_und_rueckseiten():
    kb, kh, _ = build_pdf.raster(rand=5)
    for anzahl, erwartet in [(1, 2), (8, 2), (9, 4), (17, 6)]:
        inhalt = build_pdf.erzeuge_inhalt([karte(i) for i in range(anzahl)], 5, kb, kh)
        seiten = inhalt.split("\\newpage")
        assert len(seiten) == erwartet, f"{anzahl} Karten"


def test_rueckseite_ist_spaltengespiegelt():
    kb, kh, _ = build_pdf.raster(rand=0)
    vorne, hinten = build_pdf.erzeuge_inhalt([karte(0)], 0, kb, kh).split("\\newpage")
    # Karte 0 sitzt vorne in Spalte 0 (x=0), hinten in Spalte 1 (x=kb)
    assert "\\zelle{0.000}" in vorne
    assert f"\\zelle{{{kb:.3f}}}" in hinten
    assert "V0" in vorne and "H0" in hinten


def test_kopfzeile_verbindet_thema_und_unterthema():
    kb, kh, _ = build_pdf.raster(rand=5)
    inhalt = build_pdf.erzeuge_inhalt([karte(0)], 5, kb, kh)
    assert "T \\,\\textperiodcentered\\, U" in inhalt

    ohne = dict(karte(0), unterthema="")
    assert "\\textperiodcentered" not in build_pdf.erzeuge_inhalt([ohne], 5, kb, kh)


def test_jede_karte_traegt_einen_id_kommentar_fuer_die_fehlersuche():
    kb, kh, _ = build_pdf.raster(rand=5)
    inhalt = build_pdf.erzeuge_inhalt([karte(0)], 5, kb, kh)
    assert "% karte: k-0\n" in inhalt
    assert "% karte: k-0 (rueckseite)\n" in inhalt


# --- mitgelieferte Beispieldatei -----------------------------------------


def test_beispielkarten_erfuellen_das_schema():
    karten, fehler = build_pdf.lade_karten([str(ROOT / "karten" / "beispiel.yaml")], [], [])
    assert fehler == []
    assert karten, "karten/beispiel.yaml soll als Schema-Referenz Karten enthalten"
    for k in karten:
        assert '"' not in k["vorne"] + k["hinten"], (
            f"{k['id']}: ASCII-Anführungszeichen beenden den YAML-String"
        )
