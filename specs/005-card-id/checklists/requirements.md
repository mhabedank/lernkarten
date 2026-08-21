# Specification Quality Checklist: A short, stable card id

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-21
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

### Clarification session 2026-08-21 — all markers resolved

Four questions asked, four answered. The three markers Phase 1 left open are
gone; the fourth question was raised by an answer rather than by the spec.

| Question | Decision | Requirements touched |
|---|---|---|
| Id length: 4 or 5 characters? | **5** (32⁵ = 33,554,432) | FR-003, FR-003a, SC-001, Key Entities, format contract row |
| Collision: refuse or reassign? | **Reassign automatically, and report it** | FR-013, FR-013a/b/c, SC-008, SC-009, US5 |
| Which card keeps the id? | **First occurrence wins**, by command-line order | FR-013b, SC-008, US5 scenario 5 |
| Is `--card A45DK` in scope? | **No — follow-on ticket** | FR-014 (withdrawn to scope), Assumptions |

### Two decisions worth carrying into the plan

**1. The collision answer went against the recommendation, deliberately.** The
recommendation was to refuse and offer an opt-in reassign; the user chose
automatic reassignment. The cost is stated plainly in the Clarifications entry
and is real: a reassigned id stops resolving in past conversations and orphans
any #60 revision history recorded against it — the harm #59 was filed to
prevent. It was accepted in exchange for merges that always complete.

Because that cost is now load-bearing, three consequences were specified rather
than left to the implementer:

- **FR-013a** confines reassignment to the *writing* path. `lernkarten check`
  and `check_project.py` are CI gates and must stay read-only — a gate that
  rewrites the working tree is not a gate. SC-009 asserts this by hashing the
  input files before and after a check run.
- **FR-013b** makes the choice deterministic and steerable, so the behaviour is
  testable and a user can protect the ids they cite by argument order.
- **FR-013c** requires the report to state the *consequence*, not just the
  substitution — the user must be told each time the cost is paid.

**2. Question 3 was not in the original queue.** It exists only because
"reassign automatically" is underspecified without a rule for *which* card
loses its id. Left open, the implementer would have picked arbitrarily and no
test could have asserted the outcome.

### Deferred to `/speckit-plan` — not asked, by design

Both are execution detail that the plan is the right place to settle, and
neither blocks correctness of the spec:

- **How the YAML writer preserves the file.** `scripts/yamlio.py` is read-only
  (`load()` only, no `dump`) and nothing in this repo writes YAML today, so
  backfill is the project's first writer. FR-006 requires comments, quoting,
  key order, encoding and line endings to survive byte-for-byte outside the
  inserted key. The plan must choose between a round-trip library
  (`ruamel.yaml`) and a narrow targeted line insertion, and argue it against
  Principle III rather than assume it. If it takes the library, that is this
  project's **first runtime dependency** and must clear Principle IV's gates.
- **What type size the id can reach.** FR-011 requires larger than the current
  4.6 pt; `docs/design.md` sets an 11 pt floor for printed type. Whether the
  footer band's height permits 11 pt is a measurement, not a decision. If it
  does not fit, the plan must say what the band allows and `docs/design.md`
  must record the id as a **stated** exception rather than a silent one.

### Content-quality caveat (unchanged from Phase 1)

Entries under **Dependency & Portability Impact** and **Format Contracts** name
repository files and one library. That is the project's own
`spec-template.md` asking for it — both sections are mandatory and exist to
record exactly that. FR-001 … FR-014 and SC-001 … SC-009 name no technology.

### Correction still outstanding

CLAUDE.md states a runtime dependency "cannot ship today". That is out of date
against Constitution Principle II, `scripts/deps.py`, and `bin/lernkarten`,
which already calls `deps.activate()` before doing work. This matters precisely
because FR-006 may justify the first one. Correcting CLAUDE.md belongs in this
feature's task list.
