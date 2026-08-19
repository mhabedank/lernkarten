# Specification Quality Checklist: Three landing page fixes

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-19
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — *with a stated
      deviation, see Notes*
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders — *partially, see Notes*
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — Q1 resolved, see Notes
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [ ] Success criteria are technology-agnostic — *SC-007 and SC-009 are not, and
      deliberately so; see Notes*
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification — *same deviation as above*

## Notes

Three items are marked with a deviation rather than a clean pass. Recording why,
so the next reader does not have to re-derive it:

**Implementation detail in the user stories.** The three bugs are *defined* by
their root cause: `.card { display: flex }` outranking `[hidden]`,
`align-items: stretch` letting the note set the row height, `overflow-x: auto`
with a suppressed scrollbar. A version of this spec with the CSS stripped out
would describe three symptoms nobody could act on, and would lose the one thing
that keeps the fix honest — that the sideways scroll was a deliberate trade-off
with a documented reason, so `flex-wrap` is the wrong answer. The requirements
themselves (FR-001 – FR-013) are phrased as outcomes; the CSS lives in the story
narratives and the traceability notes, which is where the template asks for
file-and-line evidence anyway.

**"Non-technical stakeholders."** The audience for this project is a person
already running Claude Code (constitution, *Identity*), and the artifact under
change is an HTML file. The stories are written so that the *symptom* and the
*value* are plain to any reader; the diagnosis is not, and cannot be.

**SC-007 and SC-009 name technology.** SC-007 ("one file, exactly one `<script>`
block, no new external asset") encodes a real design constraint from
`docs/design.md`, not an implementation preference — the page is deliberately
self-contained. SC-009 names the four pre-PR gate commands because constitution
XII defines them as commands. Both would lose their meaning if abstracted.

**Q1 is resolved, and answering it changed the spec more than expected.** The
question was framed as a trade between minimal change and design consistency,
on the premise that only the pipeline note out-measures its heading. Measuring
all three notes showed the premise was false — printing exceeds by 29 px,
install by 7 px — so the answer is "all three bands" on correctness grounds
rather than consistency grounds, and User Story 2 now records the arithmetic.

The same measurement retired a fix that had been proposed in review: shrinking
the note's type. It would need roughly 9 px against a documented 15 px floor.
That is written into User Story 2 as a rejected option rather than left out, so
it is not proposed again, and the 14 px the note already sits at became issue
\#30 rather than a silent change here.
