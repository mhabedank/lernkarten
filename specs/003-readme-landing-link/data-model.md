# Phase 1 Data Model: The README links the landing page up front

**Feature**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) ·
**Research**: [research.md](./research.md)

## Format changes

**None.** None of the four file formats that couple the two halves of the
pipeline (constitution I) is touched.

| Artifact | Change |
|---|---|
| `sources.yaml` | none |
| `knowledge/<id>/<doc>.md` frontmatter | none |
| `catalog/topics.md` structure | none |
| `cards/*.yaml` schema | none |

Nothing on a user's disk is read or written by this feature, so there is no
migration, no compatibility window and no `check_project.py` rule to add. That
is the whole of the format story; the rest of this file describes the only
structure the new assertion actually reasons about.

## The one structure involved: the regions of `README.md`

The test does not parse markdown. It slices one string into regions using
anchors that are already in the file, and asserts where a URL falls among them.
Naming the regions here keeps the assertion and the prose describing it from
drifting apart.

| Region | Bounded by | Today | After |
|---|---|---|---|
| **Opening block** | start of file → first `^## ` heading | `README.md:1-14` | same bounds, one line longer |
| ├ Banner | `![…](assets/banner.png)` | line 1 | unchanged |
| ├ Badge row | three `[![…](https://img.shields.io/…)](…)` lines, last one carrying `Claude_Code-plugin` | lines 3–5 | unchanged |
| ├ Intro paragraph | prose between the badges and the screenshot | lines 7–11 | unchanged |
| ├ **Landing link** | a markdown link whose target is `https://mhabedank.github.io/lernkarten/` | *absent* | **inserted here** |
| └ Screenshot | `![…](assets/example-cards.png)` | line 13 | unchanged |
| **Body** | first `^## ` → end of file | `README.md:15-189` | one section edited |
| └ `## The design` | that heading → the next `^## ` | lines 165–170 | keeps its `docs/index.html` link |

### Anchors, and why each was chosen

| Anchor | String | Why it is durable |
|---|---|---|
| Region boundary | `^## ` (multiline) | Structural. Survives any amount of editing inside the opening block; the first heading is `## Install`. |
| Lower bound | `Claude_Code-plugin` | Part of a shields.io badge URL, not prose. Changing it means changing the badge. |
| Upper bound | `assets/example-cards.png` | A committed file path. Changing it means moving the file. |
| Target | `https://mhabedank.github.io/lernkarten/` | The GitHub Pages URL, identical to the one already at `README.md:169`. |
| Contributor link | `docs/index.html` | A relative path `check_docs.py` independently resolves (`scripts/check_docs.py:169-178`). |

Deliberately **not** an anchor: any words from the introductory paragraph, and
the link text itself. Both are prose that a copy edit may legitimately change;
pinning either would make an unrelated edit break this test. See
[research.md](./research.md) R2.

### The invariants the assertion states

Let `opening` be the opening block as bounded above.

1. `LANDING_URL in opening`
2. `opening.index("Claude_Code-plugin") < opening.index(LANDING_URL)`
3. `opening.index(LANDING_URL) < opening.index("assets/example-cards.png")`
4. `"docs/index.html" in README.md` (the `## The design` reference survives)

Invariants 1–3 are FR-001 and FR-002 and live in
`test_the_readme_points_a_newcomer_at_the_landing_page`; invariant 4 is FR-004
and lives in `test_the_readme_still_names_the_landing_page_source`. The first
case fails against `main` today on invariant 1 — the red the constitution asks
to see before anything is written. The second passes on `main` by construction,
because it guards behaviour that already exists, so what proves it load-bearing
is deleting the link and watching it fail (FR-005b).

## Entities

None. No data is modelled, stored or exchanged; there is nothing with fields,
relationships or state transitions. This section is kept only to say so
explicitly rather than leave a reader wondering whether it was forgotten.
