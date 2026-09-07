# Quickstart: validating enumeration tiers

**Feature**: `011-enumeration-tiers` · run from the repository root.

## 0. Prerequisites

Nothing beyond a checkout and Python 3.12+. Every check here is pure text
analysis over files on disk — no engine, no network, no `pdftotext`.

## 1. The four gates

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

`check_docs.py` is the one to watch: this feature gives it its first assertion
about a skill's own text (research R-6), so a `skills/cards/SKILL.md` that has
lost the tier table fails here rather than silently teaching nothing.

## 2. The fixture stays green

```bash
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

Expected: `OK`. Warnings fail under `--strict`, so this is the gate that proves
the new checks do not fire on correct material — in particular on `F3M2Q`,
whose front carries a numeral and whose back is correct prose.

## 3. Each new finding, by hand

Build a scratch project and put one bad card in it. The failing cases live in
`tmp_path` in the test suite; this is the same thing done by hand.

```bash
python3 scripts/demo.py /tmp/tiers && cd /tmp/tiers
```

Then, one at a time, edit `cards/*.yaml` and re-run
`python3 scripts/check_project.py .`:

| Edit | Expect |
|---|---|
| a front `'Name the four stages.'` over a prose back | **E-2** warning naming the card and `'four'` |
| a front `'Describe the range over the six hours.'` over a prose back | **silence** — no cue adjacent to the numeral |
| a flat `#list` of seven items | **E-3a** warning: group them |
| a `#list` of ten items, grouped or not | **E-3b** warning: split the card |
| `'Name the four steps.'` over `#list([*A*: x, y], [*B*: z, w])` | **silence** — E-1 counts members, not group items |
| the same, with nothing else naming `w` | **A-2 error** quoting `w`, never `A` or `B` |

The last two rows are the regression guards for research R-4 and R-5. An
implementation that keeps E-1 counting items fails row 5; one that keeps A-2's
head-term cut fails row 6.

## 4. The tiers are readable

Open `skills/cards/SKILL.md` and find the tier table without searching the
issue. State, from the file alone: what 3–5 items look like, what happens at
seven, what happens at ten. That is SC-006, and `check_docs.py` holds the
mechanical half of it.

## 5. End to end

```bash
LERNKARTEN_E2E=1 pytest tests/test_e2e.py
```

The demo project grows new cards for the grouped and split tiers (research
R-7), so both card-count assertions move with it: `DEMO_CARD_COUNT` in
`tests/test_e2e.py` and the bare count in `tests/test_check_project.py`. If
this run fails on a number, that is the number.
