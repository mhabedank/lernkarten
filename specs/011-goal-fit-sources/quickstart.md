# Quickstart: validating goal fit, `nature: experience`, and discovery

How to prove this feature works, in the order the evidence arrives. Formats are
in [contracts/](contracts/), the rules in [data-model.md](data-model.md), the
ordered red assertions in [plan.md](plan.md#test-plan-first), and the decisions
behind the three deferred items in [research.md](research.md).

Most of this feature is what a run *says*, so the automated part is smaller than
usual and the manual part is larger. That is stated up front rather than hidden
in a coverage number.

## Prerequisites

```bash
cd <repo root>
python3 -m pip install -r requirements-dev.txt   # pytest, ruff, pillow, pyyaml
```

Nothing else. **This feature adds no dependency.** The card build is untouched,
so no typesetting engine is needed for anything except the one e2e run in step 4.

## 1. The four gates

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

`check_docs.py` is the one that changes behaviour here. It gains eight checks
(cases C6–C9 extend one of them rather than adding a ninth),
and **it will fail on a clean checkout until `skills/research-gaps/SKILL.md:17`
is rewritten** — that is wave G3, and it is the cleanest red assertion in the
feature because it fails against the shipped repository with nothing fabricated.

`lernkarten check cards/example.yaml` should be green throughout. If it ever
goes red, something reached the card schema, which this feature has no business
touching.

## 2. The automated evidence

```bash
pytest tests/test_check_docs.py tests/test_check_project.py -v
```

Each named case is a row in the wave A–G tables of the plan. Four are worth
watching by name:

```bash
# absence is never a finding — FR-031, SC-013, US2 scenario 5
pytest tests/test_check_project.py -k "no_nature or without_nature" -v

# "all references", not "any" — the rule that keeps FR-011 from over-firing
pytest tests/test_check_project.py -k "experience_only" -v

# the FR-034 gate does not fire on CONTRIBUTING.md's innocent sentence
pytest tests/test_check_docs.py -k "network_claim" -v

# no other skill points at discovery — green from the start, and must stay green
pytest tests/test_check_docs.py -k "discovery" -v
```

The first of those is the regression guard for the whole compatibility promise.
If it ever goes red, `nature:` has stopped being optional and every project on
disk is affected.

## 3. The demo project

```bash
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

Expected: exit 0, and the count line names topics, subtopics, sources, documents
and cards. After wave H the fixture additionally carries:

- one invented archipelago incident write-up under `raw/field-notes/`;
- its ingested twin under `knowledge/field-notes/`, carrying `nature: experience`
  — the only document in the corpus that has the key at all;
- one subtopic under `## Signals, flags and the radio` whose **only** reference
  is that document;
- **exactly one** card in `cards/signals.yaml` under that subtopic, carrying
  `source:`. One, not two: `--topic Signals` is what an e2e divider case builds,
  and at 9 cards in that file the three-divider block stops sharing its sheet.
  The arithmetic is in tasks T031 and T033.

To see the new checks bite, break one thing at a time in a scratch copy:

```bash
python3 scripts/demo.py /tmp/lk-demo --force

# A1 — an unknown value in a closed vocabulary
sed -i '' 's/nature: experience/nature: anecdote/' /tmp/lk-demo/knowledge/field-notes/*.md
python3 scripts/check_project.py /tmp/lk-demo --strict     # names the document, the value and the set

# B1 — attribution missing where the evidence is a single case
# remove the `source:` key from the card under the experience-only subtopic
python3 scripts/check_project.py /tmp/lk-demo --strict     # names the file, the card and the subtopic

# A5 — the goal-fit verdict never lands on the entry (FR-007)
# add `fit: 'serves nothing'` to any entry in /tmp/lk-demo/sources.yaml
python3 scripts/check_project.py /tmp/lk-demo --strict     # names the entry and the key
# `login: true` on harbour-office-members must stay clean — the check refuses
# five key names, not unknown keys in general
```

## 4. Before the pull request

```bash
python3 scripts/make_testdata.py
LERNKARTEN_E2E=1 pytest tests/test_e2e.py
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

The e2e run is **required, not optional, for this feature**: wave H adds a card to
the demo project, so `DEMO_CARD_COUNT` (`tests/test_e2e.py:27`) moves 32 → 33,
and a wrong count is invisible to `pytest` without the engine. **Two divider
assertions move with it** — `test_four_dividers_open_a_further_page_on_the_demo_deck`
and the `added` half of `test_the_run_says_which_paper_case_it_is_in` — because
both held only while the deck was a multiple of 16. T033 licenses those edits and
carries the arithmetic; if either is still red here, read T033 before touching
`scripts/build_pdf.py`, which this feature does not change.

## 5. The manual checklist — the larger half

Twenty-five named rows go into `docs/testing.md`, each carrying its FR number —
20 `/sources` rows (4a–4s plus **4n-i**) plus 5 pipeline rows (8m, 9f, 12-iv,
12-v, 12-vi). One **existing** row also moves: row 5's "five files under
`knowledge/field-notes/`", which is already wrong on `main`. T040 says how —
count the ingestible files under `raw/field-notes/` at edit time and write that
number (eight today, nine after T028), never "five plus one".
They are listed in
[plan.md § The named rows](plan.md#the-named-rows-in-docstestingmd). Rows 1–14
need a Claude session in the demo folder.

Set up once:

```bash
python3 scripts/demo.py ~/lernkarten-demo --raw     # sources only, goal.md included
cd ~/lernkarten-demo
python3 -m http.server 8137 --directory raw/web &   # the local site, for the web source
```

Then, in a Claude session in that folder:

### Piece A — the assessment (rows 4a–4j)

```
> /sources https://blog.example-corp.com/tag/post-mortem/
```

Expect: one goal-fit statement naming a required topic or area of `goal.md`, or
a warning naming the source id **and** the goal line it conflicts with. The
entry appears in `sources.yaml` either way, with **no** confirmation prompt
(SC-004), and with **no** verdict key on it (SC-001, FR-007).

The weighting cases are one word each, in the scratch copy only — never in
`tests/fixtures/`:

```bash
# row 4b, weigh-down: kind: exam is already the fixture's value
sed -i '' 's/^depth: working/depth: awareness/' ~/lernkarten-demo/goal.md

# row 4c, weigh-up
sed -i '' 's/^depth: awareness/depth: expert/' ~/lernkarten-demo/goal.md
```

Register the same post-mortem after each edit and read the two statements side
by side. FR-005 requires the run to say **which** of `kind` and `depth` it used,
so the two runs must differ in their stated reason, not only in their verdict.

For row 4i, `rm ~/lernkarten-demo/goal.md` and register anything: no assessment,
no warning, an entry whose key set is identical to today's, and at most one line
per run pointing at `/learning-goal`.

Row 4j is the deferred item this plan accepted explicitly: register two sources
**first**, run `/learning-goal` **second**, and confirm that nothing claims to
have assessed the material already in the register.

### Piece C — discovery (rows 4k–4p, 4n-i, 4s)

```
> /sources --discover
```

Expect: candidates grouped by the area of `goal.md` they serve, a found count
and a shown count, at most 3 per area and at most 10 in the run, **every** area
listed including the ones with nothing found, and each candidate carrying a
name, a location, what it serves, one credibility sentence and a registerable
entry. **Zero** scores, ratings, percentages or stars (SC-007). That shape is the
**neutral** contract (C1) and it holds whatever class of source a candidate turns
out to be.

Every candidate must also say **which class of material it is** — an experience
report, research literature, a reference work, a standards document, a public
dataset, a magazine or trade article, or whatever it actually is (FR-017,
SC-017). Check the non-practitioner ones especially: they name a class too. It is
a phrase, **not** a value from a list — nothing is dropped, renamed or refused
for naming a class no list contains, because there is no list — and nothing about
it reaches disk, so do **not** expect it on the `sources.yaml` entry after you
accept a candidate, and do not confuse it with the `nature:` key `/ingest` writes
later.

There is also nothing to try here for **choosing which classes discovery
searches**: that filter is deliberately not part of this feature (FR-040). There
is no class-selection argument, no way to ask for only research literature, and
no vocabulary to pass. If a run appears to offer one, that is a bug against
FR-040, not a feature.

Row 4s is the **practitioner addendum** (C2, FR-019): a candidate that *is*
practitioner material — an incident write-up, a company engineering blog — must
additionally have its sentence name that the account is a primary and interested
one, and that material of this kind is published only by the parties who came
through the incident, so the cases that ended badly are not among what can be
found. What is required is what the sentence **says**, not the words: "a
selected sample" on its own does not satisfy it. A candidate that is not
practitioner material must **not** be held to those two properties; there is one
addendum and it applies to its own class only.

Then decline everything and check that nothing moved:

```bash
git -C ~/lernkarten-demo status   # if you made it a repo; otherwise diff against a copy
```

`sources.yaml`, `knowledge/` and `catalog/` must be unchanged — zero files
created, zero modified (SC-005). Then accept one and confirm
`python3 scripts/check_project.py ~/lernkarten-demo --strict` exits 0 (SC-006).

Row 4p, next to the existing `9d`: turn the network off and run `--discover`
again. It must report that it could not search, write nothing, and exit cleanly
with no traceback.

Row **4n-i** is the honest one. Open **every** proposed URL. A candidate that
404s, that turns out to be paywalled or login-gated, or whose page does not match
its description fails the row (FR-021, FR-023). If none of them is any of those,
write **"not exercised"** — not "pass". You cannot make discovery *find* an
unretrievable or a paywalled candidate on demand, so this row catches a violation
and never confirms compliance. Row **4n** proper is different and is performable:
register a source, then run discovery, and confirm it is not proposed again
(FR-024).

### Piece D — the silence (rows 4q, 4r, 12-vi)

The negative half of the feature, and the one most easily lost:

```
> /sources ~/lernkarten-demo/raw/field-notes
> /sources
> remove field-notes
```

None of those three may mention discovery — no candidate, no proposal, no
closing line offering to go looking. For row **4r**, turn the network off and
run the same three again: all three must behave **exactly** as they did online.
A run that needs the network to register a source the user named fails FR-033 —
and that, rather than "no network request was made", is what a tester can
actually judge.

Then run the whole pipeline without ever typing `--discover`:

```
> /sources ~/lernkarten-demo/raw/field-notes
> /ingest
> /catalog
> /cards
```

Expect **zero** lines mentioning discovery across the whole run,
`/catalog`'s FR-014 report included, and a `sources.yaml` holding exactly the
sources you named and nothing else (SC-014, SC-015). That is FR-038, the
property this feature exists to preserve rather than weaken.

Then run `/learning-goal` and `/research-gaps` in the same session and read their
closing lines. Neither may offer to go looking for material. **These two are the
part of row 12-vi that carries real weight**: `/learning-goal` is token-gated
from T021a onwards but its paraphrase is not, and `/research-gaps` cannot be
token-gated at all, because T006 writes `/sources --discover` into it on purpose
for FR-034's seam. A pointer added there would fail no automated gate — this row
is the only thing that catches it.

### Piece B — the experience report (rows 8m, 9f, 12-iv, 12-v)

After `/ingest`, open the stored incident write-up:

```bash
head -8 ~/lernkarten-demo/knowledge/field-notes/*.md
```

The incident document carries `nature: experience`; the handbook document
carries **no** `nature:` key at all — not `nature: reference`, not
`nature: none`.

Then read the cards `/cards` wrote for the experience-only subtopic. Every one
that states a fact from the report must name the case through the existing
`source:` key, none may read as an unattributed general rule, and a card whose
fact depends on the scale of the case must carry that scale (SC-009, FR-012).
**Both** the `/catalog` run (row 9f) and the `/cards` run (row **12-iv**) must
also have warned about the material base, and each warning must carry all four
of FR-013's contents: which subtopic and what it rests on, why that base is
skewed *written out* rather than named, what it means for the cards, and what
would balance it. A run that says only "published incidents are a selected
sample" fails the row — that is the jargon FR-013 was rewritten to forbid. The
worked example is in [spec.md § FR-013](spec.md).

## What none of this proves

Whether the model's judgement is any *good* — whether a source it called
off-goal really is, whether a candidate it proposed is worth reading. This
feature asserts that the assessment exists, names a goal line and a source id,
and never blocks; that a proposal validates as an entry; and that nothing the
user did not choose reaches their register. Whether the verdict is right is what
reading a printed card is for.
