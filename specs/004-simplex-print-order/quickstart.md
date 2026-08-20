# Quickstart: validating the simplex print order

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Contracts**: [cli.md](contracts/cli.md), [engine-inputs.md](contracts/engine-inputs.md)

How to prove this feature works — by command, by automated test, and on paper.
The success criteria it covers are named per step.

## Prerequisites

```bash
python3 --version          # 3.12 or newer
pip install -r requirements-dev.txt
pdftotext -v               # poppler's, for the page-order assertions
```

Without `pdftotext`, or with a `pdftotext` that is not poppler's, the
order tests **skip** and everything else still runs. The first end-to-end run
fetches the typesetting engine (~15 MB); set `LERNKARTEN_E2E=1` to allow it.

## 1. The two orders, side by side (SC-001)

```bash
DEMO=tests/fixtures/demo-project/cards
python3 bin/lernkarten build $DEMO/*.yaml -o /tmp/duplex.pdf
python3 bin/lernkarten build $DEMO/*.yaml -o /tmp/simplex.pdf --sides simplex
```

Expected — both 8 pages, and the closing lines differ:

```text
OK: 29 cards (english, german, greek, russian) -> /tmp/duplex.pdf (8 pages, duplex, flip on long edge).
OK: 29 cards (english, german, greek, russian) -> /tmp/simplex.pdf (8 pages, simplex: print pages 1-4 at 100 % scale, turn the stack over on the long edge, then print pages 5-8).
```

Read the face marks out of each — every card footer prints `1/2` on a front and
`2/2` on a back:

```bash
for p in 1 2 3 4 5 6 7 8; do
  echo -n "page $p: "
  pdftotext -f $p -l $p /tmp/simplex.pdf - | grep -o '[12]/2' | sort -u | tr '\n' ' '
  echo
done
```

Expected: pages 1–4 show only `1/2`, pages 5–8 only `2/2`. The same loop over
`/tmp/duplex.pdf` alternates. That is SC-001, read straight off the artifact.

## 2. Every back behind its own front (SC-002)

```bash
pytest tests/test_e2e.py -k "simplex" -q
```

Expected: green, or skipped with a message naming `pdftotext`. These compare
the card-id grid of page `4 + i` against page `i` row by row, reversed — the
same check `test_the_backs_are_mirrored_across_the_requested_columns` makes for
duplex, applied to the simplex layout at both grids.

## 3. The default did not move (SC-003)

```bash
pytest tests/test_e2e.py tests/test_build_pdf.py -q
```

Expected: green, **with no existing assertion rewritten**. The five places that
assert `"N pages, duplex"` are the check: if one of them had to change, the
default path moved and FR-008 is broken. Confirm nothing was edited:

```bash
git diff main -- tests/test_e2e.py | grep '^-' | grep 'pages, duplex'
```

Expected: no output.

## 4. Page ranges at every deck size (SC-004)

```bash
python3 bin/lernkarten build $DEMO/*.yaml -o /tmp/a8.pdf --sides simplex --grid a8
python3 bin/lernkarten build $DEMO/tides.yaml -o /tmp/one.pdf --sides simplex
```

Expected:

| Build | Pages | The line says |
|---|---|---|
| `a8`, 29 cards | 4 | `print pages 1-2 …then print pages 3-4` |
| one 8-card deck | 2 | `print page 1 …then print page 2` — **not** `pages 1-1` |

## 5. Refusals and the sibling command

```bash
python3 bin/lernkarten build $DEMO/*.yaml -o /tmp/never.pdf --sides both ; echo "exit $?"
python3 bin/lernkarten check $DEMO/*.yaml --sides simplex ; echo "exit $?"
```

Expected: exit 2 naming `duplex` and `simplex`, with `/tmp/never.pdf` not
created; then exit 0 with `29 cards valid`, the check line unchanged by the
flag.

## 6. The docs gate (SC-006)

```bash
python3 scripts/check_docs.py ; echo "exit $?"
```

Expected **before** the documentation is updated: exit 1, naming every line
that still gives duplex as the only way to print — `README.md`,
`docs/workflow.md`, `docs/design.md`, `docs/testing.md`,
`skills/print/SKILL.md`. That failure is the point; it is the sweep, enforced.

Expected **after**: exit 0.

`docs/index.html` is not read by this gate (`markdown_files()` covers `*.md`,
`docs/*.md` and `skills/*/SKILL.md`). Its printing paragraph has to be updated
by hand in the same change — this line is here so it is not forgotten.

## 7. On paper (SC-005, SC-007)

The one thing no test can prove. `docs/testing.md` check 17 splits in two, and
both are per grid:

- **17a — duplex**: print `/tmp/duplex.pdf` duplex, flip on long edge, 100 %
  scale. Every back exactly behind its front. *This must still pass* — it is
  the regression check for FR-008 on paper.
- **17b — simplex**: print pages 1–4 of `/tmp/simplex.pdf` at 100 % scale.
  Take the stack out, turn it over on the long edge, put it back in the tray,
  print pages 5–8. Every back exactly behind its front.

If a printer stacks face-up, the second job needs reverse page order — every
common print dialog offers it. That is documented rather than built; if it
turns out not to be enough, the spec's Assumptions name it as its own feature
rather than a patch to this one.

For SC-007, do 17b using only the build's closing line and `README.md`. If you
had to open the source to know which pages to print or which way to turn the
stack, the closing line is not carrying its weight.

## The four gates, before the PR

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

Plus one full end-to-end run, once:

```bash
LERNKARTEN_E2E=1 pytest tests/test_e2e.py -q
```
