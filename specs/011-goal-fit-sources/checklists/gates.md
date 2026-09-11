# Gate & Scope Checklist: Practitioner material, goal fit, and source discovery

**Purpose**: Validate that the spec and plan route **every** requirement of this
feature to a named verification artifact, that the test-first order is written
down rather than assumed, that the guarantees stated as *absences* are written as
rules a reviewer can apply, and that the deliberate non-goals are recorded where
a well-meaning implementation would otherwise drift into them.

**Created**: 2026-09-08
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) ·
[contracts/](../contracts/)
**Audience / timing**: reviewer, at pull request — and the implementer, before
wave G

**Not a duplicate of [requirements.md](requirements.md).** That checklist asks
whether the *specification* is well written and has been re-validated four
times. This one asks whether the **prompt/gate seam** holds: this feature is
mostly prompt work, so almost every rule it adds is enforced by a check in
`check_docs.py`, a check in `check_project.py`, or a **named** row in
`docs/testing.md` — and the risk is a rule that lands in none of the three.

**How to read an item**: each is a question about what the artifacts *say*. A
"no" is traceable to the FR, SC, plan wave or contract named in brackets, and is
fixed by editing that artifact — not by arguing about intent in review.

## A. Constitution XI routing — every requirement reaches a gate

- [ ] CHK001 Does every one of the **39 active** requirements (FR-001 – FR-040, FR-028 withdrawn) appear in the routing table with at least one artifact named? [Completeness, Plan §Which gate holds which requirement]
- [ ] CHK002 Is each routing entry a **specific** artifact — a wave id (A1, D1d, D6, G3), or a `docs/testing.md` row id (4a–4s, **4n-i**, 8m, 9f, 12-iv, 12-v, 12-vi) — never the bare phrase "the manual checklist" or "the prompt"? [Traceability, FR-032]
- [ ] CHK003 For **FR-003** (the warning names the source id *and* the goal line), does the routing table name case **C6** *and* say what C6 can and cannot see — that it asserts the rule is stated in `skills/sources/SKILL.md` and cannot see a warning — so the check column is not read as coverage of the behaviour? [Gap, FR-003, C6, rows 4b/4f]
- [ ] CHK004 For **FR-007** (nothing persisted), does the routing table name cases **A5/A6** and the `VERDICT_KEYS` refusal in `check_sources`, is the decision to reject **five key names rather than unknown keys in general** written down with its reason, and does `contracts/sources-yaml-unchanged.md` still carry the positive statement of the negative? [Gap, FR-007, A5, A6, contracts/sources-yaml-unchanged.md]
- [ ] CHK005 For **FR-038** (the whole-pipeline guarantee), is its single manual row named and is the reason no script can see it stated? [Gap, FR-038, row 12-vi]
- [ ] CHK006 For **FR-040**, is the split routing explicit — the *hook* is gated by D8, the *"no filter ships"* half is **deliberately ungated** with the reason (a negative check would have to name an argument spelling that does not exist)? [Ambiguity, FR-040, Plan §Risks]
- [ ] CHK007 Does each `docs/testing.md` row carry its **FR number inside the row**, in the established `**run output (FR-0xx):**` form, so `docs/testing.md` is traceable without the plan open beside it? [Traceability, FR-032, SC-012]
- [ ] CHK008 Does every routing decision respect constitution XI's table — is any rule about a `SKILL.md`'s **own text** routed to `check_project.py`, or any rule about a **key on disk** routed to `check_docs.py`? [Consistency, Constitution XI]
- [ ] CHK009 Is **FR-011** identified as the one card-*content* rule placed in `check_project.py`, with the placement argued in Complexity Tracking rather than assumed? [Consistency, Plan §Complexity Tracking]
- [ ] CHK010 Is the list of requirements that are **run-output only** stated in one place and said plainly to be unautomated, and is it distinguished from the requirements whose *prompt sentence* is gated while their *behaviour* is not (FR-003, FR-005, FR-006, FR-009 — cases C6–C9)? [Completeness, Plan §Not automated, and said so plainly]
- [ ] CHK011 Does the enumerated set of `docs/testing.md` rows actually contain the **25** rows the plan claims (20 `/sources` rows 4a–4s **plus 4n-i**, and 5 pipeline rows 8m, 9f, 12-iv, 12-v, 12-vi), with no row referenced in the routing table that the row list omits (and vice versa)? [Consistency, FR-032]
- [ ] CHK012 Is the placement rule stated for anything discovered mid-implementation — that a new rule about run output becomes a **named** row, never an implicit expectation? [Coverage, Constitution XI carve-out]

## B. Test-first discipline — the red artifact per wave

- [ ] CHK013 Does every new check function in `check_docs.py` / `check_project.py` have a named assertion that must be seen **failing on its assertion** — not on an ImportError — before the prompt or fixture that satisfies it exists? [Clarity, Constitution XI, Plan §Test plan first]
- [ ] CHK014 Is **wave G3** identified as the assertion that is red against the **shipped repository today**, so the first commit needs no fabricated input at all? [Clarity, wave G, FR-034]
- [ ] CHK015 Is **wave G2**'s false-positive guard named concretely (`CONTRIBUTING.md:82`'s "even reaches the network:" must **not** fire), so the regex is scoped to the exclusivity claim rather than to the words? [Edge case, R5, FR-034]
- [ ] CHK016 Are wave A's **regression guards** (A3: a project with no `nature:` anywhere exits 0 with **no errors and no warnings**; A4: the shipped demo still passes `--strict`) marked as *green from the start*, so nobody "fixes" them into red tests? [Clarity, wave A, FR-031, SC-013]
- [ ] CHK017 Is the **"all, not any"** rule for an experience-only subtopic pinned by its own case (B3) rather than left to fall out of B1? [Coverage, wave B, US3 scenario 3]
- [ ] CHK018 Is the **severity** of the FR-011 attribution failure fixed as an `error` (not a `warn`), with the reason — `check_cards` already warns on a missing `source:` — recorded? [Clarity, Plan §Phase 1]
- [ ] CHK019 Is the wave **order** stated as a constraint (A–G green → H fixture → I prompts → J docs), so no prompt edit lands before the check that was supposed to fail against it? [Consistency, Plan §Test plan first]
- [ ] CHK020 Are the *guard* rows (A4, **A6**, B4, C5, **D5**, D7, E4, F4) distinguished from the *red* rows, so a reviewer can tell which case proves the **gate** works and which proves the **prompt** was edited — and is **D5b** on the **red** side, not the guard side, because it reads the shipped `skills/sources/SKILL.md` and is red until the addendum heading exists? [Clarity, T017 vs T018a]
- [ ] CHK021 Is the monkeypatch seam (`read_skill`) named, so each red case can be written against synthetic skill text without editing a shipped `SKILL.md`? [Completeness, Plan §Structure Decision]
- [ ] CHK022 Is it stated that a requirement for which **no failing check can be written** goes back to the spec rather than forward to the prompt? [Coverage, Constitution XI]

## C. The negative guarantees — the rules that assert an absence

- [ ] CHK023 Is the `sources.yaml` negative enumerated rather than implied — **no** `fit:`, **no** `assessed:`, **no** `discovered:`/`proposed_by:`, **no** timestamp, **no** sixth type, `SOURCE_TYPES` does not move? [Completeness, FR-007, contracts/sources-yaml-unchanged.md]
- [ ] CHK024 Is the reason the verdict is not persisted recorded **next to the format it governs**, so a later "just a small note on the entry" has something to argue with? [Clarity, FR-007, Q2]
- [ ] CHK025 Is "an absent `nature:` key is **never** a finding" written as its own severity row **and** its own regression guard, rather than left to fall out of the membership test? [Coverage, FR-015, FR-031, SC-013, A3]
- [ ] CHK026 Is the difference between *absent* and an invented second value stated for `/ingest` — not `nature: reference`, not `nature: none`, absence **is** the other state? [Ambiguity, contracts/knowledge-frontmatter.md]
- [ ] CHK027 Is "an ordinary `/sources` run neither enters nor mentions discovery" given a checkable form for `/sources` **itself** (E3), and not only for the other five skills the token gate reads? [Measurability, FR-036]
- [ ] CHK028 Is the **limit** of the `--discover` token gate stated — it catches the pointer somebody adds, not the paraphrase "you could go looking for more material" — and is the paraphrase case routed to a named row rather than left implicit? [Ambiguity, FR-037, Plan §Risks, row 12-vi]
- [ ] CHK029 Is the spelling `--discover` justified as an **exact token** (absent from the repository today) with the false-positive it avoids named (`skills/catalog/SKILL.md:67`, `scripts/build_pdf.py:745`)? [Clarity, R4]
- [ ] CHK030 Is FR-038 stated as an **inspectable end state** — after a full pipeline run `sources.yaml` holds exactly the sources the user named — rather than as an intention about behaviour? [Measurability, FR-038, SC-014]
- [ ] CHK031 Is "nothing about a candidate's **class** reaches disk" stated in every artifact a reader might consult alone — the spec's Format Contracts table, `contracts/discovery-proposal.md`, `data-model.md`? [Consistency, FR-017, SC-017]
- [ ] CHK032 Is the prohibition on a `CLASSES` tuple, a class vocabulary or any class validation stated **with a stop-and-flag rule** if implementation finds itself writing one? [Coverage, FR-040, Plan §Risks]
- [ ] CHK033 Is the FR-006 cap written as a number a reviewer can count — **at most one** `/learning-goal` pointer per run, never one per source? [Measurability, FR-006, row 4i]
- [ ] CHK034 Is the "no confirmation prompt" half of FR-002 stated as a countable expectation (**zero** prompts between the warning and the write), not merely as "advisory"? [Measurability, FR-002, SC-004, row 4b]

## D. Neutrality and separability (FR-039, FR-040)

- [ ] CHK035 Is the C1/C2 boundary drawn **requirement by requirement**, so a reviewer can name which FRs are neutral and which one is the addendum without re-reading the group? [Completeness, Spec §C1, §C2]
- [ ] CHK036 Is "**exactly one** addendum ships" repeated in every artifact that could be read on its own — spec, plan, `contracts/discovery-proposal.md` — so neutrality is not misread as coverage of research literature? [Consistency, FR-039, Plan §Risks]
- [ ] CHK037 Is the separability criterion stated as a **testable condition against the file that ships** — excise the `### Practitioner material` sub-section from the real `skills/sources/SKILL.md` **by its heading**, feed the remainder through the `read_skill` seam, and assert that exactly one of the checks reading that file reports — **one of four at T018a/T019, widened to one of five at T021, once `check_sources_skill_states_the_explicit_request()` exists** — rather than as a condition on synthetic text a test author wrote? [Measurability, SC-016, D5b, T018a, T021]
- [ ] CHK038 Is the neutrality criterion stated in words a reviewer can apply mechanically — **zero** C1 assertions may name practitioner material, an incident, a post-mortem or a company blog? [Clarity, SC-016, FR-039]
- [ ] CHK039 Are the two check functions named and separate (`check_sources_skill_carries_the_discovery_contract()` neutral; `check_sources_skill_carries_the_practitioner_addendum()`), with neither reading the other's text? [Completeness, Plan §Phase 1]
- [ ] CHK040 Is **D8** placed **inside** the neutral check, and does it assert that a candidate's class is *named* and never *which* classes exist? [Consistency, FR-017, FR-040]
- [ ] CHK041 Are the **silence** gates of wave E classified as C1-level, so a later addendum touches none of them? [Coverage, FR-039, wave E]
- [ ] CHK042 Is the procedure for adding a later addendum written down — a new sub-section plus **one added check**, nothing above the C2 heading reopened, reworded or re-scoped? [Completeness, contracts/discovery-proposal.md §Adding an addendum later]
- [ ] CHK043 Is the two-axis distinction — an addendum governs **how a credibility sentence reads**; a filter would govern **what discovery searches** — stated wherever a reader meets either one? [Ambiguity, FR-040, round 4]
- [ ] CHK044 Is FR-018's **form** rule (a sentence, never a score, rating, percentage, star count or rank) held against every class equally, with the practitioner additions kept out of the requirement's own text? [Consistency, FR-018, FR-019]

## E. Repo gates and conventions

- [ ] CHK045 Are the four PR gates named as the release condition (`ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`)? [Completeness, Constitution XII, SC-012]
- [ ] CHK046 Is `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` stated as **required for this feature**, not optional, because `DEMO_CARD_COUNT` moves? [Clarity, Plan §Risks, quickstart.md]
- [ ] CHK047 Is it recorded that the new cards go into `cards/signals.yaml` so `TIDES_CARD_COUNT` does **not** move? [Edge case, Plan §Risks]
- [ ] CHK048 Is `python3 scripts/check_project.py tests/fixtures/demo-project --strict` named as its own wave-H step, run **before** the prompts are touched, given the catalog's `Status:`/`Parents:`/`Also covers:`/`Related:`/`Term:` invariants? [Coverage, Plan §Risks]
- [ ] CHK049 Is the subject-agnosticism obligation stated for the new fixture — invented archipelago material, nothing quoted from anyone — **and** flagged as needing an explicit note in the PR description? [Constitution VII, Plan §Constitution Check row VII]
- [ ] CHK050 Is "extend the demo project, never a second corpus" applied to **both** open problems — the experience-report fixture and FR-005's `kind`/`depth` weighting (a `scripts/demo.py` scratch copy with one word edited, nothing new committed)? [Consistency, R2, Constitution VII & XI]
- [ ] CHK051 Is the user-content rule restated for this feature — `sources.yaml`, `knowledge/`, `catalog/`, `cards/` (except `example.yaml`) and `output/` are never committed and never forced in with `git add -f`? [Completeness, Constitution VII]
- [ ] CHK052 Is "**no** new runtime dependency, **no** new dev dependency, **no** new external binary" stated together with the **stop-and-flag** rule if one turns out to be needed? [Assumption, Constitution II–IV, R6]
- [ ] CHK053 Are the four assertions on `skills/sources/SKILL.md`'s `description` enumerated — `name: sources`, ≥ 20 characters, the word `Triggers`, the domain word `flashcard` — before it is rewritten to name both jobs? [Coverage, Constitution X, Plan §Risks]
- [ ] CHK054 Is the `tests/test_testdata.py:265-273` hazard recorded — it parses `skills/ingest/SKILL.md` literally near lines 27-28 — so the `nature:` edits stay in the frontmatter block and the extraction rules? [Edge case, Plan §Risks]
- [ ] CHK055 Are the repo-level conventions stated for the change itself: English throughout, branch `feat/goal-fit-sources`, no direct push to `main`, no new file under `scripts/`? [Constitution V, XIII, XIV]

## F. Scope containment — the things this feature deliberately does not do

- [ ] CHK056 Is "**no sixth source type** — `web` already covers this material" stated as a requirement rather than as an assumption a reader could miss? [Scope, FR-029, Format Contracts]
- [ ] CHK057 Is "**no** arXiv, OpenAlex, Crossref or any source-specific search backend, and **no** bibliographic identity (DOI, authors, year, venue, citation count) in any frontmatter" recorded as out of scope and attributed to issue #43? [Scope, round 3, Assumptions]
- [ ] CHK058 Is "**no** `/ingest` pagination and **no** change to `depth:`" stated together with what ships instead — the archive-reach sentence at registration (`depth: 1`, the index page plus same-domain linked posts, capped at 20)? [Scope, FR-029, Q5, row 4h]
- [ ] CHK059 Is "**no second addendum**, **no** class-selection argument, **no** class filter, **no** class vocabulary" stated in the spec, the plan **and** the contract? [Scope, FR-039, FR-040]
- [ ] CHK060 Is the untouched-file list explicit — `assets/brand/*.typ`, the three rendered PNGs, `scripts/render_brand.py`, `docs/index.html`, `tests/test_landing_page.py`, `CLAUDE.md`, `.specify/memory/constitution.md`, `docs/design.md`, `templates/*.typ`, `scripts/build_pdf.py`, `bin/lernkarten`? [Scope, Plan §Not touched, deliberately]
- [ ] CHK061 Is the **seven-step** count stated as unchanged everywhere the pipeline is described, and is the decision *not* to edit `docs/index.html` recorded as a scoping decision rather than discovered in review? [Scope, SC-011, Plan §Phase 1]
- [ ] CHK062 Is "**the constitution needs no amendment**" stated, with the reason (no step is added) rather than left as an absence? [Assumption, Spec §Assumptions]
- [ ] CHK063 Is the R1 decision recorded — **no back-fill** for a goal written after the sources — together with exactly what ships instead (one gated sentence in `skills/sources/SKILL.md`, one ordering sentence in `docs/workflow.md` Step 1) so FR-008 is not silently widened? [Gap, R1, row 4j]
- [ ] CHK064 Are the discovery caps fixed as **numbers** (≤ 3 per area, ≤ 10 per run, every area listed including the empty ones) rather than left to the implementer's judgement? [Measurability, R3, FR-027]
- [ ] CHK065 Is FR-034's correction scoped to the **exclusivity claim** — what replaces it states *going looking for material the user did not choose* versus *fetching what the user named* — rather than deleting the network sentence outright? [Clarity, FR-034, US6 scenario 5]

## Notes

- Check items off as `[x]`. A "no" is a defect in the artifact named in brackets;
  fix it there before the PR, not in review comments.
- **Two** requirements have **no automated assertion at all** — **FR-004** and
  **FR-038** — plus FR-032, which *is* the row set, and FR-040's ungated half.
  Both reach **named** `docs/testing.md` rows (4d and 12-vi), which is the
  run-output carve-out used as written. It was seven until the 2026-09-08 review
  remediation, which added a gate for FR-003, FR-005, FR-006 and FR-009 (cases
  C6–C9) and for FR-007 (cases A5/A6). If any of CHK003 – CHK006 is "no", the
  feature has a rule nothing holds.
- CHK013 – CHK022 are worth re-reading **before** the first commit, not after:
  wave G3 is the only assertion that is red against a clean checkout, so it is
  the cheapest place to prove the discipline is real.
- CHK037 and CHK038 are the two items that decide whether issue #43 can attach a
  research-literature addendum later by **adding** a check, or has to edit one.

## G. The material-base warning (FR-013) and the addendum sentence (FR-019)

*Added by the 2026-09-08 remediation, when FR-013 stopped prescribing a phrase
and started requiring four contents.*

- [ ] CHK066 Does **FR-013** demand **four contents** — which subtopic and what it rests on; why that base is skewed, *written out* rather than named; what it means for the cards; what would balance it — rather than any particular wording, and does it say plainly that the bare phrase *"published incidents are a selected sample"* does **not** satisfy it? [Clarity, FR-013, US3 scenario 5]
- [ ] CHK067 Is FR-013 routed to **both** `/catalog` **and** `/cards` everywhere — the plan's routing table (F2 **and** F3), the wave-F case list, T024 **and** T025, and the two named rows **9f** and **12-iv**? [Coverage, FR-013, US3 scenario 5]
- [ ] CHK068 Is the FR-013 warning stated as **non-blocking** — a statement about the state of the sources, never an error, never a reason to refuse a card or a source, and never a suggestion to run discovery (FR-037)? [Consistency, FR-013, FR-037]
- [ ] CHK069 Does **FR-019**'s addendum demand the **content** of its second property — that material of this kind is published only by the parties who came through the incident, so the cases that ended badly are not among what can be found — rather than the phrase "a selected sample", while staying **one** sentence (FR-018)? [Clarity, FR-018, FR-019]
- [ ] CHK070 Is the worked example of a conforming FR-013 warning written **once** (spec.md § FR-013), in the demo project's invented vocabulary — signals, flags, harbours, tides, field notes — and with **no** real field of study anywhere in it? [Constitution VII, FR-013]

## H. The gates the 2026-09-08 review added, and what they are worth

*Added by the review remediation. Five requirements gained a check; the risk
this section exists for is that a check column reads as coverage of a behaviour
it cannot see.*

- [ ] CHK071 Do the routing entries for **FR-003, FR-005, FR-006 and FR-009** name their case (C6, C7, C8, C9) **and** say in the same cell that the case asserts the *rule is stated in the prompt* and nothing more, with the behavioural half still on its named row? [Clarity, W-3, C6–C9]
- [ ] CHK072 Is **FR-009**'s circularity recorded plainly — a substring gate cannot see an invention, and the only evidence a tester has that a run did not look at a source is the run's own statement that it did not — rather than left to read as verified? [Measurability, FR-009, Plan §What no artifact can decide]
- [ ] CHK073 Is the **FR-007** check scoped to **five key names** (`fit`, `assessed`, `goal_fit`, `discovered`, `proposed_by`) rather than to unknown keys in general, with the reason written down — an allowlist would invalidate `login:` and every project on disk carrying a key this repo has not thought of — and is the ungated "no timestamp" clause named? [Scope, FR-007, A5, A6, contracts/sources-yaml-unchanged.md]
- [ ] CHK074 Do the four requirements **no** artifact can decide (FR-009, FR-021, FR-023, FR-027's *found* count) each say so where a reader meets them, and does row **4n-i** state that "not exercised" — never "pass" — is the honest outcome when discovery finds no unretrievable or paywalled candidate? [Measurability, W-6, rows 4k, 4n-i]
- [ ] CHK075 Does row **4r** give FR-033 an **observable** — the three ordinary invocations re-run with the network off, behaving exactly as they did online — rather than "makes no network request", which a session exposes no way to judge? [Measurability, FR-033, row 4r, US5 scenario 3]
