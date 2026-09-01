# Check-Semantics Checklist: Deck anchors

**Purpose**: Unit-test the *requirements* that define what A-1 (anchor) and A-2
(orphan) actually do — before a line of `scripts/check_project.py` is written.
Every item asks whether something is **written down** in `spec.md`, `plan.md`,
`data-model.md` or `contracts/`, not whether code behaves.
**Created**: 2026-09-01
**Feature**: [spec.md](../spec.md)
**Audience / timing**: reviewer, at PR time and again before `/speckit-tasks`
**Depth**: standard
**IDs**: CHK001–CHK024. The companion file [delivery.md](delivery.md) uses
CHK101+, so no ID means two things in this feature.

## Requirement Completeness

- [x] CHK001 Is every outcome of a `Term:` line enumerated with a severity — absent, one-or-more aliases, present-but-empty, parses to zero aliases, sitting on a `##` topic? [Completeness, data-model §1, contracts/catalog-topics-md.md §Validation]
- [x] CHK002 Is the empty-`Term:` error backed by a numbered requirement in `spec.md`, or does it exist only as a plan-level decision? [Gap, plan §1 decision 2, data-model I-7]
- [x] CHK003 Are requirements stated for a **repeated** `Term:` line on one subtopic (first wins, via `setdefault`)? [Coverage, plan §2]
- [x] CHK004 Is A-1's behaviour specified for a card whose `subtopic:` key is absent or names a subtopic not in the catalog? [Coverage, spec §Edge Cases, contracts/check-messages.md §Silent when]
- [x] CHK005 Is A-2's behaviour specified for a card whose `back` is missing, empty, or not a string? [Gap]
- [x] CHK006 Is behaviour specified for a subtopic that carries **both** `Status: gap`/`out of scope` **and** cards, and is that decision traceable to a requirement rather than only to plan §1 decision 1? [Gap, FR-009, plan §1]
- [x] CHK007 Are the requirements for A-1 on a project with **no** `goal.md` stated explicitly? [Coverage, FR-016, Story 1 scenario 5]
- [x] CHK008 Are the requirements for A-2 on a project with **no** `catalog/topics.md` stated explicitly? [Coverage, quickstart §4]

## Requirement Clarity

- [x] CHK009 Is "names the term" quantified as *space-padded token containment over `topic_key()` output* rather than left as prose, and is the substring counter-example (`Nipptidenhub` does not anchor `Tidenhub`) written down? [Clarity, FR-011, data-model §1]
- [x] CHK010 Is the head-term separator set enumerated exhaustively and character-by-character (em dash, en dash, comma, colon, semicolon, `" ("`, and — added in review W3 — the spaced hyphen-minus `" - "`) rather than described as "punctuation"? [Clarity, FR-013]
- [x] CHK011 Is the maths gate stated as **skip any item containing a `$…$` span**, with strip-maths-then-head-term explicitly named and rejected? [Clarity, FR-013a, Risk 5]
- [ ] CHK012 Is "no stemming" stated as a requirement on what `skills/catalog/SKILL.md` and the contract must **say**, not only as a risk row? [Clarity, Risk 6, contracts/catalog-topics-md.md §Matching rules]
- [x] CHK013 Is the identifier A-1 binds to defined precisely enough to be implemented — the `cards/<name>.yaml` `where` string, not the topic, not the deck? [Clarity, FR-010, data-model §3 `anchor_text`]

## Requirement Consistency

- [x] CHK014 Do FR-010, FR-014 and `contracts/check-messages.md` all state the **per-file** binding and the "one finding per (card file, subtopic) pair" consequence, with no deck-wide reading surviving anywhere? [Consistency, FR-010, FR-014]
- [x] CHK015 Is FR-010's haystack the same as `data-model.md`'s? FR-010 says the file must "hold at least one card that names the term" (any card in the file); `anchor_text` is keyed `(where, subtopic)` and accumulates only the cards **under that subtopic**. A card in the same file under a *different* subtopic that names the term satisfies one and not the other. [Conflict, FR-010 vs data-model §3]
- [x] CHK016 Are the two A-1 message shapes in `contracts/check-messages.md` reconciled — is it stated which applies when, and does the shorter one still name all three FR-014 elements (file, subtopic, term)? [Conflict, FR-014, contracts/check-messages.md]
- [x] CHK017 Is it specified **which** alias appears in the message when a `Term:` line carries several ("the first alias"), and is that rule stated once rather than implied by an example? [Clarity, contracts/check-messages.md]
- [x] CHK018 Do FR-015, the contract and the data model agree that neither check may ever be a warning, with the `--strict` reasoning stated in the same terms? [Consistency, FR-015]

## Acceptance Criteria Quality

- [x] CHK019 Is the expected finding set for a whole-repo run enumerated as a closed list — exactly `Skarn` and `Bellhorn` in `tests/fixtures/demo-project/cards/geography.yaml`, and **nothing** in `cards/example.yaml`? [Measurability, FR-013a, FR-023]
- [x] CHK020 Are all three of `cards/example.yaml`'s Kolmogorov list items reproduced verbatim in the artifacts, so a reviewer can decide item-by-item that each is skipped rather than trusting a summary? [Completeness, FR-013a]
- [x] CHK021 Is the "no `Term:` line anywhere → A-1 emits nothing" property stated as a requirement that rules out **both** an error and a warning, and is the `GOOD_CARDS`/`GOOD_CATALOG` regression pinned by a **named** test rather than only by an Assumption bullet? [Coverage, FR-011a, spec §Assumptions, plan §4 regression guard]

## Edge Case Coverage

- [x] CHK022 Is the "an alias may not contain a comma" limitation stated in the contract **and** required to be reflected — or at minimum not contradicted — by the wording that FR-027 puts into `skills/catalog/SKILL.md` and `CLAUDE.md`? [Edge Case, contracts/catalog-topics-md.md §Limitations, FR-027, Risk 7]
- [x] CHK023 Are the two "give up rather than guess" cases specified — an unbalanced bracket scan skips the whole card with no finding, and a nested `[…]` inside an item is extracted whole? [Edge Case, FR-013, data-model I-6]
- [x] CHK024 Are Unicode requirements stated for both halves — that normalisation must not mangle Greek/Cyrillic/umlauts, and that a non-Latin item is traced normally — and is an item that appears only on its own enumerating card required to be reported? [Coverage, spec §Edge Cases, FR-012, data-model I-5]

## Notes

- Items are requirement-quality questions. A `[ ]` that cannot be ticked means an
  artifact needs an edit, not that code is wrong.
- CHK015 and CHK016 are the two items most likely to fail on first read; both are
  wording conflicts between artifacts that agree in intent.

### Second pass, 2026-09-01 (`/speckit-analyze`)

Every item was re-read against the artifacts and against the tree. All but one
now hold and are ticked. Three were closed by edits made in this pass:

- **CHK003** — the repeated `Term:` line (first wins, via `setdefault`) had lived
  only in `plan.md` §2 and research R9. It is now a row in
  [contracts/catalog-topics-md.md](../contracts/catalog-topics-md.md) §Validation
  and in [data-model.md](../data-model.md) §1, with the reason.
- **CHK008** — A-2 on a project with no `catalog/topics.md` had lived only in
  `quickstart.md` §4. It is now stated in
  [contracts/check-messages.md](../contracts/check-messages.md) §A-2 under *No
  catalog required*.
- **CHK022** — the "an alias may not contain a comma" limitation was **contradicted**
  by FR-011 and by the 2026-09-01 clarification entry, both of which claimed
  `catalog_names()` handles embedded commas. It does not: it is called here with no
  `known` set and splits on every comma. Both claims were struck and now point at
  the contract's §Limitations.

**CHK012 stays open.** The contract says matching is literal with no stemming, and
T029 requires `skills/catalog/SKILL.md` to say so — but **FR-027 does not**. Its
list of what the prompt must document is *what the line is for*, *comma-separated
aliases covering every language*, and *absent means silent*; the no-stemming
clause reaches the prompt through a task, not through a requirement. That is a
one-clause gap in FR-027 and it is left visible rather than papered over, because
Risk 6 rates inflected aliases *medium for real users*.
