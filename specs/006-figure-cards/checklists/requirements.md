# Specification Quality Checklist: Figure cards

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-22
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

- File formats (`front_image:`/`back_image:`, `figures:`, `figures/`) are named concretely rather
  than described abstractly. Deliberate, not an implementation leak: constitution I makes the
  file formats the *contract* between the two halves, so naming them is naming the interface.
- One named package (`pypdfium2`) appears in the Dependency section, marked as a candidate whose
  Principle IV vetting belongs in `plan.md`. Kept because the spec has to state that this feature
  needs a runtime dependency at all — that is a scope fact, not a design choice.
- **Resolved 2026-08-22** — all three clarifications answered by the user:
  - Q1 → images come from folder files, PDF pages, web pages *and* markdown links (FR-008).
  - Q2 → figure cards are legal at every grid, with a once-per-run note at `a8` (FR-007).
  - Q3 → pictures may sit on either face, so the schema gained a sided pair (FR-001).
- **Carried into planning**: FR-018 makes the PDF dependency optional at runtime, so `plan.md`
  must show where that degrade is implemented and how `deps.py` reports a package that is
  pinned but not required.
