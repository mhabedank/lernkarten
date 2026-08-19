# Phase 0 Research: Goal-driven catalog

Four questions blocked design. Each is answered below with the decision, why,
and what was rejected.

---

## R1 — Is there a library for parsing the extended catalog?

**Decision**: No library. The catalog is parsed by line scanning inside
`scripts/check_project.py`, factored into a pure `parse_catalog(text)` function.

**Rationale**: Constitution III makes "use a library" the default and
hand-rolling the exception that needs a reason, so this was asked first rather
than assumed.

`markdown-it-py`, `mistune` and `marko` were considered. All three are
maintained, pure Python, permissively licensed, and would clear Principles II
and IV on their own merits — this is not a quality objection.

The objection is fit. `catalog/topics.md` is a *constrained* format: `##`
headings, `###` headings, and `Key: value` attribute lines inside a subtopic
body. A markdown AST resolves the headings — which the existing 12-line scan in
`check_catalog()` already resolves — and hands back the attribute lines as
paragraph text, which is exactly the part that needs writing either way. The
library removes the easy fraction and leaves the hard one.

The second objection is cost. `check_project.py` runs under `lernkarten check`,
so anything it imports is a *runtime* dependency: pinned exactly in
`scripts/deps.py`, installed on the user's first run, and required to have a
wheel on all six platform pairs including Windows ARM64. That is a real price
for a checker.

**Alternatives considered**:

- *`markdown-it-py`* — the most capable, CommonMark-compliant, plugin
  architecture. Rejected on fit and on the runtime cost above.
- *Parsing the catalog as YAML frontmatter per subtopic* — would let PyYAML,
  already a dependency, do the work. Rejected: it turns a document a human reads
  and edits into a data file, which is the opposite of what
  `catalog/topics.md` is for.
- *A regex per attribute line* — this is what is actually built, but structured
  as one pass producing a `Catalog` object rather than several independent
  regex sweeps, so the reciprocity invariants can be checked against a complete
  picture rather than line by line.

---

## R2 — Where does `goal.md` live, and how does the fixture survive `.gitignore`?

**Decision**: `goal.md` at the **project root**, beside `sources.yaml`. Ignored
by `.gitignore`, with `!tests/fixtures/**/goal.md` letting the fixture back in.

**Rationale**: The goal is an *input* to the pipeline, like the source register,
not an output like `catalog/` or `cards/`. Root placement makes that visible and
matches how a user thinks about the two things they hand over: what I want to
learn, and where my material is.

The gitignore detail is load-bearing and easy to get wrong. `.gitignore:5` lists
`sources.yaml` with **no slash**, so git matches it at every directory level —
which is why `.gitignore:18` carries `!tests/fixtures/**/sources.yaml` with the
comment *"`sources.yaml` above matches at every level, so the fixture register
has to be let back in."* `goal.md` has no slash either, so it inherits the same
behaviour and needs the same negation. Without it, the demo fixture's `goal.md`
is silently untracked and every check that depends on it passes locally and
fails on a fresh clone.

By contrast `catalog/*` and `cards/*` *do* contain a slash, which anchors them
to the repository root — that is why `tests/fixtures/demo-project/catalog/` is
committed with no negation at all. Do not copy that pattern for `goal.md`; it is
the wrong one.

**Alternatives considered**:

- *`catalog/goal.md`* — groups it with what it shapes. Rejected: it makes the
  goal look like an output of `/catalog`, when the whole point is that it is the
  input `/catalog` is driven by. It would also be swept up by the anchored
  `catalog/*` rule and committed by accident.
- *A `goal:` block inside `sources.yaml`* — no new format, no gitignore work.
  Rejected: it conflates "what I want to learn" with "where my material is", and
  every consumer of `sources.yaml` (the ingest path, `check_sources`,
  `sources.example.yaml`, the demo register) would have to tolerate a key that
  has nothing to do with sources.

---

## R3 — How do seven steps fit a five-column strip?

**Decision**: Do **not** go to seven equal columns. Keep the five core steps as
the visual spine and give the two optional steps a distinct, narrower treatment.
Exact visual solution is a design task for implementation; what is settled here
is the constraint it has to satisfy.

**Rationale**: the measured facts, from `docs/index.html`:

| Fact | Where |
|---|---|
| `grid-template-columns: repeat(5, minmax(0, 1fr))` | line 182 |
| two columns below 1080 px, with `.step:last-child { grid-column: 1 / -1 }` for the orphaned fifth | lines 291–296 |
| one column below 540 px | line 319 |
| step caption text is `13.5px` | `.step__body p`, line 188 |
| step body padding `18px 20px` — 40 px of horizontal padding per cell | line 186 |

At the desktop breakpoint the container is about 1080 px. Five columns give each
cell ~176 px of content after padding. **Seven would give ~114 px** — a 35 %
narrower measure for text already set at 13.5 px, which is *below* the 15 px
screen floor `docs/design.md` states for reading text. The captions get away with
13.5 px today by being captions rather than paragraphs; squeezing the measure to
114 px removes that defence and makes an existing tension into a visible one.

**A correction to the plan's first draft**: the comment about an unbreakable word
at `docs/index.html:118` governs the **hero headline** (`clamp(40px, 12vw,
104px)` on the word "flashcards"), not the step strip. It is not a constraint on
this decision. The binding constraints are the caption size and the two-column
arithmetic below.

The breakpoint arithmetic also changes and must be re-derived, not copied. The
rule at line 296 exists because *five* items in two columns leave one alone in
the final row. With seven items in two columns the same thing happens — the rule
would appear to survive — but only by coincidence, and it would be wrong the
moment the count is even. Whatever the final count, the rule has to be written
against it deliberately.

**Alternatives considered**:

- *Seven equal columns* — simplest diff, one number. Rejected on the measure
  arithmetic above.
- *Two rows of 4 + 3* — keeps the measure. Rejected as the default because it
  reads as two phases when the pipeline is one sequence, and it doubles the
  border-rule bookkeeping that the flat strip currently handles with
  `:last-child`.
- *Showing only the five core steps and mentioning the optional two in prose* —
  keeps the graphic untouched. Rejected: it hides exactly the feature this work
  exists to add, and the README table would then disagree with the picture
  beside it.

---

## R4 — Where do the new broken fixtures go?

**Decision**: built in `tmp_path` through the existing `project()` helper in
`tests/test_check_project.py`. **Not** in `tests/fixtures/demo-project/broken/`.

**Rationale**: `broken/` holds six broken *card YAML files*
(`invalid-markup.yaml`, `malformed.yaml`, `missing-fields.yaml`,
`not-a-mapping.yaml`, `overflowing.yaml`, `unknown-language.yaml`). They are
inputs to the **build**, used to prove `lernkarten check` names the culprit.

The new failure cases are project-level — a malformed `goal.md`, a bad `Status:`
value, a dangling `Parents:` name — and every existing project-level breakage in
the suite is already built in a temp folder by `project(tmp_path, catalog=…)`.
Putting them in `broken/` would mix two kinds of fixture and, worse, would put a
deliberately invalid `goal.md` inside a demo project that must stay valid.

**This corrects the spec.** SC-008 says the new broken fixtures live under
`tests/fixtures/demo-project/broken/`. That placement is wrong; the requirement
it expresses — six named failure cases, each naming the culprit — is unchanged
and is carried into the Wave A–D tables in [plan.md](plan.md). The spec line
should be amended when it is next touched.

**Alternatives considered**:

- *A `broken-projects/` sibling directory* — rejected: constitution XI says
  extend the demo project, never start a second corpus, and the temp-folder
  idiom already covers this without any corpus at all.

---

## Summary of decisions

| # | Decision |
|---|---|
| R1 | Hand-rolled line scan in a pure `parse_catalog()`; no markdown library, reason recorded under Principle III |
| R2 | `goal.md` at project root; `.gitignore` entry **plus** `!tests/fixtures/**/goal.md`, matching the `sources.yaml` precedent |
| R3 | Not seven equal columns — the measure drops to ~114 px under 13.5 px captions; core spine plus distinct optional treatment, breakpoint rule re-derived |
| R4 | New broken fixtures in `tmp_path`, not `broken/`; spec SC-008 corrected |

No `NEEDS CLARIFICATION` markers remain.
