# Specification Quality Checklist: Deck anchors

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-01
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No clarification markers remain — all five were resolved in the Clarifications session of 2026-09-01 (see Notes)
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

- **The five open questions are intentional.** Issue #49 explicitly leaves them
  undecided ("Open, not decided here") and the spec records them rather than
  guessing: FR-011 (what counts as "names the term"), FR-013 (A-2's
  normalisation), FR-018 (marking `awareness` cards), FR-019 (subtopic vs
  catalog bullet), FR-020 (fan-out merge pass). This exceeds the usual limit of
  three markers; the first two are load-bearing — FR-011 decides whether A-1 can
  be an error at all, and FR-013 decides whether A-2 can match anything. Phase 2
  (`/speckit-clarify`) resolved all five on 2026-09-01, plus a sixth it surfaced
  (whether A-1 binds per card file or deck-wide, which FR-010 and FR-014
  answered differently). The answers are in the spec's `## Clarifications`
  section and written into the requirements themselves.
- Named file paths (`scripts/check_project.py`, `skills/*/SKILL.md`,
  `tests/fixtures/demo-project`) are not implementation leakage here: this repo's
  spec template makes the pipeline stage and the implementation half mandatory,
  and both are stated in terms of the file formats that couple the two halves
  (Constitution I).
- FR-023 records a fact worth carrying into planning: the demo project's own
  `cards/geography.yaml` fails A-2 today (*Skarn* and *Bellhorn* appear only
  inside the `#list([…])`), so the demo deck changes and both card-count
  assertions move with it — `DEMO_CARD_COUNT` in `tests/test_e2e.py` and the
  bare `assert counts["cards"] == 31` in `tests/test_check_project.py`.
