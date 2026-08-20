# Specification Quality Checklist: Simplex print order — all fronts, then all backs

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-20
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

- **"No implementation details" is met in this project's sense, not the generic
  one.** The spec names files (`scripts/build_pdf.py`, `templates/cards.typ`,
  `skills/print/SKILL.md`, `scripts/check_docs.py`) and a flag spelling
  (`--sides simplex`). That is what the project's own spec template asks for —
  "Pipeline stage(s) touched", "Implementation half", and user journeys written
  as "the actual command they type". No algorithm, data structure or internal
  function is prescribed; the flag spelling is explicitly flagged as open in
  Assumptions.
- **Zero clarification markers.** Three decisions could have been questions —
  one PDF vs. two, deck key vs. run-time flag, and whether to build a
  reverse-back-order option. Each is resolved in Assumptions with the reasoning
  and, for the reverse-order one, a named trigger (SC-005 failing) that would
  turn it into its own feature.
- **Every acceptance scenario has a failing assertion today**: page-order
  checks over a built PDF in `tests/test_e2e.py` (US1), the closing line in the
  same suite (US2), and a new gate in `scripts/check_docs.py` that fails on the
  repository as it stands (US3, SC-006). Test-first is satisfiable as written
  (constitution XI).
