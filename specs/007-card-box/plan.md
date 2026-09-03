# Implementation Plan: Ship the card box as a download

**Branch**: `feat/card-box` | **Date**: 2026-09-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-card-box/spec.md`

## Summary

`assets/card-box.pdf` exists, folds, and holds a deck. It is untracked,
`.gitignore` refuses it, and nothing links it. This feature commits it, publishes
it with the landing page, says beside the link which deck it fits, and amends
constitution VIII so a committed source-less PDF is a named exception rather than
a violation. No new code, no new dependency, no format change.

**Phase 0 and Phase 1 produced no separate artifacts.** There is nothing to
research beyond the two findings below, no data model (no data), and no contract
(no format change). A `research.md`, `data-model.md`, `contracts/` and
`quickstart.md` for a feature this size would be ceremony, and this scope was cut
specifically to avoid that. The two findings are recorded here instead.

## Findings

### F1 — The published site is one file, so the PDF is not reachable by a relative link

`.github/workflows/pages.yml` assembles the site as:

```yaml
mkdir -p _site
cp docs/index.html _site/index.html
touch _site/.nojekyll
```

`assets/` is never copied. Its own comment says so: *"The page is one
self-contained file, so the site is that file and nothing else."* A link to
`../assets/card-box.pdf` from the deployed page **404s**. That the existing page
reaches its social-card image through an absolute `raw.githubusercontent.com` URL
is the same fact, already worked around once.

The workflow also only triggers on `docs/index.html` and `pages.yml`, so adding
the PDF alone would not redeploy.

**Decision**: copy the PDF into `_site` and add it to the trigger paths.

```yaml
paths:
  - docs/index.html
  - assets/card-box.pdf          # + added
  - .github/workflows/pages.yml
...
cp docs/index.html _site/index.html
cp assets/card-box.pdf _site/card-box.pdf     # + added
```

The link is then `href="card-box.pdf"` — same origin, no external dependency, and
`tests/test_landing_page.py::test_the_page_stays_one_self_contained_file` stays
green because it inspects `<link rel=stylesheet>` and `<img src>`, not `<a href>`.

**Rejected**: linking `raw.githubusercontent.com/.../main/assets/card-box.pdf`.
Two lines smaller, but it makes the feature's whole deliverable depend on a
third-party host and hard-codes the `main` branch into the page.

### F2 — Three things the sheet says about itself are wrong, and cannot be fixed

Measured from `assets/card-box.pdf`:

| | The sheet prints | Measured |
|---|---|---|
| Orientation | `a4 landscape` | **portrait** — `/MediaBox 0 0 595.2 841.8`, no `/Rotate` |
| Card size | `cards 70 × 49 mm` | the A8 card at the default margin is **71.75 × 50 mm** |
| Grid | *(silent)* | **`a8` only** — an A7 card is 100 mm against a 73 mm opening |

Without a source these cannot be corrected, which is what FR-004 and FR-005 are
for: the documentation beside the download carries the true figures. The plan
must not let a test assert the sheet's own wording, because the wording is wrong.

## Technical Context

Unchanged from the project defaults in every respect that matters: Python
`>=3.12`, `pyyaml==6.0.3`, Typst 0.15.1 pinned, ruff, pytest. **This feature adds
no code, no dependency, no engine change and no format change**, so the
project-level context is untouched and is not restated here.

**Testing**: additions to `tests/test_repo_hygiene.py` and
`tests/test_landing_page.py`. No engine needed, so nothing is gated behind
`LERNKARTEN_E2E=1`.

## Dependency Decisions

**No dependency change.**

### Reuse check (constitution III)

**Is anything being hand-rolled here?** No — nothing is written at all.

## Constitution Check

| # | Gate | Pass? |
|---|---|---|
| I | Halves coupled only through the four file formats | [x] No format change |
| II | New dependency / binary rules | [x] N/A |
| III | Nothing hand-rolled | [x] N/A |
| IV | Dependency vetting | [x] N/A |
| V | Code lands in an existing module | [x] No new module |
| VI | Imports acyclic | [x] No import change |
| VII | No user content; nothing forced past `.gitignore` | [x] **Needs a PR note** — see below |
| VIII | No binaries committed | [x] **After FR-009** — see below |
| IX | Typst sources edited, never generated files | [x] N/A — no Typst source exists for this artifact, by decision |
| X | Skill frontmatter valid | [x] `skills/print/SKILL.md` body only |
| XI | **(NON-WAIVABLE)** Tested first, red on the assertion | [x] Test plan below |
| XII | Four gates pass | [x] |
| XIII | English throughout | [x] |
| XIV | Branch `<prefix>/<short-kebab-name>`; `main` untouched | [x] `feat/card-box` |
| XV | Engine version unchanged | [x] |
| XVI | `docs/design.md` read before a visible change | [x] Read in full; FR-005 adds the box section |
| XVII | Card style / Typst escaping | [x] N/A |

**On VIII**: this gate passes *because FR-009 makes it pass*. The artifact is a
committed binary, which VIII forbids except for a named list. FR-009 adds the box
to that list, on the same reasoning VIII already gives for the brand PNGs. The
amendment and the committed PDF must land in the same pull request — a PR that
commits the file without amending the principle leaves the repository
self-contradictory.

**On VII**: VII is about *user content*, and a project artifact is not user
content, so it passes. But this feature deliberately negates a `.gitignore` rule,
which is the same motion as the `git add -f` VII forbids. The difference is real —
a negation is visible in the diff, a forced add is not — and **the PR description
must say so**, so a reviewer is not left to infer it.

**Open-item check**: does not touch the constitution's one still-open item
(dependencies pinned by version rather than hash).

## Project Structure

```text
.gitignore                      # M negate *.pdf for assets/card-box.pdf
assets/card-box.pdf             # + committed, unchanged, as it stands
docs/index.html                 # M download link + the grid constraint beside it
docs/design.md                  # M new box section; the "buy a box" sentence
README.md                       # M name the box
skills/print/SKILL.md           # M one sentence after the cutting instructions
scripts/build_pdf.py            # M the "box you can buy" comment at :42
.github/workflows/pages.yml     # M copy the PDF into _site; add the trigger path
.specify/memory/constitution.md # M Principle VIII — widen the named exception
tests/test_repo_hygiene.py      # M committable, tracked, no stale sentence
tests/test_landing_page.py      # M the link and its caption
```

**Structure Decision**: no new file, no new module. Every change is a line or a
section in a file that already exists — which is the point of the reduced scope.

### The two halves

**Model-driven** (`skills/`): one sentence in `skills/print/SKILL.md`, after the
cutting instructions, naming the box and where to get it. **Run output** — it
leaves nothing on disk, so constitution XI's carve-out applies: it goes on the
manual checklist in `docs/testing.md` and is **named there**.

**Deterministic**: everything else, each with a red assertion below.

**The seam**: none.

## Test plan first

Constitution XI is non-waivable. Each assertion is red for a stated reason before
the change that makes it green.

| # | Assertion | Module | Red because |
|---|---|---|---|
| 1 | `ignored(["assets/card-box.pdf"]) == set()` | `test_repo_hygiene` | `.gitignore:43` is `*.pdf` — the file is uncommittable today |
| 2 | `"assets/card-box.pdf" in versioned_files()` | `test_repo_hygiene` | untracked today |
| 3 | the landing page links `card-box.pdf` | `test_landing_page` | no link |
| 4 | the text beside that link names `a8` **and** the default margin | `test_landing_page` | no text |
| 5 | the page is still one self-contained file, external sub-resources unchanged | `test_landing_page` | **regression guard, green from the start** |
| 6 | nothing versioned still says a box is one **you can buy** | `test_repo_hygiene` | `build_pdf.py:42` and `docs/design.md` both do |
| 7 | the Pages workflow copies the PDF into `_site` and triggers on it | `test_landing_page` | it copies only `index.html` |

Case 7 is the one that would otherwise ship a **404 as the feature's main
deliverable**, and it is invisible in local testing because the page works fine
from the filesystem. It is asserted against `pages.yml` as text, which is the only
thing a test can reach.

**On the manual checklist** (constitution XI carve-out, named explicitly, added to
`docs/testing.md`):

1. Follow the deployed link and confirm a PDF downloads.
2. Print at 100 %, measure the scale bar, fold, glue, fill with an A8 deck.
3. Read the caption beside the download and confirm an A7 user would stop.
4. The `/print` advisory sentence appears in a real run.

Steps 2 has been done once already, on the artifact as it stands. It is on the
list because nothing in the repository records that it was.

## Complexity Tracking

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| A committed binary with no source in the repository | VIII | The box is finished and does not need to change. Building a Typst source and a render script to regenerate a file nobody will edit is cost without benefit — the scope was cut for exactly this reason. | *Ship a Typst source and render script.* Specified in full, then rejected by the user as unnecessary complexity. The residual risk — that the box silently goes wrong if the card geometry ever changes — is written into spec.md as trade-off 5 rather than defended against. |
| Editing `.github/workflows/pages.yml`, which no other feature has needed to touch | — | Not a violation. F1 makes it the only way the download works at all. | *Link `raw.githubusercontent.com`.* Rejected: hard-codes `main` and puts the feature's deliverable on a third-party host. |

Principle XI has no row here. It is not waivable.
