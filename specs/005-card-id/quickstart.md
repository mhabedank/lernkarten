# Quickstart: validating the card id end to end

**Feature**: `specs/005-card-id` · **Date**: 2026-08-21

How to prove this feature works once it is implemented. Every scenario maps to a
success criterion in [spec.md](./spec.md). Details of the format live in
[contracts/cards-yaml.md](./contracts/cards-yaml.md); the shapes are in
[data-model.md](./data-model.md).

## Prerequisites

```bash
python3 --version          # 3.12 or newer
pip install -r requirements-dev.txt
```

No new dependency is needed for this feature. The typesetting engine downloads
itself on first build; scenarios 5 and 6 need it, the rest do not.

## Scenario 1 — the id is stable (SC-002)

The defect this feature exists to fix. Every step changes the id **today**.

```bash
python3 scripts/demo.py /tmp/idcheck      # scratch project
cd /tmp/idcheck
lernkarten id --backfill cards/*.yaml

# note the id of the third card
grep -m3 'id:' cards/tides.yaml | tail -1
```

Now break it four ways and confirm the id does not move:

```bash
# 1. insert a card before it      2. delete a card before it
# 3. rename the file              4. edit the card's front and back
mv cards/tides.yaml cards/renamed.yaml
grep -m3 'id:' cards/renamed.yaml | tail -1     # same id
```

**Expected**: the noted id is unchanged after all four. Also build with
`--subtopic` and confirm the id matches the unfiltered build.

## Scenario 2 — existing decks still build (SC-003)

The backwards-compatibility guarantee. Run against decks with **no** `id:` key.

```bash
cd /path/to/repo
lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/noids.pdf
echo "exit: $?"
```

**Expected**: exit 0, and the same page count as before the feature —
`2 × ⌈cards ÷ 8⌉` at a7. `lernkarten check` on the same files also exits 0 and
prints **one** advisory line naming the backfill path, not one line per card.

## Scenario 3 — backfill preserves the file (SC-006)

```bash
cp cards/example.yaml /tmp/before.yaml
lernkarten id --backfill cards/example.yaml
diff /tmp/before.yaml cards/example.yaml     # only `id:` lines added
lernkarten id --backfill cards/example.yaml  # again
```

**Expected**: the first run adds one `id:` line per card and touches nothing
else — all 11 comments intact, all single-quoted Typst markup byte-identical.
The second run changes the file **not at all**.

The precise property, and the one the test asserts, is a byte-exact round trip:

```python
remove_ids(insert_ids(src)) == src      # on LF, CRLF and non-ASCII decks
```

A naive "strip the `id:` lines and compare" check gives a **false failure** —
`id` sits first, so the `- ` list dash moves onto the new line. That movement is
structural (stripping the id line alone leaves invalid YAML), not reformatting.

## Scenario 4 — a broken id is reported, and nothing is written (SC-004, SC-009)

```bash
cd /path/to/repo
shasum tests/fixtures/demo-project/broken/*.yaml > /tmp/before.sha
lernkarten check tests/fixtures/demo-project/broken/duplicate-id.yaml
echo "exit: $?"
shasum -c /tmp/before.sha
```

**Expected**: non-zero exit; the message names **both** cards sharing the id,
file and card, not just the id. The bad-alphabet, bad-length and non-string
fixtures each fail naming file, card and what is wrong. **Every input file is
byte-identical afterwards** — the checker is a read-only CI gate and never
resolves a collision itself.

## Scenario 5 — the id is legible on paper (SC-005) *(needs the engine)*

```bash
lernkarten build cards/example.yaml -o /tmp/cards.pdf
```

**Expected, asserted by measuring rather than by eye**: the rendered
`<id> · 1/2` is **52.80 pt** wide against the `cw / 3` cap of **94.49 pt** —
55.9 %, nowhere near the `clip: true` boundary. The type size is **8 pt**, up
from 4.6 pt.

Print one sheet on a black-only laser printer and read the id at arm's length.
That last part is a manual check and is named in `docs/testing.md`, because per
Constitution XI it leaves nothing on disk to assert against.

## Scenario 6 — collision reassignment is steerable (SC-008) *(writing path)*

```bash
lernkarten id --reassign deck-a.yaml deck-b.yaml   # both contain A45DK
```

**Expected**: the card in `deck-a.yaml` keeps `A45DK`; the one in `deck-b.yaml`
is reassigned. The report names the card, both ids, **and the consequence** —
that the old id no longer resolves in past conversations and any revision
history against it is orphaned.

Swap the arguments and the *other* card is reassigned. That is the whole point
of first-occurrence-wins: argument order is the user's lever, so putting the deck
whose ids they actually cite first preserves those ids.

## The four gates

Before the PR, all four must be green — CI runs the same:

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

And once, because the e2e suite skips silently without it:

```bash
LERNKARTEN_E2E=1 pytest tests/test_e2e.py
```

## Manual checklist items

Two requirements leave nothing on disk, so per Constitution XI they belong on the
manual checklist in `docs/testing.md` and are **named there**, not left implicit:

- **SC-007** — read an id off a printed card, use it in a Claude session to
  identify that card, and confirm it still resolves after the session edits it.
- The **wording** of the missing-id advisory line (its exit code is asserted;
  its phrasing is not).
