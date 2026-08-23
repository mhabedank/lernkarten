# Quickstart — validating figure cards

**Feature**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

Six runnable scenarios, each proving one of the Success Criteria end to end.
Run them from the repository root.

## Prerequisites

```bash
python3 scripts/make_testdata.py     # generates the demo binaries, figures included
python3 scripts/demo.py              # a scratch copy of the demo project
```

The engine downloads itself on first build. The tests that need it skip unless
`LERNKARTEN_E2E=1` is set.

---

## 1. A card carries a picture — SC-001

```bash
LERNKARTEN_E2E=1 pytest tests/test_e2e.py -k figure
lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/figures.pdf
```

**Expected**: exits 0, `/tmp/figures.pdf` has the same page count as the same
deck without pictures — `2 × ⌈cards ÷ 8⌉`. Each picture appears on the face
that named it and on no other.

---

## 2. The four broken references are named — SC-002

```bash
for f in missing-image unreadable-image image-outside-project image-wrong-format; do
  lernkarten check tests/fixtures/demo-project/broken/$f.yaml
  echo "  → exit $?"
done
```

**Expected**: each exits non-zero with a message naming the card id, the face
and the path, and the four causes read differently from one another. See
[contracts/cards-yaml.md](./contracts/cards-yaml.md#error-messages).

---

## 3. `/ingest` judges and keeps — SC-003

In a Claude session, in the scratch project:

```text
/ingest island-images handbook
```

**Expected**:

- `knowledge/island-images/` holds two documents; the chart's frontmatter
  carries `visual: chart` and a `path:` under `figures/island-images/`, the
  photograph's carries `visual: none` and a `why:`.
- The handbook document carries one entry per figure on its pages, with the
  repeated page logo rejected once rather than four times.
- Each kept figure appears in the body as a markdown image link.

```bash
python3 scripts/check_project.py .        # exits 0
rm figures/island-images/tide-chart.png
python3 scripts/check_project.py .        # exits 1, names the document
```

---

## 4. Nothing is re-judged, nothing is rewritten — SC-004

```bash
find figures -type f -newer sources.yaml   # note what is there
```

Re-run `/ingest` unchanged.

**Expected**: the summary reports every picture skipped, no file under
`figures/` has a new mtime, and no picture is looked at a second time. Delete
exactly one figure, re-run, and exactly that one comes back.

---

## 5. The degraded path without the PDF reader — SC-005

```bash
LERNKARTEN_DEPS_DIR=$(mktemp -d) python3 scripts/figures.py extract \
  tests/fixtures/demo-project/raw/handbook/kestrel-handbook.pdf \
  --project tests/fixtures/demo-project --source-id handbook --no-install
echo "exit $?"
```

**Expected**: exit 3, one line on stderr naming the document, no traceback. A
full `/ingest` in this state still writes every transcription and names the
documents whose figures it could not extract.

---

## 6. Both grids build — SC-009

```bash
lernkarten build tests/fixtures/demo-project/grids/tides-a7.yaml -o /tmp/a7.pdf
lernkarten build tests/fixtures/demo-project/grids/tides-a8.yaml -o /tmp/a8.pdf
python3 scripts/check_project.py tests/fixtures/demo-project
```

**Expected**: both exit 0. `check_project.py` says once — not once per card —
that pictures are small at A8.

---

## The four gates, before any PR

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

## What no command can check

Three requirements leave nothing on disk, so they live on the manual checklist
in `docs/testing.md` under constitution XI's run-output carve-out, and are named
there rather than left implicit:

1. `/ingest` reports unreadable pictures in its summary with the reason (FR-015).
2. `/ingest` counts pictures found inside PDFs and web pages towards the
   "ask before looking at more than N" threshold (FR-017).
3. `/cards` reports how many cards it wrote carry a picture (FR-025).

Plus one that is a judgement, not an assertion: **hold a printed figure card**.
A chart whose meaning is carried by colour turns to grey on grey on a black-only
laser, and no check can tell you whether it survived.
