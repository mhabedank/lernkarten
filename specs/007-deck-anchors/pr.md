# PR description — feat/deck-anchors

*(Two things a reviewer would otherwise have to infer are stated explicitly: why
A-1 is opt-in rather than automatic, and why the demo deck is pinned at exactly
32 cards.)*

---

## The deck has to name what it uses

Closes #49.

`depth` was documented as a ceiling and implemented as a slice.
`skills/learning-goal/SKILL.md` introduced it as *"`depth` sets how far the cards
go"*, and its three levels read as mutually exclusive. Nothing said `expert`
**includes** the two below it, and `skills/cards/SKILL.md` never mentioned
`goal.md` or `depth` at all. So at `depth: expert` the deck came out arguing edge
cases about concepts no card ever named.

The failure is invisible card by card. Every individual card is well-formed,
atomic and passes `lernkarten check`. The defect exists only at the level of the
whole deck, and the question that surfaces it — *which terms does this deck use
but never name?* — is one no reviewer asks while reading cards one at a time.

### What changed

| File | Change |
|---|---|
| `scripts/check_project.py` | **A-1** (anchor) and **A-2** (list orphan), +194 lines |
| `skills/learning-goal/SKILL.md` | `depth` is a ceiling: `expert` implies `working` implies `awareness` |
| `skills/cards/SKILL.md` | the anchor rule, the no-`#list`-only-introduction rule, and a new step 6 that runs `check_project.py` |
| `skills/catalog/SKILL.md` | the `Term:` line — documented **and** instructed |
| `CLAUDE.md`, `docs/testing.md` | the convention and three manual rows (`8l`, `11d`, `12-iii`) |
| `tests/fixtures/demo-project/` | seven `Term:` lines, one added card, four rewords, a README section |
| `tests/test_check_project.py` | +233 lines |

### The two checks

**A-1 (anchor)** — for each `(card file, subtopic)` pair, a card *under that
subtopic in that file* must name one of the subtopic's aliases. The aliases come
from a new optional `Term:` line in `catalog/topics.md`.

**A-2 (orphan)** — every item in a `#list([…])` back must appear on another card
in the same file. Items containing a `$` are skipped, so a card that argues in
symbols is not read as an enumeration of labels.

### Two things worth a reviewer's attention

**1. A-1 is opt-in, and that is the design, not a compromise.**

The obvious rule — match the subtopic heading against the card text — was
measured against the demo project and passes **1 of 9** card-bearing subtopics.
The one pass is an accident (`Tidenhub` matching inside `Nipptidenhub`). The
killer is not description-headings (1 of 12) but `X and Y` conjunctions (4 of
12). A content-word variant reaches 7 of 9 but fires on every non-English pair:
an English catalog heading cannot match Greek or Cyrillic card text, ever.

So the term is declared rather than guessed. `Term:` absent means A-1 says
nothing — the same shape `Status:`, `Parents:` and `Related:` already have, and
the reason no existing catalog needs editing.

The cost is real and worth naming: **the cheapest way to pass A-1 is to write no
`Term:` line.** That is why `skills/catalog/SKILL.md` does not merely document
the format — step 5 instructs `/catalog` to write the line wherever a heading
names a concept. A format the prompts never write is a dead format.

**2. The demo deck is pinned at exactly 32 cards.**

`tests/test_e2e.py` asserts bare page-count literals in about thirteen places
rather than deriving them from `DEMO_CARD_COUNT`. At 32 cards four assertions
move; at 33 roughly fifteen do, including structural ones. So every gap except
one is closed by *rewording* an existing card rather than adding one.

An earlier draft held the budget by withholding `Term:` lines from three
subtopics that are themselves instances of this bug — which would have shipped a
fixture demonstrating the evasion, certified green. All three are anchored by
reword instead. `Nipptidenhub` and `Springtidenhub` are deliberately left alone:
they demonstrate that a substring is not a match.

This pin is a symptom worth a follow-up — the literals should derive from
`DEMO_CARD_COUNT`. That is a separate change and out of scope here.

### Test-first

Four commits, in order: the red cases, then the checks, then the fixture, then
the prompts. The three red tests failed on their **assertions**, never on an
`AttributeError` — no test in the red commit names a function that does not exist
yet, and the helper unit tests deliberately sit in the implementation commit for
that reason.

`test_the_demo_project_is_consistent` went red on its own when A-2 landed, on two
genuine orphans in `geography.yaml` (`Skarn` and `Bellhorn`), and green again when
the fixture was fixed.

### Verification

Four gates green; 550 tests passing; e2e green under `LERNKARTEN_E2E=1`. Seven
edge cases were probed directly against the built checks: a substring does not
anchor, per-file binding holds, the spaced-hyphen head term cuts correctly, maths
items are skipped, `Term:` on a topic is ignored, and an empty `Term:` errors.

### Not done

`docs/testing.md` row `12-iii` — driving `/cards` in a real session to watch the
new step fire — has not been run. It needs an interactive session against a
scratch project.
