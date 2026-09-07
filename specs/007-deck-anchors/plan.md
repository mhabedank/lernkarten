# Implementation Plan: Deck anchors — `depth` as a ceiling, and every term the deck uses is named by a card

**Branch**: `feat/deck-anchors` | **Date**: 2026-09-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-deck-anchors/spec.md`, clarified
2026-09-01, zero open questions. GitHub issue
[#49](https://github.com/mhabedank/lernkarten/issues/49).

## Summary

`depth` is documented as a ceiling and implemented as a slice, so an `expert`
deck argues about terms no card ever names. The fix has three parts that have to
ship together: make `depth` cumulative in the prompts, state an anchor rule in
`/cards`, and back both with two deterministic checks in
`scripts/check_project.py` — **A-1** (a subtopic whose catalog entry declares a
`Term:` has, in every card file holding its cards, one card that names it) and
**A-2** (every item enumerated in a `#list(...)` back is named by some other card
in the same file). Both are errors, both are pure text over files already on
disk, and both reuse the `topic_key()` and `catalog_names()` helpers that are
already there. One format changes, additively: an optional `Term:` line on a
catalog subtopic.

## Technical Context

Unchanged from the project defaults. Python `>=3.12`, ruff at line length 100
with `select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]`, pytest with
`testpaths = ["tests"]`, PyYAML `6.0.3` as the sole runtime dependency reaching
the user through `scripts/deps.py`, Typst pinned by SHA-256 per platform in
`scripts/engine.py`, Windows/macOS/Linux treated as equals.

**This feature changes none of it.** It adds no dependency, touches no template,
needs no engine, reads no file the checker does not already open, and runs on
every supported platform without a platform surface of any kind.

## Dependency Decisions

**No dependency change.** No runtime package, no dev package, no external binary,
no removal.

### Reuse check (constitution III)

**Is anything being hand-rolled here?** One thing, narrowly: the **bracket-depth
scan** that pulls `[...]` items out of a `#list(...)` body — about fifteen lines.

Everything else reuses what exists:

| Need | Existing helper |
|---|---|
| normalise a term or an item | `topic_key()` (`check_project.py:128`) — Unicode-aware, already used for goal/catalog drift |
| split a comma-separated attribute value | `catalog_names()` (`:463`) — already strips trailing parentheticals |
| read an attribute line off a subtopic | `ATTRIBUTE` + `parse_catalog` + `Entry.attribute` (`:61`, `:432`, `:405`) |
| report and exit | `Report.error` (`:97`) |

**Why no library for the scan.** No maintained package parses Typst *markup
fragments*; the only Typst parser is inside the `typst` binary, which this
project invokes as a typesetter rather than importing. A regex
(`\[([^\]]*)\]`) was considered and rejected: it cannot handle a nested `[...]`
inside an item, which FR-013 requires, and it cannot express "give up rather
than guess" on an unbalanced fragment.

**Why no fuzzy-match or stemming library** for the matching itself: the rule is
exact token-sequence containment by design. The failure this feature exists to
prevent is a check nobody trusts, and a fuzzy matcher is how you get one.
`rapidfuzz`, `nltk` and `snowballstemmer` were considered and rejected on that
ground, not on packaging grounds — all three would clear constitution II.

## Constitution Check

*GATE: passed before Phase 0, re-checked after Phase 1 design. Result below is
the post-design re-check.*

| # | Gate | Pass? |
|---|---|---|
| I | The halves stay coupled only through the file formats | **yes** — one format changes (`catalog/topics.md`, additively). The prompts write it; `check_project.py` reads it; neither calls into the other |
| II | Dependencies install frictionlessly | **yes** — none added |
| III | Nothing hand-rolled that a library does | **yes** — see the Reuse check; the one exception is stated and narrow |
| IV | Vetting table for every new dependency | **n/a** — none |
| V | Code lands in an existing module | **yes** — everything goes in `scripts/check_project.py`. No new file under `scripts/` |
| VI | Script imports stay acyclic | **yes** — no new import. `check_project → build_pdf, cardid, yamlio` is unchanged |
| VII | No user content committed; examples subject-agnostic | **yes** — every example is the invented Kestrel archipelago. `cards/example.yaml` is unchanged. The PR description still needs the Principle VII note because the demo fixture changes |
| VIII | No binaries committed | **yes** — nothing binary is touched; `make_testdata.py` is not involved |
| IX | Typst sources edited, never generated files | **yes** — no Typst touched |
| X | Skill frontmatter valid | **yes** — `name` and `description` of all three edited skills are untouched; only body prose changes. `check_docs.py` re-verifies |
| XI | **(NON-WAIVABLE)** Tested first, red on the assertion | **yes** — see [Test plan](#test-plan-the-red-sequence). The prompt half's red artifact is A-1 itself, exactly as XI prescribes |
| XII | The four gates pass; ruff not loosened | **yes** — no per-file ignore added |
| XIII | English throughout | **yes** — all prose, code and commit text is English. The Greek and Russian strings are the invented fixture's card text, plus the `Term:` aliases in its catalog that exist only to match that card text. XIII carves out the cards a user generates; an alias is the catalog's handle on one, and the demo fixture is the repo's one acknowledged carve-out (VII) |
| XIV | Branch `<prefix>/<short-kebab-name>` | **yes** — `feat/deck-anchors`; commit subjects use `test:`, `feat:`, `skill:`, `docs:` |
| XV | Engine version unchanged | **yes** — untouched |
| XVI | `docs/design.md` read before a visible change | **n/a** — nothing visible changes. The deck gains one card; the card looks identical |
| XVII | Card style and Typst escaping respected | **yes** — the one new demo card and the four rewords obey the ~120/~400 budget, single-star emphasis and the `\ ` line-break rule |

**Open-item check**: this feature does not touch the constitution's one open
item (dependencies pinned by version rather than by hash). It adds no
dependency, so it neither closes nor works around it.

**Complexity Tracking**: not needed — no "no" above.

## Project Structure

### Documentation (this feature)

```text
specs/007-deck-anchors/
├── plan.md                        # this file
├── research.md                    # Phase 0 — R1..R10
├── data-model.md                  # Phase 1 — the Term: format and the in-memory shapes
├── quickstart.md                  # Phase 1 — how to prove it works
├── contracts/
│   ├── catalog-topics-md.md       # the Term: line
│   └── check-messages.md          # the two error messages
├── checklists/                    # already present
└── tasks.md                       # Phase 2 — /speckit-tasks, NOT created here
```

### Source code touched

```text
scripts/
└── check_project.py            # ALL production code lives here

skills/
├── cards/SKILL.md              # anchor rule, no-#list-only-introduction, depth, the new step
├── catalog/SKILL.md            # the Term: line
└── learning-goal/SKILL.md      # depth is cumulative

tests/
├── test_check_project.py       # both red cases + the unit tests + two count edits
├── test_e2e.py                 # three assertion edits + stale comments
└── fixtures/demo-project/
    ├── catalog/topics.md       # seven Term: lines
    ├── cards/tides.yaml        # +1 anchor card
    ├── cards/geography.yaml    # 1 reworded back (closes both orphans)
    ├── cards/gezeiten-de.yaml  # 2 reworded backs (anchor Tidenrhythmus, Tidenhub)
    ├── cards/signals.yaml      # 1 reworded front (anchors The six flags)
    └── README.md               # a section on the two new modes (FR-024)

CLAUDE.md                       # the Term: line in the catalog convention
docs/testing.md                 # manual checklist rows
```

**Structure Decision**: everything deterministic goes into
`scripts/check_project.py`. It is already the module that reads a whole project,
already parses the catalog and already walks every card with its `subtopic:`
key; a new `scripts/anchors.py` would need both of those and would import
`check_project` or duplicate it, so constitution V says put it where it fits.
No new file under `scripts/`.

### The two halves

**Model-driven work** (`skills/`): the `depth` wording in
`skills/learning-goal/SKILL.md`, the anchor rule and the checker step in
`skills/cards/SKILL.md`, the `Term:` line in `skills/catalog/SKILL.md`. Per
constitution XI the red artifact for all of it is **A-1**, which fails against
what the current prompts produce — the fixture as it stands today has a
`tides.yaml` that never names *Rhythm of the tide*.

**Deterministic work** (`scripts/`): A-1, A-2, the `ATTRIBUTE` change and the
empty-`Term:` validation, all in `check_project.py`, all covered by
`tests/test_check_project.py`.

**The seam**: `catalog/topics.md` ↔ `cards/*.yaml`. The prompts decide *which*
concept a subtopic is about and write a card that names it — judgement. The
checker only asks two mechanical questions of what was written and never opens a
knowledge document.

---

# Design

## 1. Where each check hooks in

### `scripts/check_project.py` — the full set of edits

| # | Location | Change | New or reused |
|---|---|---|---|
| 1 | `ATTRIBUTE`, line 61 | `^(Status\|Parents\|Also covers\|Related\|References\|Goal\|Term):(.*)$` | reused machinery, one alternative added |
| 2 | `check_catalog`, in the `for entry in catalog.subtopics` loop (~line 610) | read `entry.attribute("term")`; if the key is present, `catalog_names(value)`; zero aliases → **error**; else `terms[entry.name] = aliases` | new ~8 lines, reuses `catalog_names` |
| 3 | `check_catalog`, `return` (line 675) | `return subtopics, marked, terms` | signature change |
| 4 | `check`, line 895 | `subtopics, marked, terms = check_catalog(...)`; `check_cards(project, subtopics, report, marked, terms=terms, strict=strict)` | wiring |
| 5 | `check_cards`, signature (line 704) | add `terms=None` **after** `marked`, before `strict` | keyword with a default, so no other caller breaks |
| 6 | `check_cards`, beside `figure_faces` / `by_subtopic` (~line 727) | `anchor_text = {}` | new accumulator |
| 7 | `check_cards`, in the per-card loop next to the existing `by_subtopic.setdefault` (~line 826) | append this card's `front + " " + back` to `anchor_text[(where, subtopic)]` | new 2 lines |
| 8 | `check_cards`, at the end of the per-**file** body, after the inner card loop | `_check_orphans(where, data["cards"] or [], report)` — **A-2** | new helper |
| 9 | `check_cards`, after the file loop, beside the existing `figure_faces` / `by_subtopic` judgements (~line 838) | `_check_anchors(anchor_text, terms or {}, report)` — **A-1** | new helper |

### New module-level helpers

All private, all in `check_project.py`, all pure functions:

```python
LIST_HEAD = "#list("
ITEM_SEPARATOR = re.compile(r"[—–,:;]|\s\(|\s-\s")   # em dash, en dash, comma, colon, semicolon, " (", " - "

def _mentions(haystack_key, needle_key)  -> bool          # space-padded token containment
def _list_items(back)                    -> list | None   # bracket-depth scan; None = unbalanced
def _item_key(item)                      -> str | None    # maths gate + head term + topic_key
def _check_orphans(where, cards, report) -> None          # A-2
def _check_anchors(anchor_text, terms, report) -> None    # A-1
```

`_mentions` is the whole matching rule and both checks call it, so they cannot
drift apart — the same arrangement `cardid.problems_in` already sets between
`check_project` and `build_pdf`.

### Why A-1 runs after the file loop and A-2 inside it

A-2's question — "does any *other* card in this file name it?" — is answerable
with one file's `data["cards"]` in hand, so it runs as each file finishes and
reports in card order.

A-1's question is per `(file, subtopic)` pair and needs every card of that pair
accumulated first. That is exactly the shape `figure_faces` and `by_subtopic`
already have, and the module's own comment says why: *"both filled in the loop
and judged after it, because both questions are about a whole file rather than
about one card."* A-1 joins them. Iterating `sorted(anchor_text)` keeps the
output stable across platforms, which matters because tests assert on messages.

### Behaviour decisions not forced by an FR

Three, flagged here so a reviewer sees them rather than discovering them:

1. **A subtopic marked `Status: gap` / `out of scope` that nonetheless has
   cards is still checked by A-1.** The rule keys off *cards existing*, not off
   the mark — if a file carries cards for a subtopic, it anchors them. No
   fixture reaches this state, and the demo deliberately puts no `Term:` on a
   marked subtopic. *(No longer plan-only: written up as **FR-009a** in the
   post-checklist session, because FR-009 did not cover the case.)*
2. **An empty `Term:` line is an error** (research R9). "Present but useless"
   must not be silently equivalent to "absent", or the format has a shape that
   means nothing. The message mirrors the invalid-`Status:` error one loop
   above. *(No longer plan-only: **FR-011b**.)*
3. **A `Term:` line on a topic (`##`) is silently ignored**, consistent with how
   a `Parents:` line on a topic is treated today.

## 2. The `Term:` parse path, end to end

```
catalog/topics.md
  "Term: Rhythm of the tide, Tidenrhythmus, παλίρροια"
        │
        ▼  ATTRIBUTE.match(line)                          [edit 1]
  ("Term", " Rhythm of the tide, Tidenrhythmus, παλίρροια")
        │
        ▼  parse_catalog: key.lower(), value.strip(), setdefault
  Entry(kind="subtopic", name="Rhythm of the tide",
        attributes={"term": "Rhythm of the tide, Tidenrhythmus, παλίρροια", ...})
        │
        ▼  check_catalog: entry.attribute("term")          [edit 2]
        ▼  catalog_names(value)      # known=() — splits on commas, strips a trailing (…)
  ["Rhythm of the tide", "Tidenrhythmus", "παλίρροια"]
        │
        ▼  terms[entry.name] = aliases                      [edit 3 returns it]
        ▼  check() threads it to check_cards(..., terms=terms)   [edit 4, 5]
        │
        ▼  _check_anchors(anchor_text, terms, report)       [edit 9]
  for (where, subtopic), text in sorted(anchor_text.items()):
      aliases = terms.get(subtopic)
      if not aliases:            continue      # FR-011a: no Term: → silent
      if any(_mentions(topic_key(text), topic_key(a)) for a in aliases): continue
      report.error(where, …)                   # FR-014: file, subtopic, term
```

**Three parser properties that come for free and must not be re-implemented**:

- `parse_catalog` uses `setdefault`, so a **repeated** `Term:` line keeps the
  first. That is the existing rule for `References:` wrapping onto a second
  line, and it applies here unchanged.
- `catalog_names` strips a **trailing parenthetical**, so `Term: Chart datum
  (LAT)` yields `Chart datum`. Desirable, and free.
- `catalog_names` with `known=()` splits on **every** comma, so an alias cannot
  itself contain one. Documented as a limitation in
  [contracts/catalog-topics-md.md](contracts/catalog-topics-md.md).

**Malformed input**:

| Input | Result |
|---|---|
| `Term:` (empty) | `catalog_names("")` → `[]` → **error**, `subtopic 'X': 'Term:' is empty — name the term, or leave the line out` |
| `Term:    ` (whitespace) | same — `.strip()` in `parse_catalog` makes it identical to the above |
| `Term: (see above)` | `PARENTHETICAL` strips it → `[]` → same error |
| `Term: A,,B` | `catalog_names` drops the empty middle → `["A", "B"]`, no error |
| line absent | `entry.attribute("term")` is `None` → no entry in `terms` → A-1 silent |
| line on a `##` topic | attached to the topic `Entry`; `check_catalog` only reads `catalog.subtopics` → ignored |

## 3. The demo fixture, in the order the edits must happen

**The constraint nobody expected.** `tests/test_e2e.py` builds the whole demo
deck in more than twenty tests, and many assert **bare page-count literals**
rather than deriving from `DEMO_CARD_COUNT`. Those move whenever the deck
crosses a sheet boundary. Full working in
[research.md § R5](research.md#r5--the-fixture-budget-the-one-that-reshaped-the-plan);
the result:

| Deck size | a7 pages | a8 pages | mixed build (+1 card) | assertions that move |
|---|---|---|---|---|
| 31 (today) | 8 | 4 | 8 | — |
| **32 (this plan)** | **8** | **4** | **10** | **4** |
| 33 | 10 | 6 | 10 | ~15 |
| 37 (a "rich" fixture) | 10 | 6 | 10 | ~15 |

**So the budget is hard: the demo deck ends at exactly 32 cards. One card added,
four cards reworded — a reword moves no count.** At 33 or more, fifteen real assertions across
`tests/test_e2e.py` move — several of them structural (`marks[:4] ==
[{"1/2"}] * 4` becomes `marks[:5]`; `range(2)` becomes `range(3)`) — and a
feature about vocabulary would ship buried under a print-layout diff.

### The ordered edit sequence

Do these **in this order, in one commit**, so the counts move once:

**(a) `tests/fixtures/demo-project/catalog/topics.md` — add seven `Term:` lines.**
Each goes directly under the subtopic's description, before `References:`:

| Subtopic | `Term:` line | Files it binds | Anchored today? |
|---|---|---|---|
| `The five islands` | `Term: The five islands, five inhabited islands` | geography | yes — card `Y4H26`'s front |
| `Rhythm of the tide` | `Term: Rhythm of the tide, Tidenrhythmus, παλίρροια` | tides, palirroia-el | **tides: NO** → needs the anchor in (c). palirroia: yes, `παλίρροια` |
| `Range and the rule of twelfths` | `Term: Tidal range, rule of twelfths, εύρος, правило двенадцатых` | tides, palirroia-el, priliv-ru | all three yes |
| `Chart datum and the Ovray rule` | `Term: Chart datum, нуля глубин` | tides, priliv-ru | both yes |
| `Tidenrhythmus` | `Term: Tidenrhythmus` | gezeiten-de | **NO** → reword in (b2) |
| `Tidenhub` | `Term: Tidenhub` | gezeiten-de | **NO** → reword in (b2); `Nipptidenhub`/`Springtidenhub` are single tokens and do not count |
| `The six flags` | `Term: The six flags` | signals | **NO** → reword in (b3) |

Deliberately **no** `Term:` line on `Settlements` and `Rules of use` — they are
descriptions rather than terms, which is itself the fixture's demonstration of
FR-011a — nor on the three subtopics with no cards: the line is inert without
cards (I-2) and is added when cards arrive, per FR-027's "at latest" rule.
`Tidenrhythmus`, `Tidenhub` and `The six flags` **do** get lines: an earlier
draft withheld them to hold the card budget, which the cross-model review
rejected as evasion-by-omission (W2); (b2) and (b3) anchor all three by reword
at zero count cost.

Note the aliases are written in the **inflected form the cards actually use**
(`нуля глубин`, not `нуль глубин`; `εύρος`). `topic_key()` does no stemming;
research R4 measured this.

**(b) `tests/fixtures/demo-project/cards/geography.yaml` — reword card `ZRKBA`'s
back.** This closes both A-2 orphans without adding a card:

```yaml
back: 'Torvig Harbour has the only deep-water pier. \ From there the mail boat
       redistributes goods to Little Kestrel, Ovray, Skarn and Bellhorn.'
```

(one YAML line; 137 characters, well inside the ~400 budget). Verified by
prototype: all five enumerated items then report OK, and it is a better card
than the one it replaces because it says where the goods go.

**It must not be fixed by adding cards under `Relief and the crater`**, the
subtopic that actually discusses Bellhorn — that subtopic is `Status: out of
scope`, and `check_cards` warns for every card under a marked subtopic, which
under `--strict` is a CI failure (research R8).

**(b2) `tests/fixtures/demo-project/cards/gezeiten-de.yaml` — two one-line
rewords, no card added** (review W2, resolved as "anchor by reword"):

- card `HNHF1`'s back becomes
  `'Zwei Hochwasser und zwei Niedrigwasser pro Tidentag — das ist der Tidenrhythmus.'`
  (80 characters; the card already defines the concept — now it also names it);
- card `R3WZ4`'s back: `Der Hub steigt` becomes `Der Tidenhub steigt` — one
  word, nothing else.

Card `P1H4B` stays as it is: `Nipptidenhub` and `Springtidenhub` are single
tokens and must **not** anchor `Tidenhub`, so after this edit the shipped
fixture itself demonstrates the token-not-substring rule R4 calls A-1's most
important property.

**(b3) `tests/fixtures/demo-project/cards/signals.yaml` — one one-line reword**:
card `NKQK0`'s front becomes
`'Which two of the six flags call for help, and how do they differ?'`
(65 characters, still unique among the file's fronts; `the six flags` now
appears as a token sequence). The two e2e assertions that touch these files
move nothing: `test_a_subtopic_filter_narrows_the_build` asserts a card
*count* (`"3 cards"`), and the script-coverage test greps `halbtägige`, which
lives in card `HNHF1`'s **front** — untouched.

**(c) `tests/fixtures/demo-project/cards/tides.yaml` — add exactly one card**,
the anchor for `Rhythm of the tide`. It needs a unique five-character Crockford
`id:` (check the existing 31 first), a `subtopic:`, a `source:`, a front under
~120 characters and a back under ~400 — or `--strict` fails on a warning. It
must name the term as a **token sequence**: *"the rhythm of the tide"* in the
front or back. Deck: 31 → 32.

**(d) `tests/fixtures/demo-project/README.md` — one section** (FR-024) naming
both new failure modes, what satisfies them in the demo, and that their red
cases live in `tmp_path` because `check_project.py` never scans `broken/`.
**`broken/README.md` gains nothing** — see research R6.

**(e) The four count assertions, all at once**:

| File:line | Today | Becomes |
|---|---|---|
| `tests/test_e2e.py:27` | `DEMO_CARD_COUNT = 31` | `= 32` |
| `tests/test_e2e.py:97` | `assert "10 cards" in result.stdout` | `"11 cards"` — `--topic Tides` selects `tides.yaml`, which gained the anchor |
| `tests/test_e2e.py:255` | `pdf_pages(target) == 8` + its message | `== 10`; the mixed build is 32 + 1 = 33 cards → 5 sheets |
| `tests/test_check_project.py:164` | `assert counts["cards"] == 31` | `== 32` |

`tests/test_e2e.py:1110` derives from `DEMO_CARD_COUNT` and needs no edit.

**(f) Stale comments**, corrected while those files are open — all four already
said the wrong number before this feature: `test_e2e.py:81` ("29 cards"),
`:415` ("29 demo cards"), `:745` ("29 cards"), `:1106` ("31 cards").

## 4. Test plan — the red sequence

Constitution XI is non-waivable, and "fails with `AttributeError`" is not red.
Every red assertion below therefore goes through `check_project.check(...)` and
asserts on `report.errors` — a list that **exists today and is empty**, so the
test fails on its assertion, not on an import.

### Commit 1 — `test:` red, no production code

Written into `tests/test_check_project.py`. **None of these may call a helper
that does not exist yet.**

| # | Test | Assertion | Why it is red today |
|---|---|---|---|
| **R-1** | `test_a_subtopic_with_a_term_and_no_anchor_is_reported` | a `tmp_path` project whose catalog subtopic carries `Term: Rhythm of the tide` and whose `GOOD_CARDS` never says it → `report.errors` contains a message naming `cards/tides.yaml`, `Rhythm of the tide` **and** the term | `errors` is empty; nothing reads `Term:` |
| **R-2** | `test_an_anchor_card_silences_the_check` | the same project plus a card naming the term → `not report.errors` | *green today* — the pinning half of the pair; keep it, it is what proves R-1 is about the anchor and not about the `Term:` line existing |
| **R-3** | `test_an_orphan_in_a_list_back_is_reported` | a `tmp_path` project with `back: '#list([Green], [Amber])'` and another card naming only *Green* → an error quoting `'Amber'` **verbatim** and naming the card by its 1-based index (`card 1`), per FR-014 | `errors` is empty |
| **R-4** | `test_the_demo_project_is_consistent` | *already exists* (`:155`) | **goes red the moment A-2 lands** — `geography.yaml`'s `Skarn` and `Bellhorn`. This is the pre-existing test that proves the check finds a real defect, and it is the feature's headline red |

R-4 is the important one: it is not a new test, it is the existing invariant, and
it failing is the evidence that A-2 detects something real rather than something
invented for it.

### Commit 2 — `feat:` the checks, in `scripts/check_project.py`

Turns R-1 and R-3 green. R-4 goes **red** here and stays red until commit 3.
Unit tests for the helpers (`_list_items`, `_item_key`, `_mentions`) are written
**in this commit**, not commit 1 — calling a function that does not exist raises
`AttributeError`, which XI explicitly does not count as red.

Unit cases to add here, one per FR-013 shape:

| Case | Expected |
|---|---|
| `#list([a], [b])` | `["a", "b"]` |
| `[$P(A) >= 0$ for every event $A$]` | extracted, then skipped by the maths gate |
| a nested `[...]` inside an item | extracted whole |
| `#list([a], [b]` — unbalanced | `None` → card skipped, no finding |
| `[Parallelisation — sectioning and voting]` | head term `parallelisation` |
| `[Amber]` named only on its own card | still an orphan (FR-012) |
| `Nipptidenhub` vs alias `Tidenhub` | **not** a match — the substring/token distinction, R4's key finding |
| `Term:` empty | error from `check_catalog` |
| a catalog with no `Term:` anywhere | A-1 silent, no error and no warning |

### Commit 3 — `test:` the fixture

The ordered sequence of § 3. Turns R-4 green again and leaves
`python3 scripts/check_project.py tests/fixtures/demo-project --strict` at zero
errors and zero warnings.

### Commit 4 — `skill:` / `docs:` the prompts

Only now do the three `SKILL.md` files change (SC-003, FR-025: the checks are
committed red *before* either prompt is edited, visible in the commit order).

### The regression guards

**One.** Add `test_a_subtopic_without_a_term_line_is_silent`, asserting that a project
built from `GOOD_CATALOG` + `GOOD_CARDS` reports neither an error nor a warning.
`GOOD_CARDS` is used at **fifteen** call sites and names neither *rhythm* nor
*tide*; it survives only because `GOOD_CATALOG` carries no `Term:` line
(research R7). That property is load-bearing and currently implicit — this test
makes it explicit so it cannot be lost by a future tightening of A-1.

**Two.** Add `test_the_shipped_example_deck_has_no_orphan`, a `tmp_path` project
whose card file is the text of the repo's own `cards/example.yaml`, asserting
`not report.errors`. This is the **only automated** guard on FR-013a. Nothing in
CI runs the project checker over the repository root — `.github/workflows/ci.yml`
runs it against `tests/fixtures/demo-project` and nothing else — and
`lernkarten check cards/example.yaml` never imports `check_project`, so without
this test a weakened maths gate reaches the pull request and is caught, if at
all, by a human remembering to type one command.

It must be a `tmp_path` copy rather than `check(ROOT)`. `check_cards` globs
`<project>/cards/*.yaml`, and a contributor's own deck lives in exactly that
folder — `cards/` (bar `example.yaml`), `catalog/`, `knowledge/` and
`sources.yaml` are gitignored precisely because the repo root doubles as a
scratch project. `check(ROOT)` would fail on their material rather than on ours.
Copy `assets/example-figure.svg` into the temporary project with the existing
`with_figure()` helper: card 10 names it as a `back_image` and a missing picture
is an error. `example.yaml`'s subtopics are not in `GOOD_CATALOG`, so the run
reports ten *warnings* and no error — assert on `report.errors` alone.

## 5. Documentation changes

| File | Change | FR |
|---|---|---|
| `skills/learning-goal/SKILL.md` | the `## Depth` section (line ~74): the three bullets currently read as mutually exclusive slices. State that the level is a **ceiling** and that each includes the ones below — `expert` implies `working` implies `awareness`. Do **not** touch the closed set or the `check_project.py` sentence at line 59 | FR-001, FR-002 |
| `skills/cards/SKILL.md` | (i) reference `goal.md` and its `depth` from the card-writing end — the file mentions neither today; (ii) the **anchor rule**; (iii) the anchor's *content* standard — a functional definition (what it changes, what it costs, what it does not fix), explicitly **not** a dictionary gloss; (iv) **anchor, not coverage**: one card per *named* concept, never a definitional layer beneath everything; (v) **nothing is introduced only inside a `#list([…])` back**, next to the existing `#list` note in § Style rules; (vi) a numbered **step** running `python3 scripts/check_project.py .` after the merge in step 4, with what to do when it reports | FR-003–FR-007, FR-026 |
| `skills/catalog/SKILL.md` | the `Term:` line in the attribute list at lines 86–92, beside `Status:`, `Parents:` and `Related:` — what it is for, that aliases are comma-separated and must cover **every language the deck is written in**, that they are matched **literally with no stemming** (so write the form the cards use), and that leaving it out means A-1 stays silent; **plus one sentence in the writing guidance instructing `/catalog` to write the line** for a subtopic whose heading names a concept, at latest when its cards exist — without it A-1 has no writer (FR-027 as amended, review W1) | FR-027 |
| `CLAUDE.md` | one clause in the **Topic catalog** convention bullet, in the existing "Optional per subtopic" sentence | FR-027 |
| `tests/fixtures/demo-project/README.md` | a section on the two new failure modes | FR-024 |
| `docs/testing.md` | manual-checklist rows for SC-006 and SC-008 (reading each prompt cold; the checker step firing during a real `/cards` run) — both are run-output requirements that leave nothing on disk, which constitution XI sends to the checklist **named**, never implicit | SC-006, SC-008 |

### Staying consistent with `scripts/check_docs.py`

`check_docs.py` is one of the four gates. It checks three things that these
edits could break, and one they cannot:

1. **Skill frontmatter** — `name` must equal the folder name and `description`
   must be ≥ 20 characters and contain the word `Triggers`. **All three edits
   are body prose only; no frontmatter is touched.** Do not "improve" a
   `description` in passing.
2. **Every relative markdown link resolves**, across `docs/`, the repo-root
   markdown and `skills/*/SKILL.md`. Any link added by these edits must point at
   a real file. Prefer naming `scripts/check_project.py` in backticks (as all
   five skills already do) over linking to it.
3. **Required files exist** — nothing is deleted, so this is unaffected.
4. **Version agreement** across the three version files — untouched by this
   feature, and separately worth remembering as a release-time trap.

Run `python3 scripts/check_docs.py` after commit 4 and before the PR.

## 6. Risks

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| **1** | **The demo deck grows past 32 and fifteen e2e assertions move.** The single largest risk, and the one the incoming brief had wrong — it named two count sites; there are also ~13 bare page-count literals over `*CARDS` | high if unwatched | the hard 32-card budget of § 3. One added card, four rewords — a reword moves no count. If a later requirement forces a 33rd, the fifteen sites are enumerated in research R5 — budget the extra work, do not discover it |
| **2** | **`GOOD_CARDS`' fifteen call sites.** An A-1 that matched the *heading* rather than a `Term:` line would break every one of them, including `test_a_minimal_project_is_clean`, which asserts zero warnings as well as zero errors | low under D1 | verified in research R7: `GOOD_CATALOG` carries no `Term:` line, so `terms` is empty and A-1 is silent. Pinned by an explicit new test |
| **3** | **`--strict` turns a warning into a CI failure on the fixture.** A new card missing an `id` or a `source` fails the build even though neither is an error | medium | § 3(c) states the per-card requirements. Run `check_project.py tests/fixtures/demo-project --strict` after **every** fixture edit, not once at the end |
| **4** | **The A-2 fix put under a marked subtopic.** `Relief and the crater` is where Bellhorn belongs by subject, and it is `Status: out of scope` — a card there warns, and warns fail under `--strict` | medium (it is the intuitive place) | § 3(b): the fix is a reword of a card already under `The five islands` |
| **5** | **The maths gate weakened to strip-maths-then-head-term.** It looks like the more thorough rule and it would report two of `cards/example.yaml`'s three Kolmogorov items as orphans. Note **which** gate sees that: `python3 scripts/check_project.py .` over the repo itself, never `lernkarten check cards/example.yaml` — `bin/lernkarten` imports `engine`, `deps`, `cardid` and `build_pdf` and never `check_project`. CI runs the project checker only over the demo fixture | medium | FR-013a names it explicitly; prototype in research R3 shows all three items skipped; the unit table in § 4 has the case; and the second regression guard in § 4 makes `pytest` the gate rather than a manual pre-PR command |
| **6** | **Inflected aliases.** `topic_key()` does no stemming, so `нуль глубин` does not match a card saying `нуля глубин`. A user writing the dictionary form gets a finding they cannot explain | medium for real users | the alias set in § 3(a) uses the measured forms; `skills/catalog/SKILL.md` and the contract both say matching is literal |
| **7** | **A term containing a comma is torn in two** by `catalog_names(line, known=())`, which has no `known` set to match against first | low | documented as a limitation in the contract; a comma-free alias is the workaround. Not worth a `known` set: the candidates would be the aliases themselves |
| **8** | **`check_catalog`'s changed arity.** Exactly one direct caller unpacks it — `tests/test_check_project.py:857` | low | named in research R2; it is a one-line edit |
| **9** | **A-1 on a marked subtopic that has cards anyway.** Not decided by any FR | low | decided explicitly in § 1; no fixture reaches it; a reviewer sees the choice rather than finding it |
| **10** | **The prompt half cannot be tested directly.** SC-006 and SC-008 are satisfied by what a prompt *says*, which leaves nothing on disk | inherent | constitution XI's run-output carve-out: they go on `docs/testing.md`'s manual checklist and are **named there**. A-1 is the assertable red artifact that XI actually requires, and Story 1 delivers it |

## Post-design constitution re-check

Re-evaluated after the design above: **all gates still pass**, no row turned to
"no", Complexity Tracking stays empty. The design added no module, no
dependency, no import edge and no format beyond the one additive attribute line
the spec already scoped.

## What Phase 2 (`/speckit-tasks`) still has to decide

Deliberately left open here:

- the task-level split of § 3's ordered fixture edits, and whether (a)–(f) are
  one task or six;
- the exact wording of the seven `Term:` lines' aliases beyond the anchors
  measured in research R4 — the *set* is fixed, the phrasing of the new anchor
  card's front and back is not;
- the exact prose of the six `skills/cards/SKILL.md` additions and where in the
  file each sits;
- which of § 4's unit cases become `pytest.mark.parametrize` rows and which
  stand alone;
- the `docs/testing.md` row numbering.
