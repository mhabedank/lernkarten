# Feature Specification: Enumeration tiers — how long a list may be, and what a counted front over prose means

**Feature Branch**: `feat/enumeration-tiers`

**Created**: 2026-09-07

**Status**: Draft

**Input**: GitHub issue [#83](https://github.com/mhabedank/lernkarten/issues/83), the half PR [#96](https://github.com/mhabedank/lernkarten/pull/96) did not take. Bug report: [specs/007-deck-anchors/bugs/BUG-009.md](../007-deck-anchors/bugs/BUG-009.md).

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/cards` (the rule a card is written to, and the reactions in its checker step), build machinery (`scripts/check_project.py`, `tests/`, `tests/fixtures/demo-project`). `/print` is untouched: nothing here changes what a card *is*, only which shape the model gives it and what the checker says about the shape. `/sources`, `/ingest`, `/catalog`, `/learning-goal` and `/research-gaps` are untouched.

**Implementation half**:

- [ ] **Model-driven** — a prompt change under `skills/<name>/SKILL.md`.
- [ ] **Deterministic** — Python under `scripts/` or `bin/lernkarten`, and/or Typst under `templates/`.
- [x] **Both** — and the seam is the `back` string in `cards/*.yaml`:
  - the **model-driven half** decides whether a fact is an enumeration at all, how its items are grouped, and which elaboration is a second card. That is judgement, and it lives in `skills/cards/SKILL.md`.
  - the **deterministic half** never decides what an enumeration is. It counts what was written — items in a `#list([…])`, a numeral in a front — and reports only where counting alone settles the question. Everything that needs judgement is a **warning**; only E-1, which shipped, is an error.

**Who runs into this**: both. The user driving Claude gets decks whose long enumerations are learnable instead of a queue of ten items; a contributor gets new warnings and new demo-project material.

## Why this is not a patch to 007-deck-anchors

BUG-009 traced this to 007-deck-anchors because that feature owns A-2, the only rule the repo has about `#list([…])` backs. The fix is a feature rather than a patch for one reason: **A-2 constrains what is inside a list, and this constrains whether there is a list and what shape it has.** The two meet on the same string, so the interaction has to be specified rather than discovered.

The interaction was measured against the shipped code before this spec was written, and it is milder than BUG-009 assumed:

> A-2 (`_check_orphans`) requires only that **some other card in the same file** names an enumerated item. One prose card naming all four items satisfies A-2 for all four; it does **not** demand a dedicated card per item.

So converting a prose back into a list costs at most one companion card, not *n*. E-2-as-warning beside A-2-as-error is a coherent pair, and the "green deck turns red" fear is bounded. The remaining sharp edge is grouping: see FR-011 and Q2.

## Measurements this spec is built on

Run against `tests/fixtures/demo-project/cards/*.yaml` plus `cards/example.yaml` with the shipped `_announced_count` and `_list_items`. These are counts, not estimates, and three of them overturn the shape issue #83 proposed.

| What | Result |
|---|---|
| Fronts that announce a count, whole repo | **4** — `Y4H26` (five/5), `4V946` (three/3), `1E782` (two, no list), `F3M2Q` (six, no list) |
| Enumerations of six or more items | **0**. Neither tier above "flat" has a single instance to point at |
| E-2 as issue #83 scopes it (numeral ≥ 3, no `#list`) | fires on **`F3M2Q`** — *"Describe how the range is distributed over the six hours of the flood"*. A good card: "the six hours" is a span of time, not a promise of six items |
| E-4 as issue #83 scopes it (counted front **and** a second question) | fires on **nothing**. Its one intended target, `NKQK0` — *"Which two of the six flags call for help, and how do they differ?"* — announces *two* counts, so `_announced_count` returns nothing and E-4 never sees it |
| Fronts with a second question, any front | **6** — `GG2H5`, `NKQK0`, `A7BSD`, `0TMD9`, `R7XQ4`, `2J1EA`. All shipped, all passing, all in the fixture CI runs under `--strict` |

Two consequences run through everything below. **A numeral in a front is not an enumeration prompt** — F3M2Q proves it — so E-2 needs a verb, not just a number. And **the general no-double-questions rule is what is unchecked**, not the counted slice of it: this repository's own deck breaks the rule six times, so E-4 cannot be added as scoped without first deciding whether `…, and why?` is a double question at all (Q3).

## Clarifications

### Session 2026-09-07

- Q: Where do the tier boundaries sit, and are they item counts at all (FR-002)? → A: **1–2 a sentence, 3–5 flat `#list`, 6–8 one card but grouped, 9+ an anchor card plus one card per group** — issue #83's proposal, confirmed. Counted in **items**, because the physical half is already checked: `MAX_BACK` warns at ~400 characters and the build warns when text runs off the card, so a measured budget would duplicate an existing check and still miss the cognitive question. The boundary that decided it is 5: the shipped `Y4H26` lists five islands flat and is a good card, so a flat tier ending below five would have made this repository's own fixture illegal.
- Q: What does "grouped" mean to a checker (FR-011)? → A: A **labelled item** — `#list([*Discover*: a, b], [*Define*: c, d])`. An item whose text opens with emphasis followed by a colon is a group; everything after the colon is its members, comma-separated. Deterministic, reuses `_list_items`, and gives the learner the hierarchy the tier exists for. **A-2 moves with it** (FR-011b): it descends into a group item and checks the *members*, rather than cutting at the first `:` and checking the label. Without that, introducing the shape would silently shrink A-2's coverage — the exact drift BUG-009 documents.
- Q: What happens to E-4 (FR-013)? → A: **Dropped from this feature**, and the general rule ticketed separately. E-4 as issue #83 scopes it — a counted front that also asks a second thing — fires on **nothing** in this repository: its one intended target `NKQK0` announces two counts and is invisible to `_announced_count`. The real gap is the *general* no-double-questions rule, which `CLAUDE.md` § Card style asserts and nothing checks, and which **six** shipped fixture cards break. Whether `…, and why?` is a double question at all is a decision with a six-card blast radius and does not belong in this feature's scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A long enumeration is written to be learnable (Priority: P1)

Someone runs `/cards` over material with a six-step process. Today, since PR #96 removed the four-item cap and put no length rule in its place, they get one card with a flat six-item list — or, because the model has no rule to reach for, a paragraph. They want the shape that can actually be recalled: the count is kept, the items are grouped, and the card still tests all six in one act.

**Why this priority**: it is the half of #83 that was deleted without a replacement. The cap is gone and nothing says how long a list may be, which is a worse state than the wrong cap was.

**Independent Test**: write a card file with a six-item and a ten-item enumeration, run `python3 scripts/check_project.py .`, and read what it says about each.

**Acceptance Scenarios**:

1. **Given** a card whose front announces a count in the flat tier and whose back is a flat `#list` of exactly that many items, **When** the checker runs, **Then** it says nothing.
2. **Given** a card whose front announces a count above the flat tier and whose back is a flat, ungrouped `#list`, **When** the checker runs, **Then** it emits **one warning** naming the card by its 1-based index, the count, and the tier it has crossed.
3. **Given** the same enumeration written as a grouped `#list`, **When** the checker runs, **Then** it is silent.
4. **Given** an enumeration in the split tier, **When** `/cards` writes it, **Then** the deck holds an anchor card that states the total and names the groups, plus one card per group, and each of those cards' fronts announces its own count (so E-1 tests both levels).

---

### User Story 2 - A counted front is not answered in prose (Priority: P2)

Someone's deck has *"What are the four types of work in the research phase?"* answered by a sentence. To grade it they must segment prose, count it, and only then compare — at the moment they are supposed to be delivering a binary verdict. They want to be told, without being blocked.

**Why this priority**: P2, not P1, because it is judgement. The measurement above shows a naive trigger already misfires on a good card in this repository, so the requirement carries a narrower trigger and the finding is a warning.

**Independent Test**: a card file with *"Name the four stages"* over a prose back, and one with *"Describe how the range is distributed over the six hours"* over a prose back. The first warns; the second does not.

**Acceptance Scenarios**:

1. **Given** a front that both announces a count of three or more **and** opens with an enumeration prompt, **When** its back carries no `#list([…])`, **Then** the checker warns once, naming the card and the count.
2. **Given** `F3M2Q`'s front — a count with no enumeration prompt — **When** the checker runs, **Then** it is **silent**. This scenario is a regression guard on the fixture and fails any implementation that triggers on the numeral alone.
3. **Given** a front announcing two different counts, **When** the checker runs, **Then** it is silent, exactly as E-1 already is.
4. **Given** a card that E-2 warns about, **When** its back is rewritten as a `#list`, **Then** A-2 is satisfied as soon as **one** other card in the file names the items — not one card per item.

---

### User Story 3 - The rule is written where a rule lives (Priority: P1)

A contributor reading `skills/cards/SKILL.md` cold can state how long an enumeration may be and what happens above that length. Today the file says there is no fixed cap and stops.

**Why this priority**: equal first. The deterministic half only reports; the model-driven half is what actually writes the card, and a check with no rule behind it teaches nobody.

**Independent Test**: read the skill and `CLAUDE.md` § Card style and state the tiers without consulting the issue.

**Acceptance Scenarios**:

1. **Given** the shipped skill, **When** a reader looks for the length rule, **Then** they find the tier table and the reaction to every new checker message in step 6.
2. **Given** a subtopic whose enumeration is split across an anchor and per-group cards, **When** `/cards` counts its cards, **Then** the 3–8 card budget is honoured or the skill says explicitly which way it yields.

### Edge Cases

- **An enumeration whose items carry maths** — `[$P(Omega) = 1$]`. The maths gate is E-1's and A-2's, not the tier rule's: counting items does not read inside them, so a maths item counts like any other.
- **A grouped list read by A-2**. Resolved by FR-011b: A-2 descends into a group item and checks its members. Left alone, its head-term rule would cut `[*Discover*: a, b]` at the first `:`, demand an anchor for `Discover` and never see `a` or `b` — coverage lost without a single failing test to show it. The group label itself is exempt (FR-011c).
- **A group with one member** — `[*Discover*: a]`. Legal markup and pointless structure. It is not a finding: a rule that counted groups as well as items would be a second tier table, and the members still reach A-2 either way.
- **A deck in a language with no number-word table**. Digits still work; words do not. E-2 inherits this from `_announced_count` unchanged, and stays quiet rather than guessing.
- **An enumeration prompt with no numeral** — *"Name the inhabited islands"*. No count is announced, so neither E-1 nor E-2 fires. Legitimate open prompt, left alone.
- **Text that does not fit**: unchanged. `MAX_BACK` already warns at ~400 characters and the build warns when text actually runs off the card. The tiers are about what is learnable, not what fits — see Assumptions A-1.
- **Idempotence**: running the checker twice reports the same set; running `/cards` twice does not regroup a list that already satisfies the rule.
- **Missing optional tooling / Python floor / platforms**: unaffected. Pure text analysis over files on disk.
- **Non-Latin card text**: the tier checks count items and never read inside them, so Greek and Cyrillic decks behave identically.

## Requirements *(mandatory)*

### Functional Requirements

**The tier rule (model-driven)**

- **FR-001**: `skills/cards/SKILL.md` MUST carry a tier table stating, for a given number of enumerated items, the shape the back takes. The tiers MUST be expressed in **item counts**, not in characters or rendered height (Assumptions A-1).
- **FR-002**: The tiers MUST be:

  | items | shape |
  |---|---|
  | 1–2 | a sentence; a `#list` of one item is absurd |
  | 3–5 | a flat `#list`, exactly *n* items |
  | 6–8 | one card still, **grouped** into 2–3 labelled groups (FR-011a) |
  | 9+ | an anchor card naming the groups and stating the total, plus one card per group (FR-004) |

  The boundary at five is load-bearing and not a taste: the shipped `Y4H26` lists five islands flat and is a good card, so a flat tier ending below five would make this repository's own fixture illegal.
- **FR-003**: The rule MUST state that an enumeration is **never split to make it shorter**: "name the six steps" does not become two cards of three, because the learner would then never once practise recalling all six. Splitting is permitted only in the top tier and only in the shape FR-004 describes.
- **FR-004**: In the top tier the deck MUST hold an **anchor card that states the total and names the groups** ("the ten steps fall into three phases — name them"), plus one card per group whose front announces that group's own count. The total therefore survives the split and E-1 tests both levels.
- **FR-005**: `CLAUDE.md` § Card style MUST state the tier rule alongside the counted-front rule PR #96 added, and `skills/cards/SKILL.md` step 6 MUST carry a reaction for every message this feature adds, in the shape the two existing reactions use.

**E-2 — a counted front over a prose back**

- **FR-006**: `scripts/check_project.py` MUST warn when a front **announces a count of three or more** and **opens with an enumeration prompt** and the back carries **no** `#list([…])`.
- **FR-007**: "Announces a count" MUST be the existing `_announced_count`, unchanged — same maths gate, same whole-token rule, same silence on two different counts, same per-language number words. One definition of a counted front, shared by E-1 and E-2, or the two drift.
- **FR-008**: "Enumeration prompt" MUST be a closed, per-language set of leading verbs (English `name`, `list`, `state`, `give`; German `nenne`, `liste`, `zähle … auf`). A front carrying a numeral but no such verb MUST NOT warn. This requirement exists because of a measurement, not a hunch: without it the check fires on `F3M2Q`, a card that is correct as written.
- **FR-009**: E-2 MUST be a **warning**, never an error. Whether a particular back should have been a list is judgement, and CI fails the fixture on a warning already, which is enough pressure.
- **FR-010**: E-2's message MUST name the card by its 1-based index within the file, quote the announced count verbatim, and say what to do — the same shape FR-014 of 007-deck-anchors fixed for A-1 and A-2 and PR #96 followed for E-1.

**E-3 — an unchunked enumeration past the flat tier**

- **FR-011**: `scripts/check_project.py` MUST warn when an enumeration is above the flat tier and is **not grouped**.
- **FR-011a**: A **group** MUST be a `#list` item whose text opens with an emphasised label followed by a colon — `[*Discover*: a, b]`. Everything after the colon is the group's members, separated by commas. The shape is documented markup inside the existing `back` string, never a schema key (Format Contracts). A member MUST NOT itself contain a comma; the limitation and its workaround — write a comma-free member — belong in the contract, and it is the same limitation `catalog_names()` already carries.
- **FR-011b**: **A-2 MUST descend into a group item** and check its *members*, instead of applying the head-term cut and checking the label. Without this, introducing the shape shrinks A-2's coverage silently: today `[*Discover*: a, b]` cuts at the first `:` and A-2 demands an anchor for `Discover` while never seeing `a` or `b`.
- **FR-011c**: The group **label** MUST NOT itself be subject to A-2. A label is structure rather than content — the members are what a learner has to recall and what A-2 exists to protect — and in the top tier the anchor card of FR-004 names the groups anyway, so a label that *is* a taught concept is taught there.
- **FR-012**: If E-3 is implemented, it MUST be a **warning** and its message MUST point at the tier table rather than restating it.

**E-4 — not this feature**

- **FR-013**: E-4 is **out of scope** and MUST NOT be implemented here. As issue #83 scopes it — a counted front that also asks a second thing — it fires on nothing in this repository, because its one intended target `NKQK0` announces two counts and is invisible to `_announced_count`. The gap it was aimed at is the *general* no-double-questions rule that `CLAUDE.md` § Card style asserts and nothing checks; six shipped fixture cards break it, so deciding whether `…, and why?` is a double question is a separate piece of work with its own blast radius. Tracked as issue [#98](https://github.com/mhabedank/lernkarten/issues/98). Recorded here so a future reader does not mistake the omission for an oversight.

**Invariants**

- **FR-014**: Every check this feature adds MUST be pure-Python text analysis over files already on disk — no new runtime dependency, no network, no typesetting engine, no reading of `knowledge/`.
- **FR-015**: E-1 MUST be unchanged. It is the only error in this family and its guards are the precedent for how much judgement a check may exercise.
- **FR-016**: The demo project MUST stay green under `python3 scripts/check_project.py tests/fixtures/demo-project --strict`, where a warning fails the build. Since the fixture holds **no** enumeration above the flat tier, new material is required to demonstrate the new modes — the failing cases themselves live in `tmp_path`, per the precedent 007-deck-anchors set in T024.
- **FR-017**: A deck written before this feature MUST still check and build. Nothing here changes the `cards/*.yaml` schema.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | **none** — no new key. What changes is a **convention inside the existing `back` string**: if Q2 chooses a labelled group shape, that shape becomes documented markup rather than a schema change | `skills/cards`, `scripts/check_project.py`, `CLAUDE.md`, the demo cards |

**Backwards compatibility**: every existing project still builds and still checks. The new findings are warnings, and a warning fails only under `--strict`, which no user project runs by default. A deck that ignores the tier rule keeps working; it is told, not blocked.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: the card, indirectly — a grouped list prints as different text in the same box. No template change, no geometry change.
- **Black-only laser print still readable**: yes. If grouping uses emphasis, `*bold*` is a weight, not a colour.
- **Minimum type size respected**: yes — unchanged; the tier rule reduces what a card carries rather than shrinking it.
- **Brand PNGs need re-rendering**: no.
- **Duplex alignment unaffected**: yes.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. E-2 reuses `_announced_count` and `_list_items` outright (FR-007), and the enumeration-prompt set is a closed word list, not stemming or fuzzy matching. Nothing here is a parsing problem a library targets.
- **New runtime dependency**: none.
- **New dev dependency**: none.
- **New external binary**: none.
- **Anything this makes redundant**: none.
- **Engine version change**: no.
- **Platforms verified**: all three via CI, since the change is pure Python and markdown.

### Key Entities

- **Enumeration**: the items of every `#list([…])` in one card back, as `_list_items` already extracts them. The feature adds no new way to write one.
- **Tier**: a band of item counts and the back shape it requires. Not a file, not a key — a rule stated in the skill and partly enforced by the checker.
- **Group**: a labelled subset of an enumeration in the chunked and split tiers. Whether it has a machine-recognisable shape is Q2.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a card file holding a flat enumeration above the flat tier, the checker emits exactly one warning naming that card; on the same enumeration written in the required shape, it emits none.
- **SC-002**: E-2 warns on a counted enumeration prompt over a prose back and is **silent on `F3M2Q`**. Measured on the fixture, not asserted in prose: the fixture stays at zero warnings under `--strict`.
- **SC-003**: The demo project after this feature holds at least one enumeration in every tier the rule defines, so each mode is visible in shipped material rather than only in `tmp_path`.
- **SC-004**: Every new check fails on its assertion before the production code exists, visible in the commit order (constitution XI).
- **SC-005**: The four repo gates stay green — `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py` — and `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` passes with any card-count assertion moved with the fixture (`DEMO_CARD_COUNT` in `tests/test_e2e.py`, and the bare card count in `tests/test_check_project.py`).
- **SC-006**: Reading `skills/cards/SKILL.md` cold, a reader can state the tiers and what happens above each boundary without opening issue #83.
- **SC-007**: No measurable cost: the checker on the demo project stays under a second.
- **SC-007a**: On a card whose back carries a grouped `#list`, A-2 reports an unnamed **member** and never the group label — asserted against a fixture where the label appears nowhere else in the file, so an implementation that keeps the head-term cut fails it.
- **SC-008**: A project written before this feature produces no new **error**, and every new finding names a card and a remedy.

## Assumptions

- **A-1 — tiers are counted in items, not characters.** The physical constraint is already checked: `MAX_BACK` warns at ~400 characters and the build warns when text actually runs off the card. What is *not* checked is whether a flat queue of nine items can be recalled, which is a property of the count and not of the length. Measuring rendered height would duplicate an existing check and still miss the cognitive one. Recorded so a future feature does not re-litigate it.
- **A-2 — the model decides what an enumeration is; the checker only counts.** Every judgement stays in `skills/cards/SKILL.md`, and every check added here is a warning. E-1 remains the only error in the family because counting a numeral against a list length is the only question in it that has one answer.
- **A-3 — E-2 triggers on a verb plus a numeral.** Forced by measurement (`F3M2Q`), not chosen. The verb set is closed and per-language, and a language with no set is simply quiet — the same shape `_announced_count` already has for number words.
- **A-4 — the A-2 interaction is bounded.** One companion card naming the items satisfies A-2 for all of them, verified against the shipped `_check_orphans` before this spec was written. Grouping is the one place this could change, which is why FR-011 refuses to leave the shape undecided.
- **A-5 — the demo project has to grow.** It holds no enumeration above the flat tier, so the new tiers cannot be demonstrated in existing material. New cards land in the fixture's own invented subject, per the subject-agnostic rule; the two cards quoted in issue #83 are real user content and stay in the issue.

## Dependencies

- PR [#96](https://github.com/mhabedank/lernkarten/pull/96) — E-1, `_announced_count`, `_list_items` reuse, and the removal of the four-item cap. Merged; this feature is meaningless without it.
- `007-deck-anchors` — A-2 and its head-term normalisation. Not modified here, but FR-011 may change what it sees.
