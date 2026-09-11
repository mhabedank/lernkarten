# Feature Specification: Practitioner material, goal fit, and source discovery

**Feature Branch**: `feat/goal-fit-sources`

**Created**: 2026-09-07

**Status**: Clarified

**Input**: GitHub issue #44 — "Practitioner material has nowhere to go, and no source is ever judged against the goal". Make practitioner material (company and engineering blogs, application scenarios, case studies, incident post-mortems, fuck-up reports) usable as source material, by wrapping two things around the existing fetch: a source is judged against `goal.md` before it is taken in, and the pipeline helps find credible sources instead of assuming the user already has a list.

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/sources` (piece A — the goal-fit assessment — **and** piece C — the discovery mode, split in round 3 into **C1**, the material-class-neutral discovery contract, and **C2**, the addenda, of which this feature ships exactly one), `/ingest` (piece B — writes the `nature: experience` marker), `/catalog` and `/cards` (piece B — read it). `/learning-goal`, `/research-gaps` and `/print` are untouched except for one stale sentence in `skills/research-gaps/SKILL.md` that this feature corrects (FR-034). FR-037 forbids `/ingest`, `/catalog`, `/cards` and `/print` from entering or mentioning discovery, which asks no change of any of them — it fixes today's behaviour in writing so a later edit cannot drift into it.

**The pipeline stays at seven steps.** Piece C is a mode of `/sources`, not a new command. See Clarification Q4: nothing about the step count, the brand graphics, the README banner, `docs/workflow.md`, `docs/index.html`, `CLAUDE.md` or the constitution's Identity section moves.

**Implementation half**:

- [x] **Both** — the behaviour is model work in `skills/*/SKILL.md`; the test-first artifacts are deterministic checks. The seam is stated below, because this feature sits on the awkward side of it.

  Almost nothing piece A or piece C does lands on disk. A goal-fit assessment is a sentence in a run; a discovery proposal is a list the user reads and then discards or accepts. Constitution XI answers exactly this case in three parts, and all three apply:

  | The rule is about | The check goes in |
  |---|---|
  | what the skill's own `SKILL.md` must contain, and what the skill says to the user | `scripts/check_docs.py` + `tests/test_check_docs.py` |
  | a key a skill writes into a user's project (`nature:`) | `scripts/check_project.py` + `tests/test_check_project.py` |
  | a requirement satisfied only by what a run *says* | the manual checklist in `docs/testing.md`, **named there**, never left implicit |

  After clarification the split is settled:

  - **Piece A leaves nothing on disk** (Q2: the verdict is not persisted). Every piece-A requirement is verified by a `check_docs.py` check on `skills/sources/SKILL.md` plus a **named manual row** in `docs/testing.md` under FR-032. `check_project.py` sees none of it.
  - **Part of piece B is assertable** (Q1: `/ingest` writes `nature: experience`). Because the marker is on disk and validated, a check can reach past it — for example, that a card drawn from a subtopic whose references include a `nature: experience` document carries the `source:` attribution FR-011 demands.
  - **Piece C leaves nothing on disk until the user picks**, and what it then writes is an ordinary `sources.yaml` entry that today's `check_project.py` already validates. Its C1/C2 split is a split of the *prompt contract*, so it lands entirely in `check_docs.py`: the neutral contract and the practitioner addendum are asserted as separate checks (FR-039), which is what lets a later material class attach an addendum without editing a neutral check.

**Who runs into this**: the user driving Claude in their own project. A contributor only meets it through the gates.

## Problem *(context for the requirements below)*

**Nothing judges a source.** `/sources` determines the type by heuristic, assigns an id, checks that the path resolves or the URL is present, and writes the entry. It never asks whether the material serves `goal.md`. A source is registered because the user named it, and the first moment anything notices a mismatch is `/catalog`, marking the resulting subtopics `Status: out of scope` — after the fetch, after the extraction, after the user has spent the time.

**Nothing finds sources.** `/research-gaps` reaches the network, but only for subtopics already marked `Status: gap` — so it cannot run at all for a user who has a goal and no sources, because there is no catalog yet — and what it produces is *synthesised content* written into `knowledge/`, not a list of sources to register. There is no path that goes looking for **sources worth registering** and hands them back for the user to decide on. The pipeline assumes the user arrives with a list.

**Practitioner material is misjudged by the usual proxies, in both directions.** A company post-mortem is a primary source and a piece of marketing at the same time: nobody else has the timeline, the graphs or the internal decisions, and it is published by the party with the strongest interest in how the incident reads. Peer review, citation counts and institutional authority score it low for being a corporate blog and have nothing to say about the part that makes it valuable. Published incident reports also carry **survivorship bias by construction** — companies publish the failures whose resolution flatters them, and the ones that ended a company rarely get a write-up. And the real question about them is **transferability, not truth**: an outage across ten thousand servers can be reported accurately and still teach nothing usable to a reader operating three.

**The goal contract already holds the hook.** `goal.md` carries two closed sets, both validated (`scripts/check_project.py:39-40`): `kind: exam | meeting | interview | self-study` and `depth: awareness | working | expert`, where `expert` is defined in `skills/learning-goal/SKILL.md` as *"argue the edge cases and the trade-offs"*. That is a description of what a post-mortem supplies and a textbook does not. So the judgement this feature adds is not "is this source any good" — it is **"does this source serve this goal"**, which has something concrete to reason from:

- `depth: expert`, or `kind: interview` / `meeting` → practitioner material is often the highest-value source available, because the edge cases and the trade-offs *are* the content.
- `kind: exam` with `depth: awareness` → largely noise. An exam asks what the term means, not how it failed at one company on one Tuesday.

**This is not a sixth source type.** A post-mortem is a URL and `type: web` already exists (`SOURCE_TYPES`, `scripts/check_project.py:32-38`; `web` at `:35`). The gap is the judgement around the fetch, not the fetch.

## Clarifications

### Session 2026-09-07

- Q: Does piece B need a `nature: experience` marker in the `knowledge/<id>/<doc>.md` frontmatter, written by `/ingest`? (FR-015) → A: Yes, as a closed vocabulary. `/ingest` writes `nature: experience`; `check_project.check_knowledge` validates the key by name and by allowed value, exactly as `CONTENT_STATES` and `VISUAL_KINDS` are validated today. The key is optional and additive, so every project on disk validates unchanged. Consequence: part of piece B becomes assertable in `check_project.py` (FR-031) rather than resting on the run-output carve-out.
- Q: Does the goal-fit assessment persist as a `fit:` note on the `sources.yaml` entry, or is it said and not stored? (FR-007) → A: Run output only. `sources.yaml` is untouched; there is no `fit:` key and the first format contract does not move. Rationale: a stored verdict is derived state about a goal that moves underneath it — edit `goal.md` and every `fit:` is stale with nothing to re-derive it, because FR-008 forbids re-assessment on a listing. That is issue #33's FR-002 objection unchanged. Consequence: every piece-A requirement is verified by named manual rows under FR-032, not by `check_project.py`. **Amended 2026-09-08**: FR-007's *negative* is the one exception. Because a stored verdict would be a **key on disk**, its absence is checkable, and `check_sources()` now refuses `fit`, `assessed`, `goal_fit`, `discovered` and `proposed_by` on an entry (cases A5/A6). Everything else in piece A — what a run *says* — remains manual rows.
- Q: Does an off-goal source get registered anyway, or does the run pause to ask the user to confirm before writing the entry? (FR-002) → A: Registered anyway, with the warning shown. Advisory always writes; there is no interactive gate in `/sources`. The warning names the source id and the conflicting goal line per FR-003. Rationale: nothing else in this pipeline blocks on a model's judgement — `/catalog` marks `Status: out of scope` and carries on — and constitution VII means this repo has no standing to withhold the user's own material from their own register.
- Q: Is source discovery a new eighth pipeline step, or does it fold into an existing one? (FR-016, FR-028) → A: There is no new step. Discovery is a mode of `/sources`, and the pipeline stays at **seven** steps. `/research-gaps` cannot do this job — it needs a catalog with `Status: gap` subtopics, so it cannot run for a user who has a goal and no sources, and it writes synthesised prose into `knowledge/` rather than handing back URLs. But `/sources` already owns `sources.yaml`, discovery's entire output is proposed `sources.yaml` entries, and piece A is putting `goal.md` reading into `/sources` anyway. Both halves of this feature live in one skill. Accepted cost: `/sources` reaches the network for the first time.
- Q: Is `type: web` with `depth: 1` enough for a paginated archive, or does `/ingest` need to follow pagination? (FR-029) → A: `depth: 1` is enough, and the skill says so. No `/ingest` pagination work and no change to `depth:`. At registration `/sources` states plainly that the fetch reaches the index page plus the linked posts on the same domain, capped at 20 by `skills/ingest/SKILL.md` today, so the user knows a ten-year archive is not fully ingested. Verified by a named row in `docs/testing.md` under FR-032.

### Session 2026-09-07 (round 2)

- Q: Is discovery entered **only** when the user explicitly asks for it, or may an ordinary run propose it — and may the later pipeline steps point at it? (FR-016, FR-030, FR-032, and the new FR-035 – FR-038) → A: **Explicit argument only, and no pointer at all.** Discovery runs only when the user asks for it at invocation; the exact syntax is a planning decision, so the requirement states the trigger and not the spelling. An ordinary `/sources` run — registering a named source, listing the register, removing a source — neither enters discovery nor mentions it, and `/ingest`, `/catalog`, `/cards` and `/print` neither enter it nor mention it, `/catalog`'s FR-014 report included: it may say a required topic is covered only by experience reports, but it may not turn that into a suggestion to go looking. Rationale: the user's actual concern is that a deck built from their own material contains nothing they did not choose — the property `/research-gaps` was built to protect — and a discovery prompt that appears on its own erodes it one nudge at a time; FR-006 already caps the `/learning-goal` pointer for the same reason, and discovery gets no allowance at all. Consequence: FR-016 no longer says `/sources` "offers" discovery, four requirements are added (FR-035 – FR-038, the last of them the whole-pipeline guarantee stated plainly in its own right), FR-030 gains the explicit-request rule as a `check_docs.py` obligation, and FR-032 gains the matching named rows in `docs/testing.md`. **Accepted cost, recorded deliberately**: a user who does not know discovery exists will find it only through the documentation — there is no hint anywhere in a run. That is the trade the user chose.

### Session 2026-09-08 (round 3)

- Q: Is the discovery contract of piece C a **practitioner-material** contract, or a **material-class-neutral** one that practitioner material is merely the first addendum on? (FR-016 – FR-027, and the new FR-039) → A: **Material-class neutral, with practitioner material as the first and — in this feature — the only addendum.** Piece C is split in two. **C1** is the discovery contract: everything that holds for *any* kind of source (FR-016, FR-017, FR-018, FR-020 – FR-027, FR-039). **C2** is the addenda: what a *particular* class of material additionally requires of its credibility sentence, on top of C1. FR-019 is the practitioner-material addendum and is the only addendum this feature ships. Rationale: issue #44 conflated a **material class** with a **general mechanism**. Issue #43 ("Public research sources: arXiv and friends") names the identical gap for research literature — *"No search. You cannot say 'the twenty most cited papers on X' — you have to know the URL first. `/research-gaps` searches, but it is driven by catalog gaps and it synthesises."* Review of piece C found it already almost neutral: FR-017, FR-018, FR-020 – FR-027 never mention practitioner material, and FR-023's refusal to propose paywalled or login-gated material is the same rule as #43's own restriction to openly accessible sources. **FR-019 was the only practitioner-specific requirement in the group.** Consequences: the group is regrouped, not renumbered — every FR keeps its number and, apart from one added cross-reference sentence on FR-018, its text; FR-039 is added to make the neutrality an obligation rather than an accident; `check_docs.py` asserts the neutral contract and the practitioner addendum as **separable** checks, so a later addendum is an addition and not an edit to the neutral checks. **Explicitly NOT pulled in**: no arXiv, OpenAlex, Crossref or other source-specific search backend; no new source type; no bibliographic identity (DOI, authors, year, venue, citation count) in any frontmatter; no frontmatter key beyond the `nature:` of round 1; and **no second addendum**. Neutrality is a shape, not a promise of research-literature support — that work stays with issue #43.

### Session 2026-09-08 (round 4)

- Q: Round 3 named the C2 mechanism with a piece of contract jargon that is not self-explanatory. Is there a term a reader meets once and understands? (the C2 group, FR-019, FR-039, SC-016, the Key Entities entry, the US4 scenarios) → A: **Rename it to "material-class addendum"** — adjective form *"the practitioner-material addendum"*. **Editorial only: no meaning changes and no requirement changes shape.** Every occurrence in the spec, the plan, `contracts/discovery-proposal.md`, `data-model.md`, `quickstart.md` and `checklists/requirements.md` is rewritten, including the C2 group heading and the check-function name the plan proposes, now `check_sources_skill_carries_the_practitioner_addendum()`. "Addendum" says what the thing is — something added to a contract for one case — where the term it replaces sent a reader to a dictionary. Consequence: nothing to verify beyond the rename being complete; no FR gains or loses an obligation.
- Q: Should discovery be configurable as to **which classes of material it searches** — only practitioner reports and post-mortems, only research literature, magazine articles as well? (FR-017 and the new FR-040) → A: **Do not specify the filter now; put the hook in place now.** The expectation is reasonable but it is a **second axis** the spec did not cover: an addendum governs how the credibility sentence reads for a class, it does not decide what discovery searches. Today discovery searches whatever serves the goal, and the addendum fires only if a find happens to be practitioner material. Two changes follow. **FR-017 gains one field**: every candidate MUST name **which class of material it is** — an experience report, research literature, a reference work, a standards document, a public dataset, a magazine or trade article. It costs nothing, because the class is *already* being determined — otherwise the C2 addendum could not know whether to fire — and it makes FR-027's grouping legible. It is **not a closed, validated vocabulary**: it is prompt-level run output, not a key on disk, and it is **not** the `nature:` key of FR-015, which is a closed marker `/ingest` writes on a stored document at a different layer. **FR-040 is added** to record the filter as a deliberate, named future extension whose hook is already in place: selecting classes is out of scope here, FR-017's per-candidate class is what a later filter attaches to, and such a filter MUST be addable without reopening any C1 requirement — the same shape obligation FR-039 states for addenda. **Explicitly NOT pulled in**: no filter behaviour, no class-selection argument, no class vocabulary or validation of any kind, no second addendum, no new source type, no new frontmatter key, and nothing of issue #43. Consequences: FR-017 extended, FR-040 added (numbering continues from FR-039; the withdrawn FR-028 is **not** reused), US4 scenario 13, SC-017, the *Candidate source* and *Material-class addendum* key entities reworded, two edge cases, one Assumptions bullet, one Format Contracts row stating the class is deliberately **not** a format, and the #43 seam note extended to say that #43 inherits **both** the neutral C1 contract and the per-candidate class hook.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A source is judged against the goal before it is taken in (Priority: P1)

The user has run `/learning-goal` and has a `goal.md`. They type `/sources https://blog.example-corp.com/tag/post-mortem/`. Before showing the updated register, the run says what it expects this source to contribute — naming the required topic or area of the goal it would serve — or warns that it fits nothing the goal asks for and names the goal line it conflicts with. The entry is written either way.

**Why this priority**: the smallest piece, useful without the other two, and it touches everyone who registers a source. It is also the piece that gives B and C something to reason from.

**Independent Test**: run `/sources <url>` against a copy of the demo project (which has a `goal.md`) and read the run output. A manual-checklist row in `docs/testing.md` states the expectation; the `check_docs.py` red artifact is that `skills/sources/SKILL.md` names `goal.md`, states the assessment, and states that it is advisory. How the demo project's single `kind`/`depth` pair exercises both the weigh-up and the weigh-down case is a planning problem — see Assumptions.

**Acceptance Scenarios**:

1. **Given** a project with a `goal.md` whose `## Required topics` include a topic the source plainly serves, **When** the user runs `/sources <url>`, **Then** the run states what it expects the source to contribute and names at least one required topic or area from `goal.md`, and `sources.yaml` gains the entry.
2. **Given** a project whose `goal.md` says `kind: exam` and `depth: awareness`, **When** the user registers an incident post-mortem, **Then** the run warns that the material is likely off-goal, **names the source id** and **names the goal line it conflicts with** — the required topic, the `## Out of scope` entry, or the `kind`/`depth` pair — and the entry is still written, with no prompt asking the user to confirm first.
3. **Given** the same registration, **When** the user reads the warning, **Then** it says nothing about whether the subject or the source is worth anything in general; it speaks only about this goal (constitution VII).
4. **Given** a project with `goal.md`, **When** the user runs `/sources` with no arguments to list the register, **Then** no source is re-assessed — the assessment happens at registration, not on every listing.
5. **Given** a source whose `note` or URL matches an `## Out of scope` line of `goal.md`, **When** it is registered, **Then** the warning quotes that out-of-scope line specifically.
6. **Given** any registration, **When** the run finishes, **Then** `sources.yaml` carries no verdict — the entry has exactly the keys its type has today, and the assessment exists only in the run.
7. **Given** a `type: web` source pointing at a paginated archive index, **When** it is registered, **Then** the run states that the fetch will reach the index page plus the linked posts on the same domain, capped at 20, so the user knows the whole archive is not ingested.
8. **Given** a project with a `goal.md`, **When** the user registers a source they named, **Then** the run states the assessment and says **nothing** about discovery — no candidate, no proposal, no closing line offering to go looking for more material.

---

### User Story 2 - A project with no goal keeps the pipeline it had (Priority: P2)

The user has never run `/learning-goal`. They type `/sources ~/Documents/notes`. Nothing about the run is different from today: no assessment, no verdict, no new key on the entry.

**Why this priority**: constitution Principle I — an absent optional artifact means the behaviour the repo had before that artifact existed. Without this the optional pair stops being optional, and it is cheap to get wrong by adding "a small nudge" per source.

**Independent Test**: run `/sources <path>` in a project with no `goal.md` and diff the written entry against what today's `/sources` writes. Same keys, same shape. Then run the pipeline through to `/cards` and diff `sources.yaml` against the sources the user named — it must be identical (FR-038). Manual-checklist rows record both run-output expectations.

**Acceptance Scenarios**:

1. **Given** a project with no `goal.md`, **When** the user registers any source, **Then** the run emits **no** goal-fit assessment and **no** off-goal warning.
2. **Given** the same project, **When** the entry is written, **Then** it carries exactly the keys the source type carries today — nothing this feature introduces.
3. **Given** the same project, **When** the run finishes, **Then** at most **one** line per run may point at `/learning-goal`, never one line per source, matching the single advisory line `/catalog` already emits without a goal.
4. **Given** that project, **When** `python3 scripts/check_project.py <project> --strict` runs, **Then** it exits 0 and reports nothing new.
5. **Given** a project whose `knowledge/` documents carry no `nature:` key at all, **When** `check_project.py` runs, **Then** it exits 0 — the marker is optional and its absence is not a finding.
6. **Given** that project, **When** the user runs the whole pipeline (`/sources` register → `/ingest` → `/catalog` → `/cards`) without ever asking for discovery, **Then** `sources.yaml` holds exactly the sources the user named and nothing else, nothing was searched for, and no step mentioned discovery.

---

### User Story 3 - An incident report is carded as an experience report, not as a rule (Priority: P3)

The user has ingested a company post-mortem. `/ingest` marks the stored document `nature: experience`. `/catalog` places it, and `/cards` writes cards from it. The cards are about **that incident**: they name the case they come from, and none of them states an unattributed general rule that only one company's outage supports.

**Why this priority**: this is the failure that produces confidently wrong cards, and no current check catches it. It depends on A only for context, not mechanically, but it is worth less than A because a user with no practitioner material never meets it.

**Independent Test**: extend the demo project with one experience-report document, run `/cards` over the subtopic it produced, and read the cards. The red artifacts are twofold: `check_docs.py` asserts that `skills/ingest/SKILL.md`, `skills/catalog/SKILL.md` and `skills/cards/SKILL.md` carry the experience-report rule, and `check_project.py` asserts the `nature:` key by name and allowed value.

**Acceptance Scenarios**:

1. **Given** a document `/ingest` judges to be an experience report, **When** it is written to `knowledge/<id>/<doc>.md`, **Then** its frontmatter carries `nature: experience`, and a document that is not an experience report carries no `nature:` key at all.
2. **Given** a `knowledge/` document whose frontmatter carries `nature: something-else`, **When** `python3 scripts/check_project.py <project> --strict` runs, **Then** it reports the value as not one of the allowed values and names the document.
3. **Given** a subtopic whose only references are experience reports, **When** `/cards` writes cards for it, **Then** every card that states a fact taken from the report is phrased about the reported case and names it (the existing optional `source:` key is where the attribution goes), and none is phrased as a general rule.
4. **Given** a card whose fact depends on the scale or the context of the case ("across ten thousand servers"), **When** the card is written, **Then** the card carries that context rather than dropping it and leaving a sentence that reads as universal.
5. **Given** a subtopic that rests **only** on published incident reports, **When** `/catalog` **or** `/cards` reports on it, **Then** that run warns about the material base in its own words, carrying all four of FR-013's contents — which subtopic and what it rests on, why that base is skewed written out rather than named, what it means for the cards, and what would balance it — so a reader who has never met the term knows what the deck cannot cover; and the warning blocks nothing.
6. **Given** a required topic the goal wants as a general rule, and only experience reports covering it, **When** `/catalog` runs, **Then** it says so rather than quietly presenting single-case coverage as coverage of the rule.

---

### User Story 4 - `/sources` proposes sources and writes nothing (Priority: P4)

The user has a `goal.md` and no material. They ask `/sources` to find some. It comes back with a handful of candidates, each with what it is, which class of material it is, why it would serve *this* goal, a sentence saying what the source is and what it is not, and a ready-to-register entry. Nothing has been written. The user picks two; those two get registered through the ordinary `/sources` path, which then assesses them exactly as User Story 1 describes.

The contract this story tells is **material-class neutral** (C1): a candidate is a candidate whatever kind of source it is. Practitioner material adds one thing — what its credibility sentence must name — and it adds it as an **addendum** (C2, FR-019), which is the only addendum this feature ships.

Every candidate says **which class of material it is** (FR-017), in the run and in the run only. What the user cannot do here is **choose which classes discovery searches**: that is a second axis — an addendum says how a credibility sentence reads for a class, it does not decide what discovery goes looking for — and it is deliberately deferred (FR-040). Today discovery searches whatever serves the goal; the class each candidate names is the hook a later filter would attach to.

**Why this priority**: the largest piece and the one that reaches the network. It is worth having only once A exists, because the assessment is what turns a proposal into a decision.

**Independent Test**: run the discovery mode in a copy of the demo project, decline everything, and confirm `sources.yaml`, `knowledge/` and `catalog/` are unchanged. Then accept one and confirm the written entry passes `python3 scripts/check_project.py --strict`. Then run `/sources` **without** asking for discovery and confirm the run neither searches nor mentions it. Manual-checklist rows record the proposal shape and the silence of the ordinary run; the `check_docs.py` red artifact is that `skills/sources/SKILL.md` carries the discovery contract — the explicit-request rule, the "writes nothing until the user picks" rule, the "never invent" rule, the candidate shape including the class of material each candidate names, no claim to write into `knowledge/`, and the seam against `/research-gaps` — asserted as the **neutral** C1 check, with the **practitioner addendum** (FR-019) asserted by a *separate* check, so a later addendum is an addition rather than an edit (FR-039).

**Acceptance Scenarios**:

1. **Given** a project with a `goal.md`, **When** discovery runs, **Then** each candidate is presented with a name, a location, the required topic or area of `goal.md` it would serve, a credibility sentence, and a source entry whose `type` is one of the registered types and whose `id` is kebab-case.
2. **Given** the same run, **When** the user picks nothing, **Then** `sources.yaml`, `knowledge/` and `catalog/` are unchanged — no entry, no document, no catalog edit.
3. **Given** the same run, **When** the user picks candidates, **Then** exactly those entries are written and every one of them validates under `check_project.py`: known type, kebab-case unique id, the required field for its type present.
4. **Given** a candidate the run could not actually retrieve, **When** it reports, **Then** that candidate is **not** proposed — a URL it did not see is not a candidate, which is `/research-gaps`'s "Never invent" rule unchanged.
5. **Given** a candidate that turns out to be paywalled or behind a login, **When** it is found, **Then** it is reported as such and not proposed, and no credentials are ever typed.
6. **Given** a source already in `sources.yaml`, **When** discovery runs, **Then** it is not proposed again.
7. **Given** a project with **no** `goal.md`, **When** discovery is asked for, **Then** it says it has nothing to search for, points at `/learning-goal`, and writes nothing.
8. **Given** an ordinary `/sources <path-or-url>` registration or a bare `/sources` listing, **When** it runs, **Then** nothing is searched and no network request is made on behalf of discovery — the network is reached only when discovery is asked for.
9. **Given** any `/sources` invocation that does not explicitly ask for discovery — a registration, a bare listing, a removal — **When** it runs, **Then** discovery is neither entered nor mentioned: no candidate, no proposal, and no follow-up question offering to look for sources.
10. **Given** a `/catalog` run that reports a required topic covered only by experience reports (FR-014), or any `/ingest`, `/cards` or `/print` run, **When** it reports, **Then** it neither enters discovery nor suggests running it.
11. **Given** a user who registered their own sources and built cards from them without ever asking for discovery, **When** they read `sources.yaml` afterwards, **Then** every entry is one they named — the only way an entry they did not name reaches the register is a discovery run they asked for and a candidate they picked.
12. **Given** a candidate that is **not** practitioner material — a public dataset, a standards document, a reference work — **When** it is proposed, **Then** it carries every C1 field (name, location, **which class of material it is**, what it serves, one credibility sentence, a registerable entry — the six of FR-017, the class included, because scenario 13 holds for it too) and the practitioner addendum's two properties are **not** demanded of its sentence: the contract is the same for every class of material, and an addendum applies only to its own class.
13. **Given** a discovery run that returns a mixture of material — a company post-mortem, a public dataset and a standards document — **When** the candidates are presented, **Then** **every** one of them names which class of material it is, the non-practitioner ones included, and that class is a phrase in the run output rather than a value from a closed list: no candidate is dropped, renamed or refused for naming a class no list contains, and nothing about the class is written to disk.

---

### User Story 5 - Discovery with no network fails clean (Priority: P5)

The user asks `/sources` to find material while on a train. It says the network is not reachable, writes nothing, and exits cleanly.

**Why this priority**: it is one paragraph of prompt, it is the difference between a degraded path and a broken one, and `/research-gaps` already establishes the pattern.

**Independent Test**: run discovery with the network unavailable and confirm no traceback, no file written, and a report naming what it could not do. A manual-checklist row, next to the existing `9d` row for `/research-gaps`.

**Acceptance Scenarios**:

1. **Given** no network, **When** discovery runs, **Then** it reports that it could not search, writes nothing, and exits cleanly — a degraded path, not a failure.
2. **Given** no network, **When** it reports, **Then** it points at the ordinary registration path for material the user already has.
3. **Given** no network, **When** the user instead registers a source they named, **Then** that path is unaffected — `/sources` registers a URL without fetching it today and continues to.

---

### User Story 6 - The documentation describes what `/sources` now does (Priority: P6)

A reader of the README, the landing page, `docs/workflow.md` or the skills themselves sees a `/sources` that both registers what the user names and proposes what the user does not have, sees where the network is reached, and sees the seam between discovery and `/research-gaps`.

**Why this priority**: it costs nothing to state and is easy to leave half-done — and one of the sentences involved is already wrong today.

**Independent Test**: `python3 scripts/check_docs.py` exits 0, and every place that describes `/sources` describes both of its jobs.

**Acceptance Scenarios**:

1. **Given** this feature ships, **When** the pipeline is described anywhere, **Then** it is still **seven** steps in the same order with the same two marked optional. `assets/brand/common.typ`, the three rendered PNGs, the README banner alt text, **the seven-step description in `docs/workflow.md`**, `docs/index.html`, `CLAUDE.md` and the constitution's Identity section are **not** touched by this feature. *(The file `docs/workflow.md` **is** edited — Step 1 gains an ordering sentence, Step 2 names both jobs of `/sources`, Step 5 states the seam — which is what scenario 2 and scenario 3 ask for. What may not move is the step count and the order, not the file. This wording was corrected on 2026-09-08: as first written, scenario 1 named the whole file and contradicted scenario 2.)*
2. **Given** this feature ships, **When** `/sources` is described in the README, `docs/workflow.md` and its own `SKILL.md`, **Then** the description names both jobs: registering the material the user names, and proposing material for the goal.
3. **Given** this feature ships, **When** discovery is described next to `/research-gaps`, **Then** the difference is stated: discovery proposes sources to read and synthesises nothing; `/research-gaps` synthesises documents into `knowledge/` to close a known catalog gap. Same network, different output.
4. **Given** discovery is mentioned in no run at all (FR-035 – FR-037), **When** the README, `docs/workflow.md` and `skills/sources/SKILL.md` describe `/sources`, **Then** they state that discovery is entered only when the user asks for it and how to ask — the documentation is the only place a user learns that it exists, which is the accepted cost of the explicit-request rule.
5. **Given** this feature ships, **When** `skills/research-gaps/SKILL.md:17` is read, **Then** its claim to be "the only step that reaches the network" is gone, because it is already inaccurate — `/ingest` fetches web pages with WebFetch (`skills/ingest/SKILL.md:69`) and Zotero collections over HTTP. What replaces it states the real distinction: `/research-gaps` and `/sources` discovery **go looking for material the user did not choose**; `/ingest` **fetches what the user named**.

---

### Edge Cases

- **No `goal.md`**: no assessment (US2), and discovery declines to run (US4 scenario 7). Both are the pre-goal behaviour Principle I requires.
- **A goal written after the sources**: a user who runs `/sources` first and `/learning-goal` second gets no assessment for the material they already registered, because FR-001 assesses at registration and FR-008 forbids re-assessing on a listing. This spec does not add a back-fill; see Assumptions.
- **No network**: discovery reports and exits clean (US5). Ordinary registration is unaffected — `/sources` registers a URL without fetching it today and continues to.
- **Missing optional tooling**: nothing new is required. Discovery uses the web access Claude Code already has; there is no path where the user installs anything.
- **A goal in one language, a candidate in another**: `goal.md` may be German while the source is English. Matching is by meaning, exactly as `/catalog` already matches ingested material to required topics — never by string.
- **A goal with areas nothing findable serves**: discovery says which areas it found nothing for rather than padding the list.
- **A source that is both**: material serving one required topic and squarely inside `## Out of scope` for another. The run says both rather than picking one.
- **A candidate whose class of material fits none of the usual names**: it names its own class in its own words. There is no vocabulary to fall outside of (FR-017), so nothing is dropped, renamed or refused over it, and nothing is validated.
- **A user who wants only one class of material searched** — only post-mortems, only research literature: not supported here, and no run pretends otherwise. Selecting classes is the second axis FR-040 defers; today discovery searches whatever serves the goal and each candidate says what class it is.
- **A user who never asks for discovery**: they never meet it. No step enters it and no step mentions it, so `sources.yaml` holds only what they named (FR-035 – FR-038). The cost is accepted: such a user learns that discovery exists only from the documentation.
- **Idempotence**: discovery run twice writes nothing either time. `/sources` run twice on the same source does not duplicate the entry and does not re-assess on a plain listing.
- **A paginated archive**: ten years of post-mortems behind a paginated index. Settled — `depth: 1` stands, the register names the archive, the fetch reaches the index page plus up to 20 linked posts on the same domain, and `/sources` says so at registration (FR-029).
- **A document that is partly an experience report**: `nature:` is a single value on the document, not a per-paragraph judgement. A document that is mostly a reference work with one anecdote is not marked; the marker is for material whose subject *is* the reported case.
- **Encoding and file names**: unchanged; the only new thing on disk is one optional frontmatter key.
- **Fresh install on each platform, Python floor, non-Latin card text, text that does not fit, hyphenation**: unaffected. Nothing printed changes.

## Requirements *(mandatory)*

### Functional Requirements

**A — the `/sources` skill judges a source against the goal**

- **FR-001**: When `goal.md` exists, the `sources` skill MUST read it before writing a new entry and state, in the run, what it expects that source to contribute to the goal — naming at least one required topic or area from `goal.md` — or warn that it serves none of them.
- **FR-002**: The assessment MUST be **advisory and never blocking**. An off-goal source is **registered anyway with the warning shown**: the entry is written to `sources.yaml` whatever the verdict, no verdict is a reason to refuse or to withhold registration, and the run MUST NOT pause to ask the user to confirm before writing. *(Clarified 2026-09-07, Q3.)*
- **FR-003**: An off-goal warning MUST name the source `id` **and** the line of `goal.md` it conflicts with — a required topic, an `## Out of scope` entry, or the `kind`/`depth` pair — never a bare "this looks off-goal".
- **FR-004**: The assessment MUST be expressed as a judgement about *this source for this goal*, never about the subject, the publisher or the source's worth in general (constitution VII).
- **FR-005**: The assessment MUST reason from `goal.md`'s `kind` and `depth` and say which of them it used: `depth: expert` and `kind: interview`/`meeting` weigh practitioner material up; `kind: exam` with `depth: awareness` weighs it down.
- **FR-006**: When `goal.md` is **absent**, the skill MUST emit no assessment and no warning, and MUST write an entry carrying exactly the keys that source type carries today. At most one line per run may point at `/learning-goal`; never one per source.
- **FR-007**: The assessment MUST be reported **in the run and nowhere else**. It MUST NOT be persisted: no `fit:` key, no other verdict field, no change to `sources.yaml` — a source entry after this feature has exactly the keys it has today. *(Clarified 2026-09-07, Q2. A stored verdict is derived state about a goal that moves underneath it: edit `goal.md` and every stored verdict is stale, with nothing to re-derive it because FR-008 forbids re-assessment on a listing. Issue #33's FR-002 objection, unchanged.)*
- **FR-008**: Listing the register (`/sources` with no arguments) MUST NOT re-assess registered sources. The assessment happens at registration.
- **FR-009**: The skill MUST NOT invent a claim about a source it has not looked at. Where it reasons only from the URL, the `note` and the type, it says so.

**B — `/ingest`, `/catalog` and `/cards` know an experience report when they see one**

- **FR-010**: The `catalog` and `cards` skills MUST treat an **experience report** — an incident post-mortem, a case study, an application scenario, a fuck-up report, a company or engineering blog post about something that happened — as evidence about a specific situation, not as a reference statement of a general rule.
- **FR-011**: A card whose evidence is an experience report MUST be phrased about the reported case and MUST name that case, and MUST NOT be phrased as an unattributed general rule. The existing optional `source:` key on the card is where the attribution goes.
- **FR-012**: When the fact depends on the scale or the circumstances of the case, the card MUST carry that context rather than dropping it.
- **FR-013**: When a subtopic rests **only** on incident reports and experience reports, **both `/catalog` and `/cards`** MUST warn, whenever either of them reports on that subtopic, about the material base it stands on. What this requirement fixes is **what the warning carries**, not how it is worded: no phrase is prescribed, the run writes it in its own words, and a run that says only *"published incidents are a selected sample"* does **not** satisfy it — that is the jargon of a field the reader may never have met, and this warning exists for exactly the reader who has not. Four contents are required, and a warning missing any one of them is incomplete:

  1. **Which subtopic, and what it rests on** — the subtopic named; its material named as incident and experience reports only, with either the count of them or the documents themselves named; and the fact that nothing covering the topic *in general* is among them.
  2. **Why that material base is skewed**, written out rather than named: reports like these are published only by the parties who came through the incident and had an account they were willing to show. Those who failed at it publish nothing, so that kind of case is missing from any collection of incident reports — and it stays missing however large the collection grows.
  3. **What that means for the cards** drawn from it: they show how a *survived* failure unfolded, not what it takes to fail for good.
  4. **What would balance it** — a general account or a reference work on the topic.

  The warning is **advisory and never blocking**: it is a statement about the state of the sources, never an error, never a reason to refuse or withhold a card, a subtopic or a source, and never a suggestion to run discovery (FR-037). *(Run output — Principle XI's carve-out; named on the manual checklist as row `9f` for `/catalog` and row `12-iv` for `/cards`. Rewritten 2026-09-08 from a single prescribed phrase to these four contents: the phrase was jargon, and it failed to reach the reader the warning is for. The obligation is unchanged in force — advisory, run-output-only — and larger in content.)*

  **A conforming warning**, on the demo project's own material (`tests/fixtures/demo-project/`) — one message, four contents, no term of art anywhere in it:

  > *Signal failures in Torvig* rests on two documents and both are incident write-ups: the harbour office's account of the night the Torvig mast went dark, and the Fenmouth tide office's account of the Ovray Cove grounding. Nothing here describes the flag code in general.
  >
  > Write-ups like these get published by the harbours that came through the incident and had an account they were willing to show. A harbour that handled it badly, or lost a boat, writes nothing — so those cases are not in this material, and they would still be missing if it held fifty write-ups instead of two.
  >
  > The cards from this subtopic therefore show how a signal failure that was *survived* unfolded. They do not show what it takes for one to end badly.
  >
  > A general account of the flag code — the harbour handbook's chapter on it, or the tide office's standing instructions — would balance it.

  This example is written **once**, here. `data-model.md` § 5 and `contracts/knowledge-frontmatter.md` point at it rather than restating it.
- **FR-014**: When a required topic wants a general rule and only experience reports cover it, `/catalog` MUST report that rather than presenting single-case coverage as coverage of the rule.
- **FR-015**: `/ingest` MUST record the recognition on disk: a document it judges to be an experience report is written with `nature: experience` in its `knowledge/<source-id>/<document>.md` frontmatter, and a document that is not one carries **no** `nature:` key. `nature:` is a **closed vocabulary** — `experience` is its only value today — and it is **optional and additive**, so every project on disk validates unchanged and `/catalog` and `/cards` may act on it without re-judging every document on every run. *(Clarified 2026-09-07, Q1. This is the change to the third format contract in Principle I; it touches `skills/ingest`, `skills/catalog`, `skills/cards`, `scripts/check_project.py` and the demo project.)*

**C1 — the discovery mode of `/sources`: the discovery contract (material-class neutral)**

*Every requirement in C1 holds for **any** kind of source — a practitioner blog, a public dataset, a standards document, research literature. None of them may be written in terms of one class of material. What a particular class needs on top of this contract is an **addendum** under C2. (Split in round 3; the requirements are regrouped, not renumbered.)*

- **FR-016**: `/sources` MUST have a **discovery mode** — entered only when the user explicitly asks for it (FR-035), never offered by the skill itself — that proposes candidate sources for the stated goal and writes **nothing** — not to `sources.yaml`, not to `knowledge/`, not to `catalog/` — until the user picks. It is a mode of the existing skill, **not a new pipeline step**: the pipeline remains seven steps. *(Clarified 2026-09-07, Q4; its entry condition settled in round 2 — see FR-035.)*
- **FR-017**: Each candidate MUST be presented with: what it is and where it lives; **which class of material it is** — an experience report, research literature, a reference work, a standards document, a public dataset, a magazine or trade article, or whatever else it turns out to be; the required topic or area of `goal.md` it would serve; a credibility sentence; and a source entry ready to register whose `type` is one of the registered source types and whose `id` matches the kebab-case id contract. Naming the class costs nothing, because the class is **already being determined**: without it the material-class addendum of C2 could not know whether to fire, so saying it out loud only writes down a judgement the run has already made — and it makes FR-027's grouping legible, because a reader can see what kind of material each goal area is being served by. The class list is **not a closed, validated vocabulary**: it is a phrase in run output, not a key on disk. Nothing validates it, no check enumerates it, and a candidate that fits none of the examples above names its own class in its own words. It is **not** the `nature:` key of FR-015, which is a different thing at a different layer — `nature:` is a closed, validated marker `/ingest` writes into a stored document's frontmatter *after* the source has been registered and fetched, whereas this is prose about a source that has not been registered at all. *(Class field added 2026-09-08, round 4.)*
- **FR-018**: Credibility MUST be stated as **a sentence naming what the source is and what it is not** — never a score, a rating, a percentage, a star count or any other invented number (issue #33 rejected invented numerators, and the objection applies unchanged). This requirement fixes the **form** of the sentence for every class of material; what a *particular* class must additionally name in it is an addendum under C2 and MUST NOT be written into this requirement. *(Cross-reference added in round 3; the rule itself is unchanged.)*
- **FR-020**: When the user picks, the chosen entries MUST be registered through the ordinary `/sources` registration path, so the goal-fit assessment of FR-001 applies to them exactly as it does to a source the user named.
- **FR-021**: Discovery MUST NOT propose a candidate it did not retrieve. A URL it has not seen is not a candidate — `/research-gaps`'s "Never invent" rule, unchanged.
- **FR-022**: Discovery MUST NOT synthesise documents into `knowledge/` and MUST NOT create a `type: research` entry. It proposes sources to read; `/research-gaps` synthesises documents to close a known catalog gap. Same network, different output. Both `skills/sources/SKILL.md` and the docs MUST state that seam.
- **FR-023**: Discovery MUST NOT propose paywalled or login-gated material, MUST say so when it finds some, and MUST never enter credentials — the same rule `/ingest` already holds. *(Round 3: this is also issue #43's restriction to openly accessible sources, stated once for every class of material rather than twice.)*
- **FR-024**: Discovery MUST NOT propose a source already present in `sources.yaml`.
- **FR-025**: With **no `goal.md`**, discovery MUST say it has nothing to search for, point at `/learning-goal`, and write nothing.
- **FR-026**: With **no network**, discovery MUST report that it could not search, write nothing, and exit cleanly, pointing at the ordinary registration path for material the user already has.
- **FR-027**: Discovery MUST report how many candidates it found and how many it is showing, and MUST group them by the required topic or area they serve, so a goal with an area nothing serves is visible as such.
- **FR-028**: **Withdrawn (2026-09-07, clarification Q4.)** This requirement constrained the name of a new pipeline step ("must not collide with a skill the plugin may ship next to, must not read as a synonym of `/research-gaps`"). There is no new step and no new name: discovery is a mode of `/sources`, which is already named and already shipped. The number is retired rather than reused, so no requirement is renumbered.
- **FR-039** *(the neutrality obligation)*: The discovery contract of C1 MUST NOT be written in terms of one class of material. Neither `skills/sources/SKILL.md` nor the documentation may state a C1 rule as a rule about practitioner material — or about research literature, or about any other class. A further class of material MUST be addable by **attaching an addendum under C2**, without reopening, rewording or re-scoping any C1 requirement. `scripts/check_docs.py` MUST assert the neutral contract and each addendum as **separate** checks, so adding an addendum never edits a neutral check. *(Added 2026-09-08, round 3. This is a requirement about shape, not about coverage: it does not promise support for any class of material other than the one addendum C2 ships.)*
- **FR-040** *(the class filter — deliberately deferred, with its hook in place)*: Choosing **which classes of material discovery searches** — only experience reports and post-mortems, only research literature, magazine and trade articles as well — is **out of scope for this feature and is not specified here**. Discovery searches whatever serves the goal, exactly as C1 describes, and the addendum of C2 fires only when a find happens to belong to its class. This feature therefore ships **no filter, no class-selection argument and no class vocabulary**. What it ships instead is the **hook**: the per-candidate class of FR-017 is the field a later filter selects on, so a filter MUST be addable by building on that field, without reopening, rewording or re-scoping any C1 requirement — the same shape obligation FR-039 states for addenda, applied to this second axis. *(Added 2026-09-08, round 4. The two axes are different questions: an addendum governs **how a credibility sentence reads** for one class; a filter would govern **what discovery goes looking for**. Only the first is specified in this feature.)*

**C2 — material-class addenda**

*An addendum states what **one class** of source additionally requires of its credibility sentence, on top of C1. That is all an addendum may do: it adds to FR-018's sentence, and it never relaxes an exclusion, changes a cap, adds a field or touches an entry condition. **This feature ships exactly one addendum — the practitioner-material addendum below.** No other class of material is in scope here; see the issue #43 seam under Assumptions.*

- **FR-019** *(practitioner-material addendum)*: For **practitioner material** — an incident post-mortem, a case study, a fuck-up report, a company or engineering blog post about something that happened — the credibility sentence of FR-018 MUST additionally name the two properties the usual proxies miss: **(1)** that a company account of its own incident is a primary source and an interested one — nobody else has the timeline, and nobody has a stronger interest in how it reads; and **(2)** that material of this kind is published only by the parties who came through the incident, so the cases that ended badly are not among what can be found. As in FR-013, what is required is **what the sentence says**, not the words it says it in: the phrase *"a selected sample"* is neither required nor, standing alone, sufficient — the sentence has to state the thing rather than name it. The sentence stays **one** sentence (FR-018); saying property (2) plainly costs a clause, not a paragraph. *(Regrouped in round 3 as the one addendum of C2. Reworded 2026-09-08 to demand the content instead of the phrase; the rule itself — which candidates it applies to, and that a non-practitioner candidate is held to neither property — is unchanged.)*

**Fetching what was registered**

- **FR-029**: Registering a practitioner archive MUST be possible with the existing source types — this feature adds no sixth type — and `type: web` with `depth: 1` is sufficient. `/ingest` MUST NOT be changed to follow pagination and `depth:` MUST NOT change. Instead, at registration `/sources` MUST state plainly what the fetch will reach: the index page plus the posts on the same domain linked from it, capped at 20 by `skills/ingest/SKILL.md` today — so a user registering a ten-year archive knows it is not fully ingested. *(Clarified 2026-09-07, Q5.)*

**The gates**

- **FR-030**: `scripts/check_docs.py` MUST fail when `skills/sources/SKILL.md` stops naming `goal.md`, stops stating that the assessment is advisory, or loses its discovery contract — the "writes nothing until the user picks" rule, the "never invent" rule, the candidate shape of FR-017 including the class of material each candidate names, the refusal to write into `knowledge/`, the seam against `/research-gaps`, or the **explicit-request rule** of FR-035 and FR-036: that discovery is entered only when the user asks for it at invocation, and that a run which registers, lists or removes neither enters it nor mentions it. The **neutral contract (C1)** and each **material-class addendum (C2)** MUST be separate checks, and no C1 check may assert anything specific to a class of material (FR-039), so a later addendum is an added check and never an edit to a neutral one. It MUST also fail when `skills/ingest`, `skills/catalog` or `skills/cards` loses the experience-report rule. These are the test-first red artifacts for the prompt changes (constitution XI).
- **FR-031**: `scripts/check_project.py` MUST keep passing unchanged on every project on disk today, and MUST validate the `nature:` key introduced by FR-015 in `check_knowledge` — by name and by allowed value, the way `CONTENT_STATES` and `VISUAL_KINDS` are validated. An absent `nature:` key MUST NOT be a finding. There is no `fit:` key to validate (FR-007).
- **FR-032**: Every requirement above satisfied only by what a run *says* MUST appear as a named row in the manual checklist in `docs/testing.md`, referencing its FR number, because no automated gate can see it (constitution XI's run-output carve-out). This is the **whole** verification of piece A (FR-001 through FR-009) and of the run-output half of pieces B and C, and it explicitly includes the archive-reach statement of FR-029. It also explicitly includes the run-output half of piece D, as named rows: that an ordinary `/sources` registration and a bare `/sources` listing say nothing about discovery (FR-036); that a full `/sources` → `/ingest` → `/catalog` → `/cards` run neither enters discovery nor mentions it, `/catalog`'s FR-014 report included (FR-037); and that after such a run `sources.yaml` holds exactly the sources the user named (FR-038).

**The network**

- **FR-033**: `/sources` MUST reach the network **only** in discovery mode. Registering a source the user named and listing the register MUST make no network request, as today. The docs MUST state where the network is reached and why: `/ingest` already fetches web pages and Zotero collections, so the distinction that matters is **going looking for material the user did not choose** (discovery, `/research-gaps`) versus **fetching what the user named** (`/ingest`).
- **FR-034**: `skills/research-gaps/SKILL.md:17`'s claim that `/research-gaps` is "the only step that reaches the network" MUST be corrected as part of this feature's documentation work. It is already inaccurate — `skills/ingest/SKILL.md:69` fetches web pages with WebFetch, and the Zotero path reaches the API over HTTP — and this feature makes it more so. `check_docs.py` MUST fail if the stale claim reappears.

**D — discovery is entered only when the user asks for it**

- **FR-035**: Discovery MUST be entered **only on an explicit user request made at invocation**. It MUST NOT start by itself, MUST NOT be offered as a follow-up prompt at the end of an ordinary run, and MUST NOT be the default of any invocation. The exact invocation syntax is a planning decision; what this requirement fixes is that a user who does not ask for discovery never gets it. *(Clarified 2026-09-07, round 2.)*
- **FR-036**: An **ordinary `/sources` run** — registering a source the user named, listing the register, removing a source — MUST NOT enter discovery and MUST NOT mention it: no candidate, no proposal, no network request on discovery's behalf (FR-033), and no line suggesting that the user could go looking for material. The discovery mode of FR-016 exists, and FR-035's explicit request is the only way into it.
- **FR-037**: `/ingest`, `/catalog`, `/cards` and `/print` MUST NOT enter discovery and MUST NOT mention it. This holds in particular for FR-014: `/catalog` MUST report that a required topic is covered only by experience reports, and MUST NOT turn that report into a suggestion to run discovery. The same holds for FR-013's material-base warning, and for a `Status: gap` subtopic, whose one pointer stays `/research-gaps` exactly as today.
- **FR-038** *(the whole-pipeline guarantee)*: A user who registers their own sources and builds cards from them MUST see **no source they did not choose**. Across a whole pipeline run — `/sources` register, `/ingest`, `/catalog`, `/cards`, `/print`, with or without `goal.md` — the **only** path by which a source the user did not name enters `sources.yaml` is a discovery run the user explicitly asked for (FR-035) and in which the user picked that candidate (FR-016, FR-020). This is the same property `/research-gaps` was built to protect — the user can always tell their own material from what the model brought in — and this feature **preserves** it rather than weakening it.

### Questions carried from the issue — all resolved

All five are answered in *Clarifications*, session 2026-09-07. None was resolved silently.

| # | Question | Where | Answer |
|---|---|---|---|
| 1 | Does the assessment persist as `fit:` on the entry? | FR-007 | No — run output only |
| 2 | Is `type: web` with `depth: 1` enough for a paginated archive? | FR-029 | Yes, and the skill says what it reaches |
| 3 | Does an off-goal source get registered anyway? | FR-002 | Yes, with the warning shown, no gate |
| 4 | Does B need a `nature: experience` marker? | FR-015 | Yes, closed vocabulary, written by `/ingest` |
| 5 | Is discovery a new pipeline step? | FR-016, FR-028 | No — a mode of `/sources`; seven steps stand |

Which gate holds this feature's red artifact follows from 1 and 4: piece A is `check_docs.py` plus named manual rows, and part of piece B is assertable in `check_project.py`.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | **None.** No new source type — `web` already covers this material — and no `fit:` key (FR-007) | — |
| `knowledge/<id>/<doc>.md` frontmatter | **`nature:` — new, optional, additive, closed vocabulary** (`experience` today). Written by `/ingest`, read by `/catalog` and `/cards` (FR-015) | `skills/ingest`, `skills/catalog`, `skills/cards`, `scripts/check_project.py` (`check_knowledge`), the demo project, and wherever the knowledge frontmatter is documented |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | none — attribution uses the existing optional `source:` key | — |
| Bibliographic identity (DOI, authors, year, venue, citation count) | **None, deliberately.** Round 3's neutrality is about the *shape* of the discovery contract, not about new fields. These belong to issue #43 and are out of scope here | — |
| The class of material a candidate names (FR-017) | **None, deliberately.** It is a phrase in run output, not a key: not on a `sources.yaml` entry, not in the knowledge frontmatter, not a closed vocabulary anything validates — and **not** the `nature:` key of FR-015, which is a different marker at a different layer | — |

**Backwards compatibility**: yes, in both directions, with no exception. Every project on disk validates unchanged; a project with no `goal.md` sees no new behaviour at all; the one format change is an additive optional key that an older reader ignores and whose absence is never a finding. No migration step, and no re-ingest is required — documents ingested before this feature simply carry no `nature:` key.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

**None.** The clarification that discovery is a mode of `/sources` rather than an eighth step removes every design surface this feature previously touched.

- **Visible surfaces touched**: none. The pipeline stays at seven steps, so `assets/brand/common.typ`'s `commands` tuple and `optional-commands` are unchanged, the three rendered PNGs (`assets/banner.png`, `assets/pipeline.png`, `assets/social-card.png`) are unchanged, and the landing-page step strip in `docs/index.html` keeps its layout. The card and the press sheet were never in scope.
- **Black-only laser print still readable**: N/A — nothing printed changes.
- **Minimum type size respected**: N/A — no strip is re-laid out.
- **Brand PNGs need re-rendering**: **no.** `python3 scripts/render_brand.py` is not part of this feature's work.
- **Duplex alignment unaffected**: yes.

The prose changes that remain are descriptions of what `/sources` does (US6) and the correction in `skills/research-gaps/SKILL.md` (FR-034) — neither is a design surface, so `docs/design.md` is not a gate for this feature.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** No. Nothing new is parsed; the goal is read with the existing frontmatter helper and the register with `yamlio`.
- **New runtime dependency**: none.
- **New dev dependency**: none.
- **New external binary**: none. Discovery uses the web access Claude Code already has, exactly as `/research-gaps` does; there is no path where the user installs anything.
- **Anything this makes redundant**: none.
- **Engine version change**: no.
- **Platforms verified**: macOS and Linux directly; Windows by inspection, as today — nothing here is platform-specific.

### Key Entities *(include if the feature involves data)*

- **Goal-fit assessment**: what the pipeline expects one source to contribute to one stated goal, or why it expects nothing. Grounded in named lines of `goal.md` plus `kind` and `depth`. Advisory, never blocking. Lives **only** in the run output — it is never written to disk. Never a score.
- **Candidate source**: a source discovery found and did not register — a name, a location, **which class of material it is**, the required topic it would serve, a credibility sentence, and a registerable entry. The class is free prose in the run: not a validated value, not a key on disk, and not the `nature:` marker of FR-015. It is stated because the run has already determined it — an addendum could not otherwise know whether to fire — and because it makes FR-027's grouping legible. **The shape is the same for every class of material** (C1): nothing in it is specific to practitioner material, to research literature or to anything else, and no field of it selects what discovery searches (FR-040). It exists only inside a discovery run the user explicitly asked for — nothing else in the pipeline produces one — and it becomes a real source only when the user picks it.
- **Credibility sentence**: one sentence naming what a source is and what it is not. Deliberately not a number, not a rating, not a rank. Its **form** is neutral and fixed by FR-018; a **material-class addendum** (C2) may say what that sentence must additionally name for its own class, and the one addendum this feature ships is FR-019's, for practitioner material.
- **Material-class addendum**: the only place a class of source may add anything to the discovery contract — one addition to the credibility sentence, for that class alone, fired when a find happens to belong to that class. An addendum never relaxes an exclusion, changes a cap, adds a candidate field or changes an entry condition, and it never decides **what discovery searches**: that is the second axis FR-040 defers, not an addendum's business. One addendum exists today (practitioner material); the mechanism is what FR-039 keeps open.
- **Experience report**: material that reports what happened in one situation — an incident post-mortem, a case study, a fuck-up report, an engineering blog post about an outage. A primary source and an interested one; material that exists at all only because someone came through the incident and chose to write it up, so the cases that ended badly are missing from any collection of it; and valuable exactly where a reference work is thin. Marked on disk by `nature: experience` in the stored document's frontmatter.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a project with a `goal.md`, **every** newly registered source produces exactly one goal-fit statement in the run, and each one names either a required topic/area of `goal.md` or the `kind`/`depth` pair. Zero statements are bare verdicts.
- **SC-002**: **Every** off-goal warning names the source id and quotes the goal line it conflicts with. Zero warnings say only that something looks off-goal.
- **SC-003**: In a copy of the demo project with `goal.md` deleted, `/sources` produces **no** assessment line and writes an entry whose key set is identical to the one today's `/sources` writes; `python3 scripts/check_project.py <project> --strict` exits 0 and reports nothing new.
- **SC-004**: An off-goal source registered against advice is present in `sources.yaml` after the run, with **zero** confirmation prompts in between — the advisory path never loses the user's material and never gates it.
- **SC-005**: A discovery run in which the user picks nothing leaves `sources.yaml`, `knowledge/` and `catalog/` unchanged — zero files created, zero files modified.
- **SC-006**: **100 %** of entries written after a discovery run pass `python3 scripts/check_project.py <project> --strict`: known type, unique kebab-case id, the required field for the type present.
- **SC-007**: **Zero** candidates carry a score, rating, percentage or any other number standing in for credibility; **every** candidate carries one sentence saying what the source is and what it is not — and that holds for **every** class of material, because the requirement is C1's, not an addendum's. Of the candidates that are practitioner material, **every** one additionally names the two properties FR-019's addendum demands; of the candidates that are not, **zero** are held to them.
- **SC-008**: With the network unavailable, discovery exits cleanly with no traceback, writes nothing, and names what it could not do.
- **SC-009**: On a demo subtopic whose only reference is an experience report, **every** generated card names the case it came from, and **zero** cards state an unattributed general rule supported only by that one case.
- **SC-010**: `python3 scripts/check_docs.py` exits 0, and fails when `skills/sources/SKILL.md` drops `goal.md`, the advisory statement, the "writes nothing" rule, the "never invent" rule or the explicit-request rule (FR-035, FR-036); when `skills/ingest`, `skills/catalog` or `skills/cards` drops the experience-report rule; and when the "only step that reaches the network" claim reappears anywhere `check_docs.py` gates — `gated_files()`: root `*.md`, `docs/*.md`, `skills/*/SKILL.md`, `scripts/*.py` (except `check_docs.py` itself) and `templates/*.typ`. `tests/` and `specs/` are outside it, deliberately (research R5), so this feature's own artifacts may quote the stale claim in order to describe it.
- **SC-011**: The pipeline is described as **seven** steps, two optional, everywhere it is described — the count is unchanged by this feature, and the diff touches **zero** brand sources, **zero** rendered PNGs and **zero** step-count sentences. Every place that describes `/sources` names both of its jobs, and every place that describes discovery next to `/research-gaps` states the seam.
- **SC-012**: The four gates are green (`ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`), and every run-output requirement has a named row in `docs/testing.md` carrying its FR number.
- **SC-013**: `python3 scripts/check_project.py --strict` reports a `knowledge/` document whose `nature:` value is not in the allowed set, naming the document; exits 0 on a project whose documents carry no `nature:` key at all; and exits 0 on every project fixture that passes today.
- **SC-014**: A full pipeline run — `/sources` register → `/ingest` → `/catalog` → `/cards` — with **no** explicit discovery invocation makes **zero** network requests looking for new sources and adds **zero** entries to `sources.yaml` beyond the ones the user named; the register after the run holds exactly those sources and no others.
- **SC-015**: Across that same run, **zero** lines of output mention discovery, propose a candidate or suggest running it — `/catalog`'s FR-014 report that a required topic is covered only by experience reports included. Discovery appears in a run **only** when the user asked for it at invocation.
- **SC-016**: The neutral discovery contract (C1) and the practitioner addendum (C2, FR-019) are asserted by **separate** checks in `scripts/check_docs.py`: deleting the addendum from `skills/sources/SKILL.md` fails exactly one check and leaves the neutral checks green, and **zero** C1 checks name practitioner material, an incident, a post-mortem or a company blog in what they assert (FR-039).
- **SC-017**: **Every** candidate in a discovery run names which class of material it is — the practitioner ones and the non-practitioner ones alike — and **zero** candidates are dropped, renamed or refused for naming a class that appears on no list, because there is no list to appear on. The feature ships **zero** class-selection arguments, **zero** class filters and **zero** class vocabularies (FR-040), and nothing about a candidate's class reaches disk.

## Assumptions

- The user has Python 3.12+ and a working Claude Code install, as today. Discovery needs the network Claude Code already has; nothing is installed.
- **The three pieces are separable and A is worth shipping alone.** A ≈ 3 person-days at RICE ~13; the whole issue ≈ 12 person-days at RICE ~4.2. If planning has to cut, the cut runs A → B → C, in that order, and A leaves a coherent product. Folding C into `/sources` (clarification Q4) reduces C's cost — no new skill, no brand re-render, no constitution amendment — but does not change the order.
- **`web` is the type for this material.** A post-mortem is a URL; adding a sixth source type would be format surface with no consumer. What this feature adds is the judgement around the fetch.
- **FR-037 names four skills, and the other two are held differently — recorded rather than left to inference.** FR-037's silence rule binds `/ingest`, `/catalog`, `/cards` and `/print`. Two skills are outside that list and each for its own reason. `/learning-goal` is not named by FR-037 but is held by the **same automated gate**: it is one of the five files the `--discover` token check reads, because it is a skill whose wrap-up already points the user at another step and the token occurs nowhere in it. `/research-gaps` **cannot** be held by that gate: FR-034 requires it to state the seam against `/sources --discover`, so it must carry the token the gate forbids elsewhere. What holds `/research-gaps` instead is the named manual row that runs it (FR-032) together with the one-paragraph scope of the FR-034 correction. **The residual risk is stated and accepted**: a paraphrased pointer added inside `skills/research-gaps/SKILL.md` — *"or run `/sources --discover`"* at the end of a run with open gaps — would fail no automated gate, and only a run of the manual row would catch it. Round 2's rationale ("no pointer at all … one nudge at a time") applies to both skills; what differs is what can enforce it.
- **Discovery is optional in use, not in the pipeline.** It is a mode of `/sources` the user must explicitly ask for at invocation (FR-035). A user who arrives with their own list never triggers it and is never told in a run that it exists; `/sources` behaves exactly as it does today for them. The cost of that silence is accepted deliberately (round 2): the documentation is the only route to discovery.
- **`/sources` reaching the network is a real cost, accepted deliberately.** Until now the skill only wrote to a register. The honest framing is that `/ingest` already reaches the network too, so "which step touches the network" was never the clean line the docs claimed; the line worth preserving is *goes looking for material the user did not choose* versus *fetches what the user named* (FR-033, FR-034).
- **Goal fit is a judgement the model makes, and only its shape is assertable** (constitution XI, the carve-out feature 001 established). This spec asserts that the assessment exists, that it names a goal line and a source id, that it never blocks, and that a proposal validates as an entry — never that the judgement is any good. Whether it is good is what reading a printed card is for.
- **Piece A leaves nothing on disk**, so its red artifacts are `check_docs.py` checks plus named manual-checklist rows, not `check_project.py` checks. Planning must not quietly invent a file to make the work assertable. Piece B is the exception, by the deliberate decision in clarification Q1.
- **The demo project is extended, never duplicated** (constitution XI, VIII, VII): one invented experience report about the archipelago — a harbour-office incident write-up — placed under the existing `raw/web` site or as a new document under an existing source. No second corpus, and nothing quoted from anyone else's material.
- **Paywalled and login-gated material stays out of scope**, for the reason the Zotero path exists: if the user has it, they register it. `/ingest` already refuses to sign in and this feature does not soften that.
- **The assessment never judges a subject.** Constitution VII means this repo does not acquire an opinion about someone's field of study; the only question it may ask is whether a source serves the goal the user themselves wrote down.
- **Auto-registration is out of scope, and so is auto-discovery.** Discovery proposes and stops, and it does not start on its own (FR-035 – FR-038). That is what keeps the property `/research-gaps` had to work for: the user can always tell their own material from what the model brought in.
- **The discovery contract is neutral; the coverage is not.** Round 3 makes C1 material-class neutral *in shape*. It does **not** widen what this feature ships: exactly one addendum exists (FR-019, practitioner material), and a reader must not mistake the neutrality for a promise that research literature, datasets or standards are supported here. They are not. Adding a class is adding an addendum, and that is a later feature's work.
- **Which classes discovery searches is a second axis, and it is deliberately deferred with its hook in place** (round 4, FR-040). A reader may reasonably expect discovery to be configurable — *search only practitioner reports and post-mortems*, *only research literature*, *magazine articles too*. That is a different question from the one C1 and C2 answer: an addendum governs how a credibility sentence reads for a class, it does not decide what discovery goes looking for. This feature specifies **no** filter, **no** class-selection argument and **no** class vocabulary. It ships one thing towards it — every candidate names its class (FR-017), which is the field a later filter would select on. Planning must not read the hook as a licence to build the filter.
- **The seam to issue #43 ("Public research sources: arXiv and friends") — recorded, not scoped.** #43 names the same gap this feature's piece C closes, for a different class of material: *"No search. You cannot say 'the twenty most cited papers on X' — you have to know the URL first. `/research-gaps` searches, but it is driven by catalog gaps and it synthesises."*
  - **What this feature hands #43 for free** — two things, and #43 inherits both. First, the **neutral C1 contract** and FR-039's obligation to keep it neutral: #43 attaches a **research-literature addendum** under C2 — what a paper's credibility sentence must name — instead of building a second discovery path beside this one, and the caps, the grouping, the exclusions, the entry condition, the "writes nothing until the user picks" rule and the `/research-gaps` seam are already written once and hold for it unchanged. Second, the **per-candidate class hook** of FR-017: every candidate already says which class of material it is, so #43 can tell its own material apart from everything else without adding a field, and a later *class filter* — deferred by FR-040 and out of scope in both features — has the field it would select on already in place.
  - **What stays with #43 and is out of scope here**: **bibliographic identity** — DOI, authors, year, venue, citation count in the knowledge frontmatter — and any **source-specific search backend**, arXiv-API-aware, OpenAlex-aware or otherwise. This feature adds **no** arXiv work, **no** new source type, and **no** frontmatter field beyond the `nature:` key settled in round 1.
  - **No conflict is being stored up**: FR-023's refusal to propose paywalled or login-gated material and #43's restriction to openly accessible sources are the **same rule**. #43 inherits it from C1 rather than restating it, and Google Scholar — which #43 rejects for the terms-of-service and CAPTCHA reasons — is refused by that same rule plus FR-021's "never propose what you did not retrieve".
- **The constitution needs no amendment.** The seven-step Identity sentence stands, because no step is added.

### Open items deferred to planning

These surfaced during the clarification scan below its five-question quota. They are planning decisions, not open specification questions, and none of them blocks `/speckit-plan`.

1. **A goal written after the sources are registered.** FR-001 assesses at registration and FR-008 forbids re-assessing on a listing, so a user who runs `/sources` first and `/learning-goal` second never gets an assessment for material they already have. Neither this spec nor its requirements say whether that is intended. Plan must either accept it explicitly (with a line in `skills/learning-goal/SKILL.md` pointing the user at re-registering, or nothing at all) or scope a one-off back-fill — but it must not silently widen FR-008.
2. **Exercising FR-005's `kind`/`depth` weighting on one fixture.** The demo project's `goal.md` holds exactly one `kind`/`depth` pair, but US1's Independent Test needs one goal and US1 scenario 2 needs `kind: exam, depth: awareness` to demonstrate the weigh-down case. Constitution VII and XI forbid a second corpus, so plan must find a way — a temporary edit inside a manual-checklist row, a scratch copy made by `scripts/demo.py`, or a scenario stated against the single fixture. Not a second demo project.
3. **How many candidates discovery shows.** FR-027 requires found/shown counts but sets no cap on the shown list. What that cap is — a number, a per-area limit, or "whatever fits one screen" — is a plan-level decision, constrained only by FR-027's grouping requirement and by the rule that a goal area with nothing found is visible as such.
