# Specification Quality Checklist: The side marker leaves the card and becomes document metadata

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-11
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

- **Question 1 resolved (2026-09-11)**: the face map is written by the real
  `lernkarten build` as an opt-in diagnostic, off by default (option B). This
  keeps the print-order tests black-box against `bin/lernkarten`, which is what
  the #48 guarantee is stated about. Encoded as FR-006, FR-006a and FR-006b,
  with SC-002 and SC-002a measuring it. The option's spelling is left to the
  plan and recorded as an assumption.
- **"No implementation details"** is read against this project's own spec
  template, which mandates naming the four file formats and the scripts that
  own them. File names in the Format Contracts and Requirements sections are the
  template's contract, not leakage.
- Two iterations of validation were run; everything except FR-006 passes.
