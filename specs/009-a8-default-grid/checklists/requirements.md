# Specification Quality Checklist: A8 becomes the default grid

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-07
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — *scoped, see Notes*
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders — *scoped, see Notes*
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic — *scoped, see Notes*
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification — *scoped, see Notes*

## Notes

**No clarification markers.** Issue #84 had already argued the decision through,
and the one genuinely open question — whether moving the default also moves the
scale reference — is not a matter of preference. Moving it is simply a defect:
measured, A7 cards grow by 39 %. So it is written as FR-002 rather than asked.

**FR-002 is the whole risk of this feature.** Everything else is a constant and
some prose. A reviewer who reads only one requirement should read that one, and
SC-003 is the assertion that catches it: the scale factors are pinned per grid
per margin, so a re-based reference fails six numbers at once rather than
producing a plausible-looking PDF.

**Four generic items are marked "scoped."** They test for implementation
detail, which this repository's own `spec-template.md` requires: the *Format
Contracts* table names modules by path, and the template's worked examples for
success criteria are page counts and exit codes. Here the millimetres and the
scale factors *are* the user-facing requirement — a card that is 39 % larger is
not an implementation detail, it is a different card.
