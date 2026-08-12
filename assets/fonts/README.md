# Fonts

The three faces of the visual system, shipped with the repo so a card prints
the same on every machine. The build passes this folder to the typesetter and
otherwise ignores system fonts — see [docs/design.md](../../docs/design.md).

| File | Family | Used for |
|---|---|---|
| `Jost.ttf` | Jost (variable, 100–900) | headings, card prompts, the wordmark |
| `Archivo.ttf` | Archivo (variable, 100–900) | reading text — the back of a card |
| `Archivo-Italic.ttf` | Archivo Italic (variable) | emphasis in reading text |
| `IBMPlexMono-Regular.ttf` | IBM Plex Mono | card ids, YAML, anything literal |

All three are licensed under the SIL Open Font License 1.1; the licences are
next to the files (`OFL-*.txt`). They come from
[github.com/google/fonts](https://github.com/google/fonts). The two Archivo
files have their width axis pinned to 100 % — the only change made to any of
them, and the reason they are a third of their original size:

```bash
python3 -c "
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
f = instancer.instantiateVariableFont(TTFont('Archivo[wdth,wght].ttf'), {'wdth': 100})
f.save('Archivo.ttf')"
```

Jost and Archivo cover Latin and Latin Extended. Greek and Cyrillic fall back
to New Computer Modern, which the typesetter carries itself, so Russian, Greek
and Ukrainian cards still set correctly. Maths always uses New Computer Modern
Math.
