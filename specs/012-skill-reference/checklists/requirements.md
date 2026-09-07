# Specification Quality Checklist: Sphinx documentation foundation

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-08
**Revised**: 2026-09-08 — scope split into 012 (foundation) / 013 (reference) / 014 (tutorial & topics)
**Revised**: 2026-09-08 — after `/speckit-clarify`: eleven questions recorded in two sessions, FR-028 … FR-035 added
**Revised**: 2026-09-08 — after the second, adversarial clarification round: seventeen questions in three sessions, FR-036 … FR-042 added, FR-035 narrowed and FR-034 widened
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

- **Seventeen decisions are recorded in `## Clarifications`**, in three sessions.
  Six were settled in the design conversation that produced the spec. Five were
  answered in the first clarification round — the repository-link transform
  (FR-029), the `docsite/` layout (FR-028), the Leitner wrapper page (FR-032),
  the all-or-nothing deploy (FR-033) and the `/docs/` sub-path (FR-013, FR-014) —
  which also resolved the FR-014/FR-016 contradiction in words and turned four
  findings into requirements (FR-031, FR-035, the FR-023 job-id collision, the
  FR-019 command).
- **Six more came out of a second, adversarial round** that checked the spec
  against the repository's code rather than against itself: full theme alignment
  and the new `docs/design.md` row (FR-027, FR-036), the `docsite/` blind spot in
  `scripts/check_docs.py` (FR-037), the miniature `_site` that keeps links
  resolving locally (FR-038), the constitution amendment
  `check_import_graph()` forces (FR-039), three platforms instead of one
  (FR-034), and the README's links (FR-042). Four pieces of implied work were
  folded in as requirements rather than left to implementation:
  `myst_heading_anchors` (FR-040), `{include}` image resolution (FR-041), the
  fact that `REQUIRED_FILES` makes `{include}` forced rather than preferred
  (FR-028), and ruff's widened scope (FR-024).
- **Two requirements were corrected, not overwritten.** FR-035 was **narrowed**:
  it demanded the 15 px floor across "every element the theme sets below it",
  which is stricter than `docs/design.md` ("Reading text means Archivo") and
  constitution XVI, both of which exempt IBM Plex Mono literals and Jost labels.
  FR-034 was **widened** from Windows-only to all three platforms, so SC-001 no
  longer claims more than anything verifies. Both changes say so in place.
- **All three original clarification markers are resolved.** They were closed by
  user decision, not by guessing:
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
  strategy, not the choice. (3) The requirements added during clarification —
  `docsite/` (FR-028), the build-time link transform (FR-029), the retargeting
  table (FR-031) — name paths and mechanisms for the same reason: each closes a
  question that would otherwise be answered differently by every reviewer, and
  FR-029 in particular exists because the naive implementation silently removes
  coverage from `scripts/check_docs.py`. FR-019 is the one requirement that
  deliberately leaves a choice open, and it does so explicitly — candidates,
  trade-offs and a recommendation recorded. That is a decision handed to
  `plan.md`, not an ambiguity.
- **Test-first (constitution XI)** is carried by FR-025. Every acceptance
  scenario fails today: there is no docs build, no `requirements-docs.txt`, no
  navigation tree, and `pages.yml` copies two files.
- **The one external ordering dependency is satisfied.** PR #105
  (`fix/pages-site-assembly`) is merged — `a28174b` on `main`, merge commit
  `6ade04a` — and this branch is rebased onto it. `pages.yml` already copies
  `docs/leitner.html` and lists it under `paths:`,
  `test_the_pages_workflow_assembles_every_relative_link` is present in
  `tests/test_landing_page.py`, and the deployed page was verified live after the
  merge. FR-016 therefore adapts an invariant that exists. *(This note previously
  said the test was not yet present in this worktree; that was written before the
  rebase and is corrected here.)*
- **Two migration hazards are requirements rather than assumptions**, as
  instructed: `docs/leitner.html` is embedded rather than converted (FR-010), and
  the `check_docs.py` Leitner gates plus `tests/test_check_docs.py`'s
  path assertion must keep holding (FR-011).
- **What `plan.md` still owns**, deliberately left open because it is execution
  rather than requirement: the Principle IV vetting table and the pinning
  strategy for `requirements-docs.txt`; the shape of the FR-029 transform and
  whether it stays under the ~30-line ceiling; and the selector-level detail of
  the FR-027 theme override. FR-019's command and FR-034's platform coverage are
  no longer open — both were settled in the third session.
- **Three manual checklist rows** are added to `docs/testing.md` and no more, each
  because the assertable part cannot carry the whole requirement (constitution
  XI): the type-size floor across the theme (FR-035, SC-008), the "gates
  unweakened" judgement (SC-005), and the deploy policy (SC-013). No success
  criterion implies an automated check that does not exist.
- Ready for `/speckit-plan`.
