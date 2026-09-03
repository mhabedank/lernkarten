# Specification Quality Checklist: Ship the card box as a download

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-01 · **Revised**: 2026-09-01 after the scope cut
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

**16/16.** This is the revised, narrow spec: publish an artifact that already
exists. The first version required a Typst source, a render script, byte-stable
regeneration and a geometry contract; that scope was cut as unnecessary
complexity, and `research.md`, `data-model.md`, `contracts/`, `quickstart.md`,
`plan.md` and `checklists/print.md` were deleted with it.

Two content-quality notes, both deliberate:

1. The spec names `.gitignore`, `docs/index.html` and
   `.specify/memory/constitution.md` by path. That is not an implementation leak —
   the *deliverable* of this feature is a set of specific versioned files, so the
   file is the requirement.
2. `## Accepted Trade-offs` is not in the template. It is here because five
   consequences follow from the scope cut, and a consequence that is written down
   is a decision while the same consequence unwritten is a defect somebody finds
   later. Trade-off 5 in particular — that the box silently becomes wrong if the
   card geometry ever changes — is the exact risk issue #45 opened by warning
   about, now knowingly accepted.

**Three facts measured from the artifact, which the documentation must carry
because the sheet itself cannot be corrected:**

| | The sheet says | Measured |
|---|---|---|
| Orientation | `a4 landscape` | **portrait** — `/MediaBox 0 0 595.2 841.8`, no `/Rotate` |
| Card size | `cards 70 × 49 mm` | the real A8 card at the default margin is **71.75 × 50 mm** |
| Grid | *(nothing)* | fits **`--grid a8` only**; an A7 card is 100 mm against a 73 mm opening |

FR-004 and FR-005 exist to put all three next to the download.

**The one item to re-read before planning is FR-009**, the constitution
amendment. It is what turns a committed source-less binary from a violation into
a named exception, and it is the only requirement here that changes a project
rule rather than a project file.
