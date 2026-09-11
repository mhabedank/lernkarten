# Quickstart: seeing the side marker leave the card

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-09-11

Six checks that prove the feature end to end. Everything runs against the demo
project in `tests/fixtures/demo-project`, so nothing here needs a project of your
own. Paths are given from the repository root.

## Prerequisites

- Python 3.12+ and `bin/lernkarten` on `PATH` (or call it by path).
- The typesetting engine. `lernkarten build` fetches it once on first use;
  `LERNKARTEN_E2E=1` is what lets the test suite do the same.
- `pdftotext` (poppler) **only** for check 2, which reads the text layer. Check 1
  is the point of this feature: it needs no text layer at all.

```bash
export DEMO=tests/fixtures/demo-project
```

## 1. The face map, and the print order in it

```bash
lernkarten build $DEMO/cards/*.yaml -o /tmp/duplex.pdf \
    --grid a7 --face-map /tmp/duplex.json
lernkarten build $DEMO/cards/*.yaml -o /tmp/simplex.pdf \
    --grid a7 --sides simplex --face-map /tmp/simplex.json

python3 - <<'PY'
import json
for name in ("duplex", "simplex"):
    m = json.load(open(f"/tmp/{name}.json"))
    print(name, m["sides"], m["grid"],
          [sorted({f["side"] for f in p["faces"]}) or ["-"] for p in m["pages"]])
PY
```

**Expect** — 33 cards at 8 up is five sheets, ten pages:

```
duplex duplex 2x4 [['front'], ['back'], ['front'], ['back'], … ]
simplex simplex 2x4 [['front'], ['front'], ['front'], ['front'], ['front'], ['back'], … ]
```

Duplex alternates page by page; simplex puts all five front pages first. This is
the #48 guarantee, read off the build with no `pdftotext` anywhere. See
[contracts/face-map.md](./contracts/face-map.md) for the full shape of the file.

## 2. The ink is gone

```bash
pdftotext -enc UTF-8 /tmp/duplex.pdf - | grep -c -E '[12]/2'   # expect: 0
pdftotext -enc UTF-8 /tmp/duplex.pdf - | grep -c '·'           # expect: 0
python3 -c "import json,subprocess; \
ids={f['ref'] for p in json.load(open('/tmp/duplex.json'))['pages'] for f in p['faces']}; \
t=subprocess.run(['pdftotext','-enc','UTF-8','/tmp/duplex.pdf','-'],capture_output=True,text=True).stdout; \
print(sorted({t.count(i) for i in ids}))"
```

**Expect** no `1/2`, no `2/2`, no separator — and `[2]`: every card id appears
exactly twice, once per face. Counted against the ids the face map names rather
than against a pattern, because an upper-case topic label in the header can look
like an id to a regex. The id stays; only the marker beside it goes.

## 3. A card with no id leaves no smudge

```bash
cat > /tmp/plain.yaml <<'YAML'
topic: 'Plain'
language: english
cards:
  - subtopic: 'No id'
    front: 'What is on the right of the footer?'
    back: 'Nothing at all, on a card written before ids existed.'
YAML

lernkarten build /tmp/plain.yaml -o /tmp/plain.pdf
lernkarten build /tmp/plain.yaml -o /tmp/plain-nologo.pdf --no-logo
pdftotext -enc UTF-8 /tmp/plain.pdf - | grep -c -E '[12]/2|·'   # expect: 0
```

**Expect** exit 0 for both and nothing matched. Then **look at
`/tmp/plain-nologo.pdf`**: the footer band is empty apart from its top rule, and
keeps its height. No vertical rule standing in front of nothing — that is the
judgement this feature has to get right, and it is a manual row in
`docs/testing.md` because a rule is not in the text layer.

## 4. A page that carries only dividers

One deck, 11 cards, at 16 up: one card sheet, and the dividers open a second one.

```bash
lernkarten build $DEMO/cards/tides.yaml -o /tmp/div.pdf \
    --grid a8 --dividers 4 --face-map /tmp/div.json
python3 -c "
import json; m = json.load(open('/tmp/div.json'))
print([(p['page'], len(p['faces'])) for p in m['pages']])"
```

**Expect** every page of the document listed, with the divider-only pages
carrying `0` faces rather than being missing from the list.

## 5. Asking for the map changes nothing

```bash
export SOURCE_DATE_EPOCH=1700000000
lernkarten build $DEMO/cards/*.yaml -o /tmp/with.pdf --face-map /tmp/x.json
lernkarten build $DEMO/cards/*.yaml -o /tmp/without.pdf
cmp /tmp/with.pdf /tmp/without.pdf && echo "identical"
unset SOURCE_DATE_EPOCH
```

**Expect** `identical`. The pin is needed because Typst writes `/CreationDate`
into the PDF; without it two builds one second apart differ for reasons that have
nothing to do with this feature.

Also check the negative: a build with no `--face-map` writes the PDF and nothing
beside it.

```bash
lernkarten build /tmp/plain.yaml -o /tmp/only.pdf && ls /tmp/only.*
```

## 6. The gates

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
LERNKARTEN_E2E=1 pytest tests/test_e2e.py
```

All five green. `check_docs.py` now also fails any document that says the card
prints `1/2` or `2/2` — try adding that sentence to `docs/design.md` and watch it
name the line, then take it out again.
