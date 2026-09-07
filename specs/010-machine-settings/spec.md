# Feature Specification: Settings that belong to the machine, not the project

**Feature Branch**: `feat/machine-settings`

**Created**: 2026-09-07

**Status**: Draft

**Input**: GitHub issue #67 — "Every answer the user gives is forgotten: no place to persist a project's choices". The project half shipped with the Leitner compartments; this is the rest.

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/print` and the build machinery.

**Implementation half**:

- [x] **Model-driven** — `skills/print/SKILL.md` stops suggesting a flag the user has already answered for.
- [x] **Deterministic** — a second settings scope, the precedence between them, and `lernkarten setup`.
- [x] **Both** — the seam is `lernkarten.yaml` and its new sibling, neither of which is one of Principle I's six formats.

**Who runs into this**: anyone who owns a printer that cannot do duplex. Today they retype `--sides simplex` on every print, in every project, forever.

## What #67 asked for, and what is already done

The project half shipped in v0.8.0: `lernkarten.yaml` holds `compartments`, `dividers_printed` and `box_printed`; `lernkarten setup` is the one place questions are asked; absent means the previous behaviour; an unknown key warns rather than failing so a newer version's keys cannot brick an older one.

Three of #67's open questions are answered by that, and are not re-opened here:

- **Eager or lazy asking** → lazy. The question is asked when it first matters.
- **Does an existing project get asked** → it is *told*, once, that `lernkarten setup` exists.
- **Does the project file get committed** → no; it is gitignored.

#84 answered a fourth: `grid`'s default is now a built-in constant, so it never needed a settings file at all. #67's warning against a settings file supplying a grid at build time stands and is now moot.

**What is left is the scope #67 identified and named**: duplex/simplex is a property of the *machine*, not the project. Asking again per project reintroduces the friction the whole ticket exists to remove.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Answer for the printer once, on this machine (Priority: P1)

Someone owns a printer that cannot print both sides. They answer once, and every project they ever start on that machine prints in the order their printer needs.

**Why this priority**: it is the example #67 was written around, and the only one where retyping is *forever* rather than once per project.

**Independent Test**: write the machine file, then build in two different scratch projects and check the print order in both.

**Acceptance Scenarios**:

1. **Given** no settings anywhere, **When** `lernkarten setup --sides simplex` runs, **Then** the answer is written to the machine file, **not** to any project.
2. **Given** that file, **When** a build runs in a project that has never heard of it, **Then** the pages come out in simplex order and the run says which order it used and why.
3. **Given** that file, **When** `--sides duplex` is passed, **Then** the flag wins.
4. **Given** no machine file, **When** a build runs, **Then** the output is what it is today — duplex, and nothing said about it.

---

### User Story 2 - The two scopes never fight (Priority: P1)

A key belongs to exactly one scope, and the user never has to know which file to edit.

**Why this priority**: equal first. Two files that can both hold the same key is the failure mode #67 spends half its text warning about, and it is cheap to make impossible rather than merely discouraged.

**Independent Test**: put a project key in the machine file and a machine key in the project file; both are reported.

**Acceptance Scenarios**:

1. **Given** `sides: simplex` written into a project's `lernkarten.yaml`, **Then** it is reported as belonging to the machine scope, and named as an unknown key there — not silently obeyed.
2. **Given** `compartments: 4` written into the machine file, **Then** the same, pointing the other way.
3. **Given** `lernkarten setup` with both a project answer and a machine answer, **Then** each lands in its own file in one run.

---

### Edge Cases

- **`XDG_CONFIG_HOME` set, unset, or pointing somewhere unwritable.** A settings file that cannot be written must not fail a build.
- **A machine file that is malformed.** Same rule as the project one: reported with the file named, and it must not take a build down that never asked for it.
- **A read-only home**, which is a real CI shape.
- **The repository's own test suite**, which runs with `cwd=ROOT`: a developer's real machine file must not change what the tests see.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A **machine-scoped** settings file MUST exist, holding choices about this computer rather than this material. It lives under the user's config home — `$XDG_CONFIG_HOME/lernkarten/settings.yaml`, defaulting to `~/.config/lernkarten/settings.yaml`.
- **FR-002**: It MUST NOT live under `~/.cache/`. `scripts/engine.py` keeps the engine there and that is right — a cache is something a user may delete without expecting to lose anything. An answer is not a cache.
- **FR-003**: `sides` is the first machine key: `duplex` or `simplex`. Invalid values are reported with the accepted set, as everywhere else.
- **FR-004**: Precedence is **flag → project → machine → built-in default**, resolved per key. A later scope never overrides an earlier one.
- **FR-005**: **Each key belongs to exactly one scope.** A machine key written into a project file — or the reverse — MUST be reported as unknown *in that file*, and MUST NOT take effect. Silently obeying it would create the second place a value can live that #67 exists to prevent.
- **FR-006**: `lernkarten setup` MUST route each answer to the file its key belongs to, in one run, without the user choosing a file.
- **FR-007**: A build that takes `sides` from the machine file MUST say so once, naming the file — a value that changes the printed output must never be invisible in its origin.
- **FR-008**: An absent machine file MUST produce exactly today's behaviour. An unreadable or unwritable one MUST warn and continue, never fail a build.
- **FR-009**: The machine file MUST be ignorable for tests: the suite must be able to run against a known-empty configuration regardless of what the developer's own machine holds.

### Format Contracts *(mandatory)*

| Artifact | Change |
|---|---|
| the six formats of Principle I | **none** |
| `lernkarten.yaml` (project) | gains nothing; its key set becomes closed rather than open-ended |
| `settings.yaml` (machine) | **new**, outside the project entirely |

**Backwards compatibility**: complete. Absent means today.

### Print & Design Impact

**None.** `--sides` already exists and already changes page order; this only changes where the answer can come from. No card, sheet or mark is touched.

### Dependency & Portability Impact

- **New dependencies**: none. The file is read through `scripts/yamlio.py`.
- **Portability**: the config home differs per platform. `$XDG_CONFIG_HOME` then `~/.config` covers Linux and macOS; Windows has no XDG convention, so the same `~/.config/lernkarten/` is used there rather than inventing a third rule — `pathlib.Path.home()` resolves on all three, and the project already treats the three as equals.

### Key Entities

- **Machine settings**: choices about this computer. One key today (`sides`).
- **Project settings**: choices about this material. Three keys today.
- **Scope**: which of the two a key belongs to. Not a value a user writes — a property of the key, enforced in both directions.

## Success Criteria *(mandatory)*

- **SC-001**: `lernkarten setup --sides simplex` writes the machine file and touches no project file.
- **SC-002**: With that file, a build in any project prints in simplex order and names the file it came from.
- **SC-003**: `--sides duplex` beats the machine file; a project file never holds `sides` at all.
- **SC-004**: `sides` in a project file and `compartments` in the machine file are each reported as unknown *in the file they appear in*, and neither takes effect.
- **SC-005**: With no machine file, every existing test passes unchanged and the build says nothing about `sides`.
- **SC-006**: The test suite is unaffected by whatever the developer's own machine file contains.
- **SC-007**: A malformed or unwritable machine file warns and the build still succeeds.

## Assumptions

- **One key is enough to prove the shape.** #67 names `language`, `margin` and `logo` as candidates; none of them is *forever* friction the way a printer is, and a scope with one key that works beats three that are guessed at. Adding a second later costs a line.
- **No deck scope is added.** #67's chain includes it, but `grid:` and `language:` already live in the card file and are read there; there is nothing to build.
- **The project file's key set becomes closed.** It has to be, for FR-005 to mean anything — and the warning it already emits for unknown keys is the mechanism.
