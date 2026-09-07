# Quickstart: proving Leitner compartments work

Runnable checks, in the order they become possible. Everything here is
verifiable from a checkout; the three things that are not are named at the end.

## Prerequisites

```bash
python3 -m pytest --version        # 3.12+, pytest from requirements-dev.txt
./bin/lernkarten deps --check      # pyyaml==6.0.3 present or bootstrapping
export LERNKARTEN_E2E=1            # lets the engine be fetched (~30 MB, once)
```

## 0. The prerequisite fix

Before any of this feature exists, the crop marks must land on the paper at A8
([research.md R3](./research.md)). On `fix/cropmarks-sheet-axis`:

```bash
pytest tests/test_e2e.py -k cropmark      # red first: bottom marks are off-page
```

Red means the bottom crop marks come back at y ≈ −241 pt on an 841.89 × 595.28 pt
page, and the right-edge marks at x = 581.1 pt instead of 827.7. Green after
`297mm`/`210mm` in `templates/cards.typ:54,59` become `sheet-h`/`sheet-w`.

## 1. The dividers exist (US1, P1)

```bash
./bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml \
    --grid a8 --dividers 4 -o /tmp/leitner.pdf
```

Expected:

- **6 pages.** Without `--dividers` the same deck is 4. The 31 cards fill
  three-and-a-bit rows of sheet 2, far less than the 2.44 free rows a two-row
  block needs, so the dividers open a further page.
- stdout reports `31 cards, 4 dividers` — two counts, never one.
- stdout says a page was added.

```bash
./bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml \
    --grid a8 --dividers 4 --sides simplex -o /tmp/simplex.pdf
```

Also 6 pages, and stdout additionally says the added page is fed twice.

### The refusals

```bash
./bin/lernkarten build cards/example.yaml --grid a8 --dividers 5   # exit != 0
./bin/lernkarten build cards/example.yaml --grid a7 --dividers 4   # exit != 0, names a8
```

Neither writes a PDF. But the *file-driven* form does not refuse:

```bash
echo 'compartments: 4' > lernkarten.yaml
./bin/lernkarten build cards/example.yaml --grid a7    # exit 0, skips, says so once
```

FR-015a: a flag is a request just made and can be corrected; a file is an answer
given once, possibly months ago, and must not make an unrelated A7 build fail.

### The geometry

```bash
pytest tests/test_build_pdf.py -k divider
```

Asserts without the engine: a divider is `card_w` wide and `card_h + 1.5 mm`
tall **at every margin**; the band is 4 mm inward and 3 mm outward; and
`divider_block()` returns positions with at least 8 mm of clear paper on every
side of every divider — nothing adjacent, so FR-006's guarantee is
unconditional.

## 2. Asked once (US2, P2)

```bash
cd "$(mktemp -d)" && mkdir cards && cp <repo>/cards/example.yaml cards/
lernkarten build cards/*.yaml                 # builds; says setup is unanswered
lernkarten setup --compartments 4 --dividers-printed no --box-printed no
cat lernkarten.yaml                           # three flat keys
lernkarten build cards/*.yaml                 # says nothing about setup
```

**Not `printf '4\nn\nn\n' | lernkarten setup`.** A pipe is not a terminal, and
FR-014b requires `setup` to refuse a non-interactive run rather than guess. The
flags above are the non-interactive path, and they are what the tests use; the
interactive path is a manual check.

Then the three failure modes:

```bash
echo 'compartment: 4' > lernkarten.yaml && lernkarten build cards/*.yaml
#   WARNING names the file, the unknown key 'compartment' and the known keys;
#   the build continues (FR-016a) — a newer version's key must not brick an
#   older one

echo 'compartments: 5' > lernkarten.yaml && lernkarten build cards/*.yaml
#   error names the key and the accepted values 3, 4, none

echo 'compartments: none' > lernkarten.yaml && lernkarten build cards/*.yaml
#   builds, and says nothing — asked and declined is not the same as never asked
```

And the compatibility guarantee:

```bash
rm lernkarten.yaml
lernkarten build cards/*.yaml -o a.pdf
```

**Not `cmp` on the PDF.** The engine stamps a `CreationDate`, so two builds of
identical input already differ in bytes — see
[research.md R8](./research.md). SC-005 is checked as: the `cards.json` handed to
the engine is byte-identical to the pre-feature one (assertable today, and what
the absent-means-`card` rule for `kind` buys), and the PDF matches on page count,
page size and card placement. The baseline is post-`fix/cropmarks-sheet-axis`
`main`, because the prerequisite deliberately moves the A8 crop marks.

## 3. The box (US3, P2)

```bash
./bin/lernkarten build cards/example.yaml --grid a8 --box
cmp output/box.pdf assets/card-box.pdf     # identical
```

stdout names 160–250 gsm and says it applies to the box only. `output/cards.pdf`
is unchanged by `--box` — nothing is merged.

## 4. The page cannot drift (US4, P3)

```bash
python3 scripts/check_docs.py
```

Passes only when `docs/leitner.html` exists, is linked from `docs/index.html`,
and carries exactly the strings in `scripts/leitner.py` — both directions, so
neither a missing interval nor an invented one gets through. Delete one interval
from the page and this goes red; that is the assertion that makes FR-017 real.

## 5. The four gates

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

Plus, once, before the pull request:

```bash
python3 scripts/make_testdata.py
LERNKARTEN_E2E=1 pytest tests/test_e2e.py
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

## What no command can check

**Four** things, named on the manual checklist in `docs/testing.md` rather than
left implicit (constitution XI). Three are physical; the fourth is a terminal:

1. A cut divider **slides into the folded box** — 51.5 mm against a 52 mm
   opening is half a millimetre of clearance, and paper is not a CAD model.
2. The 1.5 mm of extra height is **visible from above** with the box full.
3. The colour band **survives a real hand-fed simplex run** — printed, turned,
   re-fed and cut by hand, with colour still reaching every edge on both faces.
4. `lernkarten setup` **asked interactively**. FR-014b makes a pipe a
   non-interactive run, and pytest has no terminal, so the prompting path itself
   cannot be asserted. What *is* asserted is the flag path and the refusal.

Everything else in this feature, including every advisory line, is a pytest
assertion. The run-output carve-out in Principle XI is written for the
model-driven half and does not apply here: `tests/test_e2e.py` drives
`bin/lernkarten` as a subprocess and already asserts against its stdout.
