# Quickstart: validating the goal-driven catalog

How to prove this feature works, in the order the evidence arrives. Formats are
in [contracts/](contracts/), rules in [data-model.md](data-model.md), the ordered
red assertions in [plan.md](plan.md#test-plan-first).

## Prerequisites

```bash
cd <repo root>
python3 -m pip install -r requirements-dev.txt   # pytest, ruff, pillow, pyyaml
```

Nothing else. This feature adds no dependency and needs no typesetting engine —
the card build is untouched.

## 1. The four gates (must be green before the PR)

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

`check_docs.py` is the one that changes behaviour here: it gains the
domain-word rule on skill descriptions, and it will fail until `catalog` and
`ingest` have been retrofitted.

## 2. The automated evidence

```bash
pytest tests/test_check_project.py tests/test_check_docs.py -v
```

Each named case corresponds to a row in the Wave A–F tables of the plan. The
one to watch is the regression guard:

```bash
pytest tests/test_check_project.py -k "no_goal or without_status" -v
```

Those two prove SC-006 — a project with no `goal.md` is unaffected. If they ever
go red, the feature has stopped being optional.

## 3. The demo project end to end

```bash
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

Expected: exit 0, and the count line names topics, subtopics, sources and cards.
The extended fixture carries a `goal.md` with two areas, one `Status: gap`
subtopic, one `Status: out of scope` subtopic, one two-parent subtopic with its
reciprocal `Also covers:` line, one `Related:` pair, and one `research` source.

To see the checks bite, break one thing at a time in a scratch copy:

```bash
python3 scripts/demo.py /tmp/lk-demo
# then, in /tmp/lk-demo:
#   remove `kind:` from goal.md            → error naming the key
#   set `Status: irrelevant` on a subtopic → error naming subtopic and value
#   point a `Parents:` at a topic that is gone → error naming the dangling parent
#   delete an `Also covers:` line          → error naming the one-sided listing
#   drop `gap:` from the research source   → error naming the source id
python3 scripts/check_project.py /tmp/lk-demo
```

Every message must name the file **and** the culprit — that is the house style
the existing checks already follow (`catalog/topics.md: reference points nowhere
-> …`).

## 4. The manual checks

These are deliberately not automated, because nothing on disk records what a
skill *said* to the user. They belong on the checklist in `docs/testing.md`.

| Check | How | Expected |
|---|---|---|
| No-goal advisory | delete `goal.md` in a scratch project, run `/catalog` | says the catalog covers the material rather than the topic, points at `/learning-goal` |
| Out-of-scope reporting | run `/cards` on the demo project | a **count**, no warning, no list |
| Gap reporting | same run | a **warning** that the deck does not cover the whole topic, **naming** every gap, pointing at both ways to act |
| Goal conflict | run `/learning-goal` twice with contradictory briefs | every contradiction listed and asked; nothing written until answered |
| Narrowing consequence | make a required topic out of scope on the second run | names the catalog subtopics and card files affected |
| Borrowed subtopic | `/cards <secondary parent>` | cards generated once, and the user told which file they went into |
| No network | run `/research-gaps` offline | reports the gaps it could not close; writes nothing |

## 5. The visible surfaces

Read `docs/design.md` first — this feature changes visible things
(constitution XVI).

```bash
python3 scripts/render_brand.py          # banner, pipeline, social card
git diff --stat assets/                  # the three PNGs should be the only changes
```

Then open `docs/index.html` and check the step strip at three widths:

| Width | Expected |
|---|---|
| > 1080 px | every step legible; caption measure not visibly narrower than today |
| 541–1080 px | two columns; no step orphaned by accident — the rule re-derived for the new count, not inherited from the five-step one |
| ≤ 540 px | one column |

At every width the two optional steps must read as optional. See
[research.md](research.md#r3--how-do-seven-steps-fit-a-five-column-strip) for
why seven equal columns was rejected and what the measure arithmetic is.

## 6. Before the pull request

```bash
python3 scripts/make_testdata.py
LERNKARTEN_E2E=1 pytest tests/test_e2e.py
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

Plus the two things this feature specifically requires in the PR description:

- the **Principle VII note** — what user-content rule changed and why
  (`goal.md` added to `.gitignore`, `.githooks/pre-commit` and
  `tests/test_repo_hygiene.py`, with `!tests/fixtures/**/goal.md` letting the
  fixture back in);
- the **constitution amendment** — Principle I now enumerates five formats, and
  the Identity section no longer says the pipeline is five steps.

## Definition of done

- [ ] Every Wave A–F assertion was committed failing, on its assertion, before its implementation
- [ ] The four gates green; `--strict` green on the demo project
- [ ] `git grep -i "five commands"` returns nothing outside `specs/`
- [ ] The three brand PNGs re-rendered from Typst, not edited
- [ ] The manual table in §4 walked once, on a scratch project
- [ ] Branch is `feat/goal-driven-catalog`; `main` untouched
