# Specification Quality Checklist: Sphinx documentation foundation

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-08
**Revised**: 2026-09-08 — scope split into 012 (foundation) / 013 (reference) / 014 (tutorial & topics)
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — *see the caveat in Notes; the toolchain is now a settled decision, deliberately recorded*
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

- **All three clarification markers are resolved.** They were closed by user
  decision, not by guessing:
  - former **FR-018** (site beside the landing page, or absorbing it) →
    `docs/index.html` stays the site root, unchanged, keeps
    `tests/test_landing_page.py`, and the generated site lives under a sub-path.
    Now **FR-013**.
  - former **FR-004** (how much of a `SKILL.md` becomes a reference entry) →
    moved to **013**, recorded in *Follow-on features*.
  - former **FR-015** (which topic pages ship) → moved to **014**, recorded in
    *Follow-on features* with the candidate set the user has seen.
- **On "no implementation details"**: two things are named on purpose and are not
  leakage. (1) This project's spec template is normative and *requires* file
  paths, gates, exit codes and dependency shape — Format Contracts, Print &
  Design Impact and Dependency & Portability Impact are mandatory sections that
  ask for exactly that. (2) The toolchain — Sphinx + `myst-parser` +
  `pydata-sphinx-theme` — is a **settled user decision**, not a plan-phase
  question, and FR-001 records the rationale so planning does not reopen it. What
  remains for `plan.md` is the Principle IV vetting table and the pinning
  strategy, not the choice.
- **Test-first (constitution XI)** is carried by FR-025. Every acceptance
  scenario fails today: there is no docs build, no `requirements-docs.txt`, no
  navigation tree, and `pages.yml` copies two files.
- **One external ordering dependency**, recorded in Dependency & Portability
  Impact: PR #105 (`fix/pages-site-assembly`) must merge before 012 touches
  `pages.yml`, because 012's FR-016 requires the invariant that PR adds. It is
  not yet present in this worktree.
- **Two migration hazards are requirements rather than assumptions**, as
  instructed: `docs/leitner.html` is embedded rather than converted (FR-010), and
  the `check_docs.py` Leitner gates plus `tests/test_check_docs.py`'s
  path assertion must keep holding (FR-011).
- Ready for `/speckit-plan`.
