# Quickstart: validating "The README links the landing page up front"

**Feature**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) ·
**Research**: [research.md](./research.md) ·
**Structures**: [data-model.md](./data-model.md)

This is the run guide, not the implementation. It says how to prove the feature
works — including how to prove the test was red first, which constitution XI
requires and which is the only step here that has to happen in a particular
order.

## Prerequisites

Nothing beyond a checkout and Python 3.12+.

```bash
python3 -m pytest --version     # any pytest from requirements-dev.txt
```

No typesetting engine, no `pdftotext`, no network. Neither `LERNKARTEN_E2E` nor
`LERNKARTEN_DEPS_NET` is involved: nothing in this feature builds a PDF or
installs a package, so the full suite runs offline exactly as it does in CI.

## 1. Watch it fail (mandatory, and mandatory *first*)

With the new assertion committed and `README.md` untouched:

```bash
python3 -m pytest tests/test_repo_hygiene.py -k points_a_newcomer -q
```

**Expect**: one failure, on the assertion — not on an import, not on a
`FileNotFoundError`. The message names `README.md`. Anything else means the test
is not red for the right reason and does not count as the red step.

Capture that output for the pull request. This is the artifact the constitution
asks for, and it cannot be reconstructed after the README is edited.

## 2. Make it green

Edit `README.md` only. Then:

```bash
python3 -m pytest tests/test_repo_hygiene.py -q
```

**Expect**: green, including
`test_the_repo_does_not_still_promise_five_commands`, which reads the same file
and must not have been disturbed.

## 3. The four gates

The same four commands CI runs, in the order `CLAUDE.md` gives them:

```bash
ruff check . && ruff format --check .
python3 -m pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

**Expect**:

| Command | Expected |
|---|---|
| `ruff check` / `ruff format --check` | clean — the only Python touched is one test module |
| `pytest` | all green, and **no test that ran before is now skipped** (SC-004) |
| `lernkarten check cards/example.yaml` | unaffected; it never reads `README.md` |
| `check_docs.py` | `OK: … skills, version …, docs links and required files are fine.` The new absolute URL is skipped by design (`scripts/check_docs.py:174`); the relative `docs/index.html` link still resolves |

## 4. Read the result the way a newcomer would

The part no command can check. This is manual-checklist row 33, and it is done
by eye:

```bash
python3 -c "import pathlib,re; t=pathlib.Path('README.md').read_text(); print(t[:re.search(r'^## ', t, re.M).start()])"
```

That prints the opening block exactly as the test bounds it. Read it and ask:

1. Does the link appear before the screenshot, near the intro paragraph?
2. Does it read as an invitation to *look*, not to read further?
3. Open `https://mhabedank.github.io/lernkarten/` in a browser — does it load,
   and is it the page you expected?

Then, on the pull request page on github.com, check the rendered README: the
link should be visible without scrolling past the intro paragraph on an ordinary
laptop window.

## 5. Confirm the stale note is gone

```bash
grep -rn "buries" . --exclude-dir=.git --exclude-dir=specs
```

**Expect**: no output. Before the change this returns `docs/testing.md:273`.
`specs/` is excluded because it records what was true when each feature was
specified — the same exemption
`test_the_repo_does_not_still_promise_five_commands` makes.

Then read the rewritten paragraph at the end of the "The landing page" section
of `docs/testing.md`: it must no longer say "Two things" if it now lists one.

## What "done" looks like

| Success criterion | Proved by |
|---|---|
| SC-001 | Step 1 red, step 2 green |
| SC-002 | Step 4 — the link is inside the printed opening block, which is the first 14 lines |
| SC-003 | Step 3, the `check_docs.py` row |
| SC-004 | Step 3, all four commands |
| SC-005 | Step 5, plus row 33 present in `docs/testing.md` |
