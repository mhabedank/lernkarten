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

- [x] T001 `python3 -m pip install --user -r requirements-dev.txt` — pytest, ruff==0.16.2, pillow, pyyaml. **No package is added to this file by this feature.**

<!-- parallel-group: 1 (max 3 concurrent) -->

- [x] T002 [P] `scripts/install-hooks.sh` — install the pre-commit (no user content) and pre-push (no direct `main`) hooks
- [x] T003 [P] `python3 scripts/make_testdata.py` — build the binary test material under `tests/fixtures/demo-project/` so the suite can run

<!-- sequential -->

- [x] T004 Record the baseline: run `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`, and `python3 scripts/check_project.py tests/fixtures/demo-project --strict`. **All five must be green on the clean worktree** — that is what makes T005's red meaningful.

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

- [x] T005 🔴 [US6] Add `check_network_claim_is_not_exclusive()` to `scripts/check_docs.py` (paragraph-scoped over `gated_files()`, in the shape of `check_print_order()` at `:561-572`), wire one line into `main()` at `:575`, and add the wave-G cases to `tests/test_check_docs.py`:
  - **G1** — a doc claiming *"the only step that reaches the network"* is reported, and the message **names the file** (synthetic input via the `gated_project()` helper at `tests/test_check_docs.py:193`)
  - **G2** — *false-positive guard*: `CONTRIBUTING.md:82`'s *"even reaches the network:"* does **not** fire. The regex is scoped to the **exclusivity claim** (`only … that reaches the network`), never to the bare words (research.md § R5)
  - **G3** — *shipped-repo*: the check reports nothing over the real `gated_files()`

  **RED**: G3 fails, and `python3 scripts/check_docs.py` exits 1 naming `skills/research-gaps/SKILL.md`. G1 and G2 pass immediately — they are what proves the gate is scoped correctly.

  **Note for the implementer — the scope is `gated_files()`, not `markdown_files()`.** `gated_files()` (`scripts/check_docs.py:407-421`) is the wider set and is the one this check runs over: root `*.md`, `docs/*.md`, `skills/*/SKILL.md`, **plus** `scripts/*.py` (except `check_docs.py` itself) and `templates/*.typ`. Do **not** scope it to `markdown_files()` (`:168`), which omits the last two — narrowing it there would silently narrow FR-034 and SC-010. Both `specs/**` and `tests/` are outside `gated_files()`, so this feature's own quotations of the stale claim in `spec.md`, `plan.md`, `tasks.md` and `research.md` do **not** fire it, and neither does `tests/test_deps.py:10`. Across the whole gated set the one live false positive is `CONTRIBUTING.md:82`, which is what G2 pins.

- [x] T006 [US6] Rewrite `skills/research-gaps/SKILL.md:17-19` — delete the exclusivity claim and state the real distinction instead: `/research-gaps` (and `/sources --discover`) **go looking for material the user did not choose**; `/ingest` **fetches what the user named** (FR-033, FR-034). Do **not** delete the network sentence outright — FR-034 corrects the claim, it does not remove the paragraph.

  **GREEN**: G3 passes; `python3 scripts/check_docs.py` exits 0 again.

**Checkpoint**: commit here. One check, one prompt paragraph, and the discipline is proven on a real defect.

---

## Phase 3 — Wave A: `nature:` on disk

**Serves**: FR-015, FR-031, SC-013, US2 scenario 5, US3 · **plan.md** wave A ·
**contract**: [contracts/knowledge-frontmatter.md](contracts/knowledge-frontmatter.md)

<!-- sequential -->

- [x] T007 🔴 [US3] Add the wave-A cases to `tests/test_check_project.py`, building tmp projects the way the existing `content:`/`visual:` cases do:
  - **A1** — a `knowledge/<id>/<doc>.md` carrying `nature: anecdote` is reported as an **error** whose message names **the document, the bad value and the allowed set** (message shape: `` knowledge/field-notes/x.md: 'nature: anecdote' is not one of experience ``)
  - **A2** — a document carrying `nature: experience` produces **no** finding
  - **A3** — *regression guard, green from the start*: a project whose documents carry **no** `nature:` key at all exits 0 with **zero errors and zero warnings**. An absent key is **never** a finding — this single assertion is the whole of FR-031's compatibility promise and SC-013's middle clause. **Do not "fix" it into a red test.**

  **RED**: A1 fails on its assertion (`check_knowledge` reports nothing today). A2 and A3 are green from the start and are guards, not reds.

- [x] T008 [US3] In `scripts/check_project.py`: add `NATURES = ("experience",)` beside `CONTENT_STATES` (`:47`) and `VISUAL_KINDS` (`:54`), with the comment explaining why the vocabulary is closed, and add the membership test to `check_knowledge` (`:372`) in exactly the `content:` form — `if nature is not None and str(nature) not in NATURES` — so a YAML-parsed non-string is compared as text rather than crashing the checker.

  **GREEN**: A1 passes; A2 and A3 stay green.

- [x] T008a 🔴 [US1] *FR-007's negative, made checkable.* Add the wave-A **verdict-key** cases to `tests/test_check_project.py`, beside the wave-A `nature:` cases:
  - **A5** — a `sources.yaml` entry carrying a verdict key is an **error** naming **the entry id and the key**. Written as one `@pytest.mark.parametrize` case **per key name** — `fit`, `assessed`, `goal_fit`, `discovered`, `proposed_by` — so a failure says *which* key stopped being refused rather than "the verdict check broke" (message shape: `` sources.yaml [field-notes]: 'fit' is not a key of a source entry ``)
  - **A6** — *no-regression guard, green from the start*: an entry carrying `login:`, `pattern:`, `pages:`, `depth:`, `note:` — or any other key `check_sources` accepts today — is **unaffected**, and the shipped `tests/fixtures/demo-project/sources.yaml` (which carries `login: true` at `harbour-office-members`) still passes. **Do not "fix" this into a red test.**

  **RED**: A5 fails on its assertion. `check_sources` (`scripts/check_project.py:317-370`) reads `id`, `type` and the type's required field and **ignores every other key** — `login:` relies on that — so a `fit:` key validates silently today. A6 is green from the start.

  **The decision, so implementation does not re-take it: this check rejects five key names, never unknown keys in general.** An allowlist of permitted keys would make `login:` invalid, would make invalid every project on disk carrying a key this repo has not thought of, and would be a behaviour change no requirement asks for. FR-007 forbids a **verdict** on the entry, not extensibility. The five names are the ones [contracts/sources-yaml-unchanged.md](contracts/sources-yaml-unchanged.md) § *The change* already enumerates as the negative. A timestamp has no fixed key name and is therefore **not** gated — that half stays on row **4g**.

- [x] T008b [US1] In `scripts/check_project.py`: add `VERDICT_KEYS = ("fit", "assessed", "goal_fit", "discovered", "proposed_by")` beside `SOURCE_TYPES` (`:32-38`), with the comment saying why it is a **list of forbidden names** and not an allowlist of permitted keys, and report each one found on an entry as an **error** in `check_sources` (`:317-370`). Place the test **before** the `kind = entry.get("type")` block, so an entry with an unknown type still gets the finding instead of `continue`-ing past it.

  **GREEN**: A5 passes; A6 stays green; `python3 scripts/check_project.py tests/fixtures/demo-project --strict` still exits 0.

- [x] T009 [US2] *Fixture guard* **A4**: run `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — exits 0, unchanged. No document in the shipped corpus carries `nature:` yet, so this proves the new validation is invisible to every project on disk.

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

- [x] T010 🔴 [US3] Add the wave-B cases to `tests/test_check_project.py`:
  - **B1** — a card whose `subtopic:` is one **all** of whose `References:` resolve to `nature: experience` documents, and which carries **no** `source:`, is an **error** naming **the card file, the card index and the subtopic**
  - **B2** — the same card **with** `source:` passes
  - **B3** — *the "all, not any" rule*: a subtopic with one experience reference **and** one ordinary reference does **not** make its cards errors. This is its own case, not a corollary of B1
  - **B4** — *regression guard*: `test_a_minimal_project_is_clean` and the existing count assertions are unchanged by the new return values

  **RED**: B1 fails on its assertion. B2, B3, B4 are guards.

  **Call `check_project.check()`, not the internal functions.** T011 changes the signatures of `check_knowledge`, `check_catalog` and `check_cards`; a case that calls one of them directly goes red on a `TypeError` from a signature that does not exist yet, which constitution XI says does **not** count as red. Driving the whole run through `check()` — the way the existing wave-A cases do — makes B1 fail on the **error count**, which is the assertion.

- [x] T011 [US3] In `scripts/check_project.py`, thread the experience set down the road `sparse` already travels (`:380`, `:425-426`, `:428`, `:690`, `:958`, `:1180-1181`) — **do not invent a second mechanism for the same shape of fact**:
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

- [x] T012 🔴 [US1] Add `check_sources_skill_reads_the_goal()` to `scripts/check_docs.py`, wire it into `main()`, and add cases C1–C3 to `tests/test_check_docs.py` using the `read_skill` monkeypatch seam (`scripts/check_docs.py:357`) so every negative case runs against **synthetic** skill text:
  - **C1** — a `sources` skill that never names `goal.md` is reported
  - **C2** — one that names `goal.md` but never says the assessment is **advisory** / never blocks is reported
  - **C3** — one that does not say the assessment happens **at registration** and is **not re-run on a listing** is reported (FR-008 + research.md § R1 — the accepted no-back-fill gap)

  **RED**: `python3 scripts/check_docs.py` exits 1 against today's 55-line `skills/sources/SKILL.md`, which names none of it.

- [x] T012a 🔴 [US1] Extend `check_sources_skill_reads_the_goal()` — **T012's function; no new function** — and add cases **C6–C9** to `tests/test_check_docs.py`, each against synthetic skill text through the `read_skill` seam, each its **own** case so a failure names which rule left the prompt:
  - **C6** — a `sources` skill that does not say an off-goal warning names the source `id` **and** the line of `goal.md` it conflicts with is reported (FR-003)
  - **C7** — one that does not say the assessment reasons from `kind`/`depth` **and says which of the two it used** is reported (FR-005)
  - **C8** — one that does not say that with **no `goal.md`** there is no assessment and no warning, and **at most one** `/learning-goal` pointer per run, is reported (FR-006)
  - **C9** — one that does not say the skill never invents a claim about a source it has not looked at, and says so where it reasons only from the URL, the `note` and the `type`, is reported (FR-009)

  **RED**: all four fail against today's 55-line `skills/sources/SKILL.md`, which states none of them. **GREEN**: **T014**, which writes exactly these four sentences into the prompt anyway.

  **What these four gates are, exactly — read this before believing the routing table.** Each asserts that **the rule is stated in the prompt**, and nothing more. C6 cannot see a warning; C7 cannot see which of `kind`/`depth` a run actually reasoned from; C8 cannot count the pointers a run emitted; C9 cannot see whether a claim was invented. They are **drift detectors**: after this feature, an edit that drops one of these four sentences from `skills/sources/SKILL.md` fails a gate instead of failing nothing. The **behavioural** half of each stays on its named row — 4b/4f (FR-003), 4a/4b/4c (FR-005), 4i (FR-006), 4a (FR-009) — and plan.md § *Which gate holds which requirement* says so in both columns rather than letting the check column read as coverage.

- [x] T013 🔴 [US1] Add `check_sources_skill_states_the_archive_reach()` to `scripts/check_docs.py`, wire it into `main()`, and add case **C4** to `tests/test_check_docs.py`: a `sources` skill that does not state the archive reach — `depth: 1`, the index page plus same-domain linked posts, **capped at 20** — is reported (FR-029).

  **RED**: fails against the shipped skill. Separate function and separate task from T012 because it is a separate claim; same file, so **not** parallel with T012.

- [x] T014 [US1] Write the `## Goal fit` section into `skills/sources/SKILL.md` until C1–C4 pass (**C5**, the shipped-skill guard). It must carry: reading `goal.md` before writing an entry (FR-001); the assessment is **advisory and never blocking**, the entry is written whatever the verdict and the run does **not** pause to ask (FR-002); the warning names the source `id` **and** the `goal.md` line (FR-003); the judgement is about *this source for this goal*, never about the subject or the publisher (FR-004); it reasons from `kind`/`depth` and **says which of the two it used** (FR-005); with **no `goal.md`** there is no assessment and **at most one** `/learning-goal` pointer per run, never one per source (FR-006); nothing is persisted — no `fit:`, no `assessed:`, no timestamp (FR-007); a listing does not re-assess, and a goal written later does not re-judge the register (FR-008, research R1); never invent a claim about a source it has not looked at — where it reasons only from the URL, the `note` and the `type`, it says so (FR-009); and the archive-reach sentence (FR-029).

  **Tone precedent to copy**: `skills/catalog/SKILL.md:60-67` — said once, "do not turn it into a warning and do not repeat it".

  **GREEN**: C1–C5 **and C6–C9** pass.

**Checkpoint**: piece A's rules are in the prompt and two checks hold them.

---

## Phase 6 — Wave D: piece C in the prompt — C1 the neutral contract, C2 the practitioner addendum

**Serves**: FR-016 – FR-027, FR-030, FR-033, FR-035, FR-039, FR-040, US4 ·
**plan.md** wave D · **contract**: [contracts/discovery-proposal.md](contracts/discovery-proposal.md)

**The separability requirement (FR-039, SC-016) is the point of this wave.** Two
check functions, never one. **Zero** C1 assertions may name practitioner
material, an incident, a post-mortem or a company blog. Deleting the practitioner
sub-section from the **shipped** `skills/sources/SKILL.md` must fail **exactly
one** check — which is what **T018a** excises and asserts, against the real file
and by heading, rather than against text a test author wrote to pass.

<!-- sequential -->

- [x] T015 🔴 [US4] Add `check_sources_skill_carries_the_discovery_contract()` — **C1, material-class neutral** — to `scripts/check_docs.py`, wire it into `main()`, and add cases **D1, D1a–D1i, D2–D4 and D8** to `tests/test_check_docs.py` via the `read_skill` seam:
  - **D1** — a `sources` skill with no `--discover` at all is reported
  - **D1a** — one carrying everything **but** the found/shown counts grouped by goal area, with **every** area listed including the empty ones, is reported (FR-027)
  - **D1b** — one missing the caps — ≤ 3 per area and ≤ 10 per run — is reported (research R3)
  - **D1c** — one missing "one **sentence**, never a number" for credibility is reported (FR-018)
  - **D1d** — one missing the paywalled/login-gated rule (reported as found, never proposed, credentials never entered) is reported (FR-023)
  - **D1e** — one missing "a source already in `sources.yaml` is never proposed" is reported (FR-024)
  - **D1f** — one missing "no `goal.md` ⇒ nothing to search for" is reported (FR-025)
  - **D1g** — one missing "no network ⇒ report, write nothing, exit clean" is reported (FR-026)
  - **D1h** — one missing "picked entries go through the ordinary registration path" is reported (FR-020)
  - **D1i** — one missing "the network is reached **only** in discovery mode" is reported (FR-033)

    **One negative case per rule, and that is the point.** These ten used to be
    ten assertions inside the single case D1, whose synthetic input was a skill
    missing *everything* — so a check function that forgot to assert, say,
    FR-024 or the ≤ 10 cap would have passed anyway. Each case above hands the
    check a skill carrying **everything but that one rule**, so the failure
    message names the rule that broke. FR-035 is **not** in this list: T020's
    **E3** owns it, and asserting it twice means one dropped sentence fails two
    checks.
  - **D2** — one missing the *"writes nothing until the user picks"* rule is reported (FR-016)
  - **D3** — one missing the *"never invent"* rule is reported (FR-021)
  - **D4** — one missing the refusal to write into `knowledge/` or to create a `type: research` entry, or missing the `/research-gaps` seam, is reported (FR-022)
  - **D8** — one whose candidate shape does not require every candidate to **name which class of material it is** is reported (FR-017). **No new function**: this assertion lives inside the neutral check. It asserts the class is *named*, **never which classes exist** — no list, no vocabulary, no filter (FR-040)

  **The spelling `--discover` is load-bearing** (research R4): it appears nowhere in the repository today, so it is an exact token. A bare `discover` would fire on `skills/catalog/SKILL.md:67` and `scripts/build_pdf.py:745`.

  **RED**: fails against the shipped skill, which has no discovery mode at all.

- [x] T016 🔴 [US4] Add `check_sources_skill_carries_the_practitioner_addendum()` — **C2, the one addendum this feature ships** — to `scripts/check_docs.py`, wire it into `main()`, and add case **D6** to `tests/test_check_docs.py`: a `sources` skill missing the practitioner addendum — the **primary-and-interested** property and the **selected-sample** property on the credibility sentence — is reported (FR-019). This is the **only** check in wave D that may name a class of material. Neither function reads the other's text.

  **RED**: fails against the shipped skill.

- [x] T017 [US4] *Guard* **D5** — add the neutrality case to `tests/test_check_docs.py` (test file only — no `scripts/` edit):
  - **D5** — *neutrality guard*: a **synthetic** skill whose practitioner sub-section has been **deleted** still passes **every** C1 assertion (D1, D1a–D1i, D2–D4 and D8). None of them names a material class, an incident, a post-mortem or a company blog

  **GUARD, not a red artifact — and deliberately not one.** D5 runs against **synthetic** skill text through the `read_skill` seam (`scripts/check_docs.py:357`), so the state of the shipped `skills/sources/SKILL.md` is irrelevant to it: once T015 has landed it passes immediately. The only way to make D5 go red would be to write a **non-neutral** C1 check — exactly the outcome FR-039 and SC-016 exist to prevent, so a red here would be the defect and not the discipline. It is a guard in the same sense as A3, A4, A6, B4, C5, D7, E4 and F4, and `checklists/gates.md` CHK020 lists **D5** among the guard rows. It must **stay** green. Do not "fix" the marker to 🔴.

  **D5 is a documented invariant, not a defect detector**, and it is worth saying which half of FR-039 each artifact carries: D5 stops a neutral check from quietly acquiring a practitioner assertion; **D5b (T018a)** is the half that tests SC-016 against the file that ships. Neither replaces the other.

- [x] T018 [US4] Write the `## Finding sources` section into `skills/sources/SKILL.md`, **class-neutral throughout**: the `--discover` entry (and its natural-language equivalents as the same entry), the proposal shape of [contracts/discovery-proposal.md](contracts/discovery-proposal.md) § *Shape of the proposal*, the caps (≤ 3 per area, ≤ 10 per run, **every** area listed), the six per-candidate fields including the **class of material** line — with examples and an explicit statement that a candidate may name a class the examples do not cover, and **no list to choose from** — the credibility sentence as one sentence and never a number, the three exclusions (unretrieved, paywalled, already registered), the two degraded paths (no `goal.md`, no network), "writes nothing until the user picks", "picked entries go through the ordinary registration path", and the `/research-gaps` seam.

  **Not written here** (FR-040): no class-selection argument, no way to ask for one class only, no class vocabulary. **Stop and flag** if a class list appears anywhere.

  **GREEN**: D1, D1a–D1i, D2–D4, D5 and D8 pass.

- [x] T018a 🔴 [US4] **D5b — separability, asserted against the file that ships.** Add the separability case to `tests/test_check_docs.py` (test file only — no `scripts/` edit). It does **not** use synthetic text:

  1. Read the **shipped** skill: `body = check_docs.read_skill("sources")`, before any monkeypatch.
  2. `assert ADDENDUM_HEADING in body`, where `ADDENDUM_HEADING = "### Practitioner material"` is a module-level constant in the test file. **This is the assertion the test is red on**, and it is the reason the excision is done **by heading** rather than by matching the addendum's prose: if T019 renames the heading, the test fails loudly with a message naming the heading it looked for, instead of silently excising nothing and passing.
  3. Excise: cut from the line that **is** `ADDENDUM_HEADING` up to (not including) the next line matching `^#{1,3}\s` — a heading of equal or higher level — or to the end of the file.
  4. `monkeypatch.setattr(check_docs, "read_skill", lambda name: excised if name == "sources" else "")`.
  5. Run **both** wave-D checks over that text and assert:
     - `check_sources_skill_carries_the_practitioner_addendum()` reports ≥ 1 error;
     - `check_sources_skill_carries_the_discovery_contract()` reports **exactly zero**;
     - and, for the "**exactly one** check" half of SC-016, that the same excised text is also clean under every other new check that reads `skills/sources/SKILL.md` **that exists at this point in the sequence** — `check_sources_skill_reads_the_goal()` (T012, T012a) and `check_sources_skill_states_the_archive_reach()` (T013). **One of four checks fails; three stay green.**

  **Four here, five at T021 — assert only what exists.** The fifth check that reads this file, `check_sources_skill_states_the_explicit_request()`, is first written at **T020**. Naming it in step 5 now would make D5b raise `AttributeError` at T019 — the task that is meant to green it — which constitution XI does not count as a test outcome at all. **T021 extends step 5 to the fifth check** once both the check (T020) and the sentence it reads (T021) exist. Do not add it earlier.

  **RED**: fails on step 2 — the shipped `skills/sources/SKILL.md` carries no `### Practitioner material` heading, because T019 has not written it yet. **GREEN**: T019.

  **Why this is not the guard it used to be.** D5b previously ran against synthetic text through the `read_skill` seam, which made "the state of the shipped `skills/sources/SKILL.md` is irrelevant to it" true — and that is precisely the property SC-016 is about, discarded. SC-016 reads *"deleting the addendum from `skills/sources/SKILL.md` fails exactly one check and leaves the neutral checks green"*: a claim about the **file that ships**. The neutral check greps the whole skill body, so a token it demands that happens to be stated only inside the addendum sub-section would make SC-016 false, and a synthetic D5b — written by the same author, against text that author wrote to pass — would never notice. That is the assertion-green-by-construction shape constitution XI forbids. Reading the real file and cutting by heading is what makes FR-039's separability claim **mechanically** true rather than dependent on where the implementer happened to put each sentence.

  **Placed after T018 deliberately.** Before T018 the shipped skill has no `## Finding sources` section either, so D5b would be red for two reasons at once and the message would not say which. After T018 the neutral section exists and the addendum does not, so the red is exactly one thing: the heading is missing.

- [x] T019 [US4] Write the **practitioner addendum** as its own clearly separable sub-section under `## Finding sources` in `skills/sources/SKILL.md` (FR-019): for practitioner material the credibility sentence must additionally name that a company account of its own incident is a **primary source and an interested one**, and that published incidents are a **selected sample**. A candidate that is *not* practitioner material is **not** held to either property.

  **The heading is a fixed string and T018a reads it**: the sub-section opens with the line `### Practitioner material`, spelled exactly that way, at `###` level, under `## Finding sources`. Renaming it is allowed only together with `ADDENDUM_HEADING` in `tests/test_check_docs.py` — which is why T018a asserts the heading first and fails by name rather than silently excising nothing.

  **GREEN**: **D6, D7 and D5b** pass — both wave-D checks are green against the shipped skill, and excising the `### Practitioner material` sub-section from the **real** file now fails exactly one of the **four** checks that read it at this point. The fifth arrives at T020/T021, which is where D5b's assertion is widened.

**Checkpoint**: two separate checks, one neutral and one addendum, and the neutrality is asserted rather than asserted-about.

---

## Phase 7 — Wave E: piece D, the silence

**Serves**: FR-035 – FR-037, SC-015, US4 · **plan.md** wave E

**These gates are C1-level.** They are about the entry condition, which is the
same whatever a candidate turns out to be. **No assertion in this wave names a
class of material**, and a later addendum touches none of it (FR-039).

**Two check functions, not one** (plan.md § Test plan first, wave E). E3 asserts
a **presence** in the one skill this feature rewrites; E1/E2/E4 assert an
**absence** across the five skills it otherwise leaves alone — FR-037's four
plus `skills/learning-goal/SKILL.md` (case E2a). Opposite polarity,
different blast radius: one function holding both could not produce a failure
message that says which of the two rules broke. Each function gets its own
red-then-green pair below.

<!-- sequential -->

- [x] T020 🔴 [US4] Add `check_sources_skill_states_the_explicit_request()` — the **positive substring gate** on `skills/sources/SKILL.md` — to `scripts/check_docs.py`, wire it into `main()`, and add case **E3** to `tests/test_check_docs.py` via the `read_skill` seam (`scripts/check_docs.py:357`):
  - **E3** — a `sources` skill that does not state that discovery is entered **only** on an explicit request, and that an **ordinary run** (register, list, remove) neither enters nor mentions it, is reported (FR-035, FR-036)

  **RED**: E3 fails against the shipped 55-line `skills/sources/SKILL.md`, which says nothing of the kind.

  Shape to copy: `check_print_skill_relays_setup()` (`scripts/check_docs.py:363-374`), the file's existing positive gate on one named skill.

- [x] T021 [US4] Add the explicit-request and silence rules to `skills/sources/SKILL.md`: discovery is entered **only** on an explicit request at invocation, never started by itself, never offered as a follow-up at the end of an ordinary run, never the default of any invocation (FR-035); and a run that registers, lists or removes **neither enters nor mentions it** — no candidate, no proposal, no closing line suggesting the user could go looking (FR-036).

  **GREEN**: E3 passes. **And D5b (T018a) is extended here**: now that `check_sources_skill_states_the_explicit_request()` exists (T020) and the sentence it reads is in the file, add it to step 5's list of checks the excised text must be clean under. D5b then asserts **one of five fails, four stay green** — SC-016's "exactly one" over the complete set of checks that read `skills/sources/SKILL.md`. Re-run `pytest tests/test_check_docs.py` and confirm D5b is still green.

- [x] T021a 🔴 [US4] Add `check_discovery_is_not_offered_elsewhere()` — the **negative token gate** over `skills/ingest/SKILL.md`, `skills/catalog/SKILL.md`, `skills/cards/SKILL.md`, `skills/print/SKILL.md` **and `skills/learning-goal/SKILL.md`** — to `scripts/check_docs.py`, wire it into `main()`, and add cases E1, E2, E2a and E4 to `tests/test_check_docs.py`:
  - **E1** — `--discover` appearing in `skills/catalog/SKILL.md` is reported, **naming the file**
  - **E2** — the same for `ingest`, `cards` and `print`
  - **E2a** — the same for **`learning-goal`**. It is the fifth gated file, added because it is one of the two skills whose wrap-up already points the user at another step, and because `--discover` occurs nowhere in it today, so the token is exact there too. `/research-gaps` is **not** in the set and cannot be: T006 writes `/sources --discover` into it deliberately (FR-034's seam), so a token gate would fire on the sentence the feature asks for. See the residual-risk note below
  - **E4** — *shipped-repo guard, green from the start*: the five gated skills carry no `--discover`. The point is that it **stays** green

  **RED**: E1 and E2 are the assertions that prove the gate fires — they run against **synthetic** skill text carrying `--discover` (the `read_skill` seam), the same shape as wave G's G1/G2, which also pass immediately and are what prove the scoping. E4, the shipped-repo half, is green from the start and must **stay** green; its green partner is T021b. This function reads `skills/sources/SKILL.md` **never** — that file is T020's, and neither of the two wave-E functions reads the other's text.

  **Placed after T021 deliberately**: `--discover` first exists in the repository once T018 and T021 have written it into `skills/sources/SKILL.md`, so this is the point from which the absence elsewhere becomes a thing that can drift.

  **Stated limit** (plan § Risks, accepted rather than hidden): this is a **token** check, not a semantic one. It catches `--discover` in another skill — the form the drift actually takes, a pointer somebody adds. It does **not** catch the paraphrase *"you could go looking for more material"*. That case is `docs/testing.md` row **12-vi**, named there with its FR number.

  **Residual risk, stated precisely rather than left implicit — `/research-gaps` is not token-gated and cannot be.** FR-037 names four skills; T006 writes `/sources --discover` into a fifth, `skills/research-gaps/SKILL.md`, because FR-034 asks for the seam. That is the skill whose wrap-up already says *"If the user wants their own material instead, `/sources` is the way"*, so it is the likeliest place for a closing *"or run `/sources --discover`"* to appear. Three things hold it, and none of them is a token gate: (1) T006's rewrite is **one paragraph**, and its content is gated by `check_network_claim_is_not_exclusive()`; (2) row **12-vi** now runs `/research-gaps` as well as `/sources` → `/ingest` → `/catalog` → `/cards`, so a pointer in a real run is caught by a named row; (3) spec § Assumptions records the exclusion so it reads as a decision rather than an oversight. `/learning-goal` had the same hole and it is closed by **E2a** above. What remains uncovered is a paraphrase inside `skills/research-gaps/SKILL.md` that row 12-vi's run happens not to emit. **Accepted.**

- [x] T021b [US4] *Guard* **E4**: run `python3 scripts/check_docs.py` and confirm `check_discovery_is_not_offered_elsewhere()` reports nothing now that `skills/sources/SKILL.md` carries the discovery mode — no pointer leaked into `ingest`, `catalog`, `cards`, `print` or `learning-goal`. This is the gate's standing obligation, and it is restated where the four other prompts are edited (**T024**, the FR-037 clause) and where the diff is scope-checked (**T043**).

  **GREEN**: E1, E2, E2a and E4 all green, with E3 still green from T021.

**Checkpoint**: the negative half of the feature has a gate of its own, separate from the positive one, and its limit is written down.

---

## Phase 8 — Wave F: the experience-report rule in three prompts

**Serves**: FR-010 – FR-015, FR-030, US3 · **plan.md** wave F

<!-- sequential -->

- [x] T022 🔴 [US3] Add `check_skills_carry_the_experience_rule()` to `scripts/check_docs.py`, wire it into `main()`, and add cases F1–F3 to `tests/test_check_docs.py` via the `read_skill` seam:
  - **F1** — an `ingest` skill that does not name `nature: experience` is reported
  - **F2** — a `catalog` skill that has lost the experience-report rule, or the FR-013 material-base warning, is reported (FR-010; FR-013's four contents; FR-014 rule-versus-case)
  - **F3** — a `cards` skill that has lost the attribution rule, **or the FR-013 material-base warning**, is reported (FR-010; FR-011 via the existing `source:` key; FR-012 the scale; **FR-013 — it binds `/cards` as well as `/catalog`**, US3 scenario 5, and the assertion is the same one F2 makes of `catalog`)

  **RED**: fails against all three shipped skills.

<!-- parallel-group: 2 (max 3 concurrent) -->

- [x] T023 [P] [US3] `skills/ingest/SKILL.md` — write `nature: experience` into the **frontmatter format block at lines 92-111** and add the rule for when to write it and when **not** to: a document whose **subject is a reported case** gets `nature: experience`; everything else gets **no `nature:` key at all** — not `nature: reference`, not `nature: none`, absence **is** the other state; a reference work with one anecdote in it is **not** marked, because `nature:` is one value about the whole document and never a per-paragraph judgement.

  **⚠ Hazard**: `tests/test_testdata.py:265-273` parses this file **literally** around lines 27-28 for the default-pattern text. Keep every edit inside the frontmatter block and the extraction rules. **Do not reflow the paragraph near line 27.**

- [x] T024 [P] [US3] `skills/catalog/SKILL.md` — read `nature: experience`: place the document normally, but report a required topic covered **only** by experience reports rather than presenting single-case coverage as coverage of the rule (FR-014), and warn about the **material base** of a subtopic that rests only on such reports, carrying all four of FR-013's contents in the skill's own words — which subtopic and what it rests on, why that base is skewed written out rather than named, what it means for the cards, and what would balance it. **Do not prescribe a phrase**; a run that says only "published incidents are a selected sample" does not satisfy FR-013. The worked example is in [spec.md § FR-013](spec.md). That report **must not** become a suggestion to run discovery (FR-037); a `Status: gap` subtopic's one pointer stays `/research-gaps`, exactly as today.

- [x] T025 [P] [US3] `skills/cards/SKILL.md` — read `nature: experience`: phrase the card **about the reported case**, name that case through the existing optional `source:` key, never as an unattributed general rule (FR-010, FR-011), and carry the **scale or circumstances** the fact depends on rather than dropping them (FR-012).

  **And the FR-013 half that belongs to `/cards`**: when `/cards` reports on a subtopic that rests **only** on incident and experience reports, it carries the **same** material-base warning `/catalog` does — all four contents, in its own words, no prescribed phrase (spec US3 scenario 5; the worked example is in [spec.md § FR-013](spec.md)). It is a warning about the state of the sources: it never blocks a card, and it never becomes a suggestion to run discovery (FR-037). Check **F3** asserts it; manual row **12-iv** runs it.

  *Genuinely parallel*: T023, T024 and T025 touch three different `SKILL.md` files, all after T022, with no dependency between them.

<!-- sequential -->

- [x] T026 [US3] *Guard* **F4**: `python3 scripts/check_docs.py` reports nothing for `check_skills_carry_the_experience_rule()` — the three edited skills pass.

**Checkpoint**: pieces B and C are in the prompts, and waves A–G all have their checks. Commit.

---

## Phase 9 — Wave H: the fixture

**Serves**: US3, SC-009 · **plan.md** wave H · **Only once A–G are green.**

**The demo project is the one versioned corpus. No second fixture, at any point**
(constitution VII & XI, gates CHK050). All new material is **invented archipelago
content** — nothing quoted from anyone.

<!-- sequential -->

- [x] T027 **Before touching the fixture**: run `python3 scripts/check_project.py tests/fixtures/demo-project --strict` and record the exact output. This is its own step, per plan.md § Risks, because `catalog/topics.md` carries `Status:`, `Parents:`, `Also covers:`, `Related:` and `Term:` invariants that the new subtopic could disturb.

- [x] T028 [US3] New `tests/fixtures/demo-project/raw/field-notes/<incident>.md` — an invented archipelago incident write-up (a harbour-office account of a grounding or a signal failure). Plain markdown, committed text, no binary, no generator needed. It joins the seven files already in that folder.

- [x] T029 [US3] New `tests/fixtures/demo-project/knowledge/field-notes/<incident>.md` — the ingested twin of T028, carrying `source: field-notes`, `path:`, `ingested:` and **`nature: experience`**. It is the **only** document in the corpus with the key at all, which is what makes wave A's A3 guard meaningful.

- [x] T030 [US3] `tests/fixtures/demo-project/catalog/topics.md` — one new `###` subtopic under the existing `## Signals, flags and the radio` topic (line 73), whose **only** reference is the T029 document. Placed under that topic deliberately, so it serves a required topic already in the fixture's `goal.md`. Keep the file's `Status:`/`Parents:`/`Also covers:`/`Related:` conventions intact. **Write no `Term:` line on it.** A `Term:` line obliges an anchor card naming the concept (check A-1) and moves the "**seven** such lines" count in `tests/fixtures/demo-project/README.md`; the subtopic needs neither, and leaving it off is what the fixture already does for `Settlements` and `Rules of use`.

- [x] T031 [US3] `tests/fixtures/demo-project/cards/signals.yaml` — **exactly one** card under the new subtopic, carrying `source:` naming the case, phrased about the reported case rather than as a general rule, with a **fresh, unique five-character Crockford Base32 `id`**, following `CLAUDE.md`'s card style and Typst escaping. **`cards/signals.yaml` specifically**, so `TIDES_CARD_COUNT` (`tests/test_e2e.py:49`) does not move.

  **Exactly one, not "one or two" — the second card breaks an e2e assertion.** `cards/signals.yaml` holds **7** cards today, and `--topic Signals` is what `test_three_dividers_share_a_sheet_with_a_short_deck` (`tests/test_e2e.py:1301`) builds. At 16 up an A8 sheet is 4 x 4 of 71.75 x 50 mm inside a 5 mm margin on a 297 x 210 sheet, and a one-row block of three dividers is `1 x (50 + 1.5) = 51.5` mm tall with `leitner.GAP_MM = 8` above and below it (`scripts/build_pdf.py:216-257`, `divider_block`). At **8** cards the deck fills 2 rows — `5 + 2 x 50 = 105`, and `105 + 8 + 51.5 + 8 = 172.5 <= 210` — so the block still shares the sheet and the test holds. At **9** cards it fills 3 rows — `5 + 3 x 50 = 155`, and `155 + 8 + 51.5 + 8 = 222.5 > 210` — so the block opens a further sheet and the test fails. One card keeps that assertion true; two do not. If a second card is genuinely needed, it is a **stop-and-flag** back to plan.md, not a quiet edit to a spec-008 test.

<!-- parallel-group: 3 (max 3 concurrent) -->

- [x] T032 [P] [US3] `tests/fixtures/demo-project/README.md` — add the row to the **raw-material table** saying what the new material is for and which failure mode it exercises. Then **re-read two sentences of that file for staleness**: `catalog/topics.md` carries "**seven**" `Term:` lines (T030 adds none, so the count stands — confirm it) and the opening paragraph's account of the card files (T031 adds a card to an existing file, so no file count moves). Change a number only if T030/T031 actually moved it.
- [x] T033 [P] [US3] The card-count edits. **Four files' worth of literals, not one** — the "derived counts follow automatically" claim is true of the constants and false of three assertions that were written when 32 happened to be a multiple of 16.

  1. **`tests/test_e2e.py:27`** — move `DEMO_CARD_COUNT` from `32` to **33**. Confirm `TIDES_CARD_COUNT` (`:49`) is **unchanged**. `DEMO_A7_PAGES` / `DEMO_A8_PAGES` / `DEMO_A7_SHEETS` / `DEMO_A8_SHEETS` do follow from `sheet_pages()` — do not hand-edit those.
  2. **`tests/test_check_project.py:164`** — `assert counts["cards"] == 32` in `test_the_demo_project_has_all_four_artifacts` is a **literal**, not a derived count. Move it to 33. Plain `pytest` catches this one, but it is edited here rather than discovered at T044.
  3. **`tests/test_e2e.py:1285`, `test_four_dividers_open_a_further_page_on_the_demo_deck`** — **licensed edit, see the arithmetic below.** Build the case from `--topic Tides` instead of the whole deck, keep the `+ 2` expectation, and add `assert 5 <= TIDES_CARD_COUNT <= 16, "the further-sheet branch needs 2-4 filled rows on one sheet"` above it so a future move of `cards/tides.yaml` fails with a message rather than an arithmetic surprise. Rewrite the docstring: the count it cites ("31 cards fill three-and-a-bit rows of sheet 2") describes a deck that no longer exists.
  4. **`tests/test_e2e.py:1325`, `test_the_run_says_which_paper_case_it_is_in`** — its `added` half asserts `"further sheet" in added.stderr` for the **whole deck** at 4 dividers, which is the same broken branch. Move that half to `--topic Tides` too. Its `shared` half (`--topic Signals`, 3 dividers) is unaffected, because T031 keeps `signals.yaml` at 8 cards.
  5. Two **docstrings** say "32 cards" — `:464` and `:1220`. Correct them; neither is an assertion.

  **The arithmetic, verified against `scripts/build_pdf.py:216-257` (`divider_block`) and `scripts/leitner.py` rather than asserted.** A8 is the 4 x 4 grid on a 297 x 210 sheet with a 5 mm margin, so a card is 71.75 x 50 mm and 16 fit; `GAP_MM = 8.0`, `GROWTH_MM = 1.5`, `LAYOUT[4] = (2, 2)` and `LAYOUT[3] = (3,)`. A four-divider block is therefore `2 x 51.5 + 8 = 111.0` mm tall and a three-divider block `51.5` mm. The block shares the last sheet when `filled_to + gap + block_h + gap <= sheet_h`, where `filled_to = margin + used_rows x card_h`.

  | Deck | `used_rows` | `filled_to` | needed | fits? | result |
  |---|---|---|---|---|---|
  | 32 cards, 4 dividers | `32 % 16 = 0` → 4 | 205 | `205 + 8 + 111 + 8 = 332` | 332 > 210 → **no** | a further sheet: `DEMO_A8_PAGES + 2`. **This is why the assertion passes today** |
  | **33** cards, 4 dividers | `33 % 16 = 1` → 1 | 55 | `55 + 8 + 111 + 8 = 182` | 182 ≤ 210 → **yes** | the block **shares** sheet 3: pages stay `DEMO_A8_PAGES`. The `+ 2` assertion **fails** |
  | 34 cards, 4 dividers | `34 % 16 = 2` → 1 | 55 | 182 | yes | shares — the same failure |
  | **11 Tides cards, 4 dividers** | `11 % 16 = 11` → 3 | 155 | `155 + 8 + 111 + 8 = 282` | 282 > 210 → **no** | a further sheet: `sheet_pages(TIDES_CARD_COUNT, A8_UP) + 2`. **This is the replacement** |
  | 8 Signals cards, 3 dividers | `8 % 16 = 8` → 2 | 105 | `105 + 8 + 51.5 + 8 = 172.5` | 172.5 ≤ 210 → **yes** | shares — `test_three_dividers_share_a_sheet_with_a_short_deck` still holds |

  **Why the edit rather than a card count that keeps the assertion true.** The alternative was to keep the deck a multiple of 16, which means adding **16** cards for one invented incident write-up — a fixture change out of all proportion to the requirement, and one that would break the card-style rules it is supposed to demonstrate. The Tides subset is the honest repair: 11 cards fill three of four rows on one sheet, which is the "no room left" branch the test was written for, and `TIDES_CARD_COUNT` is the one count this feature pins as unchanged. The `--topic Signals` companion test keeps the "shares the sheet" branch, so both branches of `divider_block` stay covered. This edit reaches `tests/test_e2e.py`, which is **spec-008's** territory; it is licensed **here**, in writing, rather than made silently at T035.

  **It is invisible to plain `pytest`.** `tests/test_e2e.py` skips without a typesetting engine, so items 3 and 4 surface only under `LERNKARTEN_E2E=1` — which is T035, and which is why T035 is a task rather than a footnote.

  *Genuinely parallel with T032*: a fixture README on one side; `tests/test_e2e.py` and `tests/test_check_project.py` on the other. No shared file, both depending only on T031 being final.

<!-- sequential -->

- [x] T034 [US3] Run `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — exits 0, and the count line names the new subtopic and cards. Compare against T027's recorded output.

- [x] T035 **Its own task, not a footnote**: `python3 scripts/make_testdata.py && LERNKARTEN_E2E=1 pytest tests/test_e2e.py`. `DEMO_CARD_COUNT` moved in T033, and `tests/test_e2e.py` **skips without a typesetting engine**, so a wrong count is invisible to a plain `pytest` run and would ship undetected. This is **required for this feature**, not optional (quickstart § 4, gates CHK046).

**Checkpoint**: the corpus carries one experience report end to end, and the e2e count is proven.

---

## Phase 10 — Wave I: the prompts, driven for real

**Serves**: US1, US3, US4, US5, US6 · **plan.md** wave I

Waves C–F made the checks pass against the prompt text. This wave proves the
prompts actually **run**: each skill is driven against a `scripts/demo.py`
scratch copy until the project it produces passes `--strict`.

**T037 and T038 are human-in-the-loop checkpoints. An implementing agent stops
at them and hands back.** Both require a live Claude session driving `/sources`
against a scratch project, and T037 additionally requires the network to be
turned off by hand. An agent cannot run a skill against itself in a user
session, and the failure mode is that it marks them done on the strength of the
prompt text it just wrote — the review's W-5. Everything both tasks verify is
also covered by Phase 13 (T050 – T053), so nothing is lost by stopping: what is
lost by *ticking* them is the only evidence that the prompts run at all. **T036
is not a checkpoint** — it is an ordinary edit gated by `check_skills`, and it
is the first thing wave I does.

<!-- sequential -->

- [x] T036 [US6] **First thing in wave I**: rewrite the `description` in `skills/sources/SKILL.md:2-4` so it names **both jobs** — registering/listing/removing **and** finding sources for a stated goal. It is gated **four ways** by `check_skills()` (`scripts/check_docs.py:79-121`) and every one must survive: `name: sources` equals the folder name; the description is **≥ 20 characters**; it contains the word **`Triggers`**; and it contains the domain word **`flashcard`**. Add `/sources --discover` to the trigger list. Run `python3 scripts/check_docs.py` immediately — `check_skills` catches a miss at once.

- [x] T037 🧑 **HUMAN CHECKPOINT — stop here, do not tick from the prompt text** [US1] [US4] [US5] `python3 scripts/demo.py /tmp/lk-demo --force`, then drive `/sources` against it in a real Claude session — a registration, a bare listing, a removal, and `/sources --discover` — and edit `skills/sources/SKILL.md` until every wave C, D and E assertion passes **and** `python3 scripts/check_project.py /tmp/lk-demo --strict` exits 0 after accepting a candidate (SC-006). Confirm `sources.yaml` carries **no** verdict key of any kind (FR-007, SC-001).

- [x] T038 🧑 **HUMAN CHECKPOINT — stop here, do not tick from the prompt text** [US3] Drive `/ingest` → `/catalog` → `/cards` against the same scratch copy and edit `skills/ingest/SKILL.md`, `skills/catalog/SKILL.md` and `skills/cards/SKILL.md` until wave F passes **and** `python3 scripts/check_project.py /tmp/lk-demo --strict` exits 0. Confirm the incident document gets `nature: experience` and the handbook document gets **no `nature:` key**.

**Checkpoint**: the prompts do what the checks say they do.

---

## Phase 11 — Wave J: docs and the named manual rows

**Serves**: FR-032, SC-011, SC-012, US6 · **plan.md** wave J

**Twenty-five rows**: 20 `/sources` rows (4a–4s plus **4n-i**) plus 5 pipeline
rows (8m, 9f, 12-iv, 12-v, 12-vi). It was twenty-three until the FR-013
remediation of 2026-09-08 gave the `/cards` half of FR-013 its own row
(**12-iv**), and twenty-four until the 2026-09-08 review remediation split row
**4n**: FR-024 is performable on demand and FR-021/FR-023 are not, so they no
longer share a row that a tester would have to mark "pass" for a stimulus they
cannot produce. plan.md and quickstart.md say twenty-five too, and the older
"~22"/"21"/"23"/"24" counts are gone. Every row carries its FR
number **inside the row**, in the established `**run output (FR-0xx):**` form
(`docs/testing.md:203`), so `docs/testing.md` is traceable without the plan open
beside it (gates CHK007).

<!-- sequential -->

- [x] T039 [US6] `docs/testing.md` — insert the twenty `/sources` rows **after line 193** (the existing row `4`), in the table's `| # | Step | Do this | Expect |` shape:

  | Row | Covers |
  |---|---|
  | **4a** | FR-001, FR-005, FR-009 — the assessment names a required topic or area, and says which of `kind`/`depth` it used |
  | **4b** | FR-002, FR-003, **SC-002**, FR-005 weigh-down, SC-004 — scratch copy with `depth: awareness`; the warning names the id **and** quotes the goal line, the entry is written, **zero** confirmation prompts |
  | **4c** | FR-005 weigh-up — scratch copy with `depth: expert`; the same material is weighed up and the run **says so** |
  | **4d** | FR-004 — the warning says nothing about the subject or the publisher in general |
  | **4e** | FR-008 — a bare listing re-assesses nothing |
  | **4f** | FR-003, **SC-002** — a source matching an `## Out of scope` line: the warning names the source id and **quotes that line**; **zero** warnings say only that something looks off-goal |
  | **4g** | FR-007, SC-001 — after the run `sources.yaml` carries **no** verdict of any kind |
  | **4h** | FR-029 — the archive reach is stated at registration |
  | **4i** | FR-006, SC-003 — `rm goal.md`: no assessment, identical key set, **≤ 1** `/learning-goal` pointer per run |
  | **4j** | research R1 — a goal written **afterwards** produces no assessment for what is already registered, and nothing claims otherwise |
  | **4k** | FR-016 – FR-018, FR-027, FR-035, FR-039, FR-040, SC-007, SC-017 — the **neutral** proposal shape; **every** candidate names its class, the non-practitioner ones included; no candidate is dropped or renamed for naming a class no list contains, because there is no list, no class argument and no way to ask for one class. **What is decidable of FR-027**: the *shown* count equals the number of candidates listed, every goal area appears including the ones with nothing found, and *found* ≥ *shown*. **What is not**: the *found* number itself — the tester sees what the run printed and has nothing to check it against. Record it as read, not as verified |
  | **4l** | FR-016, SC-005 — decline everything: **zero** files created, **zero** modified |
  | **4m** | FR-020, FR-022, SC-006 — accept one: the ordinary path, the assessment fires, `--strict` exits 0 |
  | **4n** | FR-024 — register a source first, then run discovery: it is **not** proposed again. Performable on demand, and the only one of the three exclusions that is |
  | **4n-i** ⚠ | FR-021, FR-023 — **opportunistic, and it says so**. The stimulus is not the tester's to produce: discovery cannot be made to *find* an unretrievable or a paywalled candidate. What the tester does instead: open **every** proposed candidate's URL. A candidate that 404s, that is behind a paywall or a login, or whose page does not match its description **is a violation of FR-021 or FR-023** and the row fails. If none of the proposals is any of those, the row is **not evidence of conformance** — write "not exercised", not "pass". The row detects a violation; it cannot confirm compliance. The prompt-side halves are gated by **D3** (FR-021) and **D1d** (FR-023) |
  | **4o** | FR-025 — no `goal.md`: nothing to search for, points at `/learning-goal`, writes nothing |
  | **4p** | FR-026, SC-008 — no network (beside the existing `9d` at `:222`): reports, writes nothing, exits clean, **no traceback** |
  | **4q** | FR-036, SC-015 — a registration, a bare listing and a removal mention discovery **nowhere** |
  | **4r** | FR-033 — **the observable is the network, not the transcript**: with the machine offline (the same switch row 4p uses), run the same registration, the same bare listing and the same removal. All three must behave **exactly** as they did online — same entry, same listing, same removal, no error, no "could not reach" line (US5 scenario 3). A run that needs the network to register a source the user named fails this row. Read the transcript's tool calls as well — zero WebFetch / WebSearch / fetch of any kind — but the offline run is what decides it, because a transcript is a report and the network is a fact |
  | **4s** | FR-019, SC-007 — the **practitioner addendum**: a practitioner candidate additionally names primary-and-interested and selected-sample; a non-practitioner one is **not** held to those two properties |

**Two things about the ids**: `4s` sits between `4k` and `4l` in the table above
on purpose — it is `4k`'s addendum companion and is read beside it, though it is
the last id allocated in the 4-series. And the 12-series is contiguous: `12-iii`
already ships, and T040 adds `12-iv`, `12-v` and `12-vi`.

<!-- parallel-group: 4 (max 3 concurrent) -->

- [x] T040 [P] [US6] `docs/testing.md` — add the four pipeline rows beside the steps they belong to:

  | Row | Step | Covers |
  |---|---|---|
  | **8m** ⚠ | `/ingest` | FR-015 — the incident write-up gets `nature: experience`; the handbook document gets **no** `nature:` key |
  | **9f** | `/catalog` | FR-013, FR-014 — the material-base warning carries all four of FR-013's contents in the run's own words, and single-case coverage is not presented as coverage of the rule |
  | **12-iv** | `/cards` | FR-013 — the **`/cards`** half: a `/cards` run reporting on an experience-only subtopic carries the same four contents. **Id verified free**: the 12-series in `docs/testing.md` runs `12`, `12-i`, `12-ii`, `12-iii`, so `12-iv` is the next id and this fills the gap the plan used to skip |
  | **12-v** | `/cards` | FR-011, FR-012, SC-009 — every card names its case through `source:`, none states an unattributed general rule, the scale is kept |
  | **12-vi** | any | FR-037, FR-038, SC-014, SC-015 — a full `/sources` → `/ingest` → `/catalog` → `/cards` run with **no** `--discover`: zero mentions, zero extra entries. **Plus a `/learning-goal` run and a `/research-gaps` run in the same session**, because those are the two skills the `--discover` token gate does not bound: `/learning-goal` is gated from T021a onwards (case E2a) but its *paraphrase* is not, and `/research-gaps` **must** carry the token for FR-034's seam, so no token gate can hold it. Neither may end with a line offering to go looking |

  **And one existing row goes stale — count it, do not increment it**: row **5** (`docs/testing.md:194`) expects *"five files under `knowledge/field-notes/`"* from `/ingest field-notes`. That number was true at `51f0434` and has been **wrong on `main` ever since**: `tide-office-cover.md` (BUG-004), `chart-notes.md` (`92628bb`) and the generated `harbour-log.txt` (`scripts/make_testdata.py:287`) were added without it moving. So "five plus one" would ship a second wrong number.

  **Do this instead.** Run `python3 scripts/make_testdata.py`, then count the files under `tests/fixtures/demo-project/raw/field-notes/` **recursively** that `/ingest` turns into a document under `knowledge/field-notes/`, and write **that** number:

  - **count** every ordinary text/markdown file, including the one in `appendix/`;
  - **do not count** `empty.md` — the row itself says the empty file is reported, not invented;
  - **do not count** `diagrams/signal-flags.png` — it is a picture `chart-notes.md` links to, judged as that document's figure, not a document of its own;
  - **do count** generated `harbour-log.txt`, which is raw material like any other, which is why `make_testdata.py` has to have been run first.

  At the time of writing this task the count is **eight** today and **nine** once T028 lands. **Verify it at edit time rather than trusting that sentence** — the whole point of this instruction is that a hard-coded number in `docs/testing.md` rotted once already. Change the number and nothing else: the rest of the row (the `appendix/` file, the umlaut slug, the empty file reported and not invented) is unaffected. It is the only shipped row this feature's fixture work invalidates; the counts in rows 8a–8g are about other sources.

  **⚠ Row-id collision, already resolved — do not reintroduce it**: plan.md used to name this row **`8h`**, but `8h` is **taken** — `docs/testing.md:211` is a `/learning-goal` row. The 8-series runs `8a … 8l`, so the next free id is **`8m`**. The 2026-09-08 remediation corrected every `8h` in the feature artifacts (`plan.md` ×2, `quickstart.md`, `checklists/gates.md` CHK002), so this task only has to **write `8m`** into `docs/testing.md`. Do **not** ship a duplicate id.

- [x] T041 [P] [US6] `docs/workflow.md` — three edits, no step-count sentence touched: **Step 1** gains the ordering sentence (the goal-fit assessment happens at registration, so writing `goal.md` first is worth it, and a goal written later does not re-judge the register — research R1); **Step 2** names **both** jobs of `/sources`; **Step 5** states the seam between `/sources --discover` and `/research-gaps` (same network, different output — proposed sources to read versus synthesised documents written into `knowledge/`). Also update the knowledge-frontmatter description where it is given, to include the optional `nature:` key.

- [x] T042 [P] [US6] `README.md` — the `/sources` table row names **both** jobs (register/list/remove **and** find sources for a stated goal). The pipeline stays **seven** steps; change no step-count sentence.

  *Genuinely parallel*: `docs/testing.md`, `docs/workflow.md` and `README.md` are three different files. T040 follows T039 only because both write `docs/testing.md`, and T039 is complete before this group starts.

<!-- sequential -->

- [x] T043 [US6] Scope verification — confirm the diff touches **none** of: `docs/index.html` (the step strip at `:489-492` is a label, not a description — this is a recorded scoping decision, not an oversight), `assets/brand/*.typ`, the three rendered PNGs, `scripts/render_brand.py`, `tests/test_landing_page.py`, `.specify/memory/constitution.md`, `CLAUDE.md`, `docs/design.md`, `templates/*.typ`, `scripts/build_pdf.py`, `bin/lernkarten`. Confirm **seven steps** everywhere the pipeline is described (SC-011). Run `python3 scripts/check_docs.py` — `check_links` is the automated part of this wave.

**Checkpoint**: every run-output requirement has a **named** row carrying its FR number.

---

## Phase 12: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

<!-- sequential -->

- [x] T044 **The four PR gates**, in order, all green: `ruff check . && ruff format --check .` · `pytest` · `lernkarten check cards/example.yaml` · `python3 scripts/check_docs.py`. Ruff is not loosened; line length stays 100 (constitution XII).
- [x] T045 `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — exits 0.
- [x] T046 Confirm T035 (`LERNKARTEN_E2E=1 pytest tests/test_e2e.py`) has been re-run **after** the final fixture state, since `DEMO_CARD_COUNT` moved. Also run `pytest tests/test_testdata.py` — it parses `skills/ingest/SKILL.md` literally (`:265-273`) and is the guard against T023 reflowing the wrong paragraph.
- [x] T047 `python3 scripts/deps.py --check` / `lernkarten deps --check` — confirm the runtime dependency set is **still exactly** `pyyaml==6.0.3`. Confirm `requirements-dev.txt` is unchanged. If either moved, **stop and flag back to plan.md**.
- [x] T048 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries. Nothing was forced in with `git add -f`.
- [x] T049 Open the pull request from `feat/goal-fit-sources` (`main` rejects direct pushes). The description **must** carry the constitution VII note required by plan.md's Constitution Check row VII: the demo fixture was **extended, never duplicated**, with **invented** archipelago material, and nothing is quoted from anyone. Commit subjects use the repo prefixes (`feat:`, `skill:`, `test:`, `docs:`, `fix:`).

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
- [ ] T051 Run rows **4k – 4p, 4n-i and 4s** (piece C, discovery). **Not 4q and 4r** — those are piece D's silence rows and belong to T052, which is where they are run; splitting them here is what stops a tester running the same two rows twice. Check the **non-practitioner** candidates especially: they name a class too, and they are **not** held to the addendum's two properties. Decline everything and confirm zero files created and zero modified; then accept one and confirm `--strict` exits 0. Turn the network off for 4p. **Row 4n-i is opportunistic**: open every proposed URL, and if none is unretrievable or paywalled, write "not exercised" rather than "pass" — the row can catch a violation and cannot confirm compliance.
- [ ] T052 Run rows **4q, 4r, 12-vi** (piece D, the silence). A registration, a bare listing and a removal mention discovery nowhere; then a full `/sources` → `/ingest` → `/catalog` → `/cards` run with `--discover` never typed produces **zero** lines mentioning discovery — `/catalog`'s FR-014 report included — and a `sources.yaml` holding exactly the sources you named. **Then run `/learning-goal` and `/research-gaps` in the same session** and read their closing lines: neither may offer to go looking for material. Those two are row 12-vi's extension and they are the only cover the `--discover` token gate cannot give — `/learning-goal`'s paraphrase, and `/research-gaps` entirely, since T006 puts the token in it on purpose. For **4r**, turn the network off and repeat the registration, the listing and the removal: all three must behave identically to the online run.
- [ ] T053 Run rows **8m, 9f, 12-iv, 12-v** (piece B, the experience report). For 9f and 12-iv read the two warnings side by side: **both** `/catalog` and `/cards` must carry all four of FR-013's contents, in their own words, and neither may get away with the bare phrase "a selected sample". Confirm the incident document carries `nature: experience` and the handbook document carries **no** `nature:` key — not `nature: reference`, not `nature: none`.
- [ ] T054 Walk [checklists/gates.md](checklists/gates.md) CHK001 – CHK075 and check each item off. CHK003 – CHK006, CHK013 – CHK022 and section H (CHK071 – CHK075) are the ones this checklist exists for; a "no" is a defect in the artifact named in brackets, fixed **there** and not in review comments.

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

- `scripts/check_docs.py` is touched by **nine** tasks (T005, T012, **T012a**, T013, T015, T016, T020, T021a, T022) for **eight** new check functions — T012a extends T012's function with C6–C9 rather than adding a ninth. Two tasks that both edit it are **not** parallel, however unrelated the requirements.
- `scripts/check_project.py` is touched by T008, **T008b** and T011. Serialized.
- `tests/test_check_docs.py` is touched by eleven tasks (those nine plus the test-only T017 and T018a); `tests/test_check_project.py` by **four** (T007, **T008a**, T010, T033). Serialized within each file.
- `skills/sources/SKILL.md` is touched by T014, T018, T019, T021, T036, T037. Serialized — and it is the single busiest file in the feature.
- `docs/testing.md` is touched by T039 and T040. Serialized.
- A 🔴 task and the task that greens it. Ever.

### Parallel groups found — four, ten tasks

| Group | Tasks | Files, and why they are genuinely disjoint |
|---|---|---|
| 1 | T002, T003 | `scripts/install-hooks.sh` (git hooks) vs `scripts/make_testdata.py` (fixture binaries) — no shared file, both after T001 |
| 2 | T023, T024, T025 | `skills/ingest/SKILL.md`, `skills/catalog/SKILL.md`, `skills/cards/SKILL.md` — three different prompts, all gated by the one check T022 already landed |
| 3 | T032, T033 | `tests/fixtures/demo-project/README.md` vs `tests/test_e2e.py` + `tests/test_check_project.py` — a fixture README on one side, two test modules on the other, no shared file, both depending only on T031 |
| 4 | T040, T041, T042 | `docs/testing.md`, `docs/workflow.md`, `README.md` — three different docs; T040 follows T039 on the same file, and T039 is complete before the group opens |

That is **10 of 60** tasks parallelizable (T001 – T054 plus T008a, T008b, T012a, T018a, T021a and T021b). The rest is sequential, which is the
honest shape of a feature that lands in two Python files, two test modules and
five `SKILL.md` files.

---

## Requirement → task traceability

| Requirement | Tasks |
|---|---|
| FR-001, FR-002, FR-008 | T012 (C1–C3), T014 · T050 (rows 4a, 4b, 4e) |
| FR-003, FR-005, FR-006, FR-009 | **T012a** (C6–C9, *the rule is stated in the prompt* — nothing more), T014 · T050 (rows 4b/4f, 4a/4b/4c, 4i, 4a — the behavioural half) |
| FR-004 | *no automated assertion, deliberately* · T050 (row 4d) |
| FR-007 | **T008a, T008b** (`VERDICT_KEYS` in `check_project.py`) · T050 (row 4g) · [contracts/sources-yaml-unchanged.md](contracts/sources-yaml-unchanged.md) |
| FR-010 | T022, T024, T025 · T053 |
| FR-011 | T010, T011 (**error** in `check_project.py`) · T022, T025 · T053 |
| FR-012 | T025 · T053 |
| FR-013 | T022 (F2 **and F3**), T024 (`/catalog`), **T025** (`/cards`) · T053 (rows 9f **and 12-iv**) |
| FR-014 | T022, T024 · T053 (row 9f) |
| FR-015 | T007, T008 · T022, T023 · T029 · T053 (row 8m) |
| FR-016 – FR-018, FR-020 – FR-027 | T015 (D1, D1a–D1i, D2–D4, D8 — one case per rule), T018 · T051 |
| FR-019 (the one addendum) | T016, T019 · T051 (row 4s) |
| FR-028 | *withdrawn — no task* |
| FR-029 | T013, T014 · T050 (row 4h) |
| FR-030 | *is* T005, T012, **T012a**, T013, T015, T016, T020, T021a, T022 — nine tasks, eight check functions (T012a extends T012's) |
| FR-031 | *is* T007, T008, **T008a**, **T008b**, T010, T011 — plus the A3 absence guard and the A6 unknown-key guard |
| FR-032 | *is* T039, T040 |
| FR-033 | T015 (D1i), T018 · T052 (row 4r, the offline observable) |
| FR-034 | T005, T006 |
| FR-035, FR-036 | T015, T020 (`check_sources_skill_states_the_explicit_request()`), T021 · T052 |
| FR-037 | T021a (token half over five skills, `check_discovery_is_not_offered_elsewhere()`), T021b · T024 · T052 (row 12-vi, paraphrase half, now including `/learning-goal` and `/research-gaps`) |
| FR-038 | T052 (row 12-vi) — no script can see it; stated as an inspectable end state |
| FR-039 | T015, T016, T017 (D5, neutrality on synthetic text), **T018a** (D5b, separability against the shipped file — one of four), T018, T019, **T021** (D5b widened to one of five) |
| FR-040 | T015 (D8, the hook) · T018 (nothing built) · T051 (row 4k) |

**Two requirements have no automated assertion at all: FR-004 and FR-038.**
FR-004 — *"about this source for this goal, never about the subject or the
publisher"* — is a judgement about what a warning does **not** say, and there is
no token whose absence means it. FR-038 is the whole-pipeline guarantee, and no
script can know which sources the user named. Both reach a named row (4d and
12-vi) and neither is pretended otherwise. FR-032 has none either, for a third
reason: it **is** the row set.

Five requirements the earlier drafts listed beside those two now **do** have a
gate, added by the 2026-09-08 review remediation: FR-003, FR-005, FR-006 and
FR-009 by cases **C6–C9** (T012a) and FR-007 by **A5/A6** (T008a/T008b). Read
the two columns together rather than the check column alone — C6–C9 assert that
**the rule is stated in `skills/sources/SKILL.md`**, which is a drift detector
and not a test of what a run says; the behaviour stays on rows 4a–4i. A5/A6 are
different: FR-007's obligation *is* an absence on disk, so the check sees
exactly the thing the requirement forbids, and it is as strong as the
requirement for every project the checker is pointed at.

**FR-009 is circular and the artifacts say so.** The requirement is that the
skill never invents a claim about a source it has not looked at. C9 can assert
that the prompt carries the rule; it cannot see an invention. Row 4a cannot
either: the only evidence a tester has that a run did not look at a source is
the run's own statement that it did not — which is the thing under test. Neither
artifact decides conformance, and the plan records that rather than counting
FR-009 as verified.

---

## Open items flagged during task generation

Two arithmetic/id discrepancies in plan.md that a reader would otherwise trip
over. Both are now settled; neither blocks starting at T005.

1. **`docs/testing.md` row id `8h` is already taken.** plan.md routed FR-015 to a
   new `/ingest` row `8h`, but `docs/testing.md:211` is an existing
   `/learning-goal` row `8h`. The 8-series runs `8a … 8l`. **T040 uses `8m`**, and
   the 2026-09-08 remediation corrected the `8h` references in `plan.md`,
   `quickstart.md` and `checklists/gates.md` so none survives. (`12-iv` was left
   as a gap at first; the same remediation put the `/cards` half of FR-013 in it,
   so the 12-series is now contiguous: `12-iii` shipped, then `12-iv`, `12-v`,
   `12-vi`.)
2. **Resolved: `check_docs.py` gains eight check functions, and wave E is the
   split.** The count contradicted itself (plan.md said "eight" in one place and
   "seven small functions" in another, and the waves named seven). **Decision:
   split wave E**, because E1/E2/E4 assert an *absence* of `--discover` across
   five other skills (FR-037's four plus `learning-goal`, case E2a) while E3
   asserts a *presence* in `skills/sources/SKILL.md` —
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
- The `read_skill` seam (`scripts/check_docs.py:357`) and the `gated_project()` helper (`tests/test_check_docs.py:193`) mean almost every negative case runs against **synthetic** text — no shipped `SKILL.md` is edited to make a test go red. **The one deliberate exception is D5b (T018a)**, which reads the shipped `skills/sources/SKILL.md` and excises a sub-section by heading, because SC-016 is a claim about that file and a synthetic version of it cannot be false.
- **Two markers, and they mean opposite things.** 🔴 is a task whose output must be a failing assertion. 🧑 is a **human checkpoint** — T037 and T038 — where an implementing agent stops and hands back rather than ticking.
- **Absence is never a finding.** If A3 ever goes red, `nature:` has stopped being optional and every project on disk is affected.
- **If no failing check can be written for a requirement, go back to the spec** — not forward to the prompt (constitution XI).
- English throughout: code, comments, docstrings, docs, commit messages.
