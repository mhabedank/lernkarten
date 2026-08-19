# Specification Quality Checklist: Goal-driven catalog

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-18 · **Revised**: 2026-08-18 (review round 1)
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Project-specific gates (constitution)

- [x] **Pipeline stage named** (I) — `/learning-goal`, `/research-gaps`, changes to `/catalog` and `/cards`
- [x] **Format contracts filled** (I) — one new format, two changed additively, backwards compatibility in both directions, and the tree-vs-DAG decision recorded with what was rejected
- [x] **Test-first artifact identified** (XI) — `check_project.py` and `check_docs.py` checks plus cases in the matching test modules; six new broken fixtures enumerated in SC-008
- [x] **No user content committed** (VII) — `goal.md` gitignored; the demo project carries the one committed instance
- [x] **Subject-agnostic** (VII) — low-code appears only as the reported problem, never in an artifact or fixture
- [x] **Dependency impact stated** (II–IV) — none added
- [x] **Design impact stated** (XVI) — corrected in this revision: the landing page and three brand PNGs are in scope
- [x] **Skill contract** (X) — FR-022 extends the description rule; new skills follow `skills/<name>/SKILL.md`
- [x] **Constitution amendment flagged** — Principle I's format table and the five-step Identity sentence

## Review round 1 — what changed and why

Six points were raised against the first draft. All six were accepted; two of
them corrected outright errors in it.

| # | Point | Verdict | Where it landed |
|---|---|---|---|
| 1 | `goal` may shadow another skill | **Accepted with a caveat.** No `goal` skill exists in this repo or on this machine — but the name is generic, the plugin ships into environments this repo cannot see, and `research` carries the same risk. Renamed to `learning-goal` and `research-gaps`, plus a testable description rule. | FR-021, FR-022, SC-009, Edge Cases, Assumptions |
| 2 | A goal can hold unrelated strands (interview: technology *and* HR) | **Accepted — a real gap.** The draft had a flat topic list, which would have invited the model to unify strands that share nothing. Required topics are now grouped into areas, and areas map to independent top-level topics. | FR-003, FR-010, US1 §2, US2 §2, SC-004, Key Entities |
| 3 | Re-running the goal can conflict; make it transparent and resolve by Q&A | **Accepted.** The draft said "merge rather than overwrite", which silently loses a contradiction. Now: detect, list, ask, and name what a narrowing change would orphan. | FR-005, FR-006, FR-007, US1 §4–6, SC-005 |
| 4 | Is the catalog really a tree? | **Accepted — and my first answer was wrong.** I argued the model had to stay a tree because markdown headings cannot express multiple parents. That is a statement about a rendering convention, not about the file: a `Parents:` line expresses polyhierarchy fine, and we own the format. Corrected in round 2 (below). | US5, and the rationale block in Format Contracts |
| 5 | Warn when the catalog is built without a goal | **Accepted.** Also the discovery path for the new step. Forced a correction to the old SC-004: *artifacts* stay byte-identical, the run output gains one line. | FR-013, US2 §5, SC-006 |
| 6 | Out-of-scope = count only; gaps = warning + names | **Accepted, and the asymmetry is the point.** Out-of-scope is the feature working as asked; a gap means the deck is incomplete and a bare number is unactionable. | FR-016, FR-017, US3 §2–3, SC-003 |
| 7 | Docs and landing page must be in scope | **Accepted, and it exposed two errors in the draft.** "Design impact: none" and "brand PNGs: no" were both wrong: `assets/brand/common.typ` holds the command tuple and three committed PNGs render the step count, and the landing page grid is `repeat(5, …)` with a hand-written rule for the orphaned fifth step. | US6, FR-032–FR-035, Print & Design Impact, SC-010, SC-011 |

## Review round 2 — the catalog model

The tree-vs-DAG answer from round 1 was challenged on the right grounds: it let
the persistence format dictate the domain model. Re-examined and reversed.

**What was wrong.** "Markdown headings cannot express multiple parents" is about
a heading convention, not about the artifact. `catalog/topics.md` is a format
this project owns; a `Parents:` line is polyhierarchy, readable and checkable.

**What is actually true, and where it lives.** `templates/card.typ` prints
`TOPIC / SUBTOPIC` into the header band of every physical card, so exactly one
topic has to be chosen before ink hits paper. That is a *design* constraint
(constitution XVI, the fixed band that never shrinks type), and it applies at
card-materialisation time — not to the catalog.

**The resolution.** The catalog models containment as many-to-many (`Parents:`,
primary first). Choosing a card file and a printed header is a projection rule
applied downstream. The model is not flattened to suit storage; storage projects
the model.

**A second conflation this exposed.** Two different relations were being covered
by one line. Containment ("Access control is under Security *and* Governance")
is asymmetric and many-to-many — `Parents:`. Association ("Governance and Shadow
IT are connected") is symmetric and contains nothing — `Related:`. Round 1 only
modelled the second. Both are now first-class, as in SKOS and MeSH.

**A claim withdrawn.** The option presented offered an acyclicity check as a
benefit. It would be vacuous: with two levels, edges run only from topic to
subtopic, so the graph is bipartite and no cycle can form. The invariants worth
checking are reciprocity ones instead — every parent exists, the primary agrees
with the heading, every `Also covers:` listing is reciprocated — and they catch
the failure this model genuinely invites, a half-edited catalog.

**Rejected, with reasons in the spec**: cards belonging to several topics
(`topic:` as a list) — it changes the contract with the deterministic half *and*
forces a card-layout decision the band cannot absorb; and a separate relation
file — maximum structure, minimum readability, for an artifact whose job is to
be scanned by a human.

## Notes

Three scope decisions from before the first draft still stand: goal-first catalog
instead of a separate `/review-catalog`; researched knowledge in its own marked
source type; off-goal content flagged and kept rather than deleted.

Remaining risk, deliberately accepted: the quality of the model's relevance and
relatedness judgements is not assertable. The spec asserts the *shape* of the
result only. This matches how the four existing model-driven steps are already
tested and is the boundary `check_project.py` documents in its own module
docstring.

Scope watch for `/speckit-plan`: this is now seven steps, five artifacts, six
user stories and 40 functional requirements. US5 (the `Parents:`/`Related:`
graph) remains the one piece separable without weakening the original fix — it
serves catalog fidelity and connection cards, not the source-bound-cards problem
this feature exists for. If the plan comes back too large, defer it first, and
note that deferring it costs the catalog its honesty about shared subtopics.
