# Pre-Implementation Review

**Feature**: Deck anchors — `depth` as a ceiling, and every term the deck uses is named by a card (`007-deck-anchors`, issue #49)
**Artifacts reviewed**: spec.md, plan.md, tasks.md, research.md, data-model.md, quickstart.md, contracts/catalog-topics-md.md, contracts/check-messages.md, checklists/ (requirements, checks, delivery), plus the live tree: `scripts/check_project.py`, `tests/test_check_project.py`, `tests/test_e2e.py`, `tests/fixtures/demo-project/`, `skills/{cards,catalog,learning-goal}/SKILL.md`, `.specify/memory/constitution.md`, `.github/workflows/ci.yml`, and issue #49 itself.
**Review model**: Fable 5 (claude-fable-5)
**Generating model**: the same-model pipeline that ran Phases 1–6 (14 analyze findings, all remediated). This review deliberately does not re-run that consistency pass; it verifies claims against the tree and judges the design.

## Summary

| Dimension | Verdict | Issues |
|-----------|---------|--------|
| Spec–Plan Alignment | PASS | All three stories and all FRs land in the plan; no contradiction found |
| Plan–Tasks Completeness | PASS | Traceability table checks out; FR-018's "nothing to do" is correct |
| Dependency Ordering | PASS | Four-commit red/green sequence is sound; every ordering hazard I probed is handled |
| Parallelization Correctness | PASS | Independently verified: 9 groups, max 3, no same-file pair inside any group |
| Feasibility & Risk | WARN | A-1 has no writer (W1); the fixture evades its own check (W2); separator set misses the ASCII hyphen (W3) |
| Standards Compliance | PASS | Constitution XI honoured for real (red on assertion, commit-order provable); V, VII, XIII hold |
| Implementation Readiness | WARN | One spec/task divergence on the maths gate (W4); one wrong-remedy path in the new skill step (W5) |

**Overall**: **READY WITH WARNINGS** — implementable as written; the warnings are cheap to fix now and expensive to fix after the prompts ship.

## Fact verification (what this review checked against the tree, not against the other artifacts)

Every load-bearing factual claim I sampled was correct: `ATTRIBUTE` at `check_project.py:61`, `topic_key` at `:128`, `catalog_names` at `:463`, `check_catalog` at `:580` returning at `:675`, `check_cards` at `:704`, `check` at `:891`; CI's `--strict` fixture invocation at `.github/workflows/ci.yml:120`; 31 fixture ids by the exact `grep -h '^  - id:'` command T021 prescribes; `R7XQ4` absent from the fixture; `tides.yaml` holds 10 cards and no card under `Rhythm of the tide` names the term; exactly two `#list(` backs exist in the repository (geography `Y4H26`, example `4V946`); the test helpers `project()` (`:107`), `check()` (`:136`, returns the report — T004's calling shape is right), `messages()` (`:140`, errors only — so T004's asserts read the right list), `with_figure()` (`:99`, creates parent dirs, so T007a works); `tests/test_check_project.py:164` (`== 31`) and `:857` (the sole external two-tuple unpack of `check_catalog`); `tests/test_e2e.py:27/:97/:255/:1110` exactly as described; a subtopic without `References:` is an *error* in `check_catalog`, so T005's instruction to give `### Slack water` a references line is necessary and its target (`../knowledge/field-notes/a.md`) is created by `project()`. The quickstart §4 arithmetic is right (three orphans, `Green` anchored by card 2's front). The page arithmetic at 31/32/33 cards is right, including the untouched `:98 == 4` (11 cards is still 2 sheets). This level of accuracy materially de-risks implementation.

## Findings

### Critical (FAIL — must fix before implementing)

None. Nothing here blocks implementation.

### Warnings (WARN — recommend fixing before or during implementation)

1. **W1 — A-1 has no writer, so for a real user it is dead code by default.** The whole feature keys A-1 off a `Term:` line that `/catalog` writes — but nothing ever tells `/catalog` to write it. FR-027 and T029 only *document* the line in `skills/catalog/SKILL.md`'s optional-attribute list, whose framing is "Optional lines inside a subtopic, all of which mean today's behaviour when absent" (verified at lines 83–92). No step in `/catalog`'s generation flow (`## Steps`, `## With a goal`) gains an instruction to emit `Term:` when a subtopic is a named concept. The spec itself states the danger — "A format the prompts never write is a dead format" (FR-027) — and the tasks then implement exactly that. Consequence: in a fresh project driven end-to-end by the skills, the catalog carries no `Term:` lines, A-1 is silent everywhere, and the only anchor enforcement is the untestable prompt rule in `skills/cards` — which is precisely the "suggestion with no test behind it" the issue diagnoses. The motivating private deck (eight argued-about concepts never named) would still pass the checker after this feature ships, unless its author hand-edits the catalog. The spec's own seam argument supplies the fix: "the model-driven half decides *which* concept a subtopic is about" — that decision should be *recorded* as a `Term:` line at catalog time. **Recommendation**: one sentence in T029's scope (and FR-027): amend `/catalog`'s writing step to say *"when a subtopic heading names a concept (not a description of a group of facts), write a `Term:` line carrying the aliases for every language the deck uses."* The term-vs-description judgement is exactly the judgement the seam assigns to the model. Cost: one sentence; value: the difference between a check that fires for users and one that fires only in this repo's fixture.

2. **W2 — The fixture demonstrates evasion-by-omission and doesn't disclose it.** R4 measured three `(file, subtopic)` pairs that are real instances of issue #49's defect in the shipped demo: `gezeiten-de.yaml`/`Tidenrhythmus` (no card says the word), `gezeiten-de.yaml`/`Tidenhub` (only the compound tokens `Nipptidenhub`/`Springtidenhub`, which the token rule rightly rejects), `signals.yaml`/`The six flags` (the phrase appears only in `source:` fields, which are not in the haystack). I verified all three against the card files. T018 deliberately withholds their `Term:` lines with the stated reason that anchoring them "would cost an anchor card and blow the 32-card budget". So after this feature lands, the demo deck violates FR-004's unconditional prompt rule in three subtopics and is certified green under `--strict` — the repository's own fixture teaches that the cheapest way to satisfy A-1 is to write no `Term:` line. T024's README section discloses only `Settlements` and `Rules of use` (genuine descriptions — a legitimate demonstration of FR-011a); the three *named concepts* silenced for budget reasons go unmentioned. **Recommendation**: minimum fix — T024 names the three honestly ("unanchored today; `Term:` withheld to hold the 32-card budget, see research R5") so a contributor reads a disclosed trade-off instead of learning an evasion. Better fix, if the budget is ever revisited — add the three anchors and pay R5's enumerated churn.

3. **W3 — `ITEM_SEPARATOR` omits the ASCII hyphen, which is A-2's one realistic false-positive avenue.** The set is `[—–,:;]|\s\(` (em dash, en dash, comma, colon, semicolon, ` (`). A model or user typing `[Amber - the middle stage]` with a keyboard hyphen gets no head-term cut: the whole item is matched, fails, and A-2 reports an orphan for an item another card genuinely explains. The design's stated first principle is "a check that cries wolf gets ignored" (research R1), and this is the shape most likely to make it cry wolf — nothing in spec, research, or tasks mentions the hyphen-minus, so it was not considered and rejected; it was missed. **Recommendation**: add ` - ` (space-hyphen-space, to avoid tearing hyphenated compounds like `sigma-additivity`) to `ITEM_SEPARATOR` and one parametrize row to T015, or record its deliberate rejection in research R3.

4. **W4 — FR-013 and T012 specify different maths gates.** FR-013: skip an item "containing a `$…$` **span**". T012: `_item_key` returns `None` "for any item containing a `$`". An item with a single unpaired `$` (or a currency amount) is skipped under T012's rule and not under FR-013's letter. The divergence is conservative (it produces silence, never a false positive, and an unpaired `$` is broken Typst anyway), but an implementer following the spec and one following the task produce different code and different unit tables. **Recommendation**: one line in FR-013 or T012 reconciling them — "any `$`, deliberately a superset of the span rule, because an unpaired `$` is broken markup and silence is the safe side."

5. **W5 — The new checker step teaches the wrong remedy for the missing-alias case.** The spec's multilingual edge case claims a file whose language the aliases don't cover "will report — correctly, because that deck really does not name the term." That is wrong in the common sub-case: the Greek cards *do* name the term in Greek, and it is the `Term:` line that lacks the Greek alias. The deck is fine; the catalog is stale. T028 step vi tells the model that "a missing anchor means writing the card that names the concept" — for this case that adds a redundant card instead of the one-line catalog fix. **Recommendation**: step vi (and the spec edge case) gain the second remedy: "…or, if a card already names the concept in that file's language, add that language's alias to the subtopic's `Term:` line."

6. **W6 — A-2's message overclaims what the check verifies, and the feature's own fix proves it.** The message reads "'Skarn' is enumerated and never **explained**", but the check tests *naming* (token-sequence mention). The feature's own remediation (T019) satisfies it by adding "…redistributes goods to Little Kestrel, Ovray, Skarn and Bellhorn" to another card — a second list-like mention, not an explanation. That is faithful to the issue's wording ("appears in some other card") and to the seam (a deterministic check cannot judge explanation), but the message promises more than the machine checked, and a user who "fixes" a finding the way this repo did will believe they explained something. **Recommendation**: reword to "…is enumerated and never named — no other card in this file mentions it" (contract + T013, before tests assert on the string; after implementation this becomes an API-stability question).

### Observations (informational)

1. **The `Term:` design itself is sound, and the Phase-2 rejections were correct.** I checked the alternatives against the tree rather than trusting the write-up: full-heading substring genuinely fails the demo (`Chart datum and the Ovray rule`, `Range and the rule of twelfths` never appear verbatim in a card and never plausibly would); content-word matching fails every cross-language pair (English catalog headings, Greek/Russian/German card files) and gives false positives; and any non-opt-in A-1 — even advisory — is structurally forbidden by the existing test corpus, because `GOOD_CARDS` (one card naming neither *rhythm* nor *tide*) sits behind fifteen call sites including `test_a_minimal_project_is_clean`, which asserts zero warnings. Given the determinism requirement and that corpus, an explicit declared term is the only workable trigger. Worth saying out loud, though: the fifteen `GOOD_CARDS` call sites are steering the design space here, which is a legitimate cost argument but should be recognised as one. The hollowness the opt-in shape creates is real — and it is repairable at the writer side (W1), not by a different matcher.

2. **Does it deliver issue #49?** It delivers the issue's *sketch* faithfully — the issue itself scoped A-2 to `#list([…])` backs, left "names the term" explicitly open, and even floated making A-1 advisory. Within that option space, `Term:`-gated-error is a defensible pick. It only partially delivers the issue's *title promise* ("self-contained in its own vocabulary"): A-1 fires only where someone opted in, A-2 sees only `#list` markup — an enumeration written as prose or with `\ ` line breaks is invisible — and both checks verify mention, not establishment. With W1 fixed, the pipeline at least opts in by default, which is as close as a deterministic checker can get.

3. **A-2 blind spots nobody wrote down** (all false-negative shapes, consistent with the design's bias, but they belong in the spec's edge-case list as accepted limitations): (a) **mutual enumeration** — the haystack for an item is other cards' full `front + back`, which includes *their* `#list` bodies and their question fronts, so two cards each enumerating `[Amber]` silence each other, and a front that merely *asks* "Name the four Ashwind stages" anchors nothing yet mentions everything; (b) a list produced without the literal `#list(` head (e.g. code-mode `#align(center, list([a], [b]))`) is invisible to the scan; (c) two `#list(` calls in one back — the artifacts specify behaviour for zero and one, never for two. None blocks shipping; all three should cost one sentence each in the edge-case section so a future reader knows they were seen, not missed.

4. **Failure modes that ARE handled well** (credit where due, verified): alias-as-substring (`Nipptidenhub` ≠ `Tidenhub` has its own unit row and is the load-bearing token-sequence property); an alias spanning a `\ ` line break (the backslash is stripped by `topic_key`, so the match correctly survives); all-figure subtopics (the existing "picture face with no text" *error* guarantees every card has text on both faces, so A-1 always has a haystack); front vs back (both count, by explicit `front + " " + back` in the contract); two subtopics sharing an alias (independent `(file, subtopic)` accumulators, no interference); a card with no `subtopic:` key (empty-string key, `terms.get("")` is `None`, silent — matching the existing warning's division of labour).

5. **The 32-card budget: right call for this PR, and a smell that deserves a follow-up issue.** Pinning is correct *here*: deriving ~15 bare page-count literals in `tests/test_e2e.py` is a test-infrastructure refactor orthogonal to a vocabulary feature, several sites are structural (`marks[:4] == [{"1/2"}] * 4`, `range(2)`), and bolting that diff onto this PR would bury the feature — the plan's reasoning is sound. But the budget has already done damage: W2 shows it steering *content* decisions (which subtopics get a `Term:` line was decided by test cost, not by whether they name a concept). That is the definition of brittle tests distorting the system under test. **Recommendation**: file a follow-up — a `pages_for(cards, per_sheet)` helper plus deriving the literals and the structural assertions from `DEMO_CARD_COUNT`; the sites are already enumerated in research R5, so the cost is bounded (~15 mechanical edits, a couple of hours) and it permanently removes the "hard budget" from every future fixture change.

6. **Granularity: 46 tasks for ~150 lines of Python plus prose is over-specified by task *count*, but the density is constraint documentation, not busywork.** Roughly a quarter of the tasks are run-a-command checkpoints (T001–T003, T008, T016, T021, T025, T032, T034–T045). What earns the ceremony: every checkpoint traces to a verified trap (the 15-assertion cliff at 33 cards, `--strict` turning warnings into CI failures, the `AttributeError`-is-not-red rule, the commit-order proof FR-025 demands), and the edit tasks carry exact line numbers that all check out. For an LLM implementer this is the right shape; for a human it would be padding. No change recommended.

7. **Cosmetic**: data-model §5's invariants run I-1…I-6, I-9, I-11, I-10, I-7, I-8 — renumber or reorder at will; nothing references them positionally.

## Dimension detail

### 1. Spec–Plan Alignment — PASS
All three stories map to plan sections (Story 1/2 → §1–§4, Story 3 → §5); all 27 numbered FRs (through FR-027, including the lettered suffixes) appear in the plan; the three "behaviour decisions not forced by an FR" were retroactively promoted to FRs (FR-009a, FR-011b) — correctly. Non-functional coverage: performance (R10/SC-007), portability (pure text, three platforms), backward compatibility (additive `Term:`, `check_cards(terms=None)`).

### 2. Plan–Tasks Completeness — PASS
Every plan element has a task; the traceability table's rows sampled all resolve; FR-018 mapping to "nothing to do" is correct (frozen schema). The two regression guards (T007, T007a) exist as tasks with the right colour annotations (green-today pins committed inside the red commit — legitimate).

### 3. Dependency Ordering — PASS
Setup → red → green(checks) → green(fixture) → prompts → gates → by-hand. FR-025's prompts-last ordering is structurally enforced by phase order and checked twice (T026 checkpoint, T043). T010 (arity change) precedes T011 (the unpack fix); T015's helper unit tests sit in Phase 3, after the helpers exist, for exactly the constitution-XI reason stated. T040 is correctly serialised against the read-only gates because `make_testdata.py` writes into the fixture tree. The knowingly-red intermediate commit 2 is documented in its own commit body; the repo's gates are per-PR, not per-commit, so this is acceptable.

### 4. Parallelization Correctness — PASS (verified independently, not trusted)
Group by group: G1 (T001–3, commands only), G2 (T011 `tests/test_check_project.py` / T012 `scripts/check_project.py`), G3 (T018/T019/T020 — three distinct fixture files), G4 (T022 `test_e2e.py` / T023 `test_check_project.py` / T024 fixture README), G5 (three distinct SKILL.md files), G6 (`CLAUDE.md` / `docs/testing.md`), G7–G9 (read-only commands). No group exceeds 3; no same-file pair inside any group; `tests/test_check_project.py` appears in G2 and G4 but in different phases with a sequential gate between. Phase 2's forced serialisation (one file, five tasks) is correct and stated. The "Never parallel" list catches the one non-obvious hazard (T040 vs any test run).

### 5. Feasibility & Risk — WARN
W1–W3 above. The risk table itself is honest and the two biggest technical risks (the 33-card cliff, the `GOOD_CARDS` corpus) are real, measured, and mitigated. No task exceeds a reasonable size; the largest single edit (T014) is ~30 lines in one file.

### 6. Standards Compliance — PASS
Constitution XI is honoured in substance, not ritual: red cases fail on assertions against a list that exists today, the pre-existing `test_the_demo_project_is_consistent` going red at commit 2 is genuine evidence A-2 finds a real defect, and the run-output carve-out (SC-006/SC-008 → named `docs/testing.md` rows) is used correctly. V (all code in `check_project.py`), VI (no new import), VII (Kestrel-only fixture content, PR note required and planned), X (frontmatter untouched, twice-guarded), XIII (English; the alias carve-out argument is sound), XIV (branch/commit prefixes) all hold.

### 7. Implementation Readiness — WARN
W4 and W5 above are the only ambiguities found. Otherwise the tasks are unusually executable: exact paths everywhere, verbatim message strings, verbatim YAML for the new card, verified line numbers, and checkpoints with literal expected output (`OK: … 32 cards, 0 warning(s)`).

## Recommended Actions

All six warnings were remediated in the artifacts on 2026-09-01, on the orchestrator's
instruction, after user approval (see the remediation record below). The one item
left open is repo-level, not this feature's:

- [x] **W1**: FR-027 amended and T029 extended — `/catalog` is now *instructed* to write `Term:` for a subtopic whose heading names a concept, at latest when its cards exist. Also: plan §5 row, contracts/catalog-topics-md.md § Grammar, spec Clarifications (cross-model review session).
- [x] **W2**: resolved as **anchor by reword** (option 3) — T018 adds seven `Term:` lines, new tasks T019a/T019b reword `HNHF1`, `R3WZ4` (gezeiten-de.yaml) and `NKQK0` (signals.yaml) at zero card cost; plan §3(a)/(b2)/(b3), research R4/R5 amendments, T021 diff expectation, T024 disclosure, delivery-checklist third pass.
- [x] **W3**: ` - ` (spaced hyphen-minus) added to `ITEM_SEPARATOR` in plan §Design and T012, two T015 parametrize rows (spaced cuts, unspaced does not), FR-013 amended, research R3 amendment, data-model §3, CHK010.
- [x] **W4**: reconciled on **any `$`** (deliberate superset of a balanced span) — FR-013 amended, T012 note, contracts/check-messages.md § Silent when, spec Clarifications.
- [x] **W5**: alias remedy added to T028 step vi and the spec's "Two languages, one deck" edge case; contracts/catalog-topics-md.md § What the aliases are for.
- [x] **W6**: A-2's message is now `'{item}' is enumerated and never named — no other card in this file mentions it` — contract shape, T013 snippet, rationale sentence in the contract.
- [ ] File a follow-up issue (repo-level, outside this feature): derive `tests/test_e2e.py`'s page-count literals from `DEMO_CARD_COUNT` so no future fixture change inherits the 32-card cliff.

## Remediation record (2026-09-01, same review session)

The orchestrator relayed user approval to fix all six warnings; the read-only
constraint was lifted for artifact files under `specs/007-deck-anchors/` only.
No production code, no tests, no skills and no fixtures were touched — every
edit describes what implementation will do, in the artifact that governs it.

**The W1/W2 tension, resolved as option 3 (anchor by reword).** Instructing
`/catalog` to write `Term:` (W1) obliges the demo catalog to carry the line on
`Tidenrhythmus`, `Tidenhub` and `The six flags` — which then need anchors,
which threatened the 32-card budget. Checked against the card files before
choosing: all three anchor by one-line rewords of existing cards, the same move
T019 already makes for `Skarn`/`Bellhorn` — `HNHF1`'s back gains "— das ist der
Tidenrhythmus." (80 chars), `R3WZ4`'s back changes `Der Hub` to `Der Tidenhub`
(122 chars), `NKQK0`'s front becomes "Which two of the six flags call for help,
and how do they differ?" (65 chars, still unique). Recomputed arithmetic: deck
stays 31 + 1 = 32 → a7 ⌈32/8⌉ = 4 sheets = 8 pages, a8 ⌈32/16⌉ = 2 sheets =
4 pages, mixed 33 → 5 sheets = 10 pages — identical to the plan, so the four
moving assertions stay four. The two content-level e2e assertions touching the
reworded files are count- and front-based and move nothing
(`test_a_subtopic_filter_narrows_the_build` asserts `"3 cards"`; the
script-coverage test greps `halbtägige`, which lives in `HNHF1`'s untouched
front). Option 1 (disclose) was rejected because after W1 the fixture would
contradict the instruction the feature itself adds; option 2 (35 cards:
a7 → 10 pages, a8 → 6, ~15 assertion edits including structural ones) was
rejected as pure cost once option 3 proved available.

**Task count**: 46 → 48 (T019a, T019b; parallel group 10, two tasks, two files,
max-3 respected). No existing FR or task renumbered; amendments follow the
established suffix and session-block conventions (FR-009a, T007a precedents).

**Post-remediation verdict**: **READY**. The six warnings are closed in the
artifacts; what remains is the repo-level follow-up issue above, which does not
gate this feature.
