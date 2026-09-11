# Tasks: Practitioner material, goal fit, and source discovery

**Branch**: `feat/goal-fit-sources` | **Feature dir**: `specs/011-goal-fit-sources/`

**Input**: [plan.md](plan.md) (the ordering authority), [spec.md](spec.md),
[data-model.md](data-model.md), [contracts/](contracts/),
[quickstart.md](quickstart.md), [research.md](research.md),
[checklists/gates.md](checklists/gates.md)

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every
check below is written and watched **failing on its assertion** before the
prompt, fixture or doc that satisfies it exists. The task that adds the check is
always a **separate, earlier** task than the one that makes it pass.

## Organization: waves, not user stories

This feature is organized by **plan.md's ten waves (G, A, B, C, D, E, F, H, I,
J)**, not by user-story priority. That ordering is not a stylistic choice: the
waves are sequenced so the **first commit is red against the shipped
repository** (wave G3), and re-sorting them by story priority would put a prompt
edit before the check it was supposed to fail against. Each task still carries
the user story it serves, so story-level traceability is intact.

Story map (from spec.md): **US1** goal fit at registration · **US2** a project
with no goal is unchanged · **US3** an incident is carded as an experience
report · **US4** discovery proposes and writes nothing · **US5** discovery with
no network · **US6** the documentation describes what `/sources` now does.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: can run in parallel — a **different file**, no dependency on an incomplete task
- **[Story]**: US1 – US6, on wave tasks only; Setup, Gates and By Hand carry none
- 🔴 marks a task whose output must be a **failing** assertion before the next task begins
- Every task names the exact file(s) it touches and the FR / plan wave it serves

Parallel groups are marked with `<!-- parallel-group: N (max 3 concurrent) -->`
and hold at most three genuinely file-disjoint tasks. Everything else is marked
`<!-- sequential -->`. **Most of this feature is sequential**, because it lands
in two Python files (`scripts/check_docs.py`, `scripts/check_project.py`), two
test modules and five `SKILL.md` files. No parallelism is manufactured.

## What "red" means for a prompt change

Constitution XI and `docs/testing.md` § *Write the test first* both define the
red artifact for the model-driven half as **"a check in `scripts/check_docs.py`
plus a case in `tests/test_check_docs.py` that fails against what the current
prompt produces."** The check function and its test cases are therefore **one**
task — writing the test without the function it calls produces an
`AttributeError`, which the constitution explicitly says does not count as red.
The task that **satisfies** the check (the prompt, fixture or doc edit) is always
the next, separate task. Each 🔴 task below states exactly which assertion goes
red and against what.

## Path conventions

Flat module layout, no `src/`. Implementation `scripts/<module>.py`; prompts
`skills/<name>/SKILL.md`; tests `tests/test_<module>.py`; the one shared corpus
`tests/fixtures/demo-project/`.

## Scope guards that apply to every task

- **No new file under `scripts/`** (constitution V). No new dependency, runtime
  or dev (constitution II–IV). If one turns out to be needed: **stop and flag
  back to plan.md**, do not `pip install`.
- **No `CLASSES` tuple, no class vocabulary, no class validation, no
  class-selection argument** anywhere (FR-040). If implementation finds itself
  writing one: **stop and flag**.
- **Not touched, deliberately**: `bin/lernkarten`, `templates/*.typ`,
  `assets/brand/*.typ`, the three rendered PNGs, `scripts/render_brand.py`,
  `scripts/build_pdf.py`, `scripts/demo.py`, `scripts/make_testdata.py`,
  `.specify/memory/constitution.md`, `CLAUDE.md`, `docs/design.md`,
  `docs/index.html`, `tests/test_landing_page.py`, `tests/test_repo_hygiene.py`.
- **The pipeline stays at seven steps.** No step-count sentence moves.
- Never `git add -f` `sources.yaml`, `knowledge/`, `catalog/`, non-example
  `cards/` or `output/` (constitution VII).

---

## Phase 1: Setup

**Purpose**: make the work verifiable, and record the "before" state.

<!-- sequential -->

- [ ] T001 `python3 -m pip install --user -r requirements-dev.txt` — pytest, ruff==0.16.2, pillow, pyyaml. **No package is added to this file by this feature.**

<!-- parallel-group: 1 (max 3 concurrent) -->

- [ ] T002 [P] `scripts/install-hooks.sh` — install the pre-commit (no user content) and pre-push (no direct `main`) hooks
- [ ] T003 [P] `python3 scripts/make_testdata.py` — build the binary test material under `tests/fixtures/demo-project/` so the suite can run

<!-- sequential -->

- [ ] T004 Record the baseline: run `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`, and `python3 scripts/check_project.py tests/fixtures/demo-project --strict`. **All five must be green on the clean worktree** — that is what makes T005's red meaningful.

**Checkpoint**: the repository is green and the tooling works.

---

## Phase 2 — Wave G: the stale network claim 🎯 the first red commit

**Serves**: FR-034, SC-010, US6 scenario 5 · **plan.md** § Test plan first, wave G

**Why first**: G3 is the only assertion in this feature that is **red against a
clean checkout today**, with nothing fabricated. `skills/research-gaps/SKILL.md:17`
says *"This is the only step that reaches the network"*, which is already false —
`skills/ingest/SKILL.md:69` fetches web pages with WebFetch and the Zotero path
reaches the API over HTTP.

<!-- sequential -->

- [ ] T005 🔴 [US6] Add `check_network_claim_is_not_exclusive()` to `scripts/check_docs.py` (paragraph-scoped over `gated_files()`, in the shape of `check_print_order()` at `:557-572`), wire one line into `main()` at `:575`, and add the wave-G cases to `tests/test_check_docs.py`:
  - **G1** — a doc claiming *"the only step that reaches the network"* is reported, and the message **names the file** (synthetic input via the `gated_project()` helper at `tests/test_check_docs.py:193`)
  - **G2** — *false-positive guard*: `CONTRIBUTING.md:82`'s *"even reaches the network:"* does **not** fire. The regex is scoped to the **exclusivity claim** (`only … that reaches the network`), never to the bare words (research.md § R5)
  - **G3** — *shipped-repo*: the check reports nothing over the real `gated_files()`

  **RED**: G3 fails, and `python3 scripts/check_docs.py` exits 1 naming `skills/research-gaps/SKILL.md`. G1 and G2 pass immediately — they are what proves the gate is scoped correctly.

  **Note for the implementer**: `markdown_files()` (`scripts/check_docs.py:168`) covers root `*.md`, `docs/*.md` and `skills/*/SKILL.md` only. `specs/**` is **outside** the gate, so the seventeen quotations of the stale claim in this feature's own spec/plan/research do **not** fire it, and `tests/test_deps.py:10` is outside `gated_files()` too. The one live false positive is `CONTRIBUTING.md:82`.

- [ ] T006 [US6] Rewrite `skills/research-gaps/SKILL.md:17-19` — delete the exclusivity claim and state the real distinction instead: `/research-gaps` (and `/sources --discover`) **go looking for material the user did not choose**; `/ingest` **fetches what the user named** (FR-033, FR-034). Do **not** delete the network sentence outright — FR-034 corrects the claim, it does not remove the paragraph.

  **GREEN**: G3 passes; `python3 scripts/check_docs.py` exits 0 again.

**Checkpoint**: commit here. One check, one prompt paragraph, and the discipline is proven on a real defect.

---

## Phase 3 — Wave A: `nature:` on disk

**Serves**: FR-015, FR-031, SC-013, US2 scenario 5, US3 · **plan.md** wave A ·
**contract**: [contracts/knowledge-frontmatter.md](contracts/knowledge-frontmatter.md)

<!-- sequential -->

- [ ] T007 🔴 [US3] Add the wave-A cases to `tests/test_check_project.py`, building tmp projects the way the existing `content:`/`visual:` cases do:
  - **A1** — a `knowledge/<id>/<doc>.md` carrying `nature: anecdote` is reported as an **error** whose message names **the document, the bad value and the allowed set** (message shape: `` knowledge/field-notes/x.md: 'nature: anecdote' is not one of experience ``)
  - **A2** — a document carrying `nature: experience` produces **no** finding
  - **A3** — *regression guard, green from the start*: a project whose documents carry **no** `nature:` key at all exits 0 with **zero errors and zero warnings**. An absent key is **never** a finding — this single assertion is the whole of FR-031's compatibility promise and SC-013's middle clause. **Do not "fix" it into a red test.**

  **RED**: A1 fails on its assertion (`check_knowledge` reports nothing today). A2 and A3 are green from the start and are guards, not reds.

- [ ] T008 [US3] In `scripts/check_project.py`: add `NATURES = ("experience",)` beside `CONTENT_STATES` (`:47`) and `VISUAL_KINDS` (`:54`), with the comment explaining why the vocabulary is closed, and add the membership test to `check_knowledge` (`:372`) in exactly the `content:` form — `if nature is not None and str(nature) not in NATURES` — so a YAML-parsed non-string is compared as text rather than crashing the checker.

  **GREEN**: A1 passes; A2 and A3 stay green.

- [ ] T009 [US2] *Fixture guard* **A4**: run `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — exits 0, unchanged. No document in the shipped corpus carries `nature:` yet, so this proves the new validation is invisible to every project on disk.

**Checkpoint**: `nature:` is validated by name and by value, and absence is provably silent.

---

## Phase 4 — Wave B: the experience-only subtopic and attribution

**Serves**: FR-011, SC-009, US3 scenario 3 · **plan.md** wave B ·
**data-model.md** § 2

**Design constraints fixed by plan.md and data-model.md — do not re-decide**:
"experience-only" means **all** references, not **any**; the failure is an
**error**, not a `warn` (`check_cards` already warns on a missing `source:` at
`:1097-1098`, so a warning would say nothing new and `--strict` would flatten the
distinction).

<!-- sequential -->

- [ ] T010 🔴 [US3] Add the wave-B cases to `tests/test_check_project.py`:
  - **B1** — a card whose `subtopic:` is one **all** of whose `References:` resolve to `nature: experience` documents, and which carries **no** `source:`, is an **error** naming **the card file, the card index and the subtopic**
  - **B2** — the same card **with** `source:` passes
  - **B3** — *the "all, not any" rule*: a subtopic with one experience reference **and** one ordinary reference does **not** make its cards errors. This is its own case, not a corollary of B1
  - **B4** — *regression guard*: `test_a_minimal_project_is_clean` and the existing count assertions are unchanged by the new return values

  **RED**: B1 fails on its assertion. B2, B3, B4 are guards.

- [ ] T011 [US3] In `scripts/check_project.py`, thread the experience set down the road `sparse` already travels (`:380`, `:425-426`, `:428`, `:690`, `:958`, `:1180-1181`) — **do not invent a second mechanism for the same shape of fact**:
  - `check_knowledge()` returns `(sparse, experience)` — sets of resolved paths
  - `check_catalog(..., sparse, experience)` returns `(subtopics, marked, terms, experience_only)`
  - `check_cards(..., experience_only)` raises the FR-011 attribution **error**

  Update the call site at `:1180-1181` to match.

  **GREEN**: B1 passes; B2–B4 stay green.

**Checkpoint**: the one part of piece B that leaves a trace on disk is asserted. Commit.

---

## Phase 5 — Wave C: piece A (goal fit) in the prompt

**Serves**: FR-001 – FR-009, FR-029, FR-030, US1 · **plan.md** wave C

<!-- sequential -->

- [ ] T012 🔴 [US1] Add `check_sources_skill_reads_the_goal()` to `scripts/check_docs.py`, wire it into `main()`, and add cases C1–C3 to `tests/test_check_docs.py` using the `read_skill` monkeypatch seam (`scripts/check_docs.py:357`) so every negative case runs against **synthetic** skill text:
  - **C1** — a `sources` skill that never names `goal.md` is reported
  - **C2** — one that names `goal.md` but never says the assessment is **advisory** / never blocks is reported
  - **C3** — one that does not say the assessment happens **at registration** and is **not re-run on a listing** is reported (FR-008 + research.md § R1 — the accepted no-back-fill gap)

  **RED**: `python3 scripts/check_docs.py` exits 1 against today's 55-line `skills/sources/SKILL.md`, which names none of it.

- [ ] T013 🔴 [US1] Add `check_sources_skill_states_the_archive_reach()` to `scripts/check_docs.py`, wire it into `main()`, and add case **C4** to `tests/test_check_docs.py`: a `sources` skill that does not state the archive reach — `depth: 1`, the index page plus same-domain linked posts, **capped at 20** — is reported (FR-029).

  **RED**: fails against the shipped skill. Separate function and separate task from T012 because it is a separate claim; same file, so **not** parallel with T012.

- [ ] T014 [US1] Write the `## Goal fit` section into `skills/sources/SKILL.md` until C1–C4 pass (**C5**, the shipped-skill guard). It must carry: reading `goal.md` before writing an entry (FR-001); the assessment is **advisory and never blocking**, the entry is written whatever the verdict and the run does **not** pause to ask (FR-002); the warning names the source `id` **and** the `goal.md` line (FR-003); the judgement is about *this source for this goal*, never about the subject or the publisher (FR-004); it reasons from `kind`/`depth` and **says which of the two it used** (FR-005); with **no `goal.md`** there is no assessment and **at most one** `/learning-goal` pointer per run, never one per source (FR-006); nothing is persisted — no `fit:`, no `assessed:`, no timestamp (FR-007); a listing does not re-assess, and a goal written later does not re-judge the register (FR-008, research R1); never invent a claim about a source it has not looked at — where it reasons only from the URL, the `note` and the `type`, it says so (FR-009); and the archive-reach sentence (FR-029).

  **Tone precedent to copy**: `skills/catalog/SKILL.md:60-67` — said once, "do not turn it into a warning and do not repeat it".

  **GREEN**: C1–C5 pass.

**Checkpoint**: piece A's rules are in the prompt and two checks hold them.

---

## Phase 6 — Wave D: piece C in the prompt — C1 the neutral contract, C2 the practitioner addendum

**Serves**: FR-016 – FR-027, FR-030, FR-033, FR-035, FR-039, FR-040, US4 ·
**plan.md** wave D · **contract**: [contracts/discovery-proposal.md](contracts/discovery-proposal.md)

**The separability requirement (FR-039, SC-016) is the point of this wave.** Two
check functions, never one. **Zero** C1 assertions may name practitioner
material, an incident, a post-mortem or a company blog. Deleting the practitioner
sub-section from the skill must fail **exactly one** check.

<!-- sequential -->

- [ ] T015 🔴 [US4] Add `check_sources_skill_carries_the_discovery_contract()` — **C1, material-class neutral** — to `scripts/check_docs.py`, wire it into `main()`, and add cases D1–D4 and D8 to `tests/test_check_docs.py` via the `read_skill` seam:
  - **D1** — a `sources` skill with no `--discover` is reported. Also inside this one function: the found/shown counts grouped by goal area with **every** area listed including the empty ones (FR-027); ≤ 3 per area and ≤ 10 per run (research R3); one **sentence** and never a number for credibility (FR-018); paywalled/login-gated material is reported as found and never proposed, credentials never entered (FR-023); a source already in `sources.yaml` is never proposed (FR-024); no `goal.md` ⇒ nothing to search for (FR-025); no network ⇒ report, write nothing, exit clean (FR-026); picked entries go through the ordinary registration path (FR-020); the network is reached **only** in discovery mode (FR-033); entry is by explicit request only (FR-035)
  - **D2** — one missing the *"writes nothing until the user picks"* rule is reported (FR-016)
  - **D3** — one missing the *"never invent"* rule is reported (FR-021)
  - **D4** — one missing the refusal to write into `knowledge/` or to create a `type: research` entry, or missing the `/research-gaps` seam, is reported (FR-022)
  - **D8** — one whose candidate shape does not require every candidate to **name which class of material it is** is reported (FR-017). **No new function**: this assertion lives inside the neutral check. It asserts the class is *named*, **never which classes exist** — no list, no vocabulary, no filter (FR-040)

  **The spelling `--discover` is load-bearing** (research R4): it appears nowhere in the repository today, so it is an exact token. A bare `discover` would fire on `skills/catalog/SKILL.md:67` and `scripts/build_pdf.py:745`.

  **RED**: fails against the shipped skill, which has no discovery mode at all.

- [ ] T016 🔴 [US4] Add `check_sources_skill_carries_the_practitioner_addendum()` — **C2, the one addendum this feature ships** — to `scripts/check_docs.py`, wire it into `main()`, and add case **D6** to `tests/test_check_docs.py`: a `sources` skill missing the practitioner addendum — the **primary-and-interested** property and the **selected-sample** property on the credibility sentence — is reported (FR-019). This is the **only** check in wave D that may name a class of material. Neither function reads the other's text.

  **RED**: fails against the shipped skill.

- [ ] T017 🔴 [US4] Add the separability cases to `tests/test_check_docs.py` (test file only — no `scripts/` edit):
  - **D5** — *neutrality guard*: a synthetic skill whose practitioner sub-section has been **deleted** still passes **every** C1 assertion (D1–D4 and D8). None of them names a material class, an incident, a post-mortem or a company blog
  - **D5b** — *separability*: deleting the addendum text fails **exactly one** check — `check_sources_skill_carries_the_practitioner_addendum()` — and leaves the neutral check green (SC-016). This is what lets [issue #43](https://github.com/mhabedank/lernkarten/issues/43) attach a research-literature addendum later by **adding** a function rather than editing a neutral one

  **RED against the shipped skill; green in shape.** D5 and D5b are the assertions that make FR-039 real rather than aspirational.

- [ ] T018 [US4] Write the `## Finding sources` section into `skills/sources/SKILL.md`, **class-neutral throughout**: the `--discover` entry (and its natural-language equivalents as the same entry), the proposal shape of [contracts/discovery-proposal.md](contracts/discovery-proposal.md) § *Shape of the proposal*, the caps (≤ 3 per area, ≤ 10 per run, **every** area listed), the six per-candidate fields including the **class of material** line — with examples and an explicit statement that a candidate may name a class the examples do not cover, and **no list to choose from** — the credibility sentence as one sentence and never a number, the three exclusions (unretrieved, paywalled, already registered), the two degraded paths (no `goal.md`, no network), "writes nothing until the user picks", "picked entries go through the ordinary registration path", and the `/research-gaps` seam.

  **Not written here** (FR-040): no class-selection argument, no way to ask for one class only, no class vocabulary. **Stop and flag** if a class list appears anywhere.

  **GREEN**: D1–D4, D5, D8 pass.

- [ ] T019 [US4] Write the **practitioner addendum** as its own clearly separable sub-section under `## Finding sources` in `skills/sources/SKILL.md` (FR-019): for practitioner material the credibility sentence must additionally name that a company account of its own incident is a **primary source and an interested one**, and that published incidents are a **selected sample**. A candidate that is *not* practitioner material is **not** held to either property.

  **GREEN**: **D6 and D7** pass — both checks green, and T017's D5b now demonstrably fails exactly one check when the sub-section is deleted.

**Checkpoint**: two separate checks, one neutral and one addendum, and the neutrality is asserted rather than asserted-about.

---

## Phase 7 — Wave E: piece D, the silence

**Serves**: FR-035 – FR-037, SC-015, US4 · **plan.md** wave E

**These gates are C1-level.** They are about the entry condition, which is the
same whatever a candidate turns out to be. **No assertion in this wave names a
class of material**, and a later addendum touches none of it (FR-039).

**Two check functions, not one** (plan.md § Test plan first, wave E). E3 asserts
a **presence** in the one skill this feature rewrites; E1/E2/E4 assert an
**absence** across the four skills it otherwise leaves alone. Opposite polarity,
different blast radius: one function holding both could not produce a failure
message that says which of the two rules broke. Each function gets its own
red-then-green pair below.

<!-- sequential -->

- [ ] T020 🔴 [US4] Add `check_sources_skill_states_the_explicit_request()` — the **positive substring gate** on `skills/sources/SKILL.md` — to `scripts/check_docs.py`, wire it into `main()`, and add case **E3** to `tests/test_check_docs.py` via the `read_skill` seam (`scripts/check_docs.py:357`):
  - **E3** — a `sources` skill that does not state that discovery is entered **only** on an explicit request, and that an **ordinary run** (register, list, remove) neither enters nor mentions it, is reported (FR-035, FR-036)

  **RED**: E3 fails against the shipped 55-line `skills/sources/SKILL.md`, which says nothing of the kind.

  Shape to copy: `check_print_skill_relays_setup()` (`scripts/check_docs.py:363-374`), the file's existing positive gate on one named skill.

- [ ] T021 [US4] Add the explicit-request and silence rules to `skills/sources/SKILL.md`: discovery is entered **only** on an explicit request at invocation, never started by itself, never offered as a follow-up at the end of an ordinary run, never the default of any invocation (FR-035); and a run that registers, lists or removes **neither enters nor mentions it** — no candidate, no proposal, no closing line suggesting the user could go looking (FR-036).

  **GREEN**: E3 passes.

- [ ] T021a 🔴 [US4] Add `check_discovery_is_not_offered_elsewhere()` — the **negative token gate** over `skills/ingest/SKILL.md`, `skills/catalog/SKILL.md`, `skills/cards/SKILL.md` and `skills/print/SKILL.md` — to `scripts/check_docs.py`, wire it into `main()`, and add cases E1, E2 and E4 to `tests/test_check_docs.py`:
  - **E1** — `--discover` appearing in `skills/catalog/SKILL.md` is reported, **naming the file**
  - **E2** — the same for `ingest`, `cards` and `print`
  - **E4** — *shipped-repo guard, green from the start*: the four other skills carry no `--discover`. The point is that it **stays** green

  **RED**: E1 and E2 are the assertions that prove the gate fires — they run against **synthetic** skill text carrying `--discover` (the `read_skill` seam), the same shape as wave G's G1/G2, which also pass immediately and are what prove the scoping. E4, the shipped-repo half, is green from the start and must **stay** green; its green partner is T021b. This function reads `skills/sources/SKILL.md` **never** — that file is T020's, and neither of the two wave-E functions reads the other's text.

  **Placed after T021 deliberately**: `--discover` first exists in the repository once T018 and T021 have written it into `skills/sources/SKILL.md`, so this is the point from which the absence elsewhere becomes a thing that can drift.

  **Stated limit** (plan § Risks, accepted rather than hidden): this is a **token** check, not a semantic one. It catches `--discover` in another skill — the form the drift actually takes, a pointer somebody adds. It does **not** catch the paraphrase *"you could go looking for more material"*. That case is `docs/testing.md` row **12-vi**, named there with its FR number.

- [ ] T021b [US4] *Guard* **E4**: run `python3 scripts/check_docs.py` and confirm `check_discovery_is_not_offered_elsewhere()` reports nothing now that `skills/sources/SKILL.md` carries the discovery mode — no pointer leaked into `ingest`, `catalog`, `cards` or `print`. This is the gate's standing obligation, and it is restated where the four other prompts are edited (**T024**, the FR-037 clause) and where the diff is scope-checked (**T043**).

  **GREEN**: E1, E2 and E4 all green, with E3 still green from T021.

**Checkpoint**: the negative half of the feature has a gate of its own, separate from the positive one, and its limit is written down.

---

## Phase 8 — Wave F: the experience-report rule in three prompts

**Serves**: FR-010 – FR-015, FR-030, US3 · **plan.md** wave F

<!-- sequential -->

- [ ] T022 🔴 [US3] Add `check_skills_carry_the_experience_rule()` to `scripts/check_docs.py`, wire it into `main()`, and add cases F1–F3 to `tests/test_check_docs.py` via the `read_skill` seam:
  - **F1** — an `ingest` skill that does not name `nature: experience` is reported
  - **F2** — a `catalog` skill that has lost the experience-report rule is reported (FR-010, FR-013 selected sample, FR-014 rule-versus-case)
  - **F3** — a `cards` skill that has lost the attribution rule is reported (FR-010, FR-011 via the existing `source:` key, FR-012 the scale)

  **RED**: fails against all three shipped skills.

<!-- parallel-group: 2 (max 3 concurrent) -->

- [ ] T023 [P] [US3] `skills/ingest/SKILL.md` — write `nature: experience` into the **frontmatter format block at lines 92-111** and add the rule for when to write it and when **not** to: a document whose **subject is a reported case** gets `nature: experience`; everything else gets **no `nature:` key at all** — not `nature: reference`, not `nature: none`, absence **is** the other state; a reference work with one anecdote in it is **not** marked, because `nature:` is one value about the whole document and never a per-paragraph judgement.

  **⚠ Hazard**: `tests/test_testdata.py:265-273` parses this file **literally** around lines 27-28 for the default-pattern text. Keep every edit inside the frontmatter block and the extraction rules. **Do not reflow the paragraph near line 27.**

- [ ] T024 [P] [US3] `skills/catalog/SKILL.md` — read `nature: experience`: place the document normally, but report a required topic covered **only** by experience reports rather than presenting single-case coverage as coverage of the rule (FR-014), and say that published incidents are a **selected sample** because companies publish the failures they recovered from (FR-013). That report **must not** become a suggestion to run discovery (FR-037); a `Status: gap` subtopic's one pointer stays `/research-gaps`, exactly as today.

- [ ] T025 [P] [US3] `skills/cards/SKILL.md` — read `nature: experience`: phrase the card **about the reported case**, name that case through the existing optional `source:` key, never as an unattributed general rule (FR-010, FR-011), and carry the **scale or circumstances** the fact depends on rather than dropping them (FR-012).

  *Genuinely parallel*: T023, T024 and T025 touch three different `SKILL.md` files, all after T022, with no dependency between them.

<!-- sequential -->

- [ ] T026 [US3] *Guard* **F4**: `python3 scripts/check_docs.py` reports nothing for `check_skills_carry_the_experience_rule()` — the three edited skills pass.

**Checkpoint**: pieces B and C are in the prompts, and waves A–G all have their checks. Commit.

---

## Phase 9 — Wave H: the fixture

**Serves**: US3, SC-009 · **plan.md** wave H · **Only once A–G are green.**

**The demo project is the one versioned corpus. No second fixture, at any point**
(constitution VII & XI, gates CHK050). All new material is **invented archipelago
content** — nothing quoted from anyone.

<!-- sequential -->

- [ ] T027 **Before touching the fixture**: run `python3 scripts/check_project.py tests/fixtures/demo-project --strict` and record the exact output. This is its own step, per plan.md § Risks, because `catalog/topics.md` carries `Status:`, `Parents:`, `Also covers:`, `Related:` and `Term:` invariants that the new subtopic could disturb.

- [ ] T028 [US3] New `tests/fixtures/demo-project/raw/field-notes/<incident>.md` — an invented archipelago incident write-up (a harbour-office account of a grounding or a signal failure). Plain markdown, committed text, no binary, no generator needed. It joins the seven files already in that folder.

- [ ] T029 [US3] New `tests/fixtures/demo-project/knowledge/field-notes/<incident>.md` — the ingested twin of T028, carrying `source: field-notes`, `path:`, `ingested:` and **`nature: experience`**. It is the **only** document in the corpus with the key at all, which is what makes wave A's A3 guard meaningful.

- [ ] T030 [US3] `tests/fixtures/demo-project/catalog/topics.md` — one new `###` subtopic under the existing `## Signals, flags and the radio` topic (line 73), whose **only** reference is the T029 document. Placed under that topic deliberately, so it serves a required topic already in the fixture's `goal.md`. Keep the file's `Status:`/`Parents:`/`Also covers:`/`Related:`/`Term:` conventions intact.

- [ ] T031 [US3] `tests/fixtures/demo-project/cards/signals.yaml` — one or two cards under the new subtopic, each carrying `source:` naming the case, each phrased about the reported case rather than as a general rule, each with a **fresh, unique five-character Crockford Base32 `id`**, and each following `CLAUDE.md`'s card style and Typst escaping. **`cards/signals.yaml` specifically**, so `TIDES_CARD_COUNT` (`tests/test_e2e.py:49`) does not move.

<!-- parallel-group: 3 (max 3 concurrent) -->

- [ ] T032 [P] [US3] `tests/fixtures/demo-project/README.md` — add the row saying what the new material is for and which failure mode it exercises
- [ ] T033 [P] [US3] `tests/test_e2e.py:27` — move `DEMO_CARD_COUNT` from `32` to the new total. Confirm `TIDES_CARD_COUNT` (`:49`) is **unchanged**. The derived `DEMO_A7_PAGES` / `DEMO_A8_PAGES` / sheet counts follow from `sheet_pages()` automatically — do not hand-edit them.

  *Genuinely parallel*: a fixture README and a test module, different files, both depending only on T031 being final.

<!-- sequential -->

- [ ] T034 [US3] Run `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — exits 0, and the count line names the new subtopic and cards. Compare against T027's recorded output.

- [ ] T035 **Its own task, not a footnote**: `python3 scripts/make_testdata.py && LERNKARTEN_E2E=1 pytest tests/test_e2e.py`. `DEMO_CARD_COUNT` moved in T033, and `tests/test_e2e.py` **skips without a typesetting engine**, so a wrong count is invisible to a plain `pytest` run and would ship undetected. This is **required for this feature**, not optional (quickstart § 4, gates CHK046).

**Checkpoint**: the corpus carries one experience report end to end, and the e2e count is proven.

---

## Phase 10 — Wave I: the prompts, driven for real

**Serves**: US1, US3, US4, US5, US6 · **plan.md** wave I

Waves C–F made the checks pass against the prompt text. This wave proves the
prompts actually **run**: each skill is driven against a `scripts/demo.py`
scratch copy until the project it produces passes `--strict`.

<!-- sequential -->

- [ ] T036 [US6] **First thing in wave I**: rewrite the `description` in `skills/sources/SKILL.md:2-4` so it names **both jobs** — registering/listing/removing **and** finding sources for a stated goal. It is gated **four ways** by `check_skills()` (`scripts/check_docs.py:79-121`) and every one must survive: `name: sources` equals the folder name; the description is **≥ 20 characters**; it contains the word **`Triggers`**; and it contains the domain word **`flashcard`**. Add `/sources --discover` to the trigger list. Run `python3 scripts/check_docs.py` immediately — `check_skills` catches a miss at once.

- [ ] T037 [US1] [US4] [US5] `python3 scripts/demo.py /tmp/lk-demo --force`, then drive `/sources` against it in a real Claude session — a registration, a bare listing, a removal, and `/sources --discover` — and edit `skills/sources/SKILL.md` until every wave C, D and E assertion passes **and** `python3 scripts/check_project.py /tmp/lk-demo --strict` exits 0 after accepting a candidate (SC-006). Confirm `sources.yaml` carries **no** verdict key of any kind (FR-007, SC-001).

- [ ] T038 [US3] Drive `/ingest` → `/catalog` → `/cards` against the same scratch copy and edit `skills/ingest/SKILL.md`, `skills/catalog/SKILL.md` and `skills/cards/SKILL.md` until wave F passes **and** `python3 scripts/check_project.py /tmp/lk-demo --strict` exits 0. Confirm the incident document gets `nature: experience` and the handbook document gets **no `nature:` key**.

**Checkpoint**: the prompts do what the checks say they do.

---

## Phase 11 — Wave J: docs and the named manual rows

**Serves**: FR-032, SC-011, SC-012, US6 · **plan.md** wave J

**Twenty-three rows.** The plan says "~22"; quickstart says 21; the enumerated
list is 19 `/sources` rows (4a–4s) plus 4 pipeline rows. Every row carries its FR
number **inside the row**, in the established `**run output (FR-0xx):**` form
(`docs/testing.md:203`), so `docs/testing.md` is traceable without the plan open
beside it (gates CHK007).

<!-- sequential -->

- [ ] T039 [US6] `docs/testing.md` — insert the nineteen `/sources` rows **after line 193** (the existing row `4`), in the table's `| # | Step | Do this | Expect |` shape:

  | Row | Covers |
  |---|---|---|
  | **4a** | FR-001, FR-005, FR-009 — the assessment names a required topic or area, and says which of `kind`/`depth` it used |
  | **4b** | FR-002, FR-003, FR-005 weigh-down, SC-004 — scratch copy with `depth: awareness`; the warning names the id **and** the goal line, the entry is written, **zero** confirmation prompts |
  | **4c** | FR-005 weigh-up — scratch copy with `depth: expert`; the same material is weighed up and the run **says so** |
  | **4d** | FR-004 — the warning says nothing about the subject or the publisher in general |
  | **4e** | FR-008 — a bare listing re-assesses nothing |
  | **4f** | FR-003 — a source matching an `## Out of scope` line: the warning **quotes that line** |
  | **4g** | FR-007, SC-001 — after the run `sources.yaml` carries **no** verdict of any kind |
  | **4h** | FR-029 — the archive reach is stated at registration |
  | **4i** | FR-006, SC-003 — `rm goal.md`: no assessment, identical key set, **≤ 1** `/learning-goal` pointer per run |
  | **4j** | research R1 — a goal written **afterwards** produces no assessment for what is already registered, and nothing claims otherwise |
  | **4k** | FR-016 – FR-018, FR-027, FR-035, FR-039, FR-040, SC-007, SC-017 — the **neutral** proposal shape; **every** candidate names its class, the non-practitioner ones included; no candidate is dropped or renamed for naming a class no list contains, because there is no list, no class argument and no way to ask for one class |
  | **4l** | FR-016, SC-005 — decline everything: **zero** files created, **zero** modified |
  | **4m** | FR-020, FR-022, SC-006 — accept one: the ordinary path, the assessment fires, `--strict` exits 0 |
  | **4n** | FR-021, FR-023, FR-024 — unretrieved, paywalled and already-registered candidates |
  | **4o** | FR-025 — no `goal.md`: nothing to search for, points at `/learning-goal`, writes nothing |
  | **4p** | FR-026, SC-008 — no network (beside the existing `9d` at `:222`): reports, writes nothing, exits clean, **no traceback** |
  | **4q** | FR-036, SC-015 — a registration, a bare listing and a removal mention discovery **nowhere** |
  | **4r** | FR-033 — none of those three makes a network request on discovery's behalf |
  | **4s** | FR-019, SC-007 — the **practitioner addendum**: a practitioner candidate additionally names primary-and-interested and selected-sample; a non-practitioner one is **not** held to those two properties |

<!-- parallel-group: 4 (max 3 concurrent) -->

- [ ] T040 [P] [US6] `docs/testing.md` — add the four pipeline rows beside the steps they belong to:

  | Row | Step | Covers |
  |---|---|---|
  | **8m** ⚠ | `/ingest` | FR-015 — the incident write-up gets `nature: experience`; the handbook document gets **no** `nature:` key |
  | **9f** | `/catalog` | FR-013, FR-014 — selected sample, and single-case coverage is not presented as coverage of the rule |
  | **12-v** | `/cards` | FR-011, FR-012, SC-009 — every card names its case through `source:`, none states an unattributed general rule, the scale is kept |
  | **12-vi** | any | FR-037, FR-038, SC-014, SC-015 — a full `/sources` → `/ingest` → `/catalog` → `/cards` run with **no** `--discover`: zero mentions, zero extra entries |

  **⚠ Row-id collision, must be resolved in this task**: plan.md names this row **`8h`**, but `8h` is **already taken** — `docs/testing.md:211` is a `/learning-goal` row. The 8-series runs `8a … 8l`, so the next free id is **`8m`**. Use `8m`, and correct the two `8h` references in `plan.md` (the routing table row for FR-015 and the named-rows list). Do **not** ship a duplicate id.

- [ ] T041 [P] [US6] `docs/workflow.md` — three edits, no step-count sentence touched: **Step 1** gains the ordering sentence (the goal-fit assessment happens at registration, so writing `goal.md` first is worth it, and a goal written later does not re-judge the register — research R1); **Step 2** names **both** jobs of `/sources`; **Step 5** states the seam between `/sources --discover` and `/research-gaps` (same network, different output — proposed sources to read versus synthesised documents written into `knowledge/`). Also update the knowledge-frontmatter description where it is given, to include the optional `nature:` key.

- [ ] T042 [P] [US6] `README.md` — the `/sources` table row names **both** jobs (register/list/remove **and** find sources for a stated goal). The pipeline stays **seven** steps; change no step-count sentence.

  *Genuinely parallel*: `docs/testing.md`, `docs/workflow.md` and `README.md` are three different files. T040 follows T039 only because both write `docs/testing.md`, and T039 is complete before this group starts.

<!-- sequential -->

- [ ] T043 [US6] Scope verification — confirm the diff touches **none** of: `docs/index.html` (the step strip at `:489-492` is a label, not a description — this is a recorded scoping decision, not an oversight), `assets/brand/*.typ`, the three rendered PNGs, `scripts/render_brand.py`, `tests/test_landing_page.py`, `.specify/memory/constitution.md`, `CLAUDE.md`, `docs/design.md`, `templates/*.typ`, `scripts/build_pdf.py`, `bin/lernkarten`. Confirm **seven steps** everywhere the pipeline is described (SC-011). Run `python3 scripts/check_docs.py` — `check_links` is the automated part of this wave.

**Checkpoint**: every run-output requirement has a **named** row carrying its FR number.

---

## Phase 12: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

<!-- sequential -->

- [ ] T044 **The four PR gates**, in order, all green: `ruff check . && ruff format --check .` · `pytest` · `lernkarten check cards/example.yaml` · `python3 scripts/check_docs.py`. Ruff is not loosened; line length stays 100 (constitution XII).
- [ ] T045 `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — exits 0.
- [ ] T046 Confirm T035 (`LERNKARTEN_E2E=1 pytest tests/test_e2e.py`) has been re-run **after** the final fixture state, since `DEMO_CARD_COUNT` moved. Also run `pytest tests/test_testdata.py` — it parses `skills/ingest/SKILL.md` literally (`:265-273`) and is the guard against T023 reflowing the wrong paragraph.
- [ ] T047 `python3 scripts/deps.py --check` / `lernkarten deps --check` — confirm the runtime dependency set is **still exactly** `pyyaml==6.0.3`. Confirm `requirements-dev.txt` is unchanged. If either moved, **stop and flag back to plan.md**.
- [ ] T048 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries. Nothing was forced in with `git add -f`.
- [ ] T049 Open the pull request from `feat/goal-fit-sources` (`main` rejects direct pushes). The description **must** carry the constitution VII note required by plan.md's Constitution Check row VII: the demo fixture was **extended, never duplicated**, with **invented** archipelago material, and nothing is quoted from anyone. Commit subjects use the repo prefixes (`feat:`, `skill:`, `test:`, `docs:`, `fix:`).

---

## Phase 13: By Hand

**Purpose**: the larger half of this feature's verification. Most of what it does
is what a run *says*, and nothing on disk records that (constitution XI's
run-output carve-out). Rows 1–14 need a Claude session in the demo folder.

Set up once (quickstart § 5):

```bash
python3 scripts/demo.py ~/lernkarten-demo --raw
cd ~/lernkarten-demo
python3 -m http.server 8137 --directory raw/web &
```

<!-- sequential -->

- [ ] T050 Run rows **4a – 4j** (piece A). For 4b and 4c, edit **one word** of the scratch `goal.md` (`depth: working` → `awareness`, then → `expert`) and read the two statements side by side — FR-005 requires the run to say **which** of `kind`/`depth` it used, so the two runs must differ in their **stated reason**, not only in their verdict. **Never edit `tests/fixtures/`** for this; the committed fixture keeps its single pair and no second corpus exists at any point (research R2).
- [ ] T051 Run rows **4k – 4s** (piece C, discovery). Check the **non-practitioner** candidates especially: they name a class too, and they are **not** held to the addendum's two properties. Decline everything and confirm zero files created and zero modified; then accept one and confirm `--strict` exits 0. Turn the network off for 4p.
- [ ] T052 Run rows **4q, 4r, 12-vi** (piece D, the silence). A registration, a bare listing and a removal mention discovery nowhere; then a full `/sources` → `/ingest` → `/catalog` → `/cards` run with `--discover` never typed produces **zero** lines mentioning discovery — `/catalog`'s FR-014 report included — and a `sources.yaml` holding exactly the sources you named.
- [ ] T053 Run rows **8m, 9f, 12-v** (piece B, the experience report). Confirm the incident document carries `nature: experience` and the handbook document carries **no** `nature:` key — not `nature: reference`, not `nature: none`.
- [ ] T054 Walk [checklists/gates.md](checklists/gates.md) CHK001 – CHK065 and check each item off. CHK003 – CHK006 and CHK013 – CHK022 are the ones this checklist exists for; a "no" is a defect in the artifact named in brackets, fixed **there** and not in review comments.

---

## Dependencies & Execution Order

### Wave order — a constraint, not a suggestion

```
Setup → G → A → B → C → D → E → F → H → I → J → Gates → By Hand
```

- **G first**, because G3 is the only assertion red against a clean checkout. It needs no fabricated input, so it is the cheapest place to prove the discipline is real.
- **A before B**: `check_catalog` cannot receive an experience set that `check_knowledge` does not yet return.
- **C, D, E before F only by convention** — they touch the same two files and are serialized for that reason, not by a data dependency.
- **H only once A–G are green.** The fixture is the first thing that exercises `nature:` end to end; adding it earlier hides which check caught what.
- **I after H**, because driving a skill against the demo project needs the demo project to be final.
- **J last of the work**, because a doc describing behaviour that is still moving goes stale in the same branch.
- **Never move an implementation task above its check.** That is the one rule here with no exception (constitution XI).

### Not parallel — and why

- `scripts/check_docs.py` is touched by **eight** tasks (T005, T012, T013, T015, T016, T020, T021a, T022) — one per new check function, and there are **eight** functions because T015/T016 are wave D's pair and T020/T021a are wave E's. Two tasks that both edit it are **not** parallel, however unrelated the requirements.
- `scripts/check_project.py` is touched by T008 and T011. Serialized.
- `tests/test_check_docs.py` is touched by nine tasks (those eight plus the test-only T017); `tests/test_check_project.py` by two. Serialized within each file.
- `skills/sources/SKILL.md` is touched by T014, T018, T019, T021, T036, T037. Serialized — and it is the single busiest file in the feature.
- `docs/testing.md` is touched by T039 and T040. Serialized.
- A 🔴 task and the task that greens it. Ever.

### Parallel groups found — four, ten tasks

| Group | Tasks | Files, and why they are genuinely disjoint |
|---|---|---|
| 1 | T002, T003 | `scripts/install-hooks.sh` (git hooks) vs `scripts/make_testdata.py` (fixture binaries) — no shared file, both after T001 |
| 2 | T023, T024, T025 | `skills/ingest/SKILL.md`, `skills/catalog/SKILL.md`, `skills/cards/SKILL.md` — three different prompts, all gated by the one check T022 already landed |
| 3 | T032, T033 | `tests/fixtures/demo-project/README.md` vs `tests/test_e2e.py` — a fixture README and a test module, both depending only on T031 |
| 4 | T040, T041, T042 | `docs/testing.md`, `docs/workflow.md`, `README.md` — three different docs; T040 follows T039 on the same file, and T039 is complete before the group opens |

That is **10 of 56** tasks parallelizable (T001 – T054 plus wave E's T021a and T021b). The rest is sequential, which is the
honest shape of a feature that lands in two Python files, two test modules and
five `SKILL.md` files.

---

## Requirement → task traceability

| Requirement | Tasks |
|---|---|
| FR-001 – FR-009 | T012, T013, T014 (prompt) · T050 (rows 4a–4j) |
| FR-010 | T022, T024, T025 · T053 |
| FR-011 | T010, T011 (**error** in `check_project.py`) · T022, T025 · T053 |
| FR-012 | T025 · T053 |
| FR-013, FR-014 | T022, T024 · T053 (row 9f) |
| FR-015 | T007, T008 · T022, T023 · T029 · T053 (row 8m) |
| FR-016 – FR-018, FR-020 – FR-027 | T015, T018 · T051 |
| FR-019 (the one addendum) | T016, T019 · T051 (row 4s) |
| FR-028 | *withdrawn — no task* |
| FR-029 | T013, T014 · T050 (row 4h) |
| FR-030 | *is* T005, T012, T013, T015, T016, T020, T021a, T022 — the eight check functions |
| FR-031 | *is* T007, T008, T010, T011 — plus the A3 absence guard |
| FR-032 | *is* T039, T040 |
| FR-033 | T015, T018 · T052 (row 4r) |
| FR-034 | T005, T006 |
| FR-035, FR-036 | T015, T020 (`check_sources_skill_states_the_explicit_request()`), T021 · T052 |
| FR-037 | T021a (token half, `check_discovery_is_not_offered_elsewhere()`), T021b · T024 · T052 (row 12-vi, paraphrase half) |
| FR-038 | T052 (row 12-vi) — no script can see it; stated as an inspectable end state |
| FR-039 | T015, T016, T017 (D5 neutrality + D5b separability), T018, T019 |
| FR-040 | T015 (D8, the hook) · T018 (nothing built) · T051 (row 4k) |

**FR-003, FR-007 and FR-038 have no automated row, deliberately** — each is a
statement about something that is *not* there: a warning's wording, a key that
must not exist, and a register that holds nothing extra. FR-007 is additionally
protected by [contracts/sources-yaml-unchanged.md](contracts/sources-yaml-unchanged.md).

---

## Open items flagged during task generation

Two arithmetic/id discrepancies in plan.md that a reader would otherwise trip
over. Both are now settled; neither blocks starting at T005.

1. **`docs/testing.md` row id `8h` is already taken.** plan.md routes FR-015 to a
   new `/ingest` row `8h`, but `docs/testing.md:211` is an existing
   `/learning-goal` row `8h`. The 8-series runs `8a … 8l`. **T040 uses `8m`** and
   corrects plan.md's two references. (The plan also skips `12-iv`, which is free
   — harmless, left as a gap.)
2. **Resolved: `check_docs.py` gains eight check functions, and wave E is the
   split.** The count contradicted itself (plan.md said "eight" in one place and
   "seven small functions" in another, and the waves named seven). **Decision:
   split wave E**, because E1/E2/E4 assert an *absence* of `--discover` across
   four other skills while E3 asserts a *presence* in `skills/sources/SKILL.md` —
   opposite polarity, different blast radius, and one function holding both
   cannot say which rule broke. It also makes plan.md's "eight" true rather than
   editing it down. The eight are `check_network_claim_is_not_exclusive`,
   `check_sources_skill_reads_the_goal`,
   `check_sources_skill_states_the_archive_reach`,
   `check_sources_skill_carries_the_discovery_contract`,
   `check_sources_skill_carries_the_practitioner_addendum`,
   `check_sources_skill_states_the_explicit_request` (T020),
   `check_discovery_is_not_offered_elsewhere` (T021a) and
   `check_skills_carry_the_experience_rule`. plan.md § Scale/Scope, § Structure
   Decision, wave E and the FR gate table now all say eight.

---

## Notes

- **Test-first, always.** A test written after the code tells you what the code does; only a test seen failing tells you it does what was asked.
- **Commit at every 🔴 checkpoint**, and after each wave.
- The `read_skill` seam (`scripts/check_docs.py:357`) and the `gated_project()` helper (`tests/test_check_docs.py:193`) mean every negative case runs against **synthetic** text — no shipped `SKILL.md` is edited to make a test go red.
- **Absence is never a finding.** If A3 ever goes red, `nature:` has stopped being optional and every project on disk is affected.
- **If no failing check can be written for a requirement, go back to the spec** — not forward to the prompt (constitution XI).
- English throughout: code, comments, docstrings, docs, commit messages.
