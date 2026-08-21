# Feature Specification: A short, stable card id

**Feature Branch**: `feat/card-id`

**Created**: 2026-08-21

**Status**: Draft

**Input**: GitHub issue [#59](https://github.com/mhabedank/lernkarten/issues/59) — "The card id names a position, not a card — and it is too long to say", plus its decision comment. Prerequisite for #60 (revision history and `A45DK@2` addressing).

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: `/cards` (assigns the id), `/print` (renders it), build machinery (`scripts/build_pdf.py`, `scripts/check_project.py`, `templates/card.typ`, `bin/lernkarten`)

**Implementation half**:

- [x] **Both** — the seam is the `cards/*.yaml` schema. The model-driven half (`skills/cards/SKILL.md`) must write a new top-level `id:` key on each card it creates; the deterministic half must generate ids for backfill, validate them, and render them. Nothing else crosses the seam: the deterministic half never asks the model for an id, and the model never has to compute a collision.

**Who runs into this**: **both**. The user driving Claude wants to say "A45DK needs splitting" and be understood; a contributor to this repo runs `lernkarten check` and needs a duplicate id to be reported rather than printed twice.

## Clarifications

### Session 2026-08-21

- Q: How many Crockford Base32 characters should a card id be? (FR-003) → A: **5.** In-project uniqueness is guaranteed by redraw-on-collision (SC-001), so length only prices the case redrawing cannot fix — two separate projects that assign ids independently and are later mixed. The issue puts that at ~21 % for 4 characters against under 1 % for 5, across two 500-card decks. The extra character costs one syllable and a few points of footer width, and the decision is irreversible, so the asymmetry favours 5.
- Q: On a genuine id collision, should the tool refuse or reassign automatically? (FR-013) → A: **Reassign automatically, and report it.** This was chosen over refusing with the tradeoff stated: a reassigned id stops resolving in past conversations and orphans any #60 history recorded against it, which is the harm issue #59 was filed to prevent. It is accepted deliberately, in exchange for merges that always complete. Three consequences follow and are specified rather than left implicit — reassignment is confined to the writing path (FR-013a), it is deterministic so it can be tested and predicted (FR-013b), and every reassignment reports the cost it just incurred (FR-013c).
- Q: When two decks collide on an id, which card keeps it? (FR-013b) → A: **First occurrence wins**, ordered by the files as given on the command line, then card order within each file. Chosen because it is the only rule the user can steer: argument order is under their control, so putting the deck whose ids they actually cite first preserves those ids. Lexicographic ordering was rejected as unsteerable without renaming files, and a longest-held rule was rejected because it would need a per-card timestamp — a schema key this feature does not otherwise require.
- Q: Should `/print` be able to select a card by id (`--card A45DK`)? (FR-014) → A: **Out of scope — its own ticket.** This feature already carries a schema contract change, the project's first YAML writer and a change to the printed card, and the issue rates it risk 9 of 12. Adding an addressing scheme widens the blast radius of a change whose irreversible parts most need to ship clean. `--card` costs no more later and carries no reversibility risk of its own.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Name a card in conversation, and have the name keep pointing at it (Priority: P1)

The user has a printed deck on the desk. One card uses the word "GAN" without ever defining it. They read the id off the bottom-right corner — `A45DK` — and type it into their Claude session: *"A45DK uses GAN without defining it, and 'displaced' is a strange word here. We need another card."*

Claude resolves `A45DK` against `cards/*.yaml` in the open project, finds the card, and edits it. It then adds the new card the user asked for. **After both edits, `A45DK` still names the same card** — which is the whole point, because the conversation that identified the problem is the conversation that caused the edit.

**Why this priority**: This is the request. Every other story exists to make this one safe or possible.

**Independent Test**: In a scratch project, note the id of the 3rd card in a deck. Insert a card before it, delete a different card before it, and rename the file. Re-read the deck: the noted id is still on the same card (same `front`/`back`). Today all three operations change it.

**Acceptance Scenarios**:

1. **Given** a deck where card 3 has `id: A45DK`, **When** a new card is inserted at position 1 and the deck is re-read, **Then** the card whose `front` is unchanged still reports id `A45DK`, and no other card in the file has taken that id.
2. **Given** the same deck, **When** card 1 is deleted, **Then** the remaining card still reports `A45DK`.
3. **Given** the same deck, **When** the file is renamed from `topic-a.yaml` to `topic-b.yaml`, **Then** every id in the file is unchanged. (Today every id changes, because the file stem is the id prefix.)
4. **Given** the same deck, **When** the card's `front` and `back` are both edited, **Then** the id is unchanged. (This is what rules out deriving the id from a content hash, and what #60 depends on.)
5. **Given** a deck built with `--subtopic` filtering, **When** the same deck is built unfiltered, **Then** each card carries the same id in both builds.

---

### User Story 2 - Existing decks keep working untouched (Priority: P1)

A user who wrote card files by hand before this feature existed runs `lernkarten build cards/*.yaml`. Their files have no `id:` key anywhere. **The build succeeds and produces a PDF.**

**Why this priority**: Equal to P1 because shipping this without it breaks every project on disk. Constitution Principle I treats the `cards/*.yaml` schema as a contract; adding a required key to it would be a breaking change, and this feature does not get to be one.

**Independent Test**: `lernkarten build tests/fixtures/demo-project/cards/*.yaml` on the demo decks with no `id:` keys added — exit code 0, expected page count.

**Acceptance Scenarios**:

1. **Given** a card file with no `id:` key on any card, **When** `lernkarten build` runs, **Then** it exits 0 and produces a PDF with the correct page count.
2. **Given** a card file with no `id:` key, **When** `lernkarten check` runs, **Then** it exits 0 — a missing id is not an error — and it prints **one** advisory line naming the backfill path, once per run rather than once per card. *(The advisory leaves nothing on disk, so per Principle XI its wording is a manual-checklist item in `docs/testing.md`; the exit code is the assertable part.)*
3. **Given** a card file where *some* cards have an `id:` and others do not, **When** the deck is built, **Then** it still builds, and the cards without one are handled by the same rule as a file with none.

---

### User Story 3 - The id is legible on the printed card (Priority: P1)

The user picks a card off the desk and reads its id without leaning in. Today they cannot: the measured example id renders **124.62 pt wide against a 94.49 pt box** that has `clip: true`, so it is cut off on the printed card.

**Why this priority**: An id you cannot read off the card cannot be said aloud, which is User Story 1's entry point. The current scheme fails at its own job here, independently of stability.

**Independent Test**: Measure the rendered id block through the real engine (typst 0.15.1) at the chosen size and assert its width against the `cw / 3` cap — measured, not eyeballed.

**Acceptance Scenarios**:

1. **Given** a card with the longest id the alphabet and length permit, **When** the footer is measured through the pinned engine at the chosen type size, **Then** the rendered width of `<id> · 1/2` is **strictly less than** the id block's cap, so nothing is clipped.
2. **Given** the same card, **When** the id type size is compared to the current 4.6 pt, **Then** it is **larger** — the short id uses ~29 % of the cap at 4.6 pt, and the issue measures 8 pt at 48.2 pt wide, still comfortably inside.
3. **Given** a card that has no id, **When** it is rendered, **Then** the footer is still well-formed — the wordmark and the side marker keep their positions and nothing overlaps.

---

### User Story 4 - Backfill ids into a hand-written deck (Priority: P2)

A user with existing decks wants ids without rewriting six files by hand. They run `lernkarten id --backfill cards/*.yaml`. Every card that lacks an `id:` gets one; **every card that already has one keeps it**; and the files come back with their comments and quoting intact.

**Why this priority**: P2 because P1 already guarantees those decks still *build*. This is the upgrade path, not the survival path.

**Independent Test**: Run backfill over a fixture deck that has comments, single-quoted card text, and a mix of carded and uncarded entries. Assert every card now has a unique valid id, the pre-existing ids are unchanged, and the comments survive.

**Acceptance Scenarios**:

1. **Given** a deck with no ids, **When** `lernkarten id --backfill` runs, **Then** every card has a unique id drawn from the agreed alphabet and length.
2. **Given** a deck where 2 of 5 cards already have ids, **When** backfill runs, **Then** those 2 ids are byte-identical to before and the other 3 are new and distinct from them.
3. **Given** a deck with `#` comments and single-quoted Typst markup (`'first\ *bold* rest'`), **When** backfill runs, **Then** the comments are still present and the card text is byte-identical — backfill must not reformat the file around the key it inserts.
4. **Given** a deck that has already been backfilled, **When** backfill runs a second time, **Then** the file is unchanged (idempotence).
5. **Given** a deck that is not writable, or malformed YAML, **When** backfill runs, **Then** it reports the file and the reason and leaves every file untouched — no partial rewrite.

---

### User Story 5 - A broken id is reported, not printed (Priority: P2)

A user merges two decks, or hand-types an id, and ends up with a duplicate, a wrong length, or a character outside the alphabet. `lernkarten check` / `scripts/check_project.py` names the problem and both cards involved — and **changes nothing**. If the user instead runs the writing path over the merged decks, the duplicate is resolved by reassignment (FR-013) and reported.

**Why this priority**: P2 — it protects the guarantee User Story 1 rests on. Without it a duplicate id silently makes two cards answer to one name, which is exactly the failure the feature exists to remove. The read-only/writing split matters here: the checker is a CI gate, so it must report and stop; only the writing path may resolve.

**Independent Test**: Point the checker at a fixture deck carrying a deliberate duplicate, a deliberate `I`/`L`/`O`/`U` and a wrong-length id, and assert on the messages, the non-zero exit, and that the fixture files are byte-identical afterwards.

**Acceptance Scenarios**:

1. **Given** two cards in one project sharing an id, **When** the checker runs, **Then** it exits non-zero and the message **names both cards** — file and card — not just the id.
2. **Given** a card whose id contains a character outside the alphabet (`I`, `L`, `O`, `U`, or punctuation), **When** the checker runs, **Then** it exits non-zero and names the file, the card and the offending character.
3. **Given** a card whose id is the right alphabet but not exactly 5 characters (`A45D`, `A45DKM`), **When** the checker runs, **Then** it is reported the same way, naming the length it found.
4. **Given** a card id written in lower case (`a45dk`), **When** the checker runs, **Then** it is accepted and treated as equal to `A45DK` — Crockford decoding is case-insensitive, so a user typing what they read must resolve.
5. **Given** two decks sharing an id, **When** the **writing** path runs over both, **Then** the card appearing later in command-line order is reassigned, the earlier one keeps its id, and the report names the card and both ids.
6. **Given** the same two decks, **When** the **checker** runs over both, **Then** it exits non-zero and every input file is byte-identical afterwards — the checker reports the duplicate but never fixes it.

---

### Edge Cases

- **Missing optional tooling**: id generation and validation are pure text work and must not need the engine. `lernkarten id --backfill` must work with **no typesetting engine present** — it never renders. Only User Story 3's measurement needs the engine, and that test skips without it, as the e2e suite already does.
- **Fresh install on each platform**: no new external binary and no manual step, so Windows/macOS/Linux are unaffected — provided the backfill writer does not depend on a platform-specific newline. Backfill must preserve the file's existing line endings rather than normalising them.
- **Python floor**: 3.12. Nothing here needs anything newer.
- **Encoding and file names**: backfill reads and writes UTF-8 and must round-trip umlauts and non-Latin card text unchanged. A deck that fails to parse is reported, never partially rewritten.
- **Non-Latin card text**: ids are drawn from a Latin/digit alphabet regardless of the card's language, so a Greek or Cyrillic deck gets ordinary ids. The id font (IBM Plex Mono) already covers them.
- **Idempotence**: covered explicitly in User Story 4 scenario 4 — running backfill twice changes nothing.
- **Text that does not fit**: User Story 3 turns this from a silent clip into a measured guarantee. The existing overflow reporting for `front`/`back` is untouched.
- **A card language nothing can hyphenate**: unaffected; the id is not hyphenated.
- **Empty deck**: a file with `cards: []` or `cards:` null must backfill to a no-op and still build.
- **Two projects merged on one desk**: a physical stack from two decks can collide. The header band already prints topic and subtopic on every face, so a human can still tell them apart; see the Assumptions. Where the decks are merged *on disk* rather than on the desk, FR-013 applies: the writing path reassigns the later card and says so.
- **A collision the user did not intend to resolve**: because reassignment is automatic (FR-013), a user who merely runs the writing path over two decks to inspect them will silently — well, audibly, per FR-013c — change one card's identity. The report is the only thing standing between that and a lost reference, which is why FR-013c requires it to state the consequence rather than just the substitution.
- **A card whose `id:` is present but empty or not a string** (`id:`, `id: 12345`, `id: [a]`): must be reported as a malformed id naming the file and card, not crash and not be silently treated as absent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A card MUST be able to carry an `id` stored as a key in `cards/*.yaml`. The id MUST NOT be derived from the card's position in the file, from the file name, or from the card's content.
- **FR-002**: The `/cards` skill MUST assign an id to every card it writes, and MUST NOT change the id of a card it edits.
- **FR-003**: An id MUST be **exactly 5 characters** drawn from **Crockford Base32** — the 32 symbols `0-9` and `A-Z` excluding `I`, `L`, `O` and `U` — giving an id space of 32⁵ = 33,554,432. The length is fixed project-wide and MUST NOT be configurable: a variable length would reintroduce exactly the ambiguity the fixed alphabet removes, and #60 addressing (`A45DK@2`) parses against it.
- **FR-003a**: Assignment MUST guarantee uniqueness within the project by checking ids already in use and redrawing on a clash, so an in-project collision is never surfaced to the user. This is what makes the 5-character choice about cross-project mixing rather than in-project safety.
- **FR-003b**: Redrawing MUST terminate. Assignment makes a bounded number of attempts per id; if it cannot find a free id within that bound it MUST fail with an error naming the project's id count and the bound, and MUST NOT write anything. At 5 characters this is unreachable in practice — it exists so that exhaustion surfaces as a stated error rather than as a hang.
- **FR-004**: Id comparison MUST be case-insensitive, and the confusable characters MUST decode back per the Crockford rules, so a user who types `a45dk`, or reads `O` for `0` or `I` for `1`, still resolves the card they meant.
- **FR-005**: `lernkarten build` MUST render a card that has no `id` without failing. The id block MUST then carry **only the side marker** — `1/2` on the front, `2/2` on the back — with no id text and no `·` separator. This is the specified fallback, not a matter of taste: the block keeps its position and its rule, the wordmark and side marker do not move, and nothing overlaps.
- **FR-006**: `lernkarten` MUST offer a backfill path that assigns ids to cards lacking one, leaves existing ids untouched, is idempotent, and preserves the rest of the file — comments, quoting style, key order, encoding and line endings.
- **FR-006a**: "Preserves" is defined by a **round-trip**, because writing `id` as the card's first key necessarily moves the `- ` sequence dash onto the new line: removing the inserted ids MUST reproduce the original file **byte-for-byte**, on LF and CRLF input alike. Stating it this way removes a contradiction — a literal "no byte outside the inserted key changes" reading would forbid the dash movement that first-key placement requires, and stripping the id line alone leaves *invalid* YAML, which is what shows the movement to be structural rather than cosmetic.
- **FR-007**: Backfill MUST be all-or-nothing per invocation: if any target file cannot be parsed or written, it MUST report the file and the reason and leave every file unmodified.
- **FR-008**: `scripts/check_project.py` MUST report two cards in one project sharing an id, and the message MUST name **both** cards.
- **FR-009**: `scripts/check_project.py` MUST report an id that is not exactly 5 characters, or that contains a character outside the 32-symbol alphabet, or that is present but not a string, naming the file, the card and what is wrong with it.
- **FR-010**: The rendered id MUST fit inside the footer's id block at the chosen type size without clipping, verified by **measuring** the rendered width through the pinned engine rather than by inspection.
- **FR-011**: The id MUST be set at **8 pt** at the a7 grid (up from 4.6 pt), scaled by the template's existing `scale` factor so a denser grid holds the same proportion. Measured through the pinned engine: 52.80 pt against the 94.49 pt cap — 55.9 %.
- **FR-011a**: The id MUST NOT visually overpower the wordmark set beside it in the footer band. This, not the clip cap, is what bounds the size from above: every size up to 12 pt fits the box, but at 11 pt the id dominates a band the design treats as quiet. Any later change to the id's size is bound by this as well as by FR-010.
- **FR-012**: Generating an id MUST NOT require the typesetting engine, network access, or any state outside the project's own card files.
- **FR-013**: On a genuine collision — two cards that must coexist and share an id, which per FR-003a can only arise when independently-assigned decks are combined — the **writing** path MUST reassign one of the two automatically and MUST report every reassignment it made, naming the card and both the old and the new id.
- **FR-013a**: The **validating** path MUST NOT reassign. `lernkarten check` and `scripts/check_project.py` are read-only CI gates; a gate that rewrote the working tree would be unusable as one. They report the duplicate and exit non-zero (FR-008), leaving the fix to the writing path.
- **FR-013b**: Reassignment MUST be **deterministic and first-occurrence-wins**: files are considered in the order given on the command line, cards in file order within each file, and the **first** card seen carrying an id keeps it. Every later card carrying the same id is reassigned. Given the same files in the same order, the same card is reassigned every run. The user therefore steers the outcome through argument order — putting the deck whose ids they cite in conversation first preserves those ids.
- **FR-013c**: The reassignment report MUST state the consequence, not just the change: a reassigned id no longer resolves in past conversations, and any #60 revision history recorded against it is orphaned. This is a known and accepted cost of FR-013 (see Clarifications), so the user MUST be told each time it is paid.
- **FR-013d**: A replacement id MUST itself be checked against every id in the combined set — those kept, those already reassigned, and those not yet examined — and redrawn under FR-003a and FR-003b if it clashes. Reassignment therefore never introduces a second collision, and one pass leaves no duplicates behind.
- **FR-014**: *Withdrawn to scope — retained as a numbered entry so downstream plan and task references stay stable.* Selecting a card by id (`lernkarten build --card A45DK`) is **out of scope** for this feature and belongs to a follow-on ticket. This feature delivers ids that exist, are stable and are legible; it does not make them an addressing scheme the build path understands. The deliberate consequence: nothing in this feature may add a `--card` flag, and no acceptance scenario depends on one.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | **new optional per-card key `id`** — a 5-character Crockford Base32 string, unique within the project | `skills/cards/SKILL.md`, `scripts/build_pdf.py`, `scripts/check_project.py`, `cards/example.yaml`, `CLAUDE.md`, `templates/card.typ`, the demo decks under `tests/fixtures/demo-project/cards/` |

**Backwards compatibility**: **Existing projects still build, unchanged.** The `id` key is optional: a deck written before this feature has no `id:` anywhere and must build to the same page count it did before (User Story 2). The migration is opt-in via backfill (User Story 4), not required. The one *visible* change to an old deck is that its rendered id changes — from `topic-3` to either a backfilled short id or the no-id fallback — which matters only for cards already printed, and those already carry a clipped id that could not be read.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: **the card** — the footer's id block in `templates/card.typ`. Read `docs/design.md` before changing it (Principle XIV).
- **Black-only laser print still readable**: **yes** — the id is monospaced text on white; no colour carries meaning.
- **Minimum type size respected**: **yes, and this feature improves on it.** The 11 pt floor in `docs/design.md` is scoped to *reading text*, which that document defines as Archivo prose — and it exempts the card id **by name** ("it does not bind a letterspaced label at 11 px or a card id at 8.5 px"). The id is IBM Plex Mono, which the same document classes as a literal. So no exception clause is needed and none may be added; the sentence granting the exemption must be left intact. The id nonetheless **grows** from 4.6 pt to 8 pt (FR-011), never shrinks.
- **Brand PNGs need re-rendering**: **no** — the mark and wordmark are untouched.
- **Duplex alignment unaffected**: **yes** — the footer band's height and the card's outer geometry do not change; only the text inside the existing id block does. Front and back carry the same id, so the block's width is the same on both faces.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** **Yes, and it needs a decision in the plan.** Generating a random Crockford Base32 string is a handful of lines over `secrets` and is not worth a dependency. But **FR-006 is a comment-preserving YAML round-trip**, and that is exactly the thing Principle III says not to hand-roll: `scripts/yamlio.py` today is **read-only** (`load()` only — there is no `dump`), and nothing in this repo writes YAML at all. The plan must choose between a round-trip library (`ruamel.yaml` is the standard answer) and a narrow targeted-insertion approach that never reserialises the file. The second is not "hand-rolling YAML" if it only inserts one line at a known point — but the plan must argue that explicitly rather than assume it.
- **New runtime dependency**: **undecided — a plan question, not a spec one.** Note that the constitution's Principle II *permits* runtime dependencies and `scripts/deps.py` already exists to deliver them (pinned, installed into a per-Python cache, reported by `lernkarten deps --check`). CLAUDE.md's claim that "a runtime dependency cannot ship today" is out of date against the constitution and `bin/lernkarten`, which already calls `deps.activate()` before doing work. If the plan takes a dependency it must clear Principle IV's gates and be the project's first.
- **New dev dependency**: none expected.
- **New external binary**: **none.**
- **Anything this makes redundant**: the `f"{path.stem}-{i}"` id construction in `scripts/build_pdf.py` (line ~303) is replaced, and its implicit contract — that ids are positional — disappears with it.
- **Engine version change**: **no** — 0.15.1 stays pinned; no SHA-256 bump.
- **Platforms verified**: macOS and Linux via CI. **Windows is manual** — CI has no Windows job, and this feature writes files, so the line-ending guarantee in the Edge Cases is the one thing that genuinely needs a Windows check before release.

### Key Entities *(include if the feature involves data)*

- **Card id**: a short, opaque, human-sayable handle for one card. **Exactly 5 Crockford Base32 characters**, unique within a project, assigned once at card creation and never changed thereafter — not by editing the card, not by moving it, not by renaming its file. The single exception is collision reassignment when independently-assigned decks are combined (FR-013), which is the one path that may change an id after assignment and must announce that it did. It is a *handle, not a classification*: it encodes nothing about the card's topic, subtopic, language, deck or position, and per the issue it must not be made to.
- **Project id space**: the set of ids in use across all `cards/*.yaml` in one project. Uniqueness is scoped here and nowhere wider — there is no global registry and none is planned.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across a generated corpus large enough to force repeated draws, **no two cards in one project ever share an id**, and every id is exactly 5 characters drawn only from the 32-symbol alphabet — asserted over a corpus, not a handful of cards.
- **SC-002**: A card's id is **byte-identical before and after** each of the five operations that break it today or would break it under a rejected alternative: inserting a card before it, deleting a card before it, renaming the file, editing the card's text, and building with `--subtopic`.
- **SC-003**: `lernkarten build` on the demo decks with **no `id:` keys present** exits 0 and produces the same page count as before the feature — the backwards-compatibility guarantee, asserted through the real command.
- **SC-004**: `lernkarten check` exits **non-zero** and names both offenders on a fixture carrying a duplicate id, and exits non-zero naming file, card and character on a fixture carrying an out-of-alphabet id.
- **SC-005**: The rendered width of the longest possible `<id> · 1/2` at the chosen type size, **measured through the pinned engine**, is strictly less than the id block's cap — and the type size is greater than 4.6 pt.
- **SC-006**: `lernkarten id --backfill` run twice over a deck with comments, single-quoted Typst markup and pre-existing ids leaves the file **byte-identical** to its state after the first run, with all comments and pre-existing ids intact.
- **SC-007**: A user can read an id off a printed card and use it to identify that card in a Claude session, and the id still resolves to the same card after the session edits it. *(Run-output criterion — per Principle XI this leaves nothing on disk and belongs on the manual checklist in `docs/testing.md`, named there rather than left implicit.)*
- **SC-008**: Given two decks that share an id, the writing path reassigns **the later one by command-line order**, leaves the first untouched, and reports both the old and the new id. Running the same command on the same files twice produces the **same** reassignment; swapping the two file arguments reassigns the **other** card — which is what makes FR-013b's "user steers it" claim assertable rather than asserted.
- **SC-009**: `lernkarten check` and `scripts/check_project.py` leave every input file **byte-identical** on a fixture carrying a duplicate id — the read-only guarantee of FR-013a, asserted by hashing the files before and after the run rather than by inspecting the code.

## Assumptions

- **The `id` key goes first on each card, before `subtopic`.** This is a reasonable default chosen so a diff that adds ids is readable and so the id is the first thing a human scanning the file sees. It is a genuine open question from the issue ("Does the id go into the card YAML in a fixed position?") but has an obvious default and low reversal cost, so it is recorded here rather than spending one of the three clarification markers. Clarify may still overturn it.
- **Uniqueness is per project, not global.** Two unrelated projects on different disks may legitimately hold the same id. The issue accepts this explicitly: the header band prints topic and subtopic on every card face, so a human sorting a mixed physical stack can still tell them apart, and a Claude session resolves an id against the one project it has open. This costs one sentence in the docs and is not a design constraint. A global registry or namespace is **out of scope** (Principle II refuses the friction of asking users to register anything).
- **Selecting a card by id is out of scope** (FR-014, settled in Clarifications). This feature makes ids exist, stay stable and print legibly; it does not teach the build path to filter by them. `lernkarten build --card A45DK` is a follow-on ticket and nothing here may add the flag.
- **The id encodes nothing.** Out of scope by the issue's own statement — it is a handle, not a classification. No topic prefix, no language marker, no deck code.
- **`/cards` is the only writer in the model-driven half.** No other skill assigns or changes ids.
- **The demo project carries the new fixtures.** Per `docs/testing.md` and CLAUDE.md, a new failure mode belongs in `tests/fixtures/demo-project`, not in a fixture of its own — so the duplicate-id and bad-alphabet cases go there.
- **Test-first is mandatory** (Principle XI, non-negotiable). Every acceptance scenario above was written to be sharp enough to become an assertion that fails today. The `skills/cards` change is model-driven, so its red artifact is a check in `scripts/check_project.py` plus a case in `tests/test_check_project.py`.
- **#60 is downstream and constrains this spec but is not in it.** Revision history and `A45DK@2` addressing depend on the id surviving an edit, which is why FR-001 rules out content hashing and why FR-003's length is irreversible. Nothing in #60 is specified here.

## Dependencies

- Blocks **#60** (revision history and lineage). #60 cannot be designed until this feature's primary key — alphabet and length — is fixed.
- Depends on nothing outstanding. The engine, the card schema and the check harness all exist.
