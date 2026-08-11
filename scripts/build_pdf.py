#!/usr/bin/env python3
"""Lernkarten-Build: YAML-Kartendateien -> LaTeX -> druckfertiges PDF.

A4 mit 8 Karten (105 x 74.25 mm) pro Seite. Vorderseiten und Rückseiten
liegen auf aufeinanderfolgenden Seiten, Rückseiten spaltengespiegelt —
Duplexdruck "über lange Kante spiegeln".

Beispiele:
    python3 scripts/build_pdf.py karten/*.yaml -o output/lernkarten.pdf
    python3 scripts/build_pdf.py karten/*.yaml --thema "Statistik" --unterthema "Bayes"
    python3 scripts/build_pdf.py --check karten/*.yaml
"""

import argparse
import re
import shutil
import string
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "lernkarten.tex.in"
KARTEN_PRO_SEITE = 8  # 2 Spalten x 4 Reihen
SPALTEN, REIHEN = 2, 4
A4_BREITE, A4_HOEHE = 210.0, 297.0  # mm


def raster(rand):
    """Kartenmaße und Schnittlinien für den gegebenen Seitenrand (mm)."""
    kb = (A4_BREITE - 2 * rand) / SPALTEN
    kh = (A4_HOEHE - 2 * rand) / REIHEN
    linien = []
    x_werte = [rand + i * kb for i in range(SPALTEN + 1)]
    y_werte = [rand + j * kh for j in range(REIHEN + 1)]
    if rand == 0:  # Außenkanten sind Papierkanten — keine Linien nötig
        x_werte, y_werte = x_werte[1:-1], y_werte[1:-1]
    for x in x_werte:
        linien.append(
            f"  \\draw[gray!45, line width=0.1pt] ({x:.3f}mm,0mm) -- ({x:.3f}mm,-{A4_HOEHE}mm);"
        )
    for y in y_werte:
        linien.append(
            f"  \\draw[gray!45, line width=0.1pt] (0mm,-{y:.3f}mm) -- ({A4_BREITE}mm,-{y:.3f}mm);"
        )
    return kb, kh, "\n".join(linien)


def lade_karten(dateien, themen_filter, unterthemen_filter):
    """Liest die YAML-Dateien und gibt eine flache, gefilterte Kartenliste zurück."""
    karten = []
    fehler = []
    for datei in dateien:
        pfad = Path(datei)
        try:
            daten = yaml.safe_load(pfad.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            fehler.append(f"{pfad}: YAML-Fehler: {e}")
            continue
        if not isinstance(daten, dict) or "karten" not in daten:
            fehler.append(f"{pfad}: erwartet Mapping mit Schlüsseln 'thema' und 'karten'")
            continue
        thema = str(daten.get("thema") or pfad.stem)
        if themen_filter and not any(f.lower() in thema.lower() for f in themen_filter):
            continue
        for i, k in enumerate(daten["karten"] or [], start=1):
            if not isinstance(k, dict) or "vorne" not in k or "hinten" not in k:
                fehler.append(f"{pfad}: Karte {i}: 'vorne' und 'hinten' sind Pflicht")
                continue
            unterthema = str(k.get("unterthema") or "")
            if unterthemen_filter and not any(
                f.lower() in unterthema.lower() for f in unterthemen_filter
            ):
                continue
            karten.append(
                {
                    "id": f"{pfad.stem}-{i}",
                    "thema": thema,
                    "unterthema": unterthema,
                    "vorne": str(k["vorne"]),
                    "hinten": str(k["hinten"]),
                    "quelle": str(k.get("quelle") or ""),
                }
            )
    return karten, fehler


def _seite(zellen, rand, kb, kh):
    """Formt eine Liste von (spalte, reihe, id, latex)-Zellen zu einer TikZ-Seite."""
    koerper = "\n".join(
        f"% karte: {kid}\n\\zelle{{{rand + spalte * kb:.3f}}}{{{rand + reihe * kh:.3f}}}{{{latex}}}"
        for spalte, reihe, kid, latex in zellen
    )
    return (
        "\\begin{tikzpicture}[remember picture, overlay, "
        "shift={(current page.north west)}]\n"
        "\\schnittlinien\n" + koerper + "\n\\end{tikzpicture}\\null"
    )


def erzeuge_inhalt(karten, rand, kb, kh):
    """Erzeugt den LaTeX-Body: pro 8er-Block eine Vorder- und eine Rückseite."""
    seiten = []
    for start in range(0, len(karten), KARTEN_PRO_SEITE):
        block = karten[start : start + KARTEN_PRO_SEITE]

        vorne, hinten = [], []
        for pos, k in enumerate(block):
            spalte, reihe = pos % SPALTEN, pos // SPALTEN
            kopf = k["thema"] + (
                " \\,\\textperiodcentered\\, " + k["unterthema"] if k["unterthema"] else ""
            )
            vorne.append(
                (spalte, reihe, k["id"], f"\\karteV{{{kopf}}}{{{k['vorne']}}}{{{k['id']}}}")
            )
            # Rückseite spaltengespiegelt für Duplex über die lange Kante
            hinten.append(
                (
                    1 - spalte,
                    reihe,
                    k["id"] + " (rueckseite)",
                    f"\\karteR{{{k['hinten']}}}{{{k['quelle']}}}{{{k['id']}}}",
                )
            )

        seiten.append(_seite(vorne, rand, kb, kh))
        seiten.append(_seite(hinten, rand, kb, kh))
    return "\n\\newpage\n".join(seiten)


def kompiliere(tex_quelle, ziel_pdf, arbeitsdir):
    tex_datei = arbeitsdir / "lernkarten.tex"
    tex_datei.write_text(tex_quelle, encoding="utf-8")
    # Zwei Läufe: TikZ' "remember picture" kennt die Seitenkoordinaten erst im zweiten
    for _ in range(2):
        ergebnis = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_datei.name],
            cwd=arbeitsdir,
            capture_output=True,
            text=True,
        )
        if ergebnis.returncode != 0:
            break
    log = (
        (arbeitsdir / "lernkarten.log").read_text(encoding="utf-8", errors="replace")
        if (arbeitsdir / "lernkarten.log").exists()
        else ergebnis.stdout
    )

    if ergebnis.returncode != 0:
        melde_fehler(log, tex_datei)
        return False

    for zeile in log.splitlines():
        if zeile.startswith("Overfull"):
            print(f"WARNUNG: {zeile.strip()} — Karte kürzen oder aufteilen.", file=sys.stderr)

    if ziel_pdf is not None:
        ziel_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(arbeitsdir / "lernkarten.pdf", ziel_pdf)
    return True


def melde_fehler(log, tex_datei):
    """Ordnet den LaTeX-Fehler der betroffenen Karte zu (via %-Kommentar)."""
    print("LaTeX-Fehler:", file=sys.stderr)
    treffer = re.search(r"^! (.+)$", log, re.MULTILINE)
    if treffer:
        print(f"  {treffer.group(1)}", file=sys.stderr)
    zeilen_nr = re.search(r"^l\.(\d+)", log, re.MULTILINE)
    if zeilen_nr:
        nr = int(zeilen_nr.group(1))
        quell_zeilen = tex_datei.read_text(encoding="utf-8").splitlines()
        for z in reversed(quell_zeilen[: min(nr, len(quell_zeilen))]):
            m = re.match(r"% karte: (\S+)", z.strip())
            if m:
                print(f"  Betroffene Karte: {m.group(1)}", file=sys.stderr)
                break
    print(f"  Volles Log: {tex_datei.with_suffix('.log')}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("dateien", nargs="+", help="YAML-Kartendateien (karten/*.yaml)")
    p.add_argument("-o", "--output", default="output/lernkarten.pdf", help="Ziel-PDF")
    p.add_argument(
        "--thema",
        action="append",
        default=[],
        help="Nur Themen, die diesen Text enthalten (mehrfach möglich)",
    )
    p.add_argument(
        "--unterthema",
        action="append",
        default=[],
        help="Nur Unterthemen, die diesen Text enthalten",
    )
    p.add_argument(
        "--check", action="store_true", help="Nur validieren und Probekompilat, kein PDF schreiben"
    )
    p.add_argument(
        "--rand",
        type=float,
        default=5.0,
        metavar="MM",
        help="Seitenrand in mm für Drucker mit nicht bedruckbarem Rand (Default: 5, 0 = randlos)",
    )
    args = p.parse_args()

    if not 0 <= args.rand <= 20:
        p.error("--rand muss zwischen 0 und 20 mm liegen")

    karten, fehler = lade_karten(args.dateien, args.thema, args.unterthema)
    for f in fehler:
        print(f"FEHLER: {f}", file=sys.stderr)
    if fehler and args.check:
        sys.exit(1)
    if not karten:
        print("Keine Karten nach Filterung übrig — nichts zu tun.", file=sys.stderr)
        sys.exit(1)

    kb, kh, schnittlinien = raster(args.rand)
    vorlage = string.Template(TEMPLATE.read_text(encoding="utf-8"))
    tex = vorlage.substitute(
        kb=f"{kb:.3f}",
        kh=f"{kh:.3f}",
        rand=f"{args.rand:g}",
        schnittlinien=schnittlinien,
        inhalt=erzeuge_inhalt(karten, args.rand, kb, kh),
    )

    ziel = None if args.check else Path(args.output)
    with tempfile.TemporaryDirectory() as td:
        ok = kompiliere(tex, ziel, Path(td))
    if not ok:
        sys.exit(1)

    seiten = 2 * ((len(karten) + KARTEN_PRO_SEITE - 1) // KARTEN_PRO_SEITE)
    if args.check:
        print(f"OK: {len(karten)} Karten valide, Probekompilat erfolgreich ({seiten} Seiten).")
    else:
        print(
            f"OK: {len(karten)} Karten -> {ziel} "
            f"({seiten} Seiten, Duplex über lange Kante spiegeln)."
        )


if __name__ == "__main__":
    main()
