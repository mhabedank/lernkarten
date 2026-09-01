# Quickstart: validating deck anchors

**Feature**: `007-deck-anchors` | **Date**: 2026-09-01

How to prove the feature works, end to end, without reading the implementation.
Every command runs from the repository root. Nothing here needs the typesetting
engine except the last section.

## Prerequisites

```bash
python3 --version          # 3.12 or newer
pip install -r requirements-dev.txt
```

## 1. The demo project is green under the invocation CI uses

The headline acceptance: after the feature lands, the fixture reports **no
errors and no warnings** under `--strict` (SC-001, Story 1 scenario 4).

```bash
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

**Expected**: exit 0, and a line reading
`OK: tests/fixtures/demo-project is consistent (…, 32 cards, 0 warning(s)).`

A warning here is a failure — CI runs exactly this command.

## 2. A-1 fires on a deck that argues about a term it never names

Build a project whose catalog declares a term and whose cards never say it.

```bash
mkdir -p /tmp/anchor-demo/{catalog,cards}
cat > /tmp/anchor-demo/catalog/topics.md <<'MD'
# Topics

## Tides

### Rhythm of the tide
How the tide moves.
Term: Rhythm of the tide, Tidenrhythmus
References: none
Status: gap
MD
cat > /tmp/anchor-demo/cards/tides.yaml <<'YAML'
topic: 'Tides'
language: english
cards:
  - id: A45DK
    subtopic: 'Rhythm of the tide'
    front: 'How long is a tidal day?'
    back: '24 h 50 min.'
    source: 'Field notes'
YAML
python3 scripts/check_project.py /tmp/anchor-demo
```

**Expected**: exit 1, and an error naming **all three** of the card file, the
subtopic and the term it looked for — see
[contracts/check-messages.md](contracts/check-messages.md).

Note the subtopic is `Status: gap` and has a card anyway. That is deliberate and
it is **FR-009a**: A-1 keys off cards existing, not off the mark, so it fires
here. The separate "subtopic is marked" warning `check_cards` already emits is
unaffected.

Now add the anchor and watch it go quiet (Story 1 scenario 2):

```bash
cat >> /tmp/anchor-demo/cards/tides.yaml <<'YAML'
  - id: B7QT2
    subtopic: 'Rhythm of the tide'
    front: 'What is the rhythm of the tide?'
    back: 'Two high and two low waters a tidal day, each about 50 min later than the day before.'
    source: 'Field notes'
YAML
python3 scripts/check_project.py /tmp/anchor-demo
```

**Expected**: the A-1 error is gone.

## 3. A subtopic with no `Term:` line is silent

Delete the `Term:` line from the catalog above and re-run. **Expected**: no A-1
finding at all — neither error nor warning. This is the pre-feature behaviour and
the reason no existing project gains a finding it did not have before (FR-011a,
SC-005).

## 4. A-2 fires on an enumeration that teaches labels

```bash
mkdir -p /tmp/orphan-demo/cards
cat > /tmp/orphan-demo/cards/flags.yaml <<'YAML'
topic: 'Signals'
language: english
cards:
  - id: C1XR8
    subtopic: 'Warning stages'
    front: 'Name the four Ashwind warning stages.'
    back: '#list([Green], [Amber], [Ashwind], [Full Ashwind])'
    source: 'Field notes'
  - id: D9KM3
    subtopic: 'Warning stages'
    front: 'What does the green stage mean?'
    back: 'Nothing unusual — the predicted tide holds.'
    source: 'Field notes'
YAML
python3 scripts/check_project.py /tmp/orphan-demo
```

**Expected**: exit 1, with a finding for `Amber`, one for `Ashwind` and one for
`Full Ashwind` — each quoting the item **verbatim** (SC-002) and naming the card
by its 1-based index, `card 1` (FR-014: the index, never the `id`). `Green` is
not reported: the second card names it.

Note the check needs no `catalog/topics.md` at all — A-2 is per card file by
construction.

## 5. The maths gate leaves `cards/example.yaml` alone

The regression that FR-013a exists to prevent:

```bash
python3 scripts/check_project.py .
lernkarten check cards/example.yaml
```

**Expected**: both clean. `example.yaml`'s Kolmogorov-axioms card enumerates
three items that appear on no other card in that file, and **all three contain a
`$…$` span**, so the maths gate skips them. If either command reports an orphan
there, the gate has been weakened to strip-maths-then-head-term and FR-013a has
been broken.

## 6. The repo's four gates

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

**Expected**: all four green (SC-004).

## 7. Once, before the pull request

```bash
python3 scripts/make_testdata.py
LERNKARTEN_E2E=1 pytest tests/test_e2e.py
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

**Expected**: green, with `DEMO_CARD_COUNT = 32`. The demo deck's sheet counts
do **not** move at 32 cards (8 pages at a7, 4 at a8); the mixed-file build in
`test_a_broken_file_does_not_take_the_healthy_ones_down` does move, 8 → 10,
because it adds a 33rd card. See [research.md § R5](research.md#r5--the-fixture-budget-the-one-that-reshaped-the-plan).

## 8. Reading the prompts cold (SC-006, SC-008)

Not automatable — these are on the manual checklist in `docs/testing.md`:

| Read | You should be able to say |
|---|---|
| `skills/learning-goal/SKILL.md` § Depth | that `depth: expert` carries `working` and `awareness` cards too — the level is a ceiling, not a slice |
| `skills/cards/SKILL.md` | the anchor rule, **and** the "anchor, not coverage" caution that forbids a definition card for every term |
| `skills/cards/SKILL.md` § Steps | that a numbered step runs `python3 scripts/check_project.py .` after the merge, and what to do when it reports |

## Cleanup

```bash
rm -rf /tmp/anchor-demo /tmp/orphan-demo
```
