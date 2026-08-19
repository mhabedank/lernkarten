# Feature Specification: The README links the landing page up front

**Feature Branch**: `docs/readme-landing-link`

**Created**: 2026-08-20

**Status**: Draft

**Input**: GitHub issue [#26](https://github.com/mhabedank/lernkarten/issues/26)
— "README buries the landing page". The live page is first named at
`README.md:168`, inside `## The design`, as an aside about the visual system. A
reader who wants to *see* the project before reading 160 lines of prose never
finds it.

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: none of them. `README.md` is a project surface,
not a pipeline step. Nothing under `skills/`, `scripts/`, `bin/`, `templates/`
or `docs/` changes, and no artifact a user has on disk changes.

**Implementation half**:

- [ ] **Model-driven**
- [x] **Deterministic** — one versioned file, `README.md`, whose source text is
      assertable from pytest exactly as
      `tests/test_repo_hygiene.py::test_the_repo_does_not_still_promise_five_commands`
      already asserts the text of every versioned doc today.
- [ ] **Both**

The seam is worth naming, as it was for the landing page itself: what a test can
reach is the *source text and its position in the file*, never how GitHub
renders it or where the fold falls on a given screen. Every requirement below is
therefore split — a positional claim about `README.md` that a test asserts, and,
where the point is what a reader actually sees, a named entry on the manual
checklist in `docs/testing.md`. Constitution XI allows exactly this split and
requires the assertable half to come first.

**Who runs into this**: someone who has not installed anything yet — a person
who arrived at the repository from a link, a search or the plugin marketplace
and wants to look at the thing before committing to it. A contributor never
runs into it: they already know the page exists, because the reference they use
is the one in `## The design`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A newcomer finds the live page without scrolling past the intro (Priority: P1)

Someone opens `https://github.com/mhabedank/lernkarten` for the first time. They
read the banner, the badges and the paragraph that says what the project does.
Before they decide whether to read the install instructions, they want to see
what a finished card and a finished page look like on a real site. Today the
only link that takes them there sits 160 lines further down, under a heading
about the visual system, and they never reach it. After this change the opening
block carries one line pointing at
`https://mhabedank.github.io/lernkarten/`, above the first `##` heading and
therefore above everything else in the file.

**Why this priority**: it is the entire issue. Nothing else in this feature has
value without it.

**Independent Test**: run `pytest tests/test_repo_hygiene.py` and check that the
new assertion — the landing page URL appears in `README.md` above the first `##`
heading — passes; run it against `main` and check that it fails there.

**Acceptance Scenarios**:

1. **Given** the repository as checked out, **When** the opening block of
   `README.md` (everything above the first `##` heading) is read, **Then** it
   contains a markdown link whose target is `https://mhabedank.github.io/lernkarten/`.
2. **Given** the repository as checked out, **When** `README.md` is read in
   full, **Then** the link appears after the introductory paragraph and before
   the `assets/example-cards.png` screenshot, so a reader meets it in the same
   breath as the sentence that explains what the project is.
3. **Given** `main` before this change, **When** the same assertion runs,
   **Then** it fails and names `README.md` as the offender.

---

### User Story 2 - A contributor still finds the source of the page (Priority: P2)

A contributor wants to change the landing page. They look for it where a
contributor looks — in `## The design`, next to `docs/design.md`, which is the
file they have to read first anyway. That reference must survive: it points at
`docs/index.html`, the file on disk, which is a different thing from the URL a
newcomer wants.

**Why this priority**: it is a regression guard, not new value. It ranks below
P1 because the feature is worth shipping even if this reference were merely left
alone by hand — but the two readers are genuinely distinct, and losing the
source pointer to "deduplicate" would be a net loss.

**Independent Test**: run `pytest tests/test_repo_hygiene.py` and check that the
assertion on the design section — `README.md` still links
`docs/index.html` — passes; `python3 scripts/check_docs.py` independently
confirms that relative link still resolves to a file that exists.

**Acceptance Scenarios**:

1. **Given** the repository after this change, **When** the `## The design`
   section of `README.md` is read, **Then** it still contains a relative link to
   `docs/index.html`.
2. **Given** the repository after this change, **When**
   `python3 scripts/check_docs.py` runs, **Then** it exits 0 — every relative
   link in `README.md`, including `docs/index.html`, resolves.

### Edge Cases

The recurring list mostly does not apply — no tooling runs, no file is parsed,
nothing is printed. What is left:

- **Missing optional tooling**: N/A. Nothing executes.
- **Fresh install on each platform**: N/A. `README.md` is read, not run.
- **Python floor**: the new assertion lives in the existing pytest suite and
  uses nothing beyond `pathlib` and `re`, so 3.12 is unaffected.
- **Encoding and file names**: `README.md` is UTF-8 and stays UTF-8; the new
  line is ASCII apart from the arrow glyph, which the file already uses
  elsewhere in prose.
- **Idempotence**: N/A — this is a one-off edit to a versioned file, not a step
  that regenerates anything.
- **Text that does not fit**: N/A — nothing is typeset.
- **The URL going dead**: `check_docs.py` deliberately validates only *relative*
  markdown links, so an absolute URL is not reachable by the gates and must not
  be made so — a network call in a test would make the suite fail offline and on
  a GitHub Pages outage. The assertion therefore checks the *string*, and the
  liveness of the page stays a manual concern.
- **A second copy of the URL drifting from the first**: the opening block and
  `## The design` will name the same site in two forms (absolute URL, relative
  file). If the Pages URL ever changes, both have to move; the manual checklist
  entry is where that is caught.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `README.md` MUST contain a markdown link to
  `https://mhabedank.github.io/lernkarten/` in its opening block, defined as
  everything above the first `##` heading in the file.
- **FR-002**: That link MUST sit after the introductory paragraph and before the
  `assets/example-cards.png` image, so it is the first *action* the file offers
  and is not separated from the sentence that explains what the project is.
- **FR-003**: The link text MUST tell a reader that it leads somewhere to look
  at, not somewhere to read — the issue's `**[See it →](…)**` is the shape; the
  exact wording is a writing decision, not a requirement.
- **FR-004**: `README.md` MUST still link `docs/index.html` from its
  `## The design` section, as the source reference for a contributor. The
  existing sentence is not required to survive verbatim, only the link.
- **FR-005a**: `tests/test_repo_hygiene.py` MUST carry an assertion covering
  FR-001 and FR-002 that fails on `main` today and passes after the change, and
  whose failure message names `README.md`.
- **FR-005b**: `tests/test_repo_hygiene.py` MUST carry a second, separate
  assertion covering FR-004. It passes on `main` by construction — it guards
  behaviour that already exists — so instead of a red-first commit it cannot
  produce, it MUST be proved load-bearing by deleting the link, watching the
  assertion fail, and restoring it.
- **FR-006**: The assertions MUST NOT make a network request. Both assert the
  presence and position of a string in a file, so the suite stays green offline.
- **FR-007**: `docs/testing.md` MUST name the visual half on its manual
  checklist: that the link is visible on `github.com` without scrolling past the
  intro paragraph, that it reads as an invitation to look rather than to read
  (the manual half of FR-003), and that the URL it names actually loads.

### Format Contracts *(mandatory — state "none" if untouched)*

No format change. `README.md` is prose; none of the four file formats is
touched.

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | none | — |

**Backwards compatibility**: nothing on a user's disk is read or written. Every
existing project still builds, byte for byte.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: the README as GitHub renders it. The card, the
  press sheet, the mark and the landing page itself are untouched.
- **Black-only laser print still readable**: N/A — nothing is printed. The link
  is text, not colour, so it carries its meaning without colour either way.
- **Minimum type size respected**: N/A — GitHub sets the README's type.
- **Brand PNGs need re-rendering**: no.
- **Duplex alignment unaffected**: yes.

`docs/design.md` governs the card, the mark and the landing page. This change
adds a line of prose to the README and does not alter a graphic, so it is
reading, not editing, that file.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. The
  assertion reads a file and looks for a substring above a heading.
- **New runtime dependency**: none.
- **New dev dependency**: none.
- **New external binary**: none.
- **Anything this makes redundant**: none — the `docs/index.html` reference in
  `## The design` is deliberately kept, per FR-004.
- **Engine version change**: no.
- **Platforms verified**: all three, trivially — the change is a text edit and a
  pytest assertion with no platform-specific behaviour. CI covers macOS and
  Linux; the Windows claim rests on there being nothing platform-dependent to
  claim.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: the absolute landing page URL appears in `README.md` above the
  first `##` heading — asserted by pytest, failing on `main` and passing after
  the change.
- **SC-002**: the number of lines a reader passes before meeting a link to the
  live page drops from 168 to fewer than 15.
- **SC-003**: `README.md` still links `docs/index.html` from `## The design`,
  and `python3 scripts/check_docs.py` exits 0 with that link resolving to an
  existing file.
- **SC-004**: all four gates stay green — `ruff check . && ruff format --check .`,
  `pytest`, `lernkarten check cards/example.yaml`,
  `python3 scripts/check_docs.py` — with no test skipped that ran before.
- **SC-005**: `docs/testing.md` names the three manual checks from FR-007, so the
  visual half is on a list somebody walks before a release rather than in a
  commit message.

## Assumptions

- The Pages URL is `https://mhabedank.github.io/lernkarten/` and is not about to
  change. It is what issue #26 and `README.md:168` both name today.
- One line is enough. The issue asks for one line and explicitly offers
  `**[See it →](…)**`; a badge, a hero block or a second screenshot would be a
  larger change than was reported, and is out of scope.
- The banner, the badge row and the introductory paragraph stay as they are.
  Only an insertion is in scope, plus whatever the design section needs to read
  naturally once the link is no longer the reader's first encounter with the
  page.
- `tests/test_repo_hygiene.py` is the right home for the assertion: it is
  already where claims about the *text* of versioned documentation live, and it
  already reads `README.md` through `versioned_files()`.
- No new fixture is needed. The subject of the test is the repository's own
  `README.md`, which is in the checkout by definition.
