# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[prefix]/[short-kebab-name]` — prefix required: `fix/`, `feat/`, `skill/`, `build/`, `docs/`, `ci/`, `test/`, `design/`

**Created**: [DATE]

**Status**: Draft

**Input**: User description: "$ARGUMENTS"

## Scope in the Pipeline *(mandatory)*

<!--
  Every feature belongs somewhere in `/sources` → `/ingest` → `/catalog` →
  `/cards` → `/print`, or in the machinery under those steps. Name it here
  before anything else — it decides which half implements the feature, which
  tests apply, and what can break downstream.
-->

**Pipeline stage(s) touched**: [`/sources` | `/ingest` | `/catalog` | `/cards` | `/print` | build machinery | none of them]

**Implementation half**:

- [ ] **Model-driven** — a prompt change under `skills/<name>/SKILL.md`. Behaviour is described, not coded; what can be tested is the *shape* of what it writes.
- [ ] **Deterministic** — Python under `scripts/` or `bin/lernkarten`, and/or Typst under `templates/`. Behaviour is testable to the exit code.
- [ ] **Both** — say explicitly where the seam is and which file format carries it.

**Who runs into this**: [the user driving Claude in their own project | a contributor to this repo | both]

## User Scenarios & Testing *(mandatory)*

<!--
  Stories are PRIORITIZED as user journeys, P1 most critical. Each must be
  INDEPENDENTLY TESTABLE — implementing just one still leaves something a user
  can do end to end.

  For this project, a "user journey" almost always means: a person in a Claude
  session with their own sources, or a person at a terminal running
  `lernkarten`. Write it that way, with the actual command or the actual slash
  command they type.

  TEST-FIRST IS MANDATORY (constitution XI), which puts a real burden on this
  section: every acceptance scenario must be sharp enough to become an assertion
  that FAILS today. If you cannot picture the failing assertion, the scenario is
  too vague to implement — sharpen it here rather than discovering it in the
  plan. For a prompt change, the failing assertion is a check in
  scripts/check_project.py, so the scenario has to be about an observable
  property of the file the skill writes, not about wording.
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe the journey in plain language — what the user types, what they get]

**Why this priority**: [Value, and why it ranks here]

**Independent Test**: [How this is verified on its own — e.g. "run `lernkarten build tests/fixtures/demo-project/cards/*.yaml` and check the page count", or "run `/ingest <id>` against the demo project and check the frontmatter"]

**Acceptance Scenarios**:

1. **Given** [initial state — which project, which fixture], **When** [command or slash command], **Then** [observable outcome: a file with a given shape, an exit code, a page count, an error naming the culprit]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Journey]

**Why this priority**: [Value]

**Independent Test**: [Verification]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more stories as needed, each with a priority]

### Edge Cases

<!--
  The recurring ones in this project, worth checking against every feature.
  Delete what genuinely does not apply; do not delete it because it is
  inconvenient.
-->

- **Missing optional tooling**: no `pdftotext`, no `sips`/`magick`, no typesetting engine yet. What happens? (Degrade or skip — never fail. See constitution II.)
- **Fresh install on each platform**: Windows, macOS and Linux are equals. Does the install path work on all three with one ordinary command?
- **Python floor**: does this work on 3.12, the supported floor, with only the declared dependencies?
- **Encoding and file names**: umlauts, Windows-1252, empty files, an unreadable PDF.
- **Non-Latin card text**: Greek, Cyrillic — letters, not empty boxes. The engine does not warn on a missing glyph.
- **Idempotence**: running the step twice changes nothing; deleting one output and re-running brings back exactly that one.
- **Text that does not fit** a 105 × 74.25 mm card: reported, never silently shrunk (constitution XIV).
- **A card language nothing can hyphenate**.

## Requirements *(mandatory)*

### Functional Requirements

<!--
  Write these against observable artifacts and exit codes. "System" here is the
  `lernkarten` command, or the skill, or both — say which.
-->

- **FR-001**: [The command | The `<name>` skill] MUST [specific, observable capability]
- **FR-002**: [Component] MUST [validation or error behaviour — name what the error message has to identify]
- **FR-003**: Users MUST be able to [key interaction, with the command they type]
- **FR-004**: [Component] MUST [behaviour on the degraded path — missing tool, missing file, unreachable source]

*Example of marking unclear requirements:*

- **FR-005**: [Component] MUST handle [NEEDS CLARIFICATION: which source types — folder, pdf, web, zotero?]

### Format Contracts *(mandatory — state "none" if untouched)*

<!--
  The four file formats are the entire interface between the model-driven and
  the deterministic half (constitution I). A change to any of them is a
  breaking change with a known blast radius. Fill the table or write "No format
  change."
-->

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | [new key / changed meaning / none] | `skills/sources`, `scripts/check_project.py`, `sources.example.yaml`, the demo register |
| `knowledge/<id>/<doc>.md` frontmatter | [change / none] | `skills/ingest`, `scripts/check_project.py`, the demo project |
| `catalog/topics.md` structure | [change / none] | `skills/catalog`, `scripts/check_project.py`, the demo catalog |
| `cards/*.yaml` schema | [change / none] | `skills/cards`, `scripts/build_pdf.py`, `scripts/check_project.py`, `cards/example.yaml`, `CLAUDE.md`, the demo cards |

**Backwards compatibility**: [Do existing projects on disk still build? If not, say what breaks and how a user migrates.]

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

<!--
  Anything visible means reading docs/design.md first (constitution XIV).
-->

- **Visible surfaces touched**: [the card / the press sheet / the mark / README graphics / the landing page / none]
- **Black-only laser print still readable**: [yes / N/A] — colour never carries meaning alone
- **Minimum type size respected**: [yes / N/A] — 11 pt printed, 15 px on screen
- **Brand PNGs need re-rendering**: [yes → `python3 scripts/render_brand.py` / no]
- **Duplex alignment unaffected**: [yes / explain]

### Dependency & Portability Impact *(mandatory)*

<!--
  Dependencies are allowed (constitution II) and preferred over hand-rolling
  (III), provided they clear the quality gates (IV). The gates themselves are a
  planning concern — the full vetting table lives in plan.md. What belongs here
  is the *shape* of the need.
-->

- **Is anything being hand-rolled that a library already does?** [no / yes → name it, and say why. Constitution III makes reuse the default, and the two things this project once hand-rolled have both been replaced, so neither is precedent.]
- **New runtime dependency**: [none / name it — must install with a plain `pip install` on Windows, macOS **and** Linux, with prebuilt wheels or pure Python, no compiler. Vetting table goes in plan.md.]
- **New dev dependency**: [none / name it]
- **New external binary**: [none / name it, and say which of the two acceptable shapes it takes: self-fetching + checksum-pinned like `scripts/engine.py`, or genuinely optional with a graceful degrade. A binary the user must install by hand for a core path is neither.]
- **Anything this makes redundant**: [none / name the hand-rolled code or now-unused dependency to delete]
- **Engine version change**: [no / yes → all six platform SHA-256s in `scripts/engine.py` bumped too]
- **Platforms verified**: [which of Windows / macOS / Linux you can actually check. CI has no Windows job yet, so a Windows claim is manual today.]

### Key Entities *(include if the feature involves data)*

- **[Entity]**: [What it represents, key attributes — no implementation detail]

## Success Criteria *(mandatory)*

<!--
  Measurable and technology-agnostic. For this project the useful metrics are
  about artifacts, exit codes, page counts, card counts, cold-start time and
  what a printed sheet looks like — not throughput or concurrent users.
-->

### Measurable Outcomes

- **SC-001**: [Artifact-level outcome, e.g. "`/ingest <id>` on a 9-source demo project writes one file per document with complete frontmatter, and reports the empty file instead of inventing content"]
- **SC-002**: [Command-level outcome, e.g. "`lernkarten check cards/*.yaml` exits 0 on every shipped card file and names the offending file and key on each of the six deliberately broken fixtures"]
- **SC-003**: [Print-level outcome, e.g. "page count is exactly 2 × ⌈cards ÷ 8⌉, and every back sits behind its front at 100 % scale"]
- **SC-004**: [Cold-start outcome, e.g. "a fresh checkout with only Python produces a PDF from one command, fetching the engine once"]

## Assumptions

- [Assumption about the user's environment, e.g. "the user has Python 3.12+ and a working Claude Code install"]
- [Assumption about scope, e.g. "only the `folder` source type in v1; `zotero` follows"]
- [Assumption about test material, e.g. "the demo project already carries a fixture for this — no new corpus needed"]
- [Dependency on existing behaviour, e.g. "relies on `yamlio` reporting the line number of a malformed card file"]
