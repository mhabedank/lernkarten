# Cross-model review — 007-card-box

**Date**: 2026-09-01 · **Branch**: `feat/card-box` · **Reviewer model**: `fable`
(different from the model that wrote the artifacts, per `fleet-config.yml`
`models.review`) · **Mode**: read-only

## Summary

The artifact set is accurate where it points at code — every file/line reference
checked out. But the plan walks into a trap of its own measurement: **T005's
geometry assertion, written as tasked, can never go green**, because the helper it
reuses returns `(209.97, 296.97)` for this PDF while every existing use of that
helper asserts strict equality against `(210.0, 297.0)`. Two further problems are
about honesty rather than mechanics: the Principle VIII amendment claims "the same
logic" as the brand PNGs when the PNGs are regenerable and the box is not, and
Principle VIII's "short named list" is *already* incomplete — four committed
`.ttf` fonts are named nowhere.

**Verdict: NOT READY** — one blocking task edit plus four wording fixes.

| # | Dimension | Verdict |
|---|---|---|
| 1 | Spec–plan alignment | WARN |
| 2 | Plan–tasks completeness | PASS |
| 3 | Dependency ordering | PASS |
| 4 | Parallelization correctness | PASS |
| 5 | Feasibility & risk | **FAIL** |
| 6 | Standards compliance | WARN |
| 7 | Implementation readiness | WARN |

---

## Findings, most severe first

### 1. FAIL — T005's A4 assertion is red before *and* after implementation

`tests/test_e2e.py:662` rounds to two decimals. This sheet's MediaBox is
`0 0 595.2 841.8` — a Quartz A4 approximation, not true A4 (595.276 × 841.89 pt):

```
pdf_page_size_mm(assets/card-box.pdf) -> (209.97, 296.97)
```

Every existing caller asserts strict equality (`test_e2e.py:676`, `:684`). An
implementer copying that pattern writes an assertion nothing in this feature can
satisfy, the Phase 4 checkpoint is unreachable, and constitution XI's red → green
never completes.

The plan quoted the raw MediaBox in F2 and never converted it to millimetres,
which is exactly how it missed this.

**Fix**: assert within a 0.5 mm tolerance and that width < height. Correct
SC-002's "exactly A4 portrait" to match.

### 2. WARN — nothing pins the validated bytes

The spec's whole safety argument is "it was folded and used; this feature takes
that as proven". But the file was written today at 00:35 with `/Creator (Claude)`,
and no hash is recorded anywhere. T008's "commit it unchanged" is therefore
unenforceable — unchanged relative to what?

A silent re-export, now or in any later PR, passes every test in the plan while
invalidating the one physical validation the entire scope cut rests on.

**Fix**: pin a SHA-256 in the same test. One line turns "final" from a hope into a
rule, and it is the cheap half-measure against trade-off 5.

### 3. WARN — the amendment's "same logic" claim is false in the load-bearing part

FR-009 justifies the exception as "the same exception on the same logic" as the
brand PNGs. But the PNGs have committed Typst sources at `assets/brand/*.typ` and
a render script: they are committed *for convenience* and remain regenerable and
text-reviewable, which is why Principle IX can name them. The box is the
repository's **first artifact with no source of truth at all**.

The PNG exception trades regeneration effort. The box exception abandons
regenerability. An amendment that calls these the same reasoning misrepresents its
own precedent — and that misrepresentation is what the next source-less binary
will cite.

**On whether the amendment is legitimate at all**, the reviewer argued both sides
and concluded it is: Governance routes amendments through PRs explicitly; the
artifact is a shipped user deliverable rather than test material, so VIII's core
purpose (a text-reviewable test corpus) is untouched; it is write-once so the
history stays blob-free; and T003 makes the amendment asserted rather than
decorative. **But its legitimacy depends on the amendment being honest.**

**Fix**: T004 must state the distinction rather than paper over it, and
acknowledge that Principle IX's title now has a standing counterexample.

### 4. WARN — Principle VIII's named list is already wrong: the fonts

`assets/fonts/*.ttf` — four committed binaries — are named nowhere in VIII, which
says only "the brand PNGs". The repository already contradicts VIII today.
FR-009's own rationale ("a principle and a file that contradict each other, and
every future review re-discovers it") applies verbatim to the fonts and is left
unfixed by the very amendment invoking it.

**Fix**: name the fonts while the principle is open. They are the easiest case —
redistributable font files with no conceivable in-repo source.

### 5. WARN — spec Assumption 3 is false and was never corrected

spec.md says "GitHub Pages serves the PDF from the repository, so the landing page
can link it by relative path". Plan F1 proves the opposite and the plan acts on it;
nobody went back to the spec. A future reader taking the assumption at face value
repeats exactly the 404 the plan warns about.

**Fix**: correct the assumption to what F1 established.

### 6. WARN — two readiness gaps

- **`.gitignore` is last-match-wins.** `!assets/card-box.pdf` must sit **after**
  the `*.pdf` rule at line 43. T007's named model, `!cards/example.yaml`, is at
  line 14 — *before* it. Following "in the shape of" literally produces a dead
  negation.
- **T005's "reuse the helper"** leaves import mechanics unstated;
  `import test_e2e` from another test module executes that module's top level.

### Uncaught failure mode worth naming

A YAML syntax error in T009's `pages.yml` edit **merges green**: T006 asserts the
workflow as text, CI never executes it, and the first signal is a failed deploy on
`main`. The manual checklist item "follow the deployed link" is the only net, and
it runs post-merge.

---

## What the reviewer verified rather than assumed

- **F1 true end-to-end** — `pages.yml:35-38` copies only `docs/index.html`;
  triggers list only two paths; the og:image is indeed an absolute
  `raw.githubusercontent.com` URL, correctly excluded from `EXTERNAL_SUBRESOURCES`.
- **The regression guard holds** — `test_the_page_stays_one_self_contained_file`
  inspects `<link rel=stylesheet>` and `<img src>` only; an `<a href>` cannot fail it.
- **T013's filter warning true** — `test_repo_hygiene.py:232` skips anything not
  `.md/.html/.typ/.yaml`; the two offenders are `scripts/build_pdf.py:43` and
  `docs/design.md:179`.
- **PDF basics** — one page, portrait, no `/Rotate`. F2's orientation is right.
- **`git check-ignore`** — `.gitignore:43` blocks the file today; nothing else
  blocks `assets/`.
- **`check_docs.py`** link-checks markdown only; the README and design.md links
  will resolve.
- **All four `[P]` groups** touch pairwise-different files; the three load-bearing
  sequential edges are real.

## On the scope cut itself

> The reduced scope does not leave the project worse than doing nothing — doing
> nothing leaves a validated artifact unreachable and the A7/A8 mismatch
> undocumented anywhere. It is worse than the full version only on trade-off 5
> (geometry drift), which issue #45 predicted and the spec knowingly accepts.
> The cut is sound. The paperwork around it needs the fixes above.

## Orchestrator verification

The two load-bearing claims were re-checked independently before acting:

| Claim | Result |
|---|---|
| `pdf_page_size_mm` returns `(209.97, 296.97)`; callers assert `== (210.0, 297.0)` | **Confirmed** — `test_e2e.py:667` rounds to 2 dp; `:676` and `:684` are strict |
| Four `.ttf` files are committed and unnamed in VIII | **Confirmed** — `git ls-files assets/` shows 4 ttf; VIII names only the brand PNGs |

All six findings accepted. Remediation applied to `spec.md` and `tasks.md`; see
the *Review remediation* section in `tasks.md`.
