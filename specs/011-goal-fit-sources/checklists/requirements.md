# Specification Quality Checklist: Practitioner material, goal fit, and source discovery

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-07
**Feature**: [spec.md](../spec.md)
**Re-validated**: 2026-09-07, after the `/speckit-clarify` session; again after round 2
(the explicit-request rule); again on 2026-09-08 after round 3 (the material-class-neutral
discovery contract); and again on 2026-09-08 after round 4 (the *addendum* rename and the
per-candidate class of material); and **again on 2026-09-08 after the post-analysis
remediation**, which rewrote FR-013 from a prescribed phrase into four required
contents, reworded FR-019's second property the same way, and bound FR-013 to
`/cards` as well as `/catalog`; and **once more on 2026-09-08 after the
cross-model review remediation**, which touched the spec in exactly two places —
US6 scenario 1's `docs/workflow.md` wording and one added Assumptions bullet

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — **zero**; all five round-1 questions, the one round-2 question, the one round-3 question and the two round-4 questions were answered and encoded, see Notes
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- **All nine open questions are resolved** in `## Clarifications` — five in session 2026-09-07,
  one in round 2 of the same day, one in round 3 on 2026-09-08 and two in round 4 the same day — and each answer is written into every requirement it touches. The table *Questions carried from the
  issue — all resolved* records question, home requirement and answer. Nothing was resolved
  silently.
- **Two answers moved the shape of the feature**, not just its wording:
  - Q4 collapsed piece C from a new eighth pipeline step into a **mode of `/sources`**. The
    pipeline stays at seven steps, so `assets/brand/common.typ`, the three rendered PNGs, the
    README banner alt text, `docs/workflow.md`, `docs/index.html`, `CLAUDE.md` and the
    constitution's Identity section all dropped out of scope. *Print & Design Impact* is now
    **none**, and no constitution amendment is needed. FR-028 (the step's name) is withdrawn in
    place, with its number retired rather than reused.
  - Q1 adopted `nature: experience` in the knowledge frontmatter, so **one** format contract
    moves — the third one in Principle I. It is additive, optional and a closed vocabulary, so
    every project on disk validates unchanged. Q2 declined `fit:`, so the `sources.yaml`
    contract does not move at all.
- **Which gate holds the red artifact is now settled**, which was the point of questions 1 and 2.
  Piece A is `check_docs.py` plus named manual rows in `docs/testing.md` (FR-032). Part of piece
  B is assertable in `check_project.py` (FR-031, SC-013). Piece C writes only ordinary
  `sources.yaml` entries that `check_project.py` already validates. This is stated in *Scope in
  the Pipeline* so planning cannot invent a file just to make the work testable.
- File formats and skill file names (`goal.md`, `sources.yaml`, `skills/sources/SKILL.md`,
  `check_docs.py`) are named concretely rather than described abstractly. Deliberate, not an
  implementation leak: constitution I makes the file formats the *contract* between the two
  halves, and constitution XI names which gate a rule belongs in — a spec that stayed abstract
  about them would be unimplementable here.
- **Carried into planning** — the three items under *Open items deferred to planning*, all
  surfaced by the clarification scan below its five-question quota and none of them blocking:
  1. a goal written *after* the sources are registered gets no assessment (FR-001 assesses at
     registration, FR-008 forbids re-assessing on a listing) — accept explicitly or scope a
     back-fill, but do not silently widen FR-008;
  2. the demo project's `goal.md` holds one `kind`/`depth` pair, and FR-005's weighting needs
     both a weigh-up and a weigh-down case out of it — no second corpus (constitution VII, XI);
  3. FR-027 requires found/shown counts but sets no cap on how many candidates are shown.
- **Carried into planning**: the demo project needs one invented experience report, marked
  `nature: experience`. Extend the existing corpus; never start a second one.
- **Round 2 closed the one hole a reader could still fall through**: the spec covered the
  *writing* side of discovery (FR-016 writes nothing until the user picks, FR-020 registers
  picks through the ordinary path, FR-021 never invents, FR-033 reaches the network only in
  discovery mode) but never said when discovery may be **entered**. Three gaps, all now closed:
  no requirement made the entry explicit, none forbade `/ingest`, `/catalog`, `/cards` and
  `/print` from pointing at it, and FR-006's one-line cap on the `/learning-goal` pointer had no
  counterpart. FR-035 – FR-038 answer all three, FR-016 was reworded so "MUST offer" no longer
  contradicts them, FR-030 gained the `check_docs.py` obligation that makes the rule enforceable
  (constitution XI) and FR-032 the named manual rows for the run-output half. SC-014 and SC-015
  assert the shape: a full pipeline run with no explicit discovery invocation makes zero
  searching network requests, adds zero unnamed entries to `sources.yaml`, and says zero words
  about discovery. Scenarios landed on US1 (8), US2 (6), US4 (9 – 11) and US6 (4).
- **The accepted cost is recorded, not hidden**: a user who does not know discovery exists finds
  it only through the documentation, because no run ever hints at it. That trade is stated in
  the round-2 clarification, in the Edge Cases and in the Assumptions, and US6 scenario 4 makes
  the documentation carry the weight it is now the only bearer of.
- **Round 3 separated a material class from a general mechanism.** Issue #44 wrote piece C as if
  source discovery belonged to the practitioner-material feature. It does not: issue #43 (*Public
  research sources: arXiv and friends*) names the same gap — no search, you have to know the URL
  first — for research literature. Review found piece C already almost neutral (FR-017, FR-018,
  FR-020 – FR-027 never mention practitioner material, and FR-023's paywall rule *is* #43's
  restriction to openly accessible sources), with **FR-019 the only practitioner-specific
  requirement in the group**. So the group is split rather than rewritten:
  - **C1 — the discovery contract, material-class neutral**: FR-016, FR-017, FR-018, FR-020,
    FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, plus the withdrawn FR-028 kept in
    place and the new **FR-039**.
  - **C2 — material-class addenda**: **FR-019**, the practitioner-material addendum, and the only
    addendum this feature ships.
  Every requirement keeps its number — a regrouping, not a renumbering. Only FR-018 changed text,
  gaining one cross-reference sentence that sends class-specific additions to C2; FR-023 and
  FR-030 gained a round-3 note. FR-039 makes the neutrality an obligation: C1 may not be written
  in terms of one class of material, and a further class is added by attaching an addendum without
  reopening C1, with `check_docs.py` asserting the neutral contract and each addendum **separately**.
- **No scope was added in round 3.** One addendum ships. The spec says so in FR-039's closing note,
  in the C2 heading, in the *Scope in the Pipeline* section and in the assumption *The discovery
  contract is neutral; the coverage is not*, so neutrality cannot be misread as a promise of
  research-literature support. The **issue #43 seam is recorded as an assumption, not as scope**:
  #43 inherits the neutral C1 contract (and FR-023's paywall rule) instead of building a second
  discovery path; **bibliographic identity** (DOI, authors, year, venue, citation count) and any
  **source-specific search backend** stay with #43. This feature adds no arXiv work, no new source
  type and no frontmatter field beyond round 1's `nature:` — recorded in the Format Contracts
  table as a deliberate "none".
- **Round 4 renamed one term and opened one hook, and added no behaviour.**
  - **The rename is editorial.** Round 3 named the C2 mechanism with contract jargon a reader
    has to look up, so every occurrence of it becomes **material-class addendum** (adjective form: *the practitioner-material
    addendum*) — in the spec, the plan, `contracts/discovery-proposal.md`, `data-model.md`,
    `quickstart.md` and this file, including the C2 group heading, FR-019, FR-039, SC-016, the
    Key Entities entry, the US4 scenarios and the check-function name the plan proposes
    (now `check_sources_skill_carries_the_practitioner_addendum()`). No requirement gained or lost
    an obligation; the C1/C2 split is the same split.
  - **A candidate now names its material class, and the filter is deliberately later.** The
    expectation that discovery should be configurable as to *which* classes it searches is a
    **second axis** the spec did not cover: an addendum governs how a credibility sentence reads
    for a class, it does not decide what discovery searches. **FR-017 gains one field** — every
    candidate names which class of material it is — justified in the requirement itself on the
    ground that the class is *already* determined (the C2 addendum could not fire otherwise), so
    naming it costs nothing and makes FR-027's grouping legible. The requirement states
    explicitly that this is **not a closed, validated vocabulary** — prompt-level run output, not
    a key on disk — and that it is **not** the `nature:` key of FR-015, which is a closed marker
    `/ingest` writes on a stored document at a different layer. **FR-040** records the filter as a
    deliberate, named future extension whose hook is already in place: selecting classes is out of
    scope, FR-017's class is what a later filter attaches to, and such a filter must be addable
    without reopening any C1 requirement — FR-039's shape obligation applied to the second axis.
  - **Explicitly NOT pulled in**: no filter behaviour, no class-selection argument, no class
    vocabulary or validation, no second addendum, no new source type, no new frontmatter key, and
    nothing of issue #43. The Format Contracts table carries a deliberate "none" row saying the
    candidate's class is not a format.
  - **The #43 seam now names both inheritances**: the neutral C1 contract *and* the per-candidate
    class hook.
- **Counts after round 4**: 6 user stories, 40 numbered functional requirements (FR-028
  withdrawn in place and **not** reused, so 39 active), 17 success criteria, zero
  `[NEEDS CLARIFICATION]` markers. New in round 3: FR-039, SC-016, US4 scenario 12, and the
  *Material-class addendum* key entity. New in round 4: the FR-017 class field, FR-040, SC-017,
  US4 scenario 13, two edge cases, one Assumptions bullet and one Format Contracts row.
- **Re-validation after the 2026-09-08 remediation — every box still ticks.**
  - *Requirements are testable and unambiguous*: FR-013 is **more** testable than
    before. Four named contents can each be looked for in a run; one prescribed
    phrase could be produced without the reader understanding anything. The
    checkable shape is the four contents; the wording is free, which is what a
    prompt-level requirement can honestly demand.
  - *No implementation details leak*: the worked example in FR-013 is run output
    in the demo project's invented vocabulary (signals, flags, harbours, tides,
    field notes), not a technology and not a real field of study — constitution
    VII holds.
  - *Counts unchanged*: 6 user stories, 40 numbered FRs (39 active), 17 success
    criteria. The remediation added **no** requirement and **no** criterion; it
    changed what two of them demand and where one of them is routed.
  - *Scope unchanged*: no new behaviour. FR-013 already bound `/catalog` **and**
    `/cards` in US3 scenario 5; the remediation made the plan and the tasks say
    so too, and gave the `/cards` half its own manual row (**12-iv**).
- **Re-validation after the 2026-09-08 review remediation — every box still ticks.**
  - *Counts unchanged*: 6 user stories, 40 numbered FRs (39 active, FR-028
    withdrawn and not reused), 17 success criteria, **zero**
    `[NEEDS CLARIFICATION]` markers. The remediation added no requirement, no
    criterion and no user story; almost all of it landed in `plan.md`,
    `tasks.md`, `quickstart.md` and `checklists/gates.md`.
  - *Two spec edits, both corrections rather than changes of meaning.* **US6
    scenario 1** said `docs/workflow.md` is "not touched by this feature" while
    scenario 2 and task T041 edit it in three places; it now names *the
    seven-step description in* `docs/workflow.md`, which is what spec line 15
    always meant and what the scope check T043 actually verifies. And one
    **Assumptions** bullet was added, recording why FR-037 names four skills
    and how `/learning-goal` and `/research-gaps` are held instead — the second
    of them by a manual row alone, because FR-034 obliges it to carry the token
    a gate would otherwise forbid. Neither edit changes an obligation.
  - *Requirements are testable and unambiguous*: **five became more so.**
    FR-003, FR-005, FR-006 and FR-009 gained a check on the prompt sentence that
    carries them (cases C6–C9) and FR-007 gained one on the register (A5/A6).
    The spec text of all five is unchanged; what changed is that the plan stopped
    calling them unverifiable when a check was available. Where the check is
    weaker than the requirement — all four of C6–C9 — the plan now says so in the
    routing cell rather than letting the case id imply coverage.
  - *Success criteria are measurable*: **SC-016 became measurable for the first
    time.** It asserts that deleting the addendum from `skills/sources/SKILL.md`
    fails exactly one check; the artifact that tested it ran against synthetic
    text, where the claim cannot be false. It now excises the sub-section from
    the shipped file, by heading.
  - *Scope unchanged*: no new behaviour, no new format, no new dependency. The
    one requirement whose *verification* moved rather than its text is FR-033,
    whose manual row was rewritten from an unobservable ("makes no network
    request") to an observable (the three ordinary invocations re-run offline).
- **Carried into planning**: `skills/research-gaps/SKILL.md:17` says `/research-gaps` is "the
  only step that reaches the network", which is already false — `skills/ingest/SKILL.md:69`
  fetches web pages with WebFetch and the Zotero path reaches the API over HTTP. FR-034 makes
  fixing it part of this feature's documentation work.
