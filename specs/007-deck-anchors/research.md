# Phase 0 Research: Deck anchors

**Feature**: `007-deck-anchors` | **Branch**: `feat/deck-anchors` | **Date**: 2026-09-01

**Input**: [spec.md](spec.md) — clarified, zero open questions.

## What was already settled

Six decisions were taken in the clarify session and are written into
[`spec.md` § Clarifications](spec.md#clarifications). They are **not**
re-litigated here; this file records only what was still open after them, plus
the measurements that turn each decision into an implementable rule.

| # | Decision | Where it binds |
|---|---|---|
| D1 | "Names the term" is a new optional `Term:` attribute line on a subtopic, carrying comma-separated aliases | FR-011, FR-011a |
| D2 | A-1 binds per card file, never deck-wide | FR-010 |
| D3 | A-2 normalises by maths gate + head term, items extracted by a bracket-depth scan | FR-013, FR-013a |
| D4 | No new key on `cards/*.yaml` | FR-018 |
| D5 | The anchor binds per subtopic (`###`), never per catalog bullet | FR-019 |
| D6 | No whole-deck merge pass; `skills/cards/SKILL.md` gains a step that runs the checker | FR-020, FR-026 |

## R1 — Is a library warranted? (constitution III, the first question)

**Decision**: no library, and nothing is hand-rolled that one already does.

**Rationale**. The three operations are:

1. *Normalisation* — already exists as `topic_key()` (`scripts/check_project.py:128`),
   `" ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())`. Python's `\w` is
   Unicode-aware by default, so Greek and Cyrillic survive unharmed. Verified in
   R4 below against the real fixture.
2. *Alias splitting* — already exists as `catalog_names()` (`:463`).
3. *Matching* — exact token-sequence containment, not fuzzy matching. A
   stemming or fuzzy-match library (`rapidfuzz`, `nltk`, `snowballstemmer`)
   would make the rule *less* predictable, not more: the failure mode this
   feature is built to avoid is a check that cries wolf. Space-padded substring
   containment over a normalised string is the whole algorithm.

The only genuinely new code is the bracket-depth scan over a `#list(...)` body
— about fifteen lines over a Typst fragment. No parser in the wild targets
Typst markup fragments, and `typst`'s own parser is a Rust binary we call as a
typesetter, not a library we can import. This is the "nothing suitable exists"
exception, and it is narrow.

**Alternatives considered**: a regex `\[([^\]]*)\]` over the list body. Rejected
— it cannot handle a nested `[...]` inside an item, which Typst markup permits,
and FR-013 requires nesting to parse. A regex also cannot express "give up
rather than guess" on an unbalanced fragment.

**New dependency**: none, runtime or dev.

## R2 — Where do the terms reach the card checker?

**Open because**: `check_catalog()` returns `(subtopics, marked)` — a set of
names and a status map. It does not return the parsed `Catalog`, and
`check_cards()` never opens `catalog/topics.md`. A-1 needs the `Term:` aliases
in `check_cards`.

**Decision**: `check_catalog()` returns a **three-tuple**
`(subtopics, marked, terms)`, where `terms` is `{subtopic name: [alias, ...]}`
holding only subtopics that carry a non-empty `Term:` line. `check()` threads it
through as a keyword argument: `check_cards(project, subtopics, report, marked,
terms=terms, strict=strict)`.

**Rationale**. It follows the shape `marked` already has — computed in
`check_catalog` while the catalog is parsed, consumed in `check_cards` — so no
second parse and no new module. `terms` defaults to `None` on `check_cards`, so
that signature stays backwards compatible.

**Cost**: exactly **one** existing call site unpacks `check_catalog`'s return —
`tests/test_check_project.py:857`
(`test_also_covers_is_not_parsed_as_a_subtopic`). It becomes a three-way unpack.
No other test and no other module calls `check_catalog` directly.

**Alternatives considered**: (a) a `CatalogFacts` dataclass — more churn than the
problem justifies, and `marked` would have to move into it too; (b) re-parsing
the catalog inside `check_cards` — a second read of the same file and a second
place for the `Term:` rule to live, contradicting the reuse note in FR-011.

## R3 — Does the A-2 rule really produce zero false positives here?

**Method**: prototyped the full FR-013 rule (bracket-depth scan → maths gate →
head term → `topic_key` → space-padded token match against the other cards in
the same file) and ran it over every `#list(` back in the repository.

**Result** — reproduced exactly, and it matches what the spec asserts:

```
tests/fixtures/demo-project/cards/geography.yaml card 1 (Y4H26)
  items = ['Torvig', 'Little Kestrel', 'Skarn', 'Ovray', 'Bellhorn']
  Torvig          -> OK        (card ZRKBA: "Torvig Harbour ...")
  Little Kestrel  -> OK        (card X4958: "... on Little Kestrel ...")
  Skarn           -> ORPHAN
  Ovray           -> OK        (card 00GA5: "... Ovray Cove ...")
  Bellhorn        -> ORPHAN

cards/example.yaml card 2 (4V946)
  items = ['$P(A) >= 0$ for every event $A$', '$P(Omega) = 1$',
           '$sigma$-additivity for disjoint events']
  all three -> maths gate, skipped
```

**Conclusions**:

- Exactly two orphans exist in the repository, both in `geography.yaml`, both
  named by FR-023. The rule finds them and nothing else.
- `cards/example.yaml` is untouched, confirming FR-013a: the maths gate must not
  be weakened to strip-maths-then-head-term, or two of those three items become
  false positives. **Which gate would catch that is worth naming, because the
  obvious answer is wrong**: `lernkarten check cards/example.yaml` cannot report
  an orphan at all — `bin/lernkarten` imports `engine`, `deps`, `cardid` and
  `build_pdf`, never `check_project`. The detector is
  `python3 scripts/check_project.py .`, and since CI runs the project checker
  only over `tests/fixtures/demo-project` (`.github/workflows/ci.yml:120`), the
  plan pins it with a pytest case over the shipped file instead of relying on a
  manual command.
- **A-2 can therefore be an error**, as FR-015 requires.

**Amended in cross-model review (W3)**: ` - ` (spaced hyphen-minus) joins the
separator set — `[Amber - the middle stage]` is what a keyboard produces where
this repo writes an em dash, and without the cut it was A-2's one realistic
false positive. Spaced, so hyphenated compounds (`sigma-additivity`,
`Half-mast`) are not torn. Neither `#list` back above contains a spaced hyphen,
so the zero-false-positive measurement stands unchanged.

## R4 — Which demo subtopics actually need an anchor card?

**Method**: prototyped A-1 over the fixture with a candidate `Term:` set,
per `(card file, subtopic)` pair.

**Result**:

| Card file | Subtopic | Verdict |
|---|---|---|
| `geography.yaml` | The five islands | anchored by `five inhabited islands` (card Y4H26's front) |
| `geography.yaml` | Settlements | matched only by an inflected alias — see the note below |
| `tides.yaml` | Rhythm of the tide | **no card names it — needs an anchor** |
| `tides.yaml` | Range and the rule of twelfths | anchored by `Tidal range` / `rule of twelfths` |
| `tides.yaml` | Chart datum and the Ovray rule | anchored by `Chart datum` |
| `palirroia-el.yaml` | Rhythm of the tide | anchored by `παλίρροια` |
| `palirroia-el.yaml` | Range and the rule of twelfths | anchored by `εύρος` |
| `priliv-ru.yaml` | Range and the rule of twelfths | anchored by `правило двенадцатых` |
| `priliv-ru.yaml` | Chart datum and the Ovray rule | anchored by `нуля глубин` |
| `gezeiten-de.yaml` | Tidenrhythmus | no card names it |
| `gezeiten-de.yaml` | Tidenhub | no card names it — `Nipptidenhub` is one token |
| `signals.yaml` | The six flags | no card names it |
| `signals.yaml` | Rules of use | no card names it (a description, not a term) |

**Findings that change the design**:

1. **`topic_key()` does no stemming, so an alias must be written in the exact
   inflected form the cards use.** The Russian card says `от нуля глубин`
   (genitive), not `нуль глубин` (nominative); the Greek says
   `εύρος της παλίρροιας`. This is not a defect — exact matching is what keeps
   the check from crying wolf — but it *is* something `skills/catalog/SKILL.md`
   has to say when it documents the line (FR-027), or a user will write the
   dictionary form and get a finding they cannot explain.
2. **Matching is a token sequence, not a substring.** `Nipptidenhub` contains
   `tidenhub` as a substring and must **not** anchor `Tidenhub`. This is the
   single most important behavioural property of A-1 and it gets its own unit
   test rather than a fixture card (see R6).
3. `Settlements` and `Rules of use` are **descriptions, not terms**. Under
   FR-011 they simply carry no `Term:` line, and A-1 stays silent — which is
   also the fixture's demonstration of FR-011a.

**Amended in cross-model review (W2)**: the three unanchored named-concept
pairs above (`Tidenrhythmus`, `Tidenhub`, `The six flags`) are no longer left
out of the `Term:` set. All three are anchored by rewording existing cards —
plan §3(b2)/(b3) — at zero count cost, so the R5 budget below is unaffected.
The table above measures the tree before this feature.

## R5 — The fixture budget (the one that reshaped the plan)

**Open because**: the task context stated that the demo card count lives in two
places, `DEMO_CARD_COUNT` (`tests/test_e2e.py:27`) and a bare
`assert counts["cards"] == 31` (`tests/test_check_project.py:164`), and that
`tests/test_e2e.py:1110` derives a page count from the first.

**That is incomplete.** `tests/test_e2e.py` builds the *whole* demo deck
(`*CARDS`) in more than twenty tests, and many of them assert **bare page-count
literals** rather than deriving from `DEMO_CARD_COUNT`. Those literals move
whenever the deck crosses a sheet boundary.

The arithmetic (`2 × ⌈cards ÷ per-sheet⌉`, 8 up at a7, 16 up at a8):

| Deck size | a7 pages | a8 pages | mixed build (deck + 1 card) |
|---|---|---|---|
| 31 (today) | 8 | 4 | 8 |
| **32** | **8** | **4** | **10** |
| 33 | 10 | 6 | 10 |
| 37 | 10 | 6 | 10 |

**Decision**: **the demo deck ends at exactly 32 cards — one card added, no
more.** The A-2 fix is made by *rewording* an existing card rather than adding
two, and the three A-1 gaps outside `tides.yaml` are closed the same way —
rewords of `HNHF1`, `R3WZ4` and `NKQK0`, zero count cost (review W2).

**Rationale**. At 33 or more, fifteen assertions across `tests/test_e2e.py` move
(`:83`, `:84`, `:98`, `:118`, `:255`, `:419`, `:420`, `:428`, `:441`, `:442`,
`:485`, `:751`, `:754-755`, `:768`, `:782-783`, `:786`, `:845`, `:853`) — each
one a real assertion somebody reasoned about, and several of them structural
(`marks[:4] == [{"1/2"}] * 4` becomes `marks[:5]`, `range(2)` becomes
`range(3)`). That is a large, error-prone diff bolted onto a feature that is
about neither printing nor page counts, and it would bury the change under
churn.

At exactly 32 the a7 and a8 sheet counts do not move at all, and precisely
**four** assertions change:

| Site | Today | Becomes | Why |
|---|---|---|---|
| `tests/test_e2e.py:27` | `DEMO_CARD_COUNT = 31` | `= 32` | FR-023 |
| `tests/test_e2e.py:97` | `assert "10 cards" in ...` | `"11 cards"` | the new card is in `tides.yaml`, which `--topic Tides` selects |
| `tests/test_e2e.py:255` | `pdf_pages(target) == 8` | `== 10` | the mixed build is 32 + 1 = 33 cards → 5 sheets |
| `tests/test_check_project.py:164` | `== 31` | `== 32` | FR-023 |

Plus three stale prose comments that already said the wrong number before this
feature and should be corrected while the file is open: `:81-82` ("29 cards"),
`:415` ("29 demo cards"), `:745` ("29 cards"), `:1106` ("31 cards").

**Verified**: rewording card `ZRKBA`'s back to

```
'Torvig Harbour has the only deep-water pier. \ From there the mail boat
 redistributes goods to Little Kestrel, Ovray, Skarn and Bellhorn.'
```

(137 characters, well inside the ~400 budget) closes **both** orphans and leaves
`Torvig`, `Little Kestrel` and `Ovray` anchored as before. Prototyped, all five
items report OK. It is also a better card than the one it replaces: it says
where the goods actually go.

**Alternative considered and rejected**: keeping the deck at 31 by rewording the
`Rhythm of the tide` anchor into an existing card too. Zero test churn, but the
demo would then never demonstrate an anchor card *being added*, and FR-023's
mandate that both count sites be updated would be vacuous. One added card buys
the demonstration for four line edits.

## R6 — Where does each red case live?

`check_project.py` scans only `<project>/cards/*.yaml` and
`<project>/catalog/topics.md`. `tests/fixtures/demo-project/broken/` is under
neither, has no catalog of its own, and its README documents reactions of
`lernkarten check` and the build — not of the project checker.

**Decision**: **both** red cases are `tmp_path` projects built with the existing
`project()` helper (`tests/test_check_project.py:106`), and **nothing is added
to `broken/`**.

- A-1's red case must be `tmp_path` — FR-022 forces it.
- A-2's red case *may* live in `broken/` (FR-022 permits it), but putting it
  there would need either a new row in `broken/README.md` that contradicts that
  file's stated premise, or a test that hand-assembles a project around the
  file. A `tmp_path` project is shorter, is where every other `check_project`
  red case already lives, and keeps `broken/` meaning one thing.

**Consequence for FR-024**: `broken/README.md` gains no row. The new failure
modes are documented in `tests/fixtures/demo-project/README.md` instead — FR-024
explicitly allows "or the fixture's own README" — as a short section naming both
checks, what satisfies them in the demo, and that their red cases are built in
`tmp_path` because the checker never sees `broken/`.

Every edge shape that would otherwise want a fixture goes into `tmp_path`
instead, which is both cheaper and more precise:

| Shape | Where |
|---|---|
| substring is not a token (`Nipptidenhub` ≠ `Tidenhub`) | `tmp_path` |
| alias in a second script anchors a second file | `tmp_path` + the demo (`παλίρροια`) |
| a subtopic with no `Term:` is silent | `tmp_path` + the demo (`Settlements`) |
| an empty `Term:` line | `tmp_path` |
| an unbalanced bracket scan skips the card | `tmp_path` |
| a maths item is skipped | `tmp_path` + `cards/example.yaml` |
| an item named only on its own card is still an orphan | `tmp_path` |
| a subtopic with zero cards is exempt | the demo (`Right of way in the Kestrel Deep`) |

## R7 — Does `GOOD_CARDS` survive? (the fifteen call sites)

**Verified.** `GOOD_CARDS` (`tests/test_check_project.py:65`) is one card,
`subtopic: 'Rhythm of the tide'`, front *"How long is a tidal day?"*, back
*"24 h 50 min."* — it names neither *rhythm* nor *tide*. It is paired with
`GOOD_CATALOG` (`:37`), whose single subtopic carries only a `References:` line.

It is used at **fifteen** call sites. A grep for the name reports seventeen
lines, but `:65` is the definition itself and `:1096` is a docstring; the
fifteen that matter are the uses, `:112` — the default argument of `project()` —
among them, which is why so many tests reach it without naming it.

Under D1, A-1 keys off `Term:`. `GOOD_CATALOG` has no `Term:` line, so `terms`
is empty and A-1 emits nothing. **All fifteen call sites are unaffected**, and
in particular `test_a_minimal_project_is_clean` (`:173-175`), which asserts *no
errors and no warnings*, stays green.

This property is load-bearing and is stated as an assumption in the spec: any
future tightening of A-1 that matched against the heading rather than a `Term:`
line would have to rewrite fifteen tests. The plan adds a test that pins it
(`test_a_subtopic_without_a_term_line_is_silent`) so it cannot be lost by
accident.

## R8 — `--strict`, and what "green on the fixture" means

CI runs `python scripts/check_project.py tests/fixtures/demo-project --strict`
(`.github/workflows/ci.yml:120`), where a warning fails the build just as an
error does. Two consequences for the fixture edit:

1. The new anchor card must carry a unique five-character Crockford `id:`, a
   `subtopic:` that is in the catalog, and a `source:` — `check_cards` warns on
   a missing `id` under `--strict`, and warns on a missing `source` always.
2. **The A-2 fix may not be made by adding cards under `Relief and the crater`**,
   even though that is the subtopic that mentions Bellhorn. It carries
   `Status: out of scope`, and `check_cards` warns for every card whose subtopic
   is marked — which under `--strict` is a failure. This is why the fix is a
   reword of a card already under `The five islands`.

## R9 — Malformed and edge-case `Term:` lines

The spec does not say what an empty or unparseable `Term:` line does. Three
shapes exist and each needs a decision:

| Shape | Decision | Rationale |
|---|---|---|
| `Term:` with nothing after it | **error** in `check_catalog`: *"subtopic 'X': 'Term:' is empty — name the term, or leave the line out"* | present-but-useless must not be silently equivalent to absent; this mirrors the existing invalid-`Status:` error one loop above |
| `Term: (see above)` — parses to zero names after `PARENTHETICAL` stripping | **same error** | same shape, same message |
| `Term:` on a **topic** (`##`) rather than a subtopic | **silently ignored** | consistent with today: `parse_catalog` attaches every attribute to whatever entry it is under, and `Parents:` on a topic or `Also covers:` on a subtopic is already ignored without comment |
| a term containing a comma (*"Governance, risk & compliance"*) | **torn into two aliases** | `catalog_names(line, known=())` splits on every comma; `Term:` has no natural `known` set to match against first. Documented as a limitation in the contract: write a comma-free alias |
| a trailing parenthetical (`Term: Chart datum (LAT)`) | **stripped**, giving `Chart datum` | `PARENTHETICAL` already does this for `Also covers:`; it is the desirable behaviour and needs no new code |

## R10 — Performance

Both checks are O(cards × aliases) and O(list items × cards) over strings
already in memory — `check_cards` has already read and parsed every card file
by the time either runs. No file is opened that was not opened before, and
`knowledge/` is never touched. SC-007 (the run stays under a second) is met by
construction; the plan adds no timing test because there is nothing to regress.

## Summary of Phase 0 decisions

| # | Decision |
|---|---|
| R1 | No library, no dependency. The bracket-depth scan is the one narrow hand-rolled piece, justified under constitution III |
| R2 | `check_catalog` returns `(subtopics, marked, terms)`; `check_cards` takes `terms=None`. One test call site updates |
| R3 | The FR-013 rule finds exactly `Skarn` and `Bellhorn`, and skips all three of `example.yaml`'s maths items |
| R4 | Only `tides.yaml` / `Rhythm of the tide` needs a new anchor card. Aliases must be written in the inflected form the cards use |
| R5 | **The demo deck ends at exactly 32 cards.** One added card, four reworded cards, four assertion edits — not fifteen |
| R6 | Both red cases are `tmp_path` projects. `broken/` gains nothing; the demo README documents the two modes |
| R7 | `GOOD_CARDS` and all fifteen call sites are unaffected, and a new test pins that |
| R8 | The fixture must be clean under `--strict`: ids, sources, and no cards under a marked subtopic |
| R9 | An empty `Term:` is an error; a misplaced one is ignored; a comma cannot appear inside an alias |
| R10 | No measurable cost, no timing test |
