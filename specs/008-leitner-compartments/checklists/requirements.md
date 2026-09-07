# Specification Quality Checklist: Leitner compartments

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-05
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
- [x] Success criteria are technology-agnostic (no implementation details) — *scoped, see Notes*
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

**Re-validated after the cross-model review of 2026-09-07.** The review returned
NOT READY with six HIGH findings; the spec was reworked in a second clarification
session. Two items regressed and were re-closed, and the count stands at 16/16.
The reworked area is FR-003/FR-004/FR-006 — dividers left the card grid — plus
SC-005, which was found to be unachievable as written because the engine stamps a
`CreationDate`.

**Re-validated after the clarification session of 2026-09-05.** 16/16 items
passing, unchanged from the specify pass — the five clarifications sharpened
requirements that were already testable rather than fixing failures. Nothing
regressed.

**Both [NEEDS CLARIFICATION] markers were resolved** on 2026-09-05:

1. **FR-014** — a non-interactive build reports the unanswered setup once and
   builds unchanged; `/print` relays that line and offers to run
   `lernkarten setup` (FR-014a); `lernkarten setup` is the single place the
   questions are asked and refuses without a terminal rather than guessing
   (FR-014b). The file stays deterministic and pytest-testable, and the feature
   stays reachable for a user who only types `/print`.
2. **FR-018 / FR-019** — `lernkarten.yaml` is created here with its own three keys,
   in the shape #67 specifies for the project scope, so #67 becomes additive.
   #67's user scope and full precedence chain stay #67's work.

**Four generic items are marked "scoped" rather than failed.** They test for
implementation detail, and this repository's own `spec-template.md` requires it:
the *Format Contracts* section names `scripts/check_project.py` by path, and the
template's own worked examples for success criteria are `lernkarten check …`
exit codes and page counts. The template overrides the generic checklist here.

Specifically retained on purpose:

- **Millimetres and hex colours** (FR-003, FR-005) — these *are* the user-facing
  requirement. A divider that is 2 mm taller does not fit the box; that is a
  physical outcome, not an implementation choice.
- **`templates/cards.typ:63-70`** in *Print & Design Impact* — cited because the
  claim "duplex alignment is unaffected" was verified against that code rather
  than assumed, and Principle XVI requires the check to be shown.
- **`--dividers` / `--box`** — the flags the user types. The template asks for
  requirements written "with the command they type".

Five clarifications were integrated (FR-004, FR-005 twice, FR-017, FR-019),
adding FR-006a, FR-012a, FR-017a, FR-017b and a *Testability note on run output*
that records why Principle XI's run-output carve-out does **not** apply to this
feature.

No item is left failing. The four "scoped" items are judged against this
repository's `spec-template.md` rather than the generic wording above; the
reasoning is written out here so a reviewer can disagree with it deliberately.
