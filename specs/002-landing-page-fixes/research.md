# Phase 0 research: three landing page fixes

Five unknowns stood between the spec and a design. None of them is a dependency
question — this feature adds no package, no binary and no tool — so the usual
first question of constitution III ("is there a library for this?") has a short
answer: there is nothing to hand-roll and nothing to import. The unknowns are
about *verification* and about which of several correct CSS patterns fits a page
that is deliberately one file with almost no script.

---

## R1 — How does a landing page requirement become an assertion that fails first?

**Decision**: a new test module, `tests/test_landing_page.py`, at a new level
called *page* in the table in `docs/testing.md`. It reads `docs/index.html` from
the repo root as text and asserts structural properties of the source.

**Rationale**: constitution XI is non-waivable and needs a red assertion before
any implementation. Three candidates were considered:

| Where | Why not |
|---|---|
| `tests/test_repo_hygiene.py` | Its docstring scopes it to "the repo stays subject-agnostic" — no user content, no committed binaries. Feature 001 did put the "five commands" content check here (T072), and that check fits the file's *purpose* — it guards a release from shipping a stale promise. Structural CSS assertions do not. Adding them would leave the module's docstring describing a third of its contents. |
| `tests/test_check_project.py` | Contract level, and its contract is the artifacts of the model-driven steps — `sources.yaml`, `knowledge/`, `catalog/`, `cards/`. The landing page is written by hand, not by a skill. |
| `tests/test_e2e.py` | Runs `bin/lernkarten` and takes a PDF apart. The landing page never reaches the command. |

None fits, so constitution V's question ("which existing module was considered
first, and why did it not fit?") is answered by the table above rather than
waved away. The new module needs a docstring saying what it guards and why it is
separate.

**What it can and cannot assert.** This is the limit that shapes every task
downstream:

- **Can**: that a selector exists or does not; that an attribute is present on
  an element; that an element is or is not a child of another; that a media
  query contains a given declaration; that the file still holds exactly one
  `<script>` block and no external asset reference.
- **Cannot**: any rendered geometry. No test in this repo can measure that a
  heading row is 74 px rather than 126 px, or that a link is discoverable.

So every one of the three bugs splits in two, exactly as the spec's *Scope in
the Pipeline* section says: a structural assertion that goes red first, and a
named entry on the manual checklist for the part only an eye can settle.

**Parsing**: `html.parser` from the standard library, not a regex, for the
parent/child assertions — "is this `<p>` a child of that `<div>`" is a tree
question and a regex answering it would be the kind of thing constitution III
exists to prevent. Text-level matching stays fine for the CSS assertions, since
the page has no external stylesheet and `test_repo_hygiene.py` already reads
this file as text. No new dependency either way.

**Alternatives considered**: a headless browser (Playwright, Selenium) would
lift the "cannot" list entirely and let the row heights be asserted directly.
Rejected on constitution II: it is a runtime download of a browser, on three
platforms, for one page — friction far beyond what the feature is worth, and it
would make the test suite depend on a network fetch that `LERNKARTEN_E2E=1`-style
opt-in would then have to gate. Worth revisiting if the page ever grows a second
interactive control; not for this.

---

## R2 — Which no-JavaScript disclosure pattern for the mobile navigation?

**Decision**: `<details>` / `<summary>`, with `<summary>menu</summary>` as the
control. Below 760 px the summary shows and the link panel is disclosed by it;
above 760 px the summary is hidden and the panel is forced visible, so the bar is
byte-for-byte the row it is today.

**Rationale**: it is the only candidate that satisfies FR-002, FR-003 and FR-014
at once without inventing anything.

| Pattern | Accessible name | Works without JS | Keyboard | Cost |
|---|---|---|---|---|
| `<details>`/`<summary>` | native, from the summary's text | yes | native | none — no script, no ARIA plumbing |
| Hidden checkbox + `<label>` | only via added ARIA | yes | needs `tabindex` and key handling | a control with no semantics, described after the fact |
| `:target` | via the link text | yes | yes | hijacks the fragment, which this page already uses for `#how`, `#cards`, `#print`, `#install`; every open and close becomes a history entry |
| `<button>` + script | via the button's text | **no** | native | fails FR-003 |

`:target` deserves a second sentence because it is nearly attractive: opening the
menu would be `#menu` and clicking `#install` would close it as a side effect,
which is the behaviour you want. But the page's four nav links *are* fragment
links, so the menu state and the scroll target would be fighting over the same
piece of URL, and the back button would walk through menu toggles.

`<summary>menu</summary>` carries a word, not an icon. That is FR-002, and it is
constitution XVI's rule about colour and shape carried onto a control: a
hamburger glyph alone would be a meaning that only a visual conveys.

**The part that needs verifying before it is committed to**: forcing the panel
open above the breakpoint. The technique is to hide the summary and give the
panel an explicit `display`, overriding the user-agent rule that hides a closed
`details`' non-summary children. It is a standard responsive-nav technique and
works in current Chromium, Firefox and Safari, but the user-agent rule behind it
has changed shape over the years — it has been `display: none` on the slot and,
more recently, `content-visibility: hidden`. Against a `content-visibility` rule,
an author `display` declaration does not necessarily restore visibility.

**This is a spike, and constitution XI says spikes are thrown away.** The plan
carries it as its own task, before any implementation task: build the override in
a scratch file, open it in the three engines, keep the answer, delete the file.

### Spike result — the naive override fails

Run in Chrome 151.0.7922.138, headless, viewport 1200 × 800, measuring the
panel's `getBoundingClientRect()` above the breakpoint with the summary hidden.
The scratch file has been deleted; only these numbers survive it.

| Variant | Panel width | Verdict |
|---|---|---|
| A — `display: flex !important` on the panel alone | **0 px** | **fails** |
| B — A plus `details::details-content { content-visibility: visible !important }` | 57 px | works |
| C — fallback: `open` in the markup, summary hidden above the breakpoint | 57 px | works |

**The suspicion in the paragraph above was correct, and the failure is silent.**
Under variant A the panel's *computed* `display` reads `flex` and its own
`content-visibility` reads `visible` — everything an author would think to check
says the override took. It is laid out at zero width regardless, because current
Chrome wraps a `<details>`' non-summary children in a `::details-content`
pseudo-element and hides *that*:

```css
::details-content { content-visibility: hidden; }          /* UA */
details[open] ::details-content { content-visibility: visible; }
```

A `display` declaration on the child never reaches the pseudo-element. This is
the exact trap that made the spike worth running rather than reasoning about:
the naive version looks right in devtools and renders nothing.

**Decision: variant B**, and it turns out to be more robust than the fallback
rather than merely adequate. It covers *both* user-agent behaviours at once — the
older engines that hid the slot with `display: none` are handled by the
`display: flex !important`, the newer ones by the `::details-content` override,
and an engine that has never heard of the pseudo-element simply ignores that
selector. No feature query is needed.

**Variant C stays documented but unused.** It works, but it opens the menu on a
phone at load, which costs FR-004's one-line resting bar on exactly the viewport
the feature exists to fix.

**Verified in Chromium only.** Firefox is not installed on the machine this ran
on and Safari could not be driven headless there, so Gecko and WebKit are
unconfirmed. That is not a gap this repo can close in CI — there is no browser
leg — which is why it stays a named manual step (T039) rather than an assumption.

**Closing the panel after a tap** is deliberately *not* required. FR-003 asks
that the links be reachable without JavaScript, and they are. Closing is an
enhancement, and if it is added it extends the single existing `<script>` block
per FR-014 rather than adding a second.

**Consequential deletion**: once the panel is not an overflow container below the
breakpoint, `overflow-x: auto`, `scrollbar-width: none` and the
`.nav__links::-webkit-scrollbar` rule (`docs/index.html:101-103`) have nothing
left to do. The spec's *Dependency & Portability Impact* section asks for dead
code to be deleted rather than left; these three are it. The comment at
`:96-97` that explains the sideways scroll goes with them, replaced by one that
explains why the bar still refuses to wrap.

---

## R3 — How does the note leave the band without breaking the rules around it?

**Decision**: move the `<p class="band__note">` out of `<div class="band">` and
make it the band's next sibling, in all three sections. `.band__note` becomes a
full-width block with a bottom rule; the `@media (max-width: 1080px)` block loses
the three rules that existed only to fake this arrangement.

**Rationale**: the note is already a full-width block below the heading at every
width under 1080 px — `docs/index.html:293-296` gives it `width: 100%`, drops its
left border and adds a top border. The fix is therefore not a new layout. It is
the layout the page already uses on narrow screens, applied at every width, which
is why FR-007 says "at every viewport width" and why the reading order in SC-004
is unchanged: number, heading, note, content. That order is what the markup
already produces.

**Border arithmetic**, since FR-009 turns on it. Today the band carries
`border-bottom: var(--rule)` and the note carries `border-left` (or `border-top`
below 1080 px). Once the note is a sibling *below* the band, the band's existing
bottom rule already separates heading from note — so the note must take a
`border-bottom` and must **not** take a `border-top`, or the two would stack into
a 4 px rule. The `border-left` goes.

**The install section keeps working without a selector change.** `.install
.band__note` (`docs/index.html:257`) is a descendant selector rooted at the
section, not at the band, so it still matches after the `<p>` moves. Only the
property it sets changes: `border-left-color: var(--sand)` becomes
`border-bottom-color: var(--sand)`, and the `border-top-color` rule at `:296`
goes away with the rest of the 1080 px block. That satisfies FR-010.

**What must not be touched**: `.band { flex-wrap: wrap }` and `.band h2 {
flex-basis: calc(100% - 72px) }` at `:293-294` stay. They are not there only for
the note — section `02` has a `.toggle` in its band (`docs/index.html:502`),
which still needs to wrap to full width at 1080 px (`:297`). Deleting the wrap
because the note no longer needs it would break the toggle. This is the one place
where the change could quietly damage something the spec does not mention, which
is why User Story 2 has an acceptance scenario for the `02` band.

**Alternatives considered**:

- `align-items: flex-start` on `.band`, leaving the note in place. Fixes the
  heading row's height and is a one-word change — but the note then floats
  against the top of a row whose height it no longer sets, and the band's
  vertical rules stop reaching the bottom edge. It trades an inflated heading for
  a broken frame.
- Give the note `position: absolute` out of flow. Same objection, plus it needs a
  height reserved somewhere.
- Cap the note's height and let it scroll or clamp. Hides copy, which is the same
  class of mistake as issue #27.

---

## R4 — How is the `hidden` attribute made effective without setting a new trap?

**Decision**: one rule, `[hidden] { display: none !important; }`, placed with the
reset near the top of the stylesheet.

**Rationale**: the specificity arithmetic decides this, and it rules out the
gentler options. `[hidden]` is an attribute selector — specificity (0,1,0).
`.card` is a class — also (0,1,0). Equal specificity means source order decides,
and `.card` sits at `docs/index.html:146`, far below any reset. So a plain
`[hidden] { display: none }` in the reset **loses to `.card` and changes
nothing** — the bug would survive the fix.

That leaves three ways out:

| Option | Verdict |
|---|---|
| `[hidden] { display: none !important }` in the reset | **chosen** — wins regardless of order or specificity, and keeps winning against rules written later |
| `[hidden] { display: none }` at the very end of the stylesheet | works today, by order alone. The next `display` declaration written below it silently breaks it again — the same trap, moved |
| `.card[hidden] { display: none }` | (0,2,0), beats `.card`, fixes exactly this one element. Leaves the next element that gets `hidden` to fail the same way |

FR-012 asks for the attribute to be effective against *every* element, which is
the second and third options' undoing. `!important` is usually a smell; here it
is the correct tool, and for the reason the platform itself gives — `hidden` is
not a style preference, it is a statement that the element is not relevant. This
is what normalize.css and every modern reset do with the same rule, for the same
reason.

**Why the button already hides correctly and the cards do not**, recorded so the
fix is not mistaken for a wider one: `.toggle` (`docs/index.html:283-288`) never
declares `display`, so the user-agent rule reaches it untouched. That is why the
no-JS fallback works today — button invisible, both cards side by side. Adding
the global rule keeps that path exactly as it is: both cards are authored without
`hidden` (`:507`, `:527`) and only the script sets it.

**The risk this rule carries** is that it hides anything given `hidden`
unconditionally, including a future element that wanted `hidden` for semantics
while staying visible. That combination is incoherent, so the risk is
theoretical.

---

## R5 — Where do the manual entries go, and what do they say?

**Decision**: a new subsection in `docs/testing.md` under the manual checklist,
covering the landing page, with one numbered row per visual claim.

**Rationale**: the existing checklist (`docs/testing.md`, *The checklist*) runs
19 numbered steps and is entirely about the pipeline — `/sources` through
`/print`, then the printed sheet. It has no landing page row at all, so the three
visual claims have nowhere to land today.

Constitution XI's carve-out for layout is explicit that those requirements go on
the manual checklist and are **named there, never left implicit**. Three
requirements qualify, one per bug: that the nav is usable and its links
discoverable at 360 px; that all three heading rows are heading-height above
1080 px and the rules still frame the note; that the toggle swaps the visible
card and that both cards stand side by side with script off.

The rows also need to name *how* to look, since none of it is reachable from a
command. `docs/index.html` is a self-contained file, so opening it directly in a
browser is enough — no server, no build. The narrow-viewport rows say which
width, because "on a phone" is not reproducible and 360 px is.

**Alternatives considered**: leaving the visual half unrecorded and relying on
the pull request review. Rejected — that is precisely the "left implicit" the
constitution forbids, and it is how the three bugs got here in the first place.
