# Feature Specification: Deck anchors — `depth` as a ceiling, and every term the deck uses is named by a card

**Feature Branch**: `feat/deck-anchors`

**Created**: 2026-09-01

**Status**: Draft

**Input**: GitHub issue [#49](https://github.com/mhabedank/lernkarten/issues/49) — "depth: expert reads as a slice, not a ceiling — the deck argues about terms it never names"

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/learning-goal` (one paragraph of wording), `/catalog` (one new optional attribute line, `Term:`), `/cards` (a new rule and a new step that runs the checker), build machinery (`scripts/check_project.py`, `tests/`, `tests/fixtures/demo-project`). `/sources`, `/ingest`, `/research-gaps` and `/print` are untouched: FR-018 resolved against a card-level marker, so nothing reaches `/print`.

**Implementation half**:

- [ ] **Model-driven** — a prompt change under `skills/<name>/SKILL.md`.
- [ ] **Deterministic** — Python under `scripts/` or `bin/lernkarten`, and/or Typst under `templates/`.
- [x] **Both** — and the seam is the pair `catalog/topics.md` ↔ `cards/*.yaml`:
  - the **model-driven half** decides *which* concept a subtopic is about and writes a card that names it. That is judgement, and it lives in `skills/cards/SKILL.md` and `skills/learning-goal/SKILL.md`.
  - the **deterministic half** never decides what a concept is. It only asks two mechanical questions of what was written: does at least one card in this file, **under that subtopic**, name the term the subtopic's `Term:` line declares (A-1), and does every item enumerated in a `#list([…])` back appear on another card in the same file (A-2). Both are scoped to a single card file, both read only files already on disk, and neither opens a knowledge document.

**Who runs into this**: both. The user driving Claude in their own project gets a deck that is self-contained in its own vocabulary; a contributor to this repo gets two new checks and two new failure modes in the demo project.

## Clarifications

### Session 2026-09-01

- Q: What counts as "names the term" for A-1 (FR-011)? → A: A new **optional `Term:` attribute line** on a subtopic in `catalog/topics.md`. It extends the closed `ATTRIBUTE` set in `scripts/check_project.py` (`Status|Parents|Also covers|Related|References|Goal`) with `Term`, and carries comma-separated aliases — `Term: Rhythm of the tide, Tidenrhythmus, παλίρροια` — which the existing `catalog_names()` helper already parses. An alias may not itself contain a comma — the helper is called here with no `known` set, so it splits on every one; the limitation and its workaround are in [contracts/catalog-topics-md.md](contracts/catalog-topics-md.md) § Limitations. A-1 matches a normalised alias as a token sequence against the card's text using the existing Unicode-safe `topic_key()` helper. Where `Term:` is present a missing anchor is an **error**; where it is absent A-1 emits nothing, which is exactly this repo's behaviour before the feature and the same "absent means the old behaviour" shape `Status:`, `Parents:`, `Related:` and `Also covers:` already have.
- Q: Does A-1 bind per card file or across the whole deck (a contradiction between the drafted FR-010 and FR-014)? → A: **Per card file.** Every file that carries cards for a subtopic must anchor that subtopic within that file. `Rhythm of the tide` has cards in both `cards/tides.yaml` and `cards/palirroia-el.yaml`, and deck-wide binding would let a single English anchor silently satisfy the Greek deck. Per-file binding is only workable because `Term:` carries aliases.
- Q: What is A-2's normalisation rule (FR-013)? → A: A **maths gate plus head term**. Skip any list item containing a `$…$` span outright; otherwise cut at the first em dash, en dash, comma, colon, semicolon or ` (`, normalise with `topic_key()`, then match as a space-padded token sequence against the concatenated text of the other cards in the same file. Items come out of the `#list(` body by a bracket-depth scan, so nested `[…]` and `[$P(A) >= 0$ for every event $A$]` parse correctly; an unbalanced scan skips the card. Because the rule produces zero false positives on both `#list([…])` backs that exist in this repo, A-2 is an **error**, not a warning.
- Q: Should an `awareness`-level card generated under `depth: expert` be marked, for a future `/print` filter (FR-018)? → A: **No new card key.** The `cards/*.yaml` schema stays frozen: nothing consumes such a key today and `/print` has no filter to feed it, so adding it later is purely additive. Rejected alternative, recorded so a future feature does not re-litigate it: an optional `level: awareness|working|expert` on a card.
- Q: Does the anchor bind per subtopic or per catalog bullet (FR-019)? → A: **Per subtopic (`###` heading)** — forced, not chosen. `parse_catalog` builds `Entry(kind, name, heading, attributes)` from headings and `Key: value` lines and discards every other body line; the demo catalog contains zero `- ` bullets under any subtopic (its bodies are prose sentences, despite `skills/catalog/SKILL.md` asking for bullets); and no card key points at a bullet, whereas `subtopic:` already points at a `###` heading and is already validated against the catalog.
- Q: Does step 3's fan-out need a merge pass that sees the whole deck (FR-020)? → A: **No whole-deck merge pass.** Neither check crosses an agent boundary: the fan-out is one agent per topic, card files are one per topic, and a multi-parent subtopic is written once into its primary parent's file. Instead `skills/cards/SKILL.md` gains a step that actually runs `python3 scripts/check_project.py .` after the merge — no skill in this repo runs the checker today (it is named in prose in five skills and invoked as a step in none), and step 5's `lernkarten check` cannot host A-1 because it never reads `catalog/topics.md`.

### Session 2026-09-01 (post-checklist)

- Q: Is A-1's haystack every card in the file, or only the cards under the subtopic in question (CHK015 — FR-010 against `data-model.md` §3)? → A: **Only the cards under that subtopic**, in that file. `anchor_text` is keyed `(card file, subtopic)` and the accumulator is what the check actually reads, so a card elsewhere in the same file under a different subtopic does not anchor it. FR-010 narrowed; FR-014, Story 1 scenario 2 and the "exactly one card" edge case moved with it.
- Q: Which of the two A-1 message shapes in `contracts/check-messages.md` is normative (CHK016)? → A: The **explicit** one — `cards/tides.yaml: subtopic 'Rhythm of the tide': no card names the term ('Rhythm of the tide') — one card in this file has to name the concept and say what it is`. It names all three FR-014 elements unconditionally and follows the `f"'{subtopic}': …"` shape `check_cards` already uses for its other per-`(file, subtopic)` judgement, plus the em-dash reason clause every message there carries. The short shape prints only the alias, which leaves a reader of `Term: Chart datum, нуля глубин` under `### Chart datum and the Ovray rule` unable to find the catalog entry; it is demoted to a rejected alternative in the contract.
- Q: Does A-2 name the card by `id` (FR-014 as drafted) or by index (every existing `check_cards` message)? → A: **By 1-based index, `card {i}`** — the deviation is dropped. No message anywhere in `scripts/check_project.py` addresses a card by its id; even `_check_ids`, which exists to check ids, writes `card {index}: unusable 'id' — …`. An `id` is also optional, so an id-where-one-exists rule would give one check two grammars. FR-014 amended; `contracts/check-messages.md`, `data-model.md` §4, `plan.md` §4 R-3 and `quickstart.md` §4 moved with it.
- Q: Is the empty-`Term:` error backed by a numbered requirement, or does it exist only as a plan decision (CHK002)? → A: It is now **FR-011b** — a `Term:` line yielding zero aliases is an error worded after the invalid-`Status:` error one loop above it. It previously lived only in `plan.md` §1 decision 2 and `data-model.md` I-7.
- Q: What does A-1 do about a subtopic marked `Status: gap` or `out of scope` that has cards anyway (CHK006)? → A: **It checks it**, now written down as **FR-009a**. A-1 keys off cards existing, not off the mark; the existing "subtopic is marked" warning is unaffected and is not duplicated. It previously lived only in `plan.md` §1 decision 1, which FR-009 did not cover.
- Q: What does A-2 do with a card whose `back` is missing or is not a string (CHK005)? → A: **FR-012a**. A non-mapping element, or a mapping with no `back`, is skipped entirely — the existing `card {i}: 'front' and 'back' are required` error already covers that card and A-2 must not double-report it. A non-string `back` is coerced with `str()` exactly as the surrounding loop does and then scanned normally, which yields no items and so no finding, and cannot raise.
- Q: Which alias appears in A-1's message when a `Term:` line carries several (CHK017)? → A: The **first**, verbatim as the catalog writes it — now **FR-014a** and a stated rule in the contract rather than something an example implied. Matching stays order-independent: any alias anchors the file.

### Session 2026-09-01 (cross-model review)

- Q: Who ever writes the `Term:` line — is documenting it in `skills/catalog/SKILL.md` enough (review W1)? → A: **No — `/catalog` is instructed to write it.** FR-027 now requires, beyond the documentation, an instruction in the skill's writing guidance: a subtopic whose heading names a concept (not a description of a group of facts) gets a `Term:` line, at latest when its cards exist, with an alias for every language the deck uses. Which headings name a concept is exactly the judgement the seam assigns to the model-driven half; without the instruction A-1 has no writer, never fires outside this repository's fixture, and the format is the dead format FR-027 itself warns about.
- Q: Three named-concept demo subtopics (`Tidenrhythmus`, `Tidenhub`, `The six flags`) are unanchored today, and the draft withheld their `Term:` lines to hold the 32-card budget (review W2). Disclose the omission, or anchor them? → A: **Anchor them, by rewording existing cards** — the same zero-count move FR-023 already makes for `Skarn`/`Bellhorn`. Two backs in `gezeiten-de.yaml` and one front in `signals.yaml` change by one line each; the deck stays at exactly 32 cards, the research R5 budget survives untouched, and the fixture stops demonstrating that the cheapest way to pass A-1 is omission. A bonus: `Nipptidenhub`/`Springtidenhub` stay in the file, so the shipped fixture itself demonstrates the token-not-substring rule.
- Q: Does the head-term cut include the ASCII hyphen (review W3)? → A: **Yes — ` - ` (spaced hyphen-minus) joins the separator set.** `[Amber - the middle stage]` is what a keyboard produces where this repo writes an em dash, and without the cut it was A-2's one realistic false positive. Spaced, so hyphenated compounds (`sigma-additivity`, `Half-mast`) are not torn. Neither `#list` back in the repo contains a spaced hyphen, so research R3's zero-false-positive measurement stands.
- Q: FR-013 said the maths gate skips "a `$…$` span"; the implementation sketch said "any `$`" (review W4). Which is normative? → A: **Any `$`** — deliberately a superset of a balanced span. An unpaired `$` is broken Typst markup, and silence is the safe side for a check that must never cry wolf.
- Q: What is the remedy when A-1 fires on a file whose cards already name the concept in their own language (review W5)? → A: **Add that language's alias to the `Term:` line** — the metadata is stale, not the deck. Writing a redundant card is the wrong fix, and the new `/cards` checker step names the alias remedy explicitly. The "Two languages, one deck" edge case no longer claims such a finding is simply "correct".
- Q: Does A-2's message claim the item was never "explained" (review W6)? → A: **No — "named".** The check tests naming (a token-sequence mention); "explained" would promise judgement a deterministic check cannot make. The message reads `'{item}' is enumerated and never named — no other card in this file mentions it`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every subtopic that has cards has an anchor card (Priority: P1)

A user runs `/cards` against a catalog. For each subtopic that produces cards, one of those cards is the **anchor**: it names the concept the subtopic is about and says what it is — functionally (what it changes, what it costs, what it does not fix), not as a dictionary gloss. The other cards for that subtopic go on doing what they do today: distinctions, formulas, application questions, edge cases.

Today the deck can come out like this, and nothing complains:

```yaml
- subtopic: 'Chart datum'
  front: 'Why does the Ovray rule use a datum lower than mean low water?'
- subtopic: 'Chart datum'
  front: 'Which two readings must be added before a depth is a clearance?'
- subtopic: 'Chart datum'
  front: 'Which chart correction is most often left out of a passage plan?'
```

Three well-formed cards, all of them passing `lernkarten check`, and none of them says what chart datum *is*. The defect only exists at the level of the whole deck.

**Why this priority**: it is the defect the issue is about. It is invisible card by card, it is worst at `depth: expert` (the setting chosen by someone who wants completeness), and the fan-out in `skills/cards/SKILL.md` step 3 makes it more likely, not less, the bigger the project gets.

**Independent Test**: point `python3 scripts/check_project.py` at a project whose catalog has a subtopic carrying a `Term:` line, cards in one file and no card in that file naming any of the term's aliases, and check that A-1 fires and names the file, the subtopic and the term. Shipping just this story, with nothing from Story 2 or 3, already makes the missing-parent shape visible.

**Acceptance Scenarios**:

1. **Given** the A-1 red case — a `tmp_path` project built from demo material whose catalog subtopic carries `Term:` and whose three cards name none of its aliases — **When** `python3 scripts/check_project.py <that project>` runs, **Then** A-1 reports it as an error, and the message names the card file, the subtopic and the term it looked for, not just "a subtopic".
2. **Given** the same project with one anchor card added to that file **under that subtopic**, **When** the checker runs, **Then** A-1 is silent for that subtopic. A card added to the same file under a *different* subtopic does not silence it (FR-010).
3. **Given** a subtopic in `catalog/topics.md` carrying `Status: gap` or `Status: out of scope` — which by the scope rule in `skills/cards/SKILL.md` produces no cards at all — **When** the checker runs, **Then** A-1 says nothing about it: a subtopic with zero cards is not missing an anchor.
4. **Given** the demo project as shipped (after this feature lands), **When** `python3 scripts/check_project.py tests/fixtures/demo-project --strict` runs, **Then** it exits 0 with **no errors and no warnings** — CI runs the fixture under `--strict`, where a warning is a failure just as an error is.
5. **Given** a project with no `goal.md` at all, **When** the checker runs, **Then** A-1 behaves identically — the anchor rule is a property of the deck, not of the optional goal.
6. **Given** a subtopic with cards but **no** `Term:` line in the catalog, **When** the checker runs, **Then** A-1 emits nothing at all — neither error nor warning — which is the behaviour this repo had before the feature.
7. **Given** a subtopic whose `Term:` line carries aliases and whose cards are split over two files, one of which anchors the term and one of which does not, **When** the checker runs, **Then** A-1 reports the file that does not: binding is per card file, so an English anchor in `cards/tides.yaml` does not satisfy the Greek cards in `cards/palirroia-el.yaml`.

---

### User Story 2 - Nothing is introduced only inside an enumeration (Priority: P1)

A card enumerates *k* items in a `#list([…])` back. Every one of those items is also the subject of, or is at least named by, another card in the same file. If it is not, the deck has taught the learner to recite labels:

```yaml
- subtopic: 'Warning stages'
  front: 'Name the four Ashwind warning stages.'
  back: '#list([Green], [Amber], [Ashwind], [Full Ashwind])'
```

If no other card ever touches *Amber*, *Amber* is an orphan. `#list([…])` backs make this cheap to produce and the enumeration card *looks* like coverage on review, which is why it survives a human read-through.

**Why this priority**: it is the second half of the same defect and it is the half that is genuinely mechanical — list items are delimited by the markup itself, so no judgement is needed to find them. It is independently valuable: a deck can pass A-1 and still be a list of labels.

**Independent Test**: point the checker at a project whose card file has a `#list([…])` back with a member that appears in no other card in that file, and check that A-2 fires and names the file, the card and the orphaned item.

**Acceptance Scenarios**:

1. **Given** the demo project's orphan fixture — an enumeration card with one member no other card in the file mentions — **When** the checker runs, **Then** A-2 reports it and the message names the unreferenced item verbatim, so the reader knows which of the *k* it is.
2. **Given** a card file where every list member is named by some other card in the same file, **When** the checker runs, **Then** A-2 is silent.
3. **Given** a list member that appears only on the *same* card that enumerates it, **When** the checker runs, **Then** A-2 still reports it — "some other card" means another card.
4. **Given** a `#list([…])` whose items carry markup (`[$P(Omega) = 1$]`, `[Parallelisation — sectioning and voting]`), **When** the checker runs, **Then** matching uses the maths gate plus head term of FR-013 rather than string equality: the maths item is skipped, the separator item is traced on `Parallelisation`, and the bracket-depth scan does not crash on nested brackets or maths.
5. **Given** `cards/example.yaml`, whose Kolmogorov-axioms card has a `#list([…])` back of three items that appear on no other card in that file, **When** the checker runs, **Then** A-2 is silent: every one of the three contains a `$…$` span and is skipped by the maths gate, so `example.yaml` needs no new cards.

---

### User Story 3 - `depth` reads as a ceiling, so `expert` carries the vocabulary too (Priority: P2)

A user writes `depth: expert` in `goal.md` because they want the deck to carry everything. `skills/learning-goal/SKILL.md` tells them — and tells the model that later reads it — that the level names the **highest** card the deck carries, not the only one: `expert` implies `working` implies `awareness`. `skills/cards/SKILL.md`, which today never mentions `goal.md` or `depth` at all, says the same thing from the other end.

**Why this priority**: it is the cause; A-1 and A-2 are the detectors. It is P2 rather than P1 only because it is documentation and cannot be tested on its own — per Principle XI a prompt change's red artifact is a `check_project.py` check, and here that check is A-1, which Story 1 already delivers. Shipping the wording without the checks would repeat the mistake the issue diagnoses: a suggestion with no test behind it.

**Independent Test**: `python3 scripts/check_docs.py` stays green and the closed set of `depth` values in `check_project.py` (`GOAL_DEPTHS`) is unchanged, so every `goal.md` written before this feature is still valid. The behavioural half is verified through Story 1's checks.

**Acceptance Scenarios**:

1. **Given** the current `skills/learning-goal/SKILL.md`, **When** a reader reaches the `## Depth` section, **Then** it states that the level is a ceiling and that each level includes the ones below it — the three bullets no longer read as mutually exclusive slices.
2. **Given** an existing project with `depth: working` in `goal.md`, **When** any pipeline step runs, **Then** nothing about the file format changed and no migration is needed.
3. **Given** `skills/cards/SKILL.md`, **When** the model reads it, **Then** it finds the anchor rule stated together with the caution that the anchor is **not** a definitional layer beneath everything — one card per named concept, and that card has to earn its recurring review.

---

### Edge Cases

- **A subtopic heading that is a description, not a term** — `### What the harbour office actually does`. Resolved by FR-011: the heading is never matched. The term comes from the optional `Term:` line, and a subtopic whose heading is a description simply carries no `Term:` line, so A-1 says nothing about it.
- **The same term across several topics** — resolved by FR-010 and FR-019: A-1 binds per subtopic and per card file, so each file that carries cards for the subtopic anchors it itself. A term genuinely shared by three subtopics is anchored three times, which is the price of never letting one file's anchor cover another file's cards.
- **Two languages, one deck**. The demo project carries German, Greek and Russian card files, and the catalog is English. Resolved by FR-011 and FR-010 together: `Term:` carries every alias the deck uses (`Term: Rhythm of the tide, Tidenrhythmus, παλίρροια`), and A-1 binds per card file, so the German file must anchor the German alias and the Greek file the Greek one. A subtopic whose aliases do not cover a language its cards are written in will report. When those cards already name the concept in their own language, the finding means the metadata is stale, not the deck — the fix is adding that language's alias to the `Term:` line, and the checker step in `skills/cards/SKILL.md` names that remedy (W5); only when no card names it is the fix an anchor card.
- **Non-Latin card text** — Greek and Cyrillic decks exist in the fixtures. Any normalisation (casefolding, stripping punctuation) must not mangle them, and must not depend on the ASCII alphabet.
- **A subtopic with exactly one card**. The single card may be the anchor: A-1 asks only that *some* card in the file under that subtopic names the term, so a lone card that names it satisfies the check. Nothing in the rule ever demands a second card (FR-008).
- **A subtopic with zero cards is exempt from A-1** (FR-010), so the cheapest way to satisfy the check is to write no cards at all. `Right of way in the Kestrel Deep` is already in exactly that state in the demo project — zero cards, despite an `Also covers:` line pointing at `cards/signals.yaml`. This is an **accepted limitation**: the checker cannot tell a deliberate omission from an evasion, and inventing a "every subtopic must have cards" rule would break the `Status: gap` and `out of scope` shapes the pipeline depends on.
- **Nested and escaped brackets in a `#list([…])` back** — `[$P(A) >= 0$ for every event $A$]` contains no nested bracket, but Typst markup permits one. Resolved by FR-013: extraction is a bracket-depth scan, and an unbalanced scan skips the card rather than crashing or reporting a false orphan.
- **A card file with no catalog subtopic**, or a card whose `subtopic:` key is absent (today only a warning). A-1 has nothing to bind to and must stay quiet rather than inventing a subtopic.
- **Idempotence**: running `/cards` twice must not add a second anchor card for the same subtopic — the merge rule in step 4 of `skills/cards/SKILL.md` already forbids duplicating a front "in substance", and the anchor is the card most at risk of being regenerated.
- **Missing optional tooling / Python floor / platform parity**: both checks are pure text over files already on disk, so there is nothing to degrade and nothing platform-specific. No typesetting engine, no `pdftotext`.
- **Text that does not fit**: an anchor card is subject to the same ~120/~400 character budget as any other card. The rule must not push authors into an overflowing back.

## Requirements *(mandatory)*

### Functional Requirements

**The wording — `/learning-goal`**

- **FR-001**: `skills/learning-goal/SKILL.md` MUST state that `depth` is cumulative: the level names the **highest** card the deck carries, not the only one, and `expert` implies `working` implies `awareness`. The three bullets MUST no longer be readable as three mutually exclusive descriptions.
- **FR-002**: The set of legal `depth` values MUST stay exactly `awareness`, `working`, `expert`. No new value, no new key in the `goal.md` frontmatter, no change to `GOAL_DEPTHS` in `scripts/check_project.py`.

**The rule — `/cards`**

- **FR-003**: `skills/cards/SKILL.md` MUST reference `goal.md` and its `depth`, which it does not do today, and MUST state the cumulative reading from the card-writing end.
- **FR-004**: `skills/cards/SKILL.md` MUST state the anchor rule: every subtopic that produces cards produces at least one card that names the concept the subtopic is about.
- **FR-005**: `skills/cards/SKILL.md` MUST state that no item may be introduced **only** inside a `#list([…])` back.
- **FR-006**: `skills/cards/SKILL.md` MUST state the anchor's *content* standard: a functional definition — what the concept changes, what it costs, what it does not fix — and MUST explicitly rule out a dictionary gloss. The anchor card has to earn its recurring review like any other card.
- **FR-007**: `skills/cards/SKILL.md` MUST state the rule as **anchor, not coverage**: one card per *named* concept, never a definitional layer beneath everything. The prompt MUST NOT instruct the model to add a definition card for every term it mentions — spaced repetition is a fixed-budget instrument and a deck padded with definitions of terms the learner meets daily is worse than one without them.
- **FR-008**: The anchor rule MUST NOT raise the 3–8 cards per subtopic guidance in step 3. The anchor is one of those cards, not a card on top of them.
- **FR-009**: The existing scope rules MUST be unchanged: a subtopic marked `Status: gap` or `Status: out of scope` gets no cards and therefore needs no anchor.
- **FR-009a**: A subtopic marked `Status: gap` or `Status: out of scope` that carries cards **anyway** MUST still be checked by A-1. FR-009 says a marked subtopic gets no cards and therefore needs no anchor; it does not say what happens when the user names the subtopic explicitly and cards exist regardless. A-1 keys off **cards existing**, not off the mark: if a card file holds cards for a subtopic and that subtopic carries a `Term:` line, that file must anchor it. The existing `card {i}: subtopic 'X' is marked 'Status: …'` warning in `check_cards` is unaffected and MUST NOT be duplicated by A-1 — the two say different things about the same card. (Qualifies FR-009 rather than replacing it, hence the suffix.)

**The checks — `scripts/check_project.py`**

- **FR-010**: `scripts/check_project.py` MUST implement **A-1 (anchor)**: for each subtopic in `catalog/topics.md` that carries a `Term:` line, **every card file** holding at least one card for that subtopic MUST hold at least one card **under that subtopic** that names the term. The haystack is that file's cards under that subtopic and nothing else — a card in the same file under a *different* subtopic does not anchor it, which is exactly why the accumulator is keyed `(card file, subtopic)`. The binding is per card file, never deck-wide: an anchor in `cards/tides.yaml` does not satisfy the same subtopic's cards in `cards/palirroia-el.yaml`, because a single English anchor would otherwise silently satisfy the Greek deck. A subtopic with no cards in a file is not a finding for that file, and neither is a subtopic with no `Term:` line.
- **FR-011**: A-1's "names the term" MUST be defined by a new **optional `Term:` attribute line** on a subtopic in `catalog/topics.md`, not inferred from the heading text — `### Rhythm of the tide` is a term, `### What the harbour office actually does` is a description, and no rule can tell them apart. `Term` MUST be added to the closed `ATTRIBUTE` set in `scripts/check_project.py` (today `Status|Parents|Also covers|Related|References|Goal`). The line carries **comma-separated aliases**, e.g. `Term: Rhythm of the tide, Tidenrhythmus, παλίρροια`, parsed by the existing `catalog_names()` helper. An alias MUST NOT itself contain a comma: `catalog_names()` is called here with no `known` set and therefore splits on every comma, so `Term: Governance, risk & compliance` becomes two aliases. The limitation and its workaround — write a comma-free alias — are stated in `contracts/catalog-topics-md.md` § Limitations. A card names the term when a normalised alias matches as a token sequence in the card's text, normalised by the existing Unicode-safe `topic_key()` helper.
- **FR-011a**: Where `Term:` is present, a missing anchor MUST be an **error**. Where `Term:` is absent, A-1 MUST emit nothing — no error, no warning — which is exactly this repo's behaviour before the feature, and the same "absent means the old behaviour" shape that `Status:`, `Parents:`, `Related:` and `Also covers:` already have.
- **FR-011b**: A `Term:` line that is **present but yields zero aliases** — empty, whitespace only, or nothing but a parenthetical that `catalog_names()` strips — MUST be an **error**, reported by `check_catalog` and worded to mirror the invalid-`Status:` error one loop above it: `subtopic 'X': 'Term:' is empty — name the term, or leave the line out`. "Present but useless" must not be silently equivalent to "absent" (FR-011a), or the format carries a shape that means nothing. A line reading `Term: A,,B` is **not** an error: `catalog_names()` drops the empty element and two aliases survive.
- **FR-012**: `scripts/check_project.py` MUST implement **A-2 (orphan)**: every item enumerated in a `#list([…])` back appears in some other card in the same card file. An item appearing only on the enumerating card is a finding.
- **FR-012a**: A-2 MUST NOT report, and MUST NOT crash on, a card whose `back` is missing or is not a string. A list element that is not a mapping, or a mapping carrying no `back` key, is **already** reported by the existing `card {i}: 'front' and 'back' are required` error in `check_cards`; A-2 MUST skip it entirely — contributing neither an enumeration to scan nor text to the haystack — so that one malformed card never yields two findings. A `back` that is present but is not a string (`null`, a number, a list) MUST be coerced with `str()`, exactly as the surrounding per-card loop already does, and then scanned normally; the coerced text contains no `#list(`, so A-2 yields no items and stays silent. A-2 reads a card as `front + " " + back` under the same coercion, the way A-1 does. Skipping a card MUST NOT renumber the ones after it: the 1-based index of FR-014 is the card's position in the file's unfiltered `cards` list, so a skipped card still consumes an index and A-2's `card {i}` always agrees with every other `check_cards` message about the same file.
- **FR-013**: A-2 MUST normalise with a **maths gate plus head term**. An item containing a `$` MUST be skipped outright — deliberately a superset of a balanced `$…$` span, because an unpaired `$` is broken markup and silence is the safe side (amended in the cross-model review, W4); otherwise the item MUST be cut at the first em dash, en dash, spaced hyphen-minus (` - `), comma, colon, semicolon or ` (`, normalised with `topic_key()`, and matched as a space-padded token sequence against the concatenated text of the other cards in the same file. Items MUST be extracted from the `#list(` body by a bracket-depth scan, so that a nested `[…]` inside an item and `[$P(A) >= 0$ for every event $A$]` both parse; on an unbalanced scan the card MUST be skipped rather than reported. By shape: a separator item is traced on the head before the separator; a pure-maths item is skipped; a maths-mixed prose item is skipped; a non-Latin item is traced normally (`topic_key` keeps `\w` under Unicode); a one-word item is itself. An **unspaced** hyphen is not a separator: `Half-mast` is one head, not two (W3).
- **FR-013a**: The maths gate MUST NOT be weakened to strip-maths-then-head-term. `cards/example.yaml` carries a second `#list([…])` back — `#list([$P(A) >= 0$ for every event $A$], [$P(Omega) = 1$], [$sigma$-additivity for disjoint events])` — and none of its three items appears on another card in that file. Under the maths gate all three are skipped, so it is **not** a violation and `example.yaml` needs no new cards; under strip-maths-then-head-term two of them would be false positives. The gate that sees this is `python3 scripts/check_project.py .` over the repository itself — **not** `lernkarten check cards/example.yaml`, which cannot report an orphan at all, because `bin/lernkarten` imports `engine`, `deps`, `cardid` and `build_pdf` and never `check_project`. CI runs the project checker only over `tests/fixtures/demo-project`, so this MUST additionally be pinned by a pytest case over the shipped `cards/example.yaml`, or the only guard is a manual pre-PR command.
- **FR-014**: Both checks MUST name the culprit in the message: A-1 the card file, the subtopic and the term it looked for; A-2 the card file, the card by its **1-based index within the file** (`card 3`) and the orphaned item verbatim. The index, never the `id`: no message anywhere in `scripts/check_project.py` addresses a card by its id — `_check_ids`, which exists to check ids, still writes `card {index}: unusable 'id' — …` — and an `id` is optional, so an id-where-one-exists rule would give one check two grammars and two assertion shapes. A-1's message is per `(card file, subtopic)` pair, matching the binding in FR-010 — a subtopic split over two files that anchors it in neither produces two findings, not one.
- **FR-014a**: Where a `Term:` line carries several aliases, A-1's message MUST name the **first** alias, verbatim as the catalog writes it, and MUST NOT list the rest. This is a rule, not an accident of the examples: matching itself is order-independent (any one alias anchors the file, FR-011), but the message has to be deterministic because the tests assert on it, and the first alias is the one the catalog author put first. A reader who needs the other aliases opens the catalog entry the message already names.
- **FR-015**: Both checks MUST be **errors**, never warnings. A-1 is an error wherever the subtopic carries a `Term:` line and silent where it does not (FR-011a); A-2 is an error because the rule in FR-013 produces no false positive on any `#list([…])` back in this repo. A warning would buy nothing anyway: CI runs `python scripts/check_project.py tests/fixtures/demo-project --strict` (`.github/workflows/ci.yml`), so on the fixture a warning already fails the build.
- **FR-016**: Both checks MUST run on a project with no `goal.md`. The anchor rule is a property of the deck; the `depth` wording is what changes with a goal, not the check.
- **FR-017**: Both checks MUST be pure-Python text analysis over files already on disk — no new runtime dependency, no network, no typesetting engine, and no reading of `knowledge/` documents.
- **FR-018**: An `awareness`-level card generated under `depth: expert` MUST NOT be marked as such. No new key is added to `cards/*.yaml`; the schema stays frozen. Nothing consumes such a key today and `/print` has no filter to feed it, so introducing one later is purely additive and loses nothing by waiting. **Rejected alternative**, recorded so a future feature does not re-litigate it: an optional `level: awareness|working|expert` on a card — rejected because its blast radius reaches `skills/cards`, `scripts/build_pdf.py`, `scripts/check_project.py`, `cards/example.yaml`, `CLAUDE.md` and the demo cards, for a consumer that does not exist.
- **FR-019**: The anchor MUST bind per **subtopic** (`###` heading), never per catalog bullet. This is forced by what exists, not chosen on merit: `parse_catalog` builds `Entry(kind, name, heading, attributes)` from headings and `Key: value` lines and **discards every other body line**, so a bullet is not addressable at all; the demo catalog contains **zero** `- ` bullets under any subtopic, its bodies being prose sentences despite `skills/catalog/SKILL.md` asking for bullets; and no card key points at a bullet, whereas `subtopic:` already points at a `###` heading and is already validated against the catalog.
- **FR-020**: Step 3's fan-out in `skills/cards/SKILL.md` MUST NOT gain a whole-deck merge pass. Neither check crosses an agent boundary: the fan-out is one agent per topic, card files are one per topic, and a subtopic with several parents is written once into its primary parent's file. A-1 binds per card file (FR-010) and A-2 is per card file by construction, so both questions are answerable inside a single agent's output and a merge pass would cost a step and a token budget for nothing.
- **FR-026**: `skills/cards/SKILL.md` MUST gain a step that actually runs `python3 scripts/check_project.py .` after the merge in step 4, and MUST say what to do when it reports. This is the other half of FR-020 and it is load-bearing: **no skill in this repo runs `check_project.py` at all** today — it is named in prose in five skills and invoked as a step in none — and step 5's `lernkarten check` cannot host A-1 because it never reads `catalog/topics.md`. Without this step neither new check ever fires for an actual deck author. (Numbered out of order because the clarify session added it; it belongs with FR-020.)
- **FR-027**: `skills/catalog/SKILL.md` and the catalog convention in `CLAUDE.md` MUST document the optional `Term:` line — what it is for, that it carries comma-separated aliases including the aliases of every language the deck is written in, and that leaving it out means A-1 stays silent. A format the prompts never write is a dead format — and documenting alone does not prevent that: `skills/catalog/SKILL.md` MUST additionally **instruct the writing step** to produce the line. A subtopic whose heading names a concept (not a description of a group of facts) gets a `Term:` line, at latest when its cards exist, with an alias for every language the deck uses. Which headings name a concept is the model-driven half's judgement, per the seam; the line is inert on a subtopic without cards, so writing it early costs nothing (amended in the cross-model review, W1).

**The fixtures**

- **FR-021**: `tests/fixtures/demo-project` MUST stay the only corpus, per the testing rule in `CLAUDE.md`, and MUST gain the material both checks need: `Term:` lines on the catalog subtopics that have cards, so A-1 has something to bind to at all, and cards in those files that anchor them. Where a *failing* shape cannot live inside the scanned project without breaking `test_the_demo_project_is_consistent`, it is built from demo material in `tmp_path` (FR-022) rather than invented as a new fixture directory.
- **FR-022**: Each red case MUST live where the checker can actually see it. `check_project.py` scans only `<project>/cards/*.yaml` and `<project>/catalog/topics.md`; `tests/fixtures/demo-project/broken/` is never scanned and carries no catalog of its own. Therefore **A-1's red case MUST be a `tmp_path` project** built from demo material — a catalog subtopic with a `Term:` line and cards that never name it — because `broken/` cannot express it. A-2's red case MAY live in `broken/`, since it needs no catalog; if it does, FR-024's row MUST say that the reacting tool is `check_project.py`, because `broken/README.md` documents reactions of `lernkarten check` and the build, not of the project checker. Neither case may break `test_the_demo_project_is_consistent`, which asserts the demo project itself reports nothing.
- **FR-023**: The demo project's own deck MUST satisfy both new checks once they exist. Today it does not: `tests/fixtures/demo-project/cards/geography.yaml` enumerates `[Torvig], [Little Kestrel], [Skarn], [Ovray], [Bellhorn]` and no other card in that file mentions *Skarn* or *Bellhorn* — a genuine A-2 violation that this feature MUST fix. Changing the demo cards moves the expected card count, which lives in **two** places, not one: `DEMO_CARD_COUNT` in `tests/test_e2e.py` and a bare `assert counts["cards"] == 31` in `tests/test_check_project.py`. Both MUST be updated, and `tests/test_e2e.py` derives a page count from `DEMO_CARD_COUNT` (`2 × ⌈cards ÷ 8⌉`), so that assertion moves with it.
- **FR-024**: `tests/fixtures/demo-project/broken/README.md` (or the fixture's own README) MUST gain a row per new failure mode, naming the expected reaction, as every other failure mode there does.
- **FR-025**: Per Principle XI the checks and their failing cases MUST be committed red — failing on the assertion, against what the current prompts produce — before the two `SKILL.md` files change.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | **new optional `Term:` line** on a subtopic, carrying comma-separated aliases (FR-011). Absent means the pre-feature behaviour — A-1 says nothing — exactly as `Status:`, `Parents:` and `Related:` are optional today, so no existing catalog needs editing | `skills/catalog` (FR-027), `scripts/check_project.py` (`ATTRIBUTE`, `parse_catalog`), the demo catalog, `CLAUDE.md` |
| `cards/*.yaml` schema | none — no level marker, no new key (FR-018). The demo deck's *content* changes (FR-023), its schema does not | the demo cards and the two card-count assertions (FR-023) |
| `goal.md` frontmatter | none — `depth` keeps the same three values and the same key (FR-002) | `skills/learning-goal` (wording only) |

**Backwards compatibility**: every project on disk still builds. `lernkarten build` and `lernkarten check` are untouched — both new checks live in `scripts/check_project.py`, which is the contributor-facing checker, not the user-facing build. The one format change is the optional `Term:` line, and its absence means the pre-feature behaviour (FR-011a), so no existing catalog needs editing and no existing project gains a finding it did not have before.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: none. No template, no press sheet, no brand graphic. The deck gains cards; the cards look exactly as they look today.
- **Black-only laser print still readable**: N/A
- **Minimum type size respected**: N/A
- **Brand PNGs need re-rendering**: no
- **Duplex alignment unaffected**: yes — card count changes, layout does not, and the page count stays `2 × ⌈cards ÷ per-sheet⌉`.

One caveat: an anchor card is one more card per subtopic, so a deck that gains anchors gains pages. That is a print consequence of a content rule, and it is exactly why FR-007 forbids the definitional layer.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. FR-011 and FR-013 both normalise through the existing `topic_key()` helper and parse through the existing `catalog_names()` helper, and the head-term rule is a cut at a fixed separator set — exact token matching, not fuzzy matching, so no stemming or fuzzy-match library is warranted. The bracket-depth scan is a dozen lines over a Typst fragment no parser in the wild targets.
- **New runtime dependency**: none.
- **New dev dependency**: none.
- **New external binary**: none.
- **Anything this makes redundant**: none.
- **Engine version change**: no.
- **Platforms verified**: all three. Pure text processing with no platform surface; CI's Windows legs cover it.

### Key Entities *(include if the feature involves data)*

- **Anchor card**: the one card under a subtopic that names the concept the subtopic is about and gives a functional definition — what it changes, what it costs, what it does not fix. Not a separate card *type*: it has the same schema, the same budget and the same style rules as every other card. What makes it the anchor is that it names the term.
- **Enumeration card**: a card whose back is a `#list([…])`. Its members are the items A-2 traces.
- **Orphan**: a member of an enumeration that appears in no other card in the same file.
- **Subtopic term**: the concept a `###` heading is about, made addressable by the optional `Term:` line under that heading (FR-011). It carries comma-separated aliases, so one subtopic can be anchored in English, German and Greek by the deck files that are written in those languages. A subtopic without a `Term:` line has no term as far as the checker is concerned, and A-1 ignores it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a project whose catalog has *n* subtopics carrying `Term:` lines and cards, the checker reports every (subtopic, card file) pair with no anchor card in it and no others — zero false positives on the demo project, which after the feature lands reports **no errors and no warnings** under `python3 scripts/check_project.py tests/fixtures/demo-project --strict`, the invocation CI uses.
- **SC-002**: On a card file with *k* list members, the checker reports exactly the members named by no other card in that file, and each message quotes the member verbatim so the reader does not have to diff the list by hand.
- **SC-003**: Both checks fail, on their assertions, against their red cases — A-1's in a `tmp_path` project, A-2's on its fixture — before either `SKILL.md` is edited, the red artifact Principle XI requires, visible in the commit order.
- **SC-004**: The four repo gates stay green: `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`; and `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` passes with **both** card-count assertions updated to whatever the demo deck now holds — `DEMO_CARD_COUNT` in `tests/test_e2e.py` (which the page-count assertion derives from) and the bare `assert counts["cards"] == 31` in `tests/test_check_project.py`.
- **SC-005**: A `goal.md` written before this feature — any of the three `depth` values — is still valid, produces no new error, and needs no edit.
- **SC-006**: Reading `skills/learning-goal/SKILL.md` cold, a reader can state without ambiguity that `depth: expert` carries `awareness` and `working` cards too; reading `skills/cards/SKILL.md` cold, a reader can state the anchor rule and the "anchor, not coverage" caution.
- **SC-007**: Neither check adds a measurable cost to `python3 scripts/check_project.py` on the demo project — the run stays under a second, as it is today.
- **SC-008**: `skills/cards/SKILL.md` names `python3 scripts/check_project.py .` as a numbered step with a stated reaction, so a deck author running `/cards` end to end triggers A-1 and A-2 without being told to (FR-026). Before this feature no skill in the repo runs the checker as a step.

## Assumptions

- The user has Python 3.12+ and a working Claude Code install. No typesetting engine is needed for anything in this feature.
- The demo project under `tests/fixtures/demo-project` is the only corpus. Both failure modes go there; nothing new is invented elsewhere (Principle XI, `CLAUDE.md` testing rule).
- `lernkarten check` (the user-facing schema check) is **not** extended. Both A-1 and A-2 are deck-level questions that need `catalog/topics.md` as well as `cards/*.yaml`, and `check_project.py` is the tool that already reads a whole project. If the plan finds a reason to move them, it must say what it does about a card file checked outside a project.
- `parse_catalog` in `scripts/check_project.py` already gives subtopics with their attribute lines, and `check_cards` already walks every card with its `subtopic:` key — both checks build on what exists rather than re-parsing. `Term:` is read by the same `ATTRIBUTE` machinery and its aliases by the same `catalog_names()` helper.
- The `Term:`-gated shape of FR-011 is what keeps the existing tests honest. `GOOD_CARDS` in `tests/test_check_project.py`, used at fifteen call sites, names neither *rhythm* nor *tide* and would fail any A-1 that matched text against a heading; under FR-011 it is unaffected, because the catalog it is paired with carries no `Term:` line. Any future tightening of A-1 has to keep that property or rewrite fifteen tests.
- The demo project is checked by CI under `--strict` (`.github/workflows/ci.yml`), where a warning fails the build. "Green on the fixture" therefore means no errors *and* no warnings, which is why FR-015 does not hedge either check into an advisory.
- Issue [#41](https://github.com/mhabedank/lernkarten/issues/41) (the deck never *teaches* the connections it tests) is a larger, separate claim needing a new artifact. This feature deliberately needs none, and is a precondition for judging whether #41's study script closed anything.
- The private deck that surfaced this — eight concepts argued about and never named — is not committable (Principle VII). Every example here is invented against the demo project's subject.

## Open Questions

None. The five the issue and the draft left open — "names the term" (FR-011), A-2's normalisation (FR-013), marking `awareness`-level cards (FR-018), subtopic versus catalog bullet (FR-019) and the fan-out merge pass (FR-020) — were answered in the session recorded under [Clarifications](#clarifications), together with a sixth the session surfaced: whether A-1 binds per card file or deck-wide, which the draft's FR-010 and FR-014 answered differently. Every answer is written into the requirement it belongs to, and no clarification marker survives anywhere in this file.

A second session, recorded under [Session 2026-09-01 (post-checklist)](#session-2026-09-01-post-checklist), closed the five residual ambiguities the checklists surfaced — A-1's haystack (FR-010), the normative A-1 message and how A-2 names a card (FR-014, FR-014a), the empty `Term:` line (FR-011b), a marked subtopic that has cards anyway (FR-009a) and A-2 on a missing or non-string `back` (FR-012a). Each one decided a test assertion, which is why they were closed before task generation rather than during it.
