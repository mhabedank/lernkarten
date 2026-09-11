# Phase 0 research: practitioner material, goal fit, and source discovery

Six questions had to be answered before design. Three of them are the items
[spec.md](spec.md#open-items-deferred-to-planning) deferred to planning; three
came out of reading the two gates this feature has to bite on.

Nothing here reopens a clarification. The five round-1 answers and the round-2
answer are settled and are treated as given.

---

## R1 — A goal written after the sources are registered

**Question.** FR-001 assesses at registration; FR-008 forbids re-assessing on a
listing. A user who runs `/sources` first and `/learning-goal` second therefore
never receives an assessment for the material they already have. Is that
intended, and if so, what does the pipeline say about it?

**Decision. Accept the gap explicitly. No back-fill, no re-assessment, no new
state, and no change to `skills/learning-goal/SKILL.md`.** What ships instead is
one sentence, inside `skills/sources/SKILL.md`, saying that the assessment
happens at registration and that a goal written later does not re-judge the
register — and that sentence is gated by `check_docs.py`, so FR-008 stops being
a rule nobody can see.

**Rationale.** Every route to a back-fill breaks something already settled:

| Route | What it breaks |
|---|---|
| Re-assess every entry on a bare `/sources` | FR-008 verbatim. The task brief forbids widening it silently, and widening it loudly is a new clarification, not a plan decision |
| Re-assess only entries "not yet assessed" | Needs a per-entry *assessed* flag on disk. That is a verdict-shaped key in `sources.yaml`, which FR-007 refused for exactly the reason it would come back stale (Q2) |
| Have `/learning-goal` assess the register after writing `goal.md` | Contradicts the spec's own Scope statement (spec.md:13) that `/learning-goal` is untouched, and moves a `/sources` responsibility into a different skill |
| Prompt the user to re-register | An interactive gate in a skill that has none, and FR-002 just removed the one gate this feature was tempted to add |

The gap also costs the user very little, which is why accepting it is honest
rather than lazy: the assessment is advisory, it never gated anything, and the
material is already in the register. A user who wants the judgement re-runs
`/catalog`, which is where a goal-versus-material mismatch has always surfaced
and where it surfaces with the whole corpus in view rather than one entry at a
time.

**Where it is written.** The `## Goal fit` section of `skills/sources/SKILL.md`,
plus one ordering sentence in `docs/workflow.md` Step 1 ("set the goal before you
register your material — a goal written afterwards does not re-judge what is
already in the register"). Step 1 already carries ordering advice of this shape.

**Alternatives considered**: a `--reassess` flag on `/sources`. Rejected as
scope: it is a fourth mode of a skill this feature is already giving a second
one, and no requirement asks for it.

---

## R2 — Exercising FR-005's `kind`/`depth` weighting on one fixture

**Question.** `tests/fixtures/demo-project/goal.md` holds exactly one pair —
`kind: exam`, `depth: working`. FR-005 needs the weigh-up case (`depth: expert`,
or `kind: interview`/`meeting`) *and* the weigh-down case (`kind: exam` with
`depth: awareness`). Constitution VII and XI forbid a second corpus.

**Decision. Two named manual-checklist rows, both run against a scratch copy
made by `scripts/demo.py`, each changing exactly one word of the scratch
`goal.md`. The committed fixture is never edited.**

```bash
python3 scripts/demo.py /tmp/lk-demo          # copies goal.md verbatim
# weigh-down row: edit /tmp/lk-demo/goal.md   depth: working -> depth: awareness
# weigh-up row:   edit /tmp/lk-demo/goal.md   depth: working -> depth: expert
```

**Rationale.** `demo.py` already exists to produce a throwaway project and
already copies `goal.md` unconditionally (`scripts/demo.py:61-63`). A one-word
edit in a directory under `/tmp` is not a second corpus by any reading: nothing
is committed, nothing is invented, and the fixture on disk keeps the single pair
that `check_project.py` and `tests/test_check_project.py` assert against today.
The checklist row is where the edit belongs because the thing being exercised is
run output, which is already the checklist's job under FR-032.

`kind: exam` is already the fixture's value, so the weigh-down case needs the
`depth` word only. The weigh-up case is likewise one word. Neither row has to
touch `## Required topics`, so both keep every downstream check green if the
tester runs `check_project.py` on the scratch copy afterwards.

**Alternatives considered and rejected**:

- **A `--goal-kind` / `--depth` option on `scripts/demo.py`.** Constitution V:
  new code needs a reason, and the reason here would be to save a human two
  keystrokes inside a step that is manual anyway. It would also need its own
  test, so it costs more than it saves.
- **A second `goal.md` variant committed beside the fixture** (`goal-expert.md`).
  This is a second corpus wearing one file, and `.gitignore`'s
  `!tests/fixtures/**/goal.md` would admit it without anyone noticing.
- **Stating the scenario against the single fixture only** ("assume the goal said
  `awareness`"). Rejected: a checklist row a tester cannot actually perform is
  the failure mode FR-032 exists to prevent.

**Note for the same reason**: SC-003 and US2 need a project with **no**
`goal.md`. `demo.py` has no `--no-goal`, so those rows say `rm /tmp/lk-demo/goal.md`
— same mechanism, same reasoning.

---

## R3 — How many candidates discovery shows

**Question.** FR-027 requires the found and shown counts and requires grouping by
the required topic or area served, but sets no cap.

**Decision. At most **3** candidates per goal area, at most **10** shown in one
run, and **every** area of `## Required topics` gets a line — including the areas
where the count is zero.**

**Rationale.**

- **The cap has to be per-area first**, or FR-027's grouping requirement defeats
  itself: one popular area would fill a global list and an area with a single
  find would drop off the bottom, which is precisely the "a goal area nothing
  serves is visible as such" property the requirement is protecting.
- **Three is a choice, not a browse.** The user is picking sources to register,
  and the ordinary goal has three to five areas. Three per area gives a real
  alternative without turning the run into a search-results page.
- **Ten total keeps the proposal readable in one pass** for a goal with four or
  five areas, and the found count keeps the truncation honest — "found 31,
  showing 10" is information; a silently short list is not.
- **A zero line is not padding.** FR-027 wants the empty area visible, and the
  edge case "a goal with areas nothing findable serves" (spec.md § Edge Cases)
  says the run must say which areas it found nothing for rather than pad the
  list.

The numbers live in `skills/sources/SKILL.md` and in
[contracts/discovery-proposal.md](contracts/discovery-proposal.md). They are
prompt constants, so changing them later costs one edit and one checklist row.

**Alternatives considered**: "whatever fits one screen" (not statable in a prompt
and not checkable), and a global cap with no per-area limit (breaks FR-027's
visibility property, above).

---

## R4 — What the explicit discovery request looks like

**Question.** FR-035 fixes that discovery is entered only on an explicit request
at invocation and leaves the spelling to planning. The spelling matters more than
it looks, because FR-037 needs a *negative* check — that no other skill mentions
discovery — and a negative check needs an exact token.

**Decision. The canonical invocation is `/sources --discover`**, with the
natural-language equivalents ("find me sources for my goal", "look for material")
listed in the skill as the same entry. `--discover` is the token the gates read.

**Rationale.** A bare word is unusable as a gate. `discover` already appears in
the repository as `discovered` (`skills/catalog/SKILL.md:67`) and
`discovers` (`scripts/build_pdf.py:745`), so a substring check on it would fire
on prose that has nothing to do with this feature. The exact string `--discover`
appears **nowhere** in the repository today, which makes it a precise gate in
both directions:

- FR-030 asserts `--discover` **is** in `skills/sources/SKILL.md`;
- FR-037 asserts `--discover` is **absent** from `skills/ingest/SKILL.md`,
  `skills/catalog/SKILL.md`, `skills/cards/SKILL.md` and
  `skills/print/SKILL.md`.

The second one is the whole of FR-037 made mechanical: the moment someone adds
"you could run `/sources --discover`" to the `/catalog` report, the gate goes
red. It does not catch a paraphrase, which is why FR-037 also gets a named
manual row — but it catches the form the drift actually takes.

The flag spelling also matches the CLI vocabulary the project already uses
(`--strict`, `--grid`, `--sides`, `--dividers`), so it reads as an argument
rather than as a magic word.

---

## R5 — Where the stale network claim gate can safely look

**Question.** FR-034 says `check_docs.py` must fail if
`skills/research-gaps/SKILL.md:17`'s "the only step that reaches the network"
claim reappears; SC-010 says *anywhere*.

**Decision. A paragraph-scoped negative gate over `gated_files()`, with an
exclusivity-scoped claim regex** — the `check_print_order` shape
(`scripts/check_docs.py:561-572`), not a bare substring.

**Rationale.** A bare `reaches the network` regex has two live false positives
today:

| Hit | Why it is fine |
|---|---|
| `CONTRIBUTING.md:82` — "even reaches the network:" | a section heading about the test suite |
| `tests/test_deps.py:10` — "reaches the network." | outside `gated_files()`, but it shows how ordinary the phrase is |

The claim being forbidden is the **exclusivity**, not the network. So the regex
matches "only … that reaches the network" and nothing else, and the fix a
contributor reaches for is to qualify the sentence rather than to delete the
word — the house rule visible in `tests/test_check_docs.py:386-403`.

What replaces line 17 is fixed by FR-034 and US6 scenario 5: `/research-gaps`
and `/sources --discover` **go looking for material the user did not choose**;
`/ingest` **fetches what the user named**.

---

## R6 — Is a library or a dependency needed anywhere here?

**No, and none is added.** Constitution III makes this the first question rather
than the last, so it is answered explicitly:

- **Reading `goal.md`** — `scripts/check_project.py` already has the
  `frontmatter()` reader (lines 146-156) and `parse_goal()` (249-264). The
  skills read it as prose, which is what `/catalog` and `/cards` already do.
- **Reading `sources.yaml`** — `scripts/yamlio.py`, unchanged.
- **The new `nature:` key** — one tuple constant and one membership test beside
  `CONTENT_STATES` and `VISUAL_KINDS`. There is nothing to parse.
- **Reaching the network in discovery** — the web access Claude Code already
  has, exactly as `/research-gaps` uses it. No HTTP client, no crawler, no
  `requests`, no installation path for the user.
- **The negative doc gates** — `re`, already imported by `check_docs.py`.

So the answer to "is anything being hand-rolled that a library already does" is
**no**, and the Dependency Decisions section of the plan reads *no dependency
change*. If implementation discovers otherwise, that is a stop-and-flag, not a
`pip install`.

---

## What none of this settles

- **Whether the model's judgement is any good.** Constitution XI's carve-out and
  the spec's Assumptions both say the same thing: this feature asserts that the
  assessment exists, that it names a goal line and a source id, and that it never
  blocks. Whether the verdict is *right* is what reading a printed card is for.
- **Paginated archives beyond `depth: 1`.** Settled in clarification Q5 and out
  of scope here; the plan only carries the sentence `/sources` has to say.
