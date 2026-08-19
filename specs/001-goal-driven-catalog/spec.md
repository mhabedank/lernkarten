# Feature Specification: Goal-driven catalog

**Feature Branch**: `feat/goal-driven-catalog`

**Created**: 2026-08-18 · **Revised**: 2026-08-18 (review round 1)

**Status**: Draft

**Input**: User description: "Extend the pipeline with a learning-goal step, a catalog review and a research step, so cards stop being a rote reproduction of whatever happened to be ingested and start covering the topic the user actually wants to learn."

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: a new `/learning-goal` step ahead of `/sources`, a new optional `/research-gaps` step between `/catalog` and `/cards`, plus changes to `/catalog` and `/cards`. `/ingest` and `/print` are untouched. Documentation, the landing page and the brand graphics all change, because all three currently state the pipeline has five steps.

The pipeline becomes:

```
/learning-goal → /sources → /ingest → /catalog → (/research-gaps) → /cards → /print
```

Seven steps: five required and two optional. Both new steps are skippable — a
project with no `goal.md` behaves as it does today, apart from one advisory line
— which is why both carry the optional marking in FR-037 and SC-013.

**Implementation half**:

- [x] **Both** — the seam is two file formats. The model-driven half gains two
      skills (`skills/learning-goal/`, `skills/research-gaps/`) and changes two
      (`skills/catalog/`, `skills/cards/`). The deterministic half only learns
      to *check* what they write: `scripts/check_project.py` gains a `goal.md`
      contract, `Status:`, `Parents:` and `Related:` contracts on catalog
      subtopics, and the `research` source type; `scripts/check_docs.py` gains a
      skill-name
      disambiguation rule. No build or print code changes.

**Who runs into this**: both. The user driving Claude in their own project gets
the feature; a contributor to this repo has to keep five documents and three
rendered graphics in step with a pipeline that is no longer five commands long.

## Problem *(context for the requirements below)*

The catalog is derived from the knowledge base: `catalog = f(knowledge)`.
Everything downstream inherits that dependency, which produces two distinct
failures.

**Off-goal cards.** A user studying the *concept* of low-code development
registers three academic papers about it. The papers contain a research-method
section and a literature-history section, so the catalog contains those as
subtopics, so the cards do too. The user ends up memorising how a study was
conducted instead of what low-code is. Nothing in the pipeline currently holds a
criterion by which "research methodology" could be judged irrelevant — there is
no statement anywhere of what the user is trying to learn.

**Incomplete coverage.** A user wants to know a topic completely, but their own
material covers two thirds of it. The pipeline cannot represent "this belongs to
the topic and I have nothing on it", because a subtopic only exists if a document
produced it. Absence is invisible, so the user cannot even tell they are learning
a partial deck.

Both follow from the same root: the topic tree is a summary of the *sources*
rather than a plan for the *learner*.

The fix inverts the dependency. The catalog is built from the goal first — a
syllabus of what the user needs to know — and knowledge references are attached
to that skeleton afterwards. A branch with no references is then a **gap**, and
ingested material that fits no branch is **out of scope**. Both become structural
properties of the catalog file rather than judgements a separate review pass has
to re-derive, which is why this spec has no `/review-catalog` step.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - State what you are actually learning (Priority: P1)

The user opens a Claude session in their flashcard project and types
`/learning-goal`, followed by prose ("I have a low-code exam in September, the
professor cares about governance and the make-or-buy decision"), a pasted job ad,
or a URL to a module handbook or meeting agenda — or any mix of the three. The
skill fetches what it was given a link to, asks at most a couple of short
questions where the target is genuinely unclear, and writes `goal.md`.

A goal is allowed to contain **several unrelated areas**. Preparing for a job
interview legitimately means "the technology stack" *and* "the company and the
behavioural round" — two strands with nothing in common that must not be forced
into one hierarchy. `goal.md` therefore groups required topics under named areas,
and nothing downstream tries to find a connection between them.

Running `/learning-goal` again **reconciles** rather than merges blindly. If the
second run contradicts the first — the depth changed, a required topic became
out-of-scope, an area was dropped — the skill lists every contradiction and asks
the user to resolve each one before writing.

**Why this priority**: nothing else in this feature can exist without it. `gap`
and `out of scope` are both judgements *relative to a stated goal*; with no goal
on disk there is no criterion and the rest of the feature has nothing to stand
on. It is also independently useful on its own — a user who reads their own
distilled goal back often corrects it before ingesting anything.

**Independent Test**: run `/learning-goal` in `tests/fixtures/demo-project` with
a short brief, then `python3 scripts/check_project.py tests/fixtures/demo-project`
— `goal.md` exists, carries complete frontmatter, and holds at least one area
with at least one required topic.

**Acceptance Scenarios**:

1. **Given** a project with no `goal.md`, **When** the user runs
   `/learning-goal` with a prose description of an upcoming exam, **Then**
   `goal.md` is written with frontmatter (`goal`, `kind`, `depth`, `updated`), a
   prose statement, at least one `### <Area>` under `## Required topics` with at
   least one entry, and an `## Out of scope` section.
2. **Given** a brief describing a job interview, **When** `/learning-goal` runs,
   **Then** unrelated strands are written as **separate areas** (e.g. one for the
   technical round, one for the behavioural round), and no area contains topics
   from another.
3. **Given** a URL to a requirements document, **When** `/learning-goal` runs,
   **Then** the document is fetched and distilled into `goal.md`, and it is
   **not** registered in `sources.yaml` — a job ad states the target, it is not
   study material.
4. **Given** a `goal.md` stating `depth: working` and a second run implying
   `depth: expert`, **When** `/learning-goal` runs, **Then** it names the
   contradiction, asks which holds, and writes only the answer the user gave.
5. **Given** a `goal.md` listing "Governance" as required and a second run whose
   input puts it out of scope, **When** `/learning-goal` runs, **Then** it names
   the topic, says which catalog subtopics and card files are affected, and asks
   before moving it.
6. **Given** a re-run that adds topics and contradicts nothing, **When**
   `/learning-goal` runs, **Then** it merges without asking, preserves the
   existing areas and topics, and moves `updated` to today.
7. **Given** a brief so vague that no required topic can be derived, **When**
   `/learning-goal` runs, **Then** it asks the user rather than inventing a
   syllabus, and writes no file until it has one.

---

### User Story 2 - A catalog built from the goal, not from the sources (Priority: P2)

The user has run `/learning-goal` and `/ingest`. They type `/catalog`. The skill
now builds the topic tree from `goal.md` first — the areas and topics somebody
pursuing this goal needs — and only then walks `knowledge/` and attaches each
document to the branch it belongs to. Three things fall out of that ordering:

- a branch the goal requires and no document covers is written with
  `Status: gap` and `References: none`;
- ingested material that fits no branch of the goal is written as a subtopic with
  `Status: out of scope`, keeping its references so nothing is silently lost;
- everything else is an ordinary subtopic exactly as today.

The skill closes with a tree view naming the counts: covered, gaps, out of scope.

If there is **no** `goal.md`, the catalog is still built from the sources exactly
as today — but the skill now says so, in one line: the catalog describes the
material on hand, not the topic, and `/learning-goal` is what closes that
difference. This is the only behavioural change a user without a goal sees, and
it is also how the new step gets discovered at all.

**Why this priority**: this is where both failures are actually fixed. The gap
entries make missing knowledge visible for the first time; the out-of-scope
entries are what stops the methodology cards.

**Independent Test**: run `/catalog` against the demo project (which carries a
`goal.md`, material that is off-goal, and a required topic nothing covers), then
`python3 scripts/check_project.py tests/fixtures/demo-project --strict` — the
catalog contains at least one `Status: gap` subtopic with no references and at
least one `Status: out of scope` subtopic that keeps its references, and every
required topic in `goal.md` appears somewhere in the catalog.

**Acceptance Scenarios**:

1. **Given** a project with `goal.md` and ingested knowledge, **When** `/catalog`
   runs, **Then** every required topic in `goal.md` appears as a topic or
   subtopic in `catalog/topics.md`.
2. **Given** a `goal.md` with two unrelated areas, **When** `/catalog` runs,
   **Then** each area maps to its own top-level topic (`##`) and no subtopic is
   placed under an area it does not belong to.
3. **Given** a required topic that no ingested document covers, **When**
   `/catalog` runs, **Then** that subtopic carries `Status: gap` and
   `References: none`, and still carries the bullet points saying what it ought
   to cover.
4. **Given** ingested material matching an `## Out of scope` entry in `goal.md`,
   **When** `/catalog` runs, **Then** it appears as a subtopic with
   `Status: out of scope` whose references still resolve.
5. **Given** a project with **no** `goal.md`, **When** `/catalog` runs, **Then**
   the catalog file it writes is what today's skill would write — no `Status:`
   lines, no gaps — **and** the user is told the catalog covers the material
   rather than the topic, and pointed at `/learning-goal`.
6. **Given** a catalog written before this feature (no `Status:` lines, no
   `Goal:` in the header), **When** `check_project.py` runs, **Then** it passes
   unchanged.
7. **Given** a subtopic with neither references nor `Status: gap`, **When**
   `check_project.py` runs, **Then** it reports that subtopic by name — a branch
   with nothing behind it is either a gap or a mistake.

---

### User Story 3 - Cards stay inside the goal, and say what they do not cover (Priority: P3)

The user types `/cards`. Subtopics marked `Status: out of scope` are skipped;
subtopics marked `Status: gap` are skipped because there is nothing to read.

The two omissions are reported differently, because they mean different things:

- **Out of scope is the feature working.** It gets a bare count — "12 subtopics
  skipped as out of scope" — and nothing more. No warning, no list; the user
  already declared this material irrelevant and does not need it re-litigated on
  every run.
- **A gap means the deck is incomplete.** It gets a warning that says so in
  plain terms — these cards do not cover the whole topic — followed by the gaps
  **by name**, so the user can register a source, run `/research-gaps`, or decide
  the gap is acceptable. A count alone would be useless: the user cannot act on
  a number.

Naming an out-of-scope subtopic explicitly (`/cards research methodology`) still
generates it — the mark is a default, not a lock.

**Why this priority**: without it, User Story 2 changes a file nobody acts on. It
is small, but it is the step at which the user stops getting the wrong cards and
starts being told what is missing from the right ones.

**Independent Test**: run `/cards` over the demo project and check that no card
file contains a `subtopic:` matching an out-of-scope or gap subtopic, while the
covered subtopics all produced cards.

**Acceptance Scenarios**:

1. **Given** a catalog with out-of-scope and gap subtopics, **When** `/cards`
   runs with no arguments, **Then** no card carries either as its `subtopic:`.
2. **Given** the same catalog, **When** `/cards` finishes, **Then** out-of-scope
   subtopics are reported as a count only, and gaps are reported as a warning
   that the deck does not cover the whole topic, listing each gap by name.
3. **Given** a catalog with no gaps, **When** `/cards` finishes, **Then** no gap
   warning appears at all.
4. **Given** a catalog with one out-of-scope subtopic, **When** the user runs
   `/cards` naming it, **Then** cards for it are generated anyway.
5. **Given** a catalog with no `Status:` lines at all, **When** `/cards` runs,
   **Then** every subtopic is carded, exactly as today.

---

### User Story 4 - Close the gaps without leaving the pipeline (Priority: P4)

The catalog names four things the user needs to know and has no material for.
They type `/research-gaps`. For each gap subtopic the skill searches the web,
reads what it finds, and writes a synthesised document per gap into
`knowledge/<research-id>/`, registered in `sources.yaml` under a new source type
`research` naming the gap it was created for. Every researched document carries
the URL it came from in its frontmatter. The skill then flips the catalog entry
from `Status: gap` to an ordinary subtopic with references, and `/cards` picks it
up on the next run.

The user can always tell their own material from what the model brought in —
different source id, different type, and the card's `source:` reference names it.
Deleting a `research` source and its knowledge folder removes all of it.

**Why this priority**: it delivers the second half of the problem ("learn the
topic completely"), but the first three stories are already useful without it — a
user who sees the named gap list can register their own sources instead. It is
also the only part that reaches the network, so it is worth shipping last and
behind an explicit invocation.

**Independent Test**: run `/research-gaps` against a demo project whose catalog
has a gap; assert a new `sources.yaml` entry of type `research`, one knowledge
file with a `url:` in its frontmatter, and the catalog entry no longer marked
`Status: gap`.

**Acceptance Scenarios**:

1. **Given** a catalog with two `Status: gap` subtopics, **When** `/research-gaps`
   runs, **Then** `sources.yaml` gains entries of `type: research` naming those
   gaps, `knowledge/<research-id>/` holds one document per gap, and each
   document's frontmatter names the URLs it was built from.
2. **Given** a completed research pass, **When** the catalog is re-read, **Then**
   the previously gapped subtopics carry resolving references and no longer carry
   `Status: gap`.
3. **Given** no network access, **When** `/research-gaps` runs, **Then** it
   reports which gaps it could not close and writes nothing — it never invents a
   document without a retrieved source behind it.
4. **Given** a catalog with no gaps, **When** `/research-gaps` runs, **Then** it
   says so and exits without touching anything.
5. **Given** a project where the user deletes the `research` source entry and its
   knowledge folder, **When** `/catalog` runs, **Then** the affected subtopics
   return to `Status: gap`.

---

### User Story 5 - A subtopic that belongs under more than one topic (Priority: P5)

The catalog holds two different relations, and conflating them loses
information:

- **Containment is many-to-many.** "Access control" genuinely belongs under
  *Security* and under *Governance*. A subtopic therefore declares `Parents:`
  and may name several topics. The catalog is a directed graph, not a tree.
- **Association is symmetric.** "Governance" and "Shadow IT" are connected
  without either containing the other. That is a separate `Related:` line.

A printed card carries `TOPIC / SUBTOPIC` in its header band, so one topic has
to be chosen when cards are *materialised*. The **first** name in `Parents:` is
primary: it decides which `cards/<topic-slug>.yaml` the cards land in and what
the header band prints. Every other parent lists the subtopic on its own `Also
covers:` line, naming where the cards live. Choosing a home is a projection
rule, not a limit on the model — `/cards governance` finds a borrowed subtopic,
generates it once, and says which file it went into.

`Related:` is consumed by `/cards` for two purposes and no others: connection
cards ("What is the difference between X and Y?", "How does X constrain Y?")
for related pairs, and de-duplication when two branches converge on one idea.

**Why this priority**: it is the one part of this feature that does not serve
the original complaint, so it is the one part droppable without the rest losing
its point. It earns inclusion because a catalog that claims "Access control is
under Security" when the truth is "under both" is lying to the user about their
own subject, and because connection cards are exactly what "understand the
concept" needs — nothing currently tells `/cards` which pairs are worth
contrasting, even though its style rules already ask for distinctions.

**Independent Test**: run `check_project.py` against a demo catalog holding one
two-parent subtopic and one dangling `Related:` name — the first passes, the
second is reported. Run `/cards` naming the secondary parent and assert the
cards appear once, in the primary parent's file.

**Acceptance Scenarios**:

1. **Given** a subtopic with `Parents: Security, Governance` sitting under
   `## Security`, **When** `check_project.py` runs, **Then** it passes.
2. **Given** the same subtopic sitting under `## Governance` instead, **When**
   `check_project.py` runs, **Then** it is reported — the primary parent and the
   heading it lives under must agree.
3. **Given** a subtopic naming a parent that is not a topic in the catalog,
   **When** `check_project.py` runs, **Then** the subtopic and the dangling
   parent are both named.
4. **Given** a subtopic with two parents, **When** the catalog is read, **Then**
   the non-primary topic carries an `Also covers:` line naming it and its
   primary; a missing or non-reciprocal listing is reported.
5. **Given** a two-parent subtopic, **When** `/cards` runs over the whole
   catalog, **Then** its cards are written **once**, into the primary parent's
   file, with the primary topic in `topic:`.
6. **Given** the same catalog, **When** the user runs `/cards` naming the
   secondary parent, **Then** the subtopic is generated and the user is told the
   cards live in the primary parent's file.
7. **Given** a subtopic whose primary parent is out of scope while another
   parent is required, **When** `/catalog` runs, **Then** the in-scope parent
   becomes primary.
8. **Given** two subtopics related to each other, **When** `/cards` runs,
   **Then** at least one card contrasts or connects them, written once rather
   than once per branch.
9. **Given** a `Related:` pointing at an out-of-scope or gap subtopic, **When**
   `/cards` runs, **Then** no connection card is written for that pair.
10. **Given** a catalog with no `Parents:` and no `Related:` lines, **When**
    anything runs, **Then** behaviour is unchanged.

---

### User Story 6 - The documentation describes the pipeline that exists (Priority: P6)

A newcomer reads the README, the landing page or `docs/workflow.md`. All three
currently say the pipeline is five commands, and two rendered PNGs say it in
pixels. After this feature they describe the real pipeline, mark the two optional
steps as optional, and explain what a gap is and why a deck might have one.

This is priority-last as *work*, not as a release condition: whatever subset of
Stories 1–5 ships, the documentation ships with it in the same pull request. A
release where the landing page promises five commands and the plugin has seven is
not a release.

**Why this priority**: `docs/index.html` and the brand PNGs are visible surfaces
(constitution XVI) and the step strip is a five-column grid with a hand-written
responsive rule for the odd fifth item. Changing the step count is a real design
task, not a text edit, and it is best done once the step list has stopped moving.

**Independent Test**: `python3 scripts/check_docs.py` passes; no file in the repo
outside a changelog contains "five commands"; `python3 scripts/render_brand.py`
reproduces the committed PNGs byte-for-byte from the Typst sources.

**Acceptance Scenarios**:

1. **Given** the updated pipeline, **When** the repo is searched for "five
   commands" and "Five commands", **Then** there are no matches outside the spec
   history.
2. **Given** `assets/brand/common.typ`, **When** the command tuple is read,
   **Then** it lists the new pipeline, and `banner.png`, `pipeline.png` and
   `social-card.png` have been re-rendered from it.
3. **Given** the landing page step strip, **When** it is viewed at the desktop,
   tablet and mobile breakpoints, **Then** every step is visible, none is
   orphaned in a row of its own by accident, and the optional steps are visually
   marked as optional.
4. **Given** `docs/workflow.md`, **When** it is read end to end, **Then** it has a
   section per pipeline step in order, and a passage explaining gaps and
   out-of-scope material.
5. **Given** `scripts/check_docs.py`, **When** it runs, **Then** every skill
   description names its triggers *and* a word tying it to this plugin, so a
   generic name cannot be matched by accident.

---

### Edge Cases

- **Skill name shadowing**: `goal` and `research` are generic enough that another
  installed skill could plausibly claim the same trigger, and the plugin ships to
  environments this repo cannot see. Handled by naming: canonical names are
  `learning-goal` and `research-gaps`, and every description carries a
  disambiguating domain word. See the skill-naming requirements below.
- **Missing optional tooling**: `/research-gaps` needs web access; without it, it
  degrades to reporting unclosed gaps (never fails). No other step in this feature
  reaches outside the project folder.
- **Fresh install on each platform**: nothing new to install — the whole feature
  is prompts plus checks in two existing scripts.
- **Python floor**: `check_project.py` and `check_docs.py` gain parsing only;
  3.12 with the current dependencies.
- **Encoding and file names**: `goal.md` is user-written and can hold umlauts and
  non-Latin script; read and written as UTF-8 like every other artifact.
- **Non-Latin card text**: unaffected — this feature changes which cards exist,
  never how they are typeset.
- **Idempotence**: running any step twice changes nothing the second time.
  Deleting one researched knowledge file and re-running `/catalog` brings that
  subtopic back to `Status: gap`, and `/research-gaps` restores exactly that one.
- **Text that does not fit** a 105 × 74.25 mm card: unchanged behaviour.
- **Goal and sources in different languages**: `goal.md` may be German while the
  papers are English. Topic matching is by meaning, not by string; card language
  still follows the source material and the `language:` key, unchanged.
- **A goal far larger than the knowledge base**: a catalog that is almost entirely
  gaps is a valid, useful state — it is the user's to-do list, not an error.
- **Retrofitting a goal onto an existing project**: adding `goal.md` re-shapes the
  catalog on the next `/catalog` run. Existing card files are left alone; the user
  is told which card files contain now-out-of-scope subtopics so they can decide.
- **A goal whose areas overlap after all**: two areas that turn out to share a
  subtopic are resolved by giving it both as `Parents:`. It is written once,
  under whichever is primary, and listed under the other.
- **A parent removed from the catalog**: deleting a topic that is some
  subtopic's primary parent orphans it. Reported by name rather than silently
  re-homed — the user decides which remaining parent takes over.
- **A subtopic borrowed by a topic that is out of scope**: the borrowing is kept
  but produces nothing, exactly as any other out-of-scope entry does.
- **A half-edited catalog**: a `Parents:` line updated without its matching `Also
  covers:` listing, or the reverse, is the failure mode this model actually
  invites. It is a reported error, not a warning — the next step would otherwise
  card the subtopic into a file the user cannot find.
- **Landing page at the two-column breakpoint**: the current rule exists because
  five steps in two columns leave one alone. A different step count changes that
  arithmetic and the rule has to be re-derived, not copied.

## Requirements *(mandatory)*

### Functional Requirements

**The `/learning-goal` skill**

- **FR-001**: The `learning-goal` skill MUST accept prose, pasted text and URLs
  in any combination, fetch what it is given links to, and distil all of it into
  a single `goal.md` at the project root.
- **FR-002**: `goal.md` MUST carry frontmatter with `goal` (a one-line
  statement), `kind` (one of `exam`, `meeting`, `interview`, `self-study`),
  `depth` (one of `awareness`, `working`, `expert`) and `updated` (ISO date),
  followed by `## Required topics` and `## Out of scope`.
- **FR-003**: `## Required topics` MUST be grouped into one or more named areas
  (`### <Area>`), each holding its own topics, so a goal can hold strands with
  nothing in common — a technical round and a behavioural round — without either
  being forced into the other's hierarchy.
- **FR-004**: The skill MUST NOT register the requirement documents it reads as
  entries in `sources.yaml`.
- **FR-005**: On a re-run the skill MUST detect contradictions against the
  existing `goal.md` — a changed `kind` or `depth`, a topic moving between
  required and out-of-scope, a dropped area or topic — present every one of them
  to the user, and resolve each by asking. It MUST NOT silently prefer either
  version.
- **FR-006**: When presenting a contradiction that narrows scope, the skill MUST
  name what already depends on it: the catalog subtopics and the card files that
  would become out of scope.
- **FR-007**: A re-run that only adds MUST merge without questions, preserving
  existing areas and topics and moving `updated` to today.
- **FR-008**: The skill MUST ask rather than invent required topics when the
  input does not support any, and write no file until it can.

**The `/catalog` skill**

- **FR-009**: When `goal.md` exists, the skill MUST derive the topic hierarchy
  from the goal's areas and required topics first, and attach `knowledge/`
  references to that hierarchy afterwards.
- **FR-010**: Each area in `goal.md` MUST map to its own top-level topic, and the
  skill MUST NOT merge unrelated areas or place a subtopic under an area it does
  not belong to.
- **FR-011**: A required subtopic that no document covers MUST be written with
  `Status: gap` and `References: none`, keeping the bullet points describing what
  it should cover.
- **FR-012**: Ingested material matching no required topic MUST be written with
  `Status: out of scope`, keeping its references intact.
- **FR-013**: When `goal.md` does not exist, the catalog file the skill writes
  MUST be what today's skill writes — no `Status:` lines, no gap reporting — and
  the skill MUST additionally tell the user that the catalog describes the
  material rather than the topic, and point at `/learning-goal`.
- **FR-014**: A subtopic belonging under more than one topic MUST be written
  once, under its primary parent, carrying `Parents:` with every parent and the
  primary first; every other parent MUST carry an `Also covers:` line naming the
  subtopic and where its cards live.
- **FR-015**: When a subtopic's primary parent is out of scope and another of
  its parents is required, the skill MUST make the in-scope parent primary.
- **FR-016**: The skill MUST report covered, gap and out-of-scope counts at the
  end of a run, and point at `/research-gaps` when there is at least one gap.

**The `/cards` skill**

- **FR-017**: The skill MUST skip subtopics marked `Status: out of scope` or
  `Status: gap` when invoked with no arguments.
- **FR-018**: The skill MUST report out-of-scope subtopics as a **count only** —
  no warning and no list.
- **FR-019**: The skill MUST report gaps as a **warning stating that the cards do
  not cover the whole topic**, listing every gap by name, and pointing at the two
  ways to act on it (register a source, or run `/research-gaps`).
- **FR-020**: The skill MUST generate cards for an out-of-scope subtopic when the
  user names it explicitly.
- **FR-021**: When a subtopic carries several `Parents:`, the skill MUST write
  its cards **once**, into the primary (first) parent's
  `cards/<topic-slug>.yaml`, with the primary topic as the file's `topic:`.
- **FR-022**: When the user names a non-primary parent, the skill MUST still
  generate the borrowed subtopic and MUST tell the user which file its cards
  live in.
- **FR-023**: When a subtopic carries `Related:`, the skill MUST use it to
  generate connection or distinction cards for the pair, and MUST NOT write the
  same card once per branch when two branches converge.
- **FR-024**: The skill MUST NOT write a connection card for a `Related:` target
  that is a gap or out of scope.

**Skill naming and discoverability**

- **FR-025**: The two new skills MUST be named `learning-goal` and
  `research-gaps`. Bare `goal` and `research` are common enough words that
  another installed skill may claim the trigger, and the plugin ships into
  environments this repo cannot inspect.
- **FR-026**: Every skill description in this repo MUST name a word tying it to
  this plugin's domain (`flashcard`/`flashcards`), in addition to the triggers
  constitution X already requires, so a generic slash command resolves to the
  right skill by description. This retrofits `catalog` and `ingest`, whose
  descriptions do not currently say what the topics and the sources are *for*.

**The `/research-gaps` skill**

- **FR-027**: The skill MUST take the `Status: gap` subtopics of
  `catalog/topics.md` as its work list, and report and exit when there are none.
- **FR-028**: The skill MUST register what it retrieves in `sources.yaml` as
  `type: research` with a `gap` key naming the subtopic it was created for, and
  write the resulting documents under `knowledge/<research-id>/` with the
  existing frontmatter contract, including the `url` it was built from.
- **FR-029**: The skill MUST NOT write a knowledge document with no retrieved
  source behind it, and MUST report gaps it could not close rather than filling
  them from the model's own recall.
- **FR-030**: The skill MUST update the catalog entries it closed so they carry
  resolving references and no longer carry `Status: gap`.

**`scripts/check_project.py`**

- **FR-031**: MUST validate `goal.md` when it exists: required frontmatter keys
  present, `kind` and `depth` from their closed sets, `updated` an ISO date, and
  at least one area holding at least one required topic. A project without
  `goal.md` MUST pass unchanged.
- **FR-032**: MUST accept `Status: gap` and `Status: out of scope` on catalog
  subtopics, reject any other `Status:` value by naming the subtopic and the bad
  value, and report a subtopic that has neither references nor `Status: gap`.
- **FR-033**: MUST accept `Parents:` on a subtopic and report, by subtopic name:
  a parent that is not a topic in the same catalog; a primary parent that is not
  the heading the subtopic lives under; and an `Also covers:` listing that the
  named subtopic's own `Parents:` does not reciprocate.
- **FR-034**: MUST accept `Related:` on a subtopic and report any name in it that
  is not a subtopic of the same catalog.
- **FR-035**: MUST accept `research` as a source type, require its `gap` key, and
  not require a `path` or `url` on it.
- **FR-036**: MUST warn when `goal.md` names a required topic that appears nowhere
  in `catalog/topics.md` — the catalog has drifted and `/catalog` should be re-run.
  **Matching is deliberately loose**: a goal bullet is prose ("What low-code is, and
  where the boundary to no-code runs") while the catalog heading is a label ("What
  low-code is"), so exact string equality would warn on a correct catalog. Compare
  case-insensitively after stripping punctuation, and treat a required topic as
  present when a topic or subtopic name is contained in the bullet or the bullet in
  it. False negatives are acceptable here and false positives are not: this is a
  warning that tells the user to re-run `/catalog`, and one that cries wolf gets
  ignored.

**Documentation, landing page and brand graphics**

- **FR-037**: `README.md`, `docs/workflow.md`, `docs/index.html` and `CLAUDE.md`
  MUST describe the pipeline that exists, marking `/learning-goal` and
  `/research-gaps` as optional, and MUST NOT state a command count that
  contradicts it.
- **FR-038**: `assets/brand/common.typ` MUST carry the new command list, and
  `banner.png`, `pipeline.png` and `social-card.png` MUST be re-rendered from the
  Typst sources with `python3 scripts/render_brand.py`.
- **FR-039**: The landing page step strip MUST show every step legibly at the
  desktop, tablet and mobile breakpoints, with the optional steps visually
  distinguished, and the existing hand-written rule for the orphaned fifth step
  MUST be re-derived for the new count rather than carried over.
- **FR-040**: `docs/workflow.md` MUST explain what a gap is, what out-of-scope
  material is, and what a user does about each.

**Bugfix requirements** *(added by `/speckit.bugfix.patch`, not by the original
specification — each names the report it comes from)*

**Bugfix**: 2026-08-19 — [BUG-001](bugs/BUG-001.md) the card markup contract had
no emphasis rule and stated the backslash without its precondition; FR-041 to
FR-043 close it.

- **FR-041**: The card markup contract MUST state how to emphasise text —
  `*bold*` and `_italic_`, and that `**...**` is markdown rather than Typst and
  produces two empty strong elements around unemphasised text. It MUST say so in
  all three places that carry the contract: `CLAUDE.md`, `skills/cards/SKILL.md`
  and `docs/workflow.md`.
- **FR-042**: The same three places MUST state the backslash's precondition: `\`
  is a line break only when what follows it is not a markup character, and
  before one it escapes that character instead. A card string is one line of
  YAML, so this is reachable in ordinary use.
- **FR-043**: `scripts/check_project.py` MUST report, naming the card,
  `**...**` in a card's `front` or `back`, and a backslash immediately followed
  by a markup character. Both are accepted by the typesetter — the first
  silently, the second only when the remaining delimiters happen to balance — so
  the build gate cannot catch either and the check is the only thing that can.

**Bugfix**: 2026-08-19 — [BUG-002](bugs/BUG-002.md) the knowledge store had no
uniqueness rule, so Zotero items sharing a title overwrote each other and were
counted as skipped; FR-044 and FR-045 close it.

- **FR-044**: File names under `knowledge/<id>/` MUST be unique per source
  document. `/ingest` MUST NOT drop or overwrite a document because another
  document produced the same name. For the Zotero path the identity is the
  item key, which is already written to the frontmatter as `zotero_key`, and the
  collision-free name is `<slug>-<zotero_key>.md`.
- **FR-045**: A document MUST be counted as `skipped` only when the file already
  on disk is *the same source document* — for Zotero, when its frontmatter
  `zotero_key` matches the item in hand. A name collision MUST be counted
  separately and named in the summary. A file written earlier in the same run
  MUST NOT be able to satisfy the skip test at all, whatever its timestamp says.

**Bugfix**: 2026-08-19 — [BUG-003](bugs/BUG-003.md) the reported `ROOT`-based
output path is gone, but the destination is still implicit and never reported;
FR-046 closes what survives.

- **FR-046**: A pipeline step that writes files MUST name where it wrote them.
  `scripts/zotero_ingest.py` MUST print the resolved **absolute** target
  directory in its summary, and `skills/ingest/SKILL.md` MUST pass `--project`
  explicitly rather than relying on the process's working directory being the
  project.

**Bugfix**: 2026-08-19 — [BUG-004](bugs/BUG-004.md) a thin-but-complete document
and a failed extraction were written identically, so `/catalog` had to guess;
FR-047 and FR-048 close it.

- **FR-047**: `/ingest` MUST distinguish a document with **no text layer** from
  one whose extraction **succeeded and yielded little**. The first keeps
  `pending:` and goes to the Read tool. The second MUST be written with the text
  it has, plus a frontmatter marker carrying the extracted character count, and
  MUST NOT be marked `pending:` — there is nothing for a second pass to find.
- **FR-048**: `/catalog` MUST treat a marked document as complete but low-yield:
  it may be referenced, and it MUST NOT on its own make a required topic count
  as covered. A cover page is not evidence, and FR-011's `Status: gap` is the
  honest outcome when it is all there is.

**Bugfix**: 2026-08-19 — [BUG-005](bugs/BUG-005.md) a comma inside a topic name
was parsed as a list separator, so a valid catalog failed to validate against
itself; FR-049 closes it, and FR-033 and FR-034 are read subject to it.

- **FR-049**: A topic or subtopic name MUST be allowed to contain a comma.
  `Parents:`, `Related:` and `Also covers:` MUST be resolved against the names
  the catalog actually declares, **longest match first**, before what is left
  over is split on commas and reported as dangling. This keeps the format
  unchanged, so every catalog written against 0.3.1 stays valid, and keeps the
  dangling-name diagnostics FR-033 and FR-034 exist for.

### Format Contracts *(mandatory — state "none" if untouched)*

This feature adds a **fifth** file format to the four in constitution Principle I
and changes two of the existing four. Both changes are additive: every artifact
written before this feature stays valid.

| Artifact | Change | Also needs updating |
|---|---|---|
| `goal.md` *(new)* | **New format.** Frontmatter (`goal`, `kind`, `depth`, `updated`), `## Required topics` grouped into `### <Area>`, and `## Out of scope`. Project root, alongside `sources.yaml`. | `skills/learning-goal`, `skills/catalog`, `skills/research-gaps`, `scripts/check_project.py`, `.gitignore`, `.githooks/pre-commit`, `tests/test_repo_hygiene.py`, the demo project, `docs/workflow.md`, `README.md`, `CLAUDE.md`, the constitution's format table |
| `sources.yaml` | New source type `research`, with a `gap` key and no `path`/`url` | `skills/sources`, `skills/research-gaps`, `scripts/check_project.py`, `sources.example.yaml`, the demo register |
| `knowledge/<id>/<doc>.md` frontmatter | ~~none — researched documents use the existing `source` / `url` / `ingested` contract~~ **superseded 2026-08-19 by [BUG-004](bugs/BUG-004.md)**: an optional yield marker with the extracted character count (FR-047). Additive — a document without it reads exactly as before. The row was true of *researched* documents and was read as a claim about the whole format | `scripts/zotero_ingest.py`, `skills/ingest`, `skills/catalog`, `scripts/check_project.py`, the demo project |
| `catalog/topics.md` structure | Optional `Status: gap` \| `Status: out of scope` per subtopic; optional `Parents:` naming every topic a subtopic belongs under, primary first; optional `Also covers:` on a topic listing borrowed subtopics; optional `Related:` naming associated subtopics; optional `Goal:` in the header; `References: none` permitted on a gap. **Amended 2026-08-19 by [BUG-005](bugs/BUG-005.md)**: a name may contain a comma, so these three lines are resolved against the declared names longest-first before the remainder is split (FR-049) | `skills/catalog`, `skills/cards`, `skills/research-gaps`, `scripts/check_project.py`, the demo catalog |
| `cards/*.yaml` schema | none | — |

**Why the catalog is a graph, and where the tree survives.** Containment in a
learning catalog is genuinely many-to-many, and the format was never the reason
to pretend otherwise — a `Parents:` line expresses polyhierarchy in markdown
perfectly well. The real constraint is downstream and visible: `templates/card.typ`
prints `TOPIC / SUBTOPIC` into the header band of every physical card, so one
topic has to be chosen before ink hits paper. This spec answers that with a
**projection rule** (primary parent decides the card file and the header) rather
than by flattening the model, so the catalog stays true to the subject and the
card stays printable.

Two alternatives were considered:

- **Cards belonging to several topics** — `topic:` becomes a list. This removes
  the projection rule but changes the contract with the deterministic half
  (`build_pdf`, `check_project`, the schema in `CLAUDE.md` and `example.yaml`)
  *and* forces a card-design decision: the header band is fixed-height and never
  shrinks type (constitution XVI), so two topic names in 105 mm either truncate
  or need the band redesigned. Rejected — it reopens the card layout to solve an
  organisational problem.
- **A separate relation file** carries the most structure and is the least
  readable. `catalog/topics.md` is the artifact a human scans to choose what to
  card; an adjacency list is not that, and a new format multiplies the blast
  radius Principle I already warns about.

**The graph is bipartite, so there is nothing to check for cycles.** Topics
(`##`) contain subtopics (`###`) and the catalog stays two levels deep; edges
only ever run from a topic to a subtopic, so a cycle cannot be formed. The
invariants worth checking are different and catch the failure that actually
happens — a half-edited catalog: every `Parents:` name is a real topic, the
primary parent equals the heading the subtopic lives under, and every `Also
covers:` listing is reciprocated by the subtopic's own `Parents:`. Deeper
nesting, which would make cycles possible, is out of scope.

Directed **prerequisite** edges are also out of scope: they imply a learning
order, and nothing consumes an order today — `/print` emits a sheet, not a
schedule. Adding an edge type nothing reads would be format surface without a
consumer.

**Backwards compatibility**: yes, in both directions, with **one** deliberate
exception. Invariant C-6 (FR-032) makes a subtopic carrying neither references nor
`Status: gap` an error, and a catalog written before this feature could contain one.
That is intended — US2 acceptance scenario 7 asks for exactly this report, because a
branch with nothing behind it is either a gap or a mistake — but it means the claim
below is "every *well-formed* artifact stays valid", not literally every artifact. A
project hitting it fixes it by adding `Status: gap`, which is one line and is what the
error message says. Everything else is additive: a project on disk today has
no `goal.md`, so `/catalog` and `/cards` write what they write today and
`check_project.py` passes it unchanged; the only difference the user sees is one
advisory line. A catalog written by the new `/catalog` is still valid for the old
checks — `Status:` and `Related:` are extra lines inside a subtopic body. No
migration step.

### Print & Design Impact *(mandatory)*

The card itself is untouched, but the pipeline's *step count* is drawn in three
committed PNGs and laid out by a hand-tuned CSS grid, so this is a
design-impacting feature. `docs/design.md` must be read before the landing page
is touched (constitution XVI).

- **Visible surfaces touched**: the landing page step strip
  (`docs/index.html`), the README banner (`assets/banner.png`), the pipeline
  strip (`assets/pipeline.png`) and the social card (`assets/social-card.png`).
  Not the card, not the press sheet, not the mark.
- **Black-only laser print still readable**: N/A — nothing printed changes.
- **Minimum type size respected**: yes — the step strip must stay at or above
  15 px on screen with more columns than before, which is the binding constraint
  on how the extra steps are laid out.
- **Brand PNGs need re-rendering**: **yes** — `assets/brand/common.typ` line 67
  holds the command tuple, and `banner.typ`, `pipeline.typ` and `social-card.typ`
  all render "five" from or alongside it. Re-render with
  `python3 scripts/render_brand.py`.
- **Duplex alignment unaffected**: yes.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. The new
  parsing in `check_project.py` is frontmatter and prefixed lines, both already
  handled by PyYAML and the existing `frontmatter()` helper.
- **New runtime dependency**: none.
- **New dev dependency**: none.
- **New external binary**: none. `/research-gaps` uses the web access Claude Code
  already has; there is no path where the user installs anything.
- **Anything this makes redundant**: none.
- **Engine version change**: no.
- **Platforms verified**: all three — the feature is prompts plus pure-Python
  checks, and CI already runs `pytest` and the doc checks on Windows, macOS and
  Linux.

### Key Entities

- **Learning goal** (`goal.md`): what the user is trying to be able to do, the
  occasion (`exam`, `meeting`, `interview`, `self-study`), the depth
  (`awareness`, `working`, `expert`), the required topics grouped into areas, and
  the topics explicitly unwanted. One per project.
- **Area**: a named strand of a goal. Areas are independent by construction —
  an interview goal's technical and behavioural strands share nothing, and
  nothing downstream tries to relate them.
- **Gap**: a subtopic the goal requires and no knowledge document covers.
  `Status: gap` with `References: none` — a visible entry rather than an absence.
- **Out-of-scope subtopic**: ingested material belonging to no required topic.
  Kept with its references, marked, skipped by `/cards` unless named.
- **Parent set**: the topics a subtopic belongs under, primary first.
  Containment is many-to-many, so this is a set rather than a single home. The
  primary parent is the projection rule: it decides which card file the subtopic
  materialises into and which topic name the printed header band carries.
- **Related pair**: an undirected association between two subtopics that belong
  together without either containing the other — a different relation from
  parenthood, and not a substitute for it. Consumed only by `/cards`, for
  connection cards and de-duplication.
- **Research source**: a `sources.yaml` entry of `type: research` carrying the
  `gap` it closes. Its documents live in their own `knowledge/<research-id>/`
  folder, each naming the URL it was built from, so model-supplied material stays
  distinguishable from the user's own and can be deleted wholesale.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a demo project whose sources contain both on-goal and off-goal
  material, `/catalog` marks every off-goal branch `Status: out of scope` and
  `/cards` produces **zero** cards carrying those subtopics — the low-code
  scenario, where research-methodology cards go from present to absent.
- **SC-002**: Every required topic in `goal.md` is present in
  `catalog/topics.md` after a `/catalog` run, either with references or as
  `Status: gap`. No required topic is silently absent.
- **SC-003**: A user who runs `/cards` on a deck with gaps is told, in the run
  itself, that the deck does not cover the whole topic and **which** subtopics
  are missing — never a bare number. A deck with no gaps produces no such
  warning.
- **SC-004**: A goal with two unrelated areas produces a catalog with two
  independent top-level topics, and no subtopic of one area appears under the
  other.
- **SC-005**: A re-run of `/learning-goal` that contradicts the stored goal
  writes nothing until every contradiction has been put to the user and
  answered; a re-run that only adds writes without asking.
- **SC-006**: A project with no `goal.md` produces a `catalog/topics.md` and card
  files carrying **no new line this feature introduces** — no `Status:`, no
  `Parents:`, no `Also covers:`, no `Related:`, no `Goal:` — and both validate
  unchanged against `check_project.py`. The only difference is one advisory line
  in the run output — the added steps cost nothing to a user who does not want
  them. (Byte-identity is not asserted: both artifacts are model-generated and
  two runs of today's pipeline do not reproduce each other byte for byte either.)
- **SC-007**: A project whose goal exceeds its knowledge base reports its gaps as
  a named list, and after `/research-gaps` the number of `Status: gap` subtopics
  is strictly lower, with every newly covered subtopic backed by at least one
  resolving reference whose document names a retrieved URL.
- **SC-008**: `python3 scripts/check_project.py tests/fixtures/demo-project
  --strict` exits 0 on the extended demo project, and names the offending file,
  subtopic and value on each new broken fixture: a `goal.md` missing `kind`, a
  `goal.md` with an empty area, a bad `Status:` value, a referenceless subtopic
  that is not a gap, a dangling `Related:` name, and a `research` source with no
  `gap` key.
- **SC-009**: `python3 scripts/check_docs.py` exits 0, and fails when a skill
  description carries triggers but no domain word.
- **SC-010**: Searching the repository for "five commands" returns no match
  outside this spec, and `python3 scripts/render_brand.py` reproduces the three
  committed PNGs from the Typst sources.
- **SC-011**: A subtopic with two parents appears once in `catalog/topics.md`,
  is listed under both topics, and produces its cards exactly once — in the
  primary parent's file, with the primary topic printed in the header band.
  Naming either parent in `/cards` reaches it.
- **SC-012**: `check_project.py` reports a dangling parent, a primary parent that
  disagrees with its heading, and a one-sided `Also covers:` listing, each naming
  the subtopic at fault.
- **SC-013**: The pipeline a new user has to understand grows from five steps to
  seven, of which two are marked optional, and the README command table and the
  landing page step strip both still fit on one screen at the desktop breakpoint.

**Bugfix**: 2026-08-19 — [BUG-001](bugs/BUG-001.md) to [BUG-005](bugs/BUG-005.md)
added SC-014 to SC-018.

- **SC-014**: A card file whose `back` contains `**bold**`, or a backslash
  directly followed by `*`, is reported by `scripts/check_project.py` with the
  card named — neither reaches a PDF unremarked.
- **SC-015**: Two Zotero items sharing one title produce **two** knowledge
  documents, each carrying its own `zotero_key`, and the run reports no `skipped`
  against an empty knowledge directory.
- **SC-016**: The `/ingest` summary names the absolute directory it wrote into,
  so a wrong destination is visible without listing the file system.
- **SC-017**: A PDF whose extraction yields a short but non-empty text is written
  with that text and its character count, and is not marked `pending:`; a PDF
  with no text layer still is.
- **SC-018**: A catalog whose topic name contains a comma, referenced from
  `Parents:`, `Related:` and `Also covers:`, validates clean —
  `python3 scripts/check_project.py <project> --strict` exits 0.

## Assumptions

- The user has Python 3.12+ and a working Claude Code install, as today.
- `goal.md` is user content and therefore gitignored, hook-blocked and asserted
  by `tests/test_repo_hygiene.py` alongside `sources.yaml`, `knowledge/`,
  `catalog/` and `cards/` (constitution VII). The demo project under
  `tests/fixtures/` carries the one committed `goal.md`, invented for this repo.
- One goal per project. A user pursuing two unrelated *targets* uses two project
  folders; a single target with unrelated *strands* uses areas within one goal.
- The catalog stays **two levels deep**: topics contain subtopics, and nothing
  else. Multiple parenthood makes the structure a bipartite graph rather than a
  tree, but not a general one — edges only run from topic to subtopic, so no
  cycle can form and nothing needs an acyclicity check. Deeper nesting, which
  would change that, is out of scope.
- No `goal` or `research` skill exists in this repo or on the author's machine
  today; the renaming requirement is a precaution against the environments the plugin ships into
  and against future built-ins, not a fix for an observed collision.
- `/learning-goal` fetches URLs it is handed for *requirements* and deliberately
  does not register them as sources. A user who wants a syllabus carded registers
  it with `/sources` themselves.
- `/research-gaps` produces one synthesised document per gap subtopic — enough for
  the 3–8 cards a subtopic normally yields, not an exhaustive survey. Depth
  follows the `depth` key in `goal.md`.
- The gap warning lives in `/cards`, not `/print`, on purpose. `/print` is the
  deterministic half and reads only `cards/*.yaml`; making it read the catalog
  would breach the boundary in constitution Principle I, and writing gap state
  into the card schema would pollute a format this feature otherwise leaves
  alone. A user who wants the warning at print time is asking for a different
  feature.
- Matching ingested material to required topics, and deciding which subtopics are
  related, are judgements the model makes by meaning, across languages. What is
  testable, and what this spec asserts, is the *shape* of the result — every
  required topic present, every subtopic referenced or marked, every `Related:`
  name resolving — never the quality of the judgement. Whether the judgement is
  any good is what reading a printed card is for.
- The test-first artifact for all four skill changes is a check in
  `scripts/check_project.py` plus a case in `tests/test_check_project.py`
  (constitution XI), with new broken fixtures under
  `tmp_path`, built through the existing `project()` helper — the `broken/`
  folder holds broken *card YAML* for the build, not project-level breakages.
  The `check_docs.py` domain-word rule is
  tested the same way. No new corpus: the demo project is extended with a
  `goal.md` holding two areas, one off-goal body of material, one uncovered
  required topic, one `Related:` pair and one `research` source.
- The constitution's Principle I format table and the five-step pipeline sentence
  in its Identity section both need amending. That amendment is part of this
  feature's work, by pull request like anything else.
