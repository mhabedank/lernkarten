# Delivery & Gates Checklist: Deck anchors

**Purpose**: Unit-test the *requirements* that govern how this feature lands —
the fixture budget, the red-before-green commit order, `--strict`, the
documentation set, the four PR gates and the dependency rule. Every item asks
whether something is **written down** and pinned to a number, a file or a
command, not whether the build passes.
**Created**: 2026-09-01
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md)
**Audience / timing**: reviewer, at PR time; author, before the first commit
**Depth**: standard
**IDs**: CHK101–CHK126. The companion file [checks.md](checks.md) uses
CHK001–CHK024.

## The fixture budget

- [ ] CHK101 Is the demo deck's post-feature size stated as an **exact** number (32) rather than a range or an "about"? [Clarity, plan §3, quickstart §7]
- [ ] CHK102 Are all four assertion sites that move enumerated with file **and** line — `tests/test_e2e.py:27`, `:97`, `:255`, `tests/test_check_project.py:164` — and is it stated which further site derives from `DEMO_CARD_COUNT` and therefore does not move? [Completeness, FR-023, plan §3(e)]
- [ ] CHK103 Is the cost of exceeding 32 documented as a number a reviewer can price (~15 assertions, several structural), rather than as a vague warning? [Measurability, Risk 1, research §R5]
- [ ] CHK104 Is the requirement that `Skarn` and `Bellhorn` be closed by **rewording** an existing back — not by adding cards — stated as a requirement with its reason, so a task author cannot pick the other option? [Clarity, plan §3(b)]
- [ ] CHK105 Is it stated that the A-2 fix must **not** go under `Relief and the crater`, and is the reason (a marked subtopic warns, and a warning fails under `--strict`) written next to it? [Coverage, Risk 4, research §R8]
- [ ] CHK106 Are the acceptance requirements for the one added anchor card enumerated — unique five-character Crockford `id`, `subtopic:`, `source:`, front ≤ ~120 and back ≤ ~400 characters — rather than left to "a normal card"? [Completeness, plan §3(c), Risk 3]
- [ ] CHK107 Is the requirement that the fixture's new material stay invented and subject-agnostic stated, given that the fixture is the one carve-out to the no-user-content rule? [Coverage, Constitution VII, CLAUDE.md §Repo rules]

## Test-first ordering

- [ ] CHK108 Is the red-before-green sequence specified as an ordered list of **commits**, each with the artifact it contains and the commit-subject prefix it uses? [Completeness, FR-025, plan §4]
- [ ] CHK109 Is "red on the assertion, not on an `AttributeError`" stated as an explicit acceptance condition for each red test, and is the mechanism that makes it true (asserting on `report.errors`, a list that exists and is empty today) named? [Clarity, SC-003, Constitution XI]
- [ ] CHK110 Is it stated that the helper unit tests (`_list_items`, `_item_key`, `_mentions`) belong in the **implementation** commit and not in the red commit, with the reason? [Clarity, plan §4 commit 2]
- [ ] CHK111 Is the pre-existing test that goes red when A-2 lands named (`test_the_demo_project_is_consistent`), together with the commit at which it must go green again? [Traceability, plan §4 R-4]
- [ ] CHK112 Is the location requirement for each red case stated with its reason — A-1's in `tmp_path` because `check_project.py` never scans `broken/`, and A-2's wherever it can be seen? [Completeness, FR-022]
- [ ] CHK113 Is the constraint that no red-commit test may call a function that does not exist yet stated as a rule, not only demonstrated by example? [Clarity, plan §4]
- [ ] CHK114 Is `check_catalog`'s arity change and its single external unpacking site (`tests/test_check_project.py:857`) recorded, so the red commit does not break an unrelated test? [Traceability, Risk 8, plan §1 edit 3]

## `--strict` on the demo project

- [ ] CHK115 Is the CI invocation reproduced verbatim, `--strict` included, everywhere the fixture's acceptance bar is stated? [Clarity, FR-015, `.github/workflows/ci.yml`]
- [ ] CHK116 Is the bar stated as **zero errors and zero warnings** — never "no errors" alone — in all three places it appears (SC-001, Story 1 scenario 4, quickstart §1)? [Consistency, SC-001]
- [ ] CHK117 Is the requirement to re-run `--strict` after **every** fixture edit, rather than once at the end, written into the plan as an instruction and not only as a risk mitigation? [Completeness, Risk 3]
- [ ] CHK118 Is the expected success line quoted with its card count (`…, 32 cards, 0 warning(s)`), so "green" is checkable against a literal? [Measurability, quickstart §1]

## Documentation set

- [ ] CHK119 Are all documentation targets enumerated with the FR each satisfies — `skills/learning-goal/SKILL.md`, `skills/cards/SKILL.md`, `skills/catalog/SKILL.md`, `CLAUDE.md`, `docs/testing.md`, `tests/fixtures/demo-project/README.md` — with none left implicit? [Completeness, plan §5, FR-001, FR-003–FR-007, FR-024, FR-026, FR-027]
- [ ] CHK120 Is the constraint that **no skill frontmatter** (`name`, `description`) may change stated, given that `scripts/check_docs.py` is a PR gate and the edits are body prose only? [Clarity, plan §5, Constitution X]
- [ ] CHK121 Is the requirement that every relative markdown link added by these edits resolve stated, with the preference for backticked `scripts/check_project.py` over a link? [Coverage, plan §5]
- [ ] CHK122 Are FR-006's content standard and FR-007's "anchor, not coverage" caution phrased concretely enough that a reviewer can point at the prompt sentence satisfying each, rather than judging tone? [Measurability, FR-006, FR-007, SC-006]
- [ ] CHK123 Is FR-026's new step specified with **both** the exact command (`python3 scripts/check_project.py .`) and the required reaction when it reports, and is its position (after the step-4 merge) fixed? [Completeness, FR-026, SC-008]
- [ ] CHK124 Are SC-006 and SC-008 assigned to named rows in `docs/testing.md`'s manual checklist, rather than left as unassertable prose? [Traceability, Risk 10, Constitution XI run-output carve-out]

## Gates & dependencies

- [ ] CHK125 Are the four PR gates reproduced as verbatim commands, and is the one-off `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` run named as a pre-PR requirement together with its prerequisite `python3 scripts/make_testdata.py`? [Completeness, SC-004, quickstart §6–§7]
- [ ] CHK126 Is "no new runtime, dev or external-binary dependency" stated as an explicit requirement, and is the one hand-rolled piece (the bracket-depth scan) justified with the rejected alternatives named (`rapidfuzz`, `nltk`, `snowballstemmer`, a `\[([^\]]*)\]` regex)? [Clarity, FR-017, Constitution III, plan §Reuse check]

## Notes

- Items are requirement-quality questions. A `[ ]` that cannot be ticked means an
  artifact needs an edit, not that the build is broken.
- CHK101–CHK106 exist because the 32-card budget is the single constraint that
  turns a two-line content fix into a fifteen-assertion diff if it is missed.
