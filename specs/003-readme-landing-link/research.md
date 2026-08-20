# Phase 0 Research: The README links the landing page up front

**Feature**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) ·
**Issue**: [#26](https://github.com/mhabedank/lernkarten/issues/26)

Six questions had to be answered before the design could be written. None of
them needed a spike; all six were settled by reading files already in the
repository, and each answer names what was read.

---

## R1 — Which test module carries the assertion?

**Decision**: `tests/test_repo_hygiene.py`.

**Rationale**: the boundary between the two candidate modules is already drawn,
explicitly, in the docstring of `tests/test_landing_page.py:1-19`:

> Separate from `test_repo_hygiene.py` on purpose. That module guards what the
> repository must not contain — user content, committed binaries — and its one
> landing-page check ("still promises five commands") belongs there because it
> guards a release from shipping a stale promise. The assertions here are about
> how the page is *built*, which is a different question.

The line that docstring draws is **"how the landing page is built"** versus
**"what a release ships in its docs"**. A claim about where a link sits in
`README.md` says nothing about how `docs/index.html` is built. It is the second
kind: a release must not ship a README that hides the live page.

The mechanical evidence points the same way. `test_repo_hygiene.py` already
reads `README.md` — `versioned_files()` at `tests/test_repo_hygiene.py:29`
returns every tracked path, and
`test_the_repo_does_not_still_promise_five_commands` at line 203 filters it down
to the `.md`/`.html`/`.typ`/`.yaml` files and reads their text. The new
assertion needs the same file, at the same level, with no new import.
`test_landing_page.py` by contrast is built around a single module constant,
`PAGE = ROOT / "docs" / "index.html"` (line 26), and an HTML parser; a README
assertion would have neither use for the parser nor a home under that constant.

**Consequences that become tasks** — both docstrings are made inaccurate by this
choice and have to move with it:

- `tests/test_repo_hygiene.py:1-5` scopes the module to "Guards that the repo
  stays subject-agnostic". That was already strained by the five-commands test;
  a second doc-text guard makes it plainly too narrow.
- `tests/test_landing_page.py:4-5` says `test_repo_hygiene.py` has "its **one**
  landing-page check". After this feature it has two.

**Alternatives considered**:

| Option | Rejected because |
|---|---|
| `tests/test_landing_page.py` | Its own docstring rules the case out, and its `PAGE` constant and `HTMLParser` machinery are for `docs/index.html`. `docs/testing.md:273` mentioning the buried README inside the landing-page section is about where the *issue* was noticed, not about which file the assertion reads. |
| A new `tests/test_readme.py` | Constitution V puts new code in an existing module where one fits, and one fits. A new module would also fall outside the placement table in constitution XI, which lists the seven test modules by name — adding a row to the constitution to hold two assertions is out of proportion to a one-line README edit. |

---

## R2 — How does a test say "the opening block", and how sharp can it get?

**Decision**: the opening block is **everything above the first `^## ` heading**,
found with `re.search(r"^## ", text, re.M)`. Within it, the link is pinned
between two stable anchors: it must appear **after** the last badge
(`Claude_Code-plugin`, `README.md:5`) and **before** the screenshot
(`assets/example-cards.png`, `README.md:13`).

**Rationale**: the first `##` is `## Install` at `README.md:15`, so the opening
block is lines 1–14: banner, three badges, the introductory paragraph, the
example-cards screenshot. That is exactly the region issue #26 calls "the top
block", and a heading offset is a structural boundary rather than a line number
that drifts with every edit.

The two anchors are the sharpest honest pinning available. Both are strings the
file is not going to lose casually: `Claude_Code-plugin` is a shields.io badge
URL, `assets/example-cards.png` is a committed file whose path
`check_docs.py` does not police but whose absence would be obvious. Together
they confine the link to the gap between the badge row and the screenshot —
which is precisely the region issue #26 offers ("next to the badges, or
immediately under the intro paragraph and before the first screenshot").

**What is deliberately *not* asserted**: whether the link sits above or below
the introductory paragraph *inside* that gap. The paragraph has no durable
anchor string — pinning to its closing words ("happened to contain.") would
make an ordinary copy edit break an unrelated test. That last increment of
placement is editorial, so under constitution XI's layout carve-out it goes on
the manual checklist instead of being faked into an assertion. The plan's test
list is written against what is genuinely assertable, not against what would
look thorough.

**Alternatives considered**: a line-number bound ("appears before line 15") —
rejected, it breaks on the first paragraph anyone adds. A regex for the exact
`**[See it →](…)**` string — rejected, it pins the wording, which FR-003 leaves
free.

---

## R3 — Does an absolute URL disturb the docs gate?

**Decision**: no. No change to `scripts/check_docs.py` is needed or wanted.

**Rationale**: `check_links` at `scripts/check_docs.py:169-178` walks every
markdown link in the root `*.md` files and skips any target starting with
`http://`, `https://`, `mailto:` or `#` (line 174) before resolving it against
the filesystem. A new `https://mhabedank.github.io/lernkarten/` link is skipped
outright; the existing relative `docs/index.html` link keeps being resolved and
keeps passing.

Making the gate reach the absolute URL would mean a network call, which would
fail the suite offline and during any GitHub Pages outage — FR-006 forbids it
for exactly that reason. Liveness of the URL stays on the manual checklist
(FR-007).

---

## R4 — Where does the manual half go, and what stale text must go with it?

**Decision**: a new row **33** at the end of the table under
`docs/testing.md` → "The landing page", and a rewrite of the closing paragraph
of that section.

**Rationale**: that section already carries the split-requirement rows 20–32 and
introduces them with the reason constitution XI requires. Its closing paragraph
(`docs/testing.md:271-273`) currently reads:

> Two things are known and are not regressions: the card toggle still does not
> explain itself (the open half of the issue that produced it), and the readme
> still buries the landing page.

That second clause **is** issue #26. Shipping the fix while leaving the sentence
in place would tell the next reader the bug is still open. `grep` confirms this
is the only occurrence anywhere outside `specs/`, so one edit closes it — and
"Two things" has to become "One thing", which is the kind of leftover a
find-and-replace misses.

The new row covers what no test reaches: that the link is *visible* on
github.com without scrolling past the intro, that it reads as an invitation to
look rather than to read, and that the URL actually loads.

**Alternatives considered**: a new "The README" subsection — rejected as
overweight for one row, and it would separate the row from the sentence it
supersedes.

---

## R5 — Reuse check: is anything being hand-rolled? (constitution III)

**Decision**: no, and no dependency is involved either way.

**Rationale**: the whole implementation is one inserted line of markdown plus an
assertion that reads a file, finds a heading offset with `re` and compares two
`str.index` results. `pathlib` and `re` are standard library and are already
imported across the test suite. There is no library to prefer here — the
question constitution III asks ("is there a library for this?") has no
meaningful candidate, because there is no problem of any size to delegate.

No runtime dependency, no dev dependency, no external binary, no engine bump.

---

## R6 — Does anything else in the repo point at the landing page, and would this duplicate it?

**Decision**: two pointers coexist by design; nothing else changes.

**Rationale**: `README.md:168-169` names the page twice over in one sentence —
the file `docs/index.html` and the URL `https://mhabedank.github.io/lernkarten/`.
The spec (FR-004) keeps the relative file link, because that is what a
contributor needs and what `check_docs.py` can actually verify. The new opening
link is the absolute URL, which is what a newcomer needs.

Whether the design section keeps its own copy of the absolute URL is left open
to implementation as a writing decision: the sentence reads a little redundantly
once the URL appears fourteen lines into the file, but FR-004 requires only the
`docs/index.html` link to survive. The drift risk of two absolute URLs is real
but small, and row 33 is where a stale one gets caught.

`docs/index.html` itself needs no change: it links back to the repository in
four places (`docs/index.html:407`, `424`, `726`, `753`) and never mentions the
README, so the return path is already there.

---

## Summary of decisions

| # | Question | Decision |
|---|---|---|
| R1 | Which test module? | `tests/test_repo_hygiene.py`; both affected docstrings updated with it |
| R2 | How to define "opening block"? | Above the first `^## `; link pinned between `Claude_Code-plugin` and `assets/example-cards.png`; exact spot relative to the intro paragraph left to the manual row |
| R3 | Docs gate impact? | None — `check_docs.py:174` skips absolute links; no network call is added |
| R4 | Manual half? | New row 33 under "The landing page" in `docs/testing.md`; the "still buries the landing page" sentence is rewritten |
| R5 | Hand-rolling / dependencies? | Neither. Standard library, no new dependency of any kind |
| R6 | Duplicate pointers? | Deliberate — absolute URL for the newcomer up top, relative `docs/index.html` for the contributor in `## The design` |

No `NEEDS CLARIFICATION` markers remain, and none were carried in from the spec.
