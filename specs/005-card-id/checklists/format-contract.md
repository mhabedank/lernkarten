# Format Contract Checklist: A short, stable card id

**Purpose**: Validate the *requirements* governing the `cards/*.yaml` schema change — completeness, clarity and internal consistency — before implementation. This is the fifth contract under Constitution Principle I, so an underspecified requirement here becomes a breaking change with an unbounded blast radius.
**Created**: 2026-08-21
**Feature**: [spec.md](../spec.md) · [contracts/cards-yaml.md](../contracts/cards-yaml.md)

**How to use**: each item asks whether the requirement is *written well enough to implement unambiguously* — not whether the code works. An unchecked box means go back to the spec, not go forward to a bug report.

## Requirement Completeness

- [x] CHK001 Is the rendered fallback **value** specified for a card with no `id`, or only the outcome ("well-formed footer")? [Gap, Spec §FR-005] — `data-model.md` says "the agreed fallback" without ever agreeing it; an implementer must choose between empty string, a dash and a placeholder with no guidance.
      → **Resolved 2026-08-21 — FR-005 now names the fallback: the side marker alone, no id text, no separator.**
- [ ] CHK002 Are requirements defined for a deck where the `cards:` key is present but empty or null? [Coverage, Spec §Edge Cases] — the edge case names backfill as a no-op but does not say what `check` and `build` report.
- [x] CHK003 Are requirements defined for **id-space exhaustion** — backfill unable to draw an unused id? [Gap] — FR-003a mandates redraw-on-clash but specifies no termination condition or error.
      → **Resolved 2026-08-21 — FR-003b adds a bounded redraw and a named exhaustion error.**
- [x] CHK004 Is the behaviour specified when **reassignment itself collides** with an existing id? [Gap, Spec §FR-013] — the reassignment rule is defined; the recursive case is not.
      → **Resolved 2026-08-21 — FR-013d specifies the recursive case; one pass leaves zero duplicates.**
- [ ] CHK005 Are requirements defined for a card file that parses but is not the expected shape (`cards:` a mapping, a card a scalar)? [Coverage, Gap] — existing `build_pdf` behaviour covers some of this; the spec does not say whether id validation runs before or after that check.
- [x] CHK006 Does the spec state whether `lernkarten id` **requires** an explicit subcommand flag, or whether bare `lernkarten id <files>` is defined? [Ambiguity] — `quickstart.md` uses both `lernkarten id --backfill` and bare `lernkarten id` for reassignment without distinguishing them.
      → **Resolved 2026-08-21 (Phase 6) — contracts/cards-yaml.md § The `id` subcommand fixes the surface: `--backfill` and `--reassign`, bare `lernkarten id` exits non-zero with usage.**

## Requirement Clarity

- [x] CHK007 Is "byte-for-byte outside the inserted key" precise enough to implement, given that `id`-first placement necessarily moves the `- ` list dash? [Conflict, Spec §FR-006] — as literally written FR-006 forbids the very edit the placement requires; the reconciliation lives only in [research.md](../research.md) and [plan.md](../plan.md), not in the requirement itself.
      → **Resolved 2026-08-21 — FR-006a restates preservation as a round-trip, removing the contradiction.**
- [x] CHK008 Can "well-formed footer" be objectively measured, or does it rest on reviewer judgement? [Measurability, Spec §FR-005] — contrast FR-010, which is measurable by construction.
      → **Resolved 2026-08-21 — FR-005's fallback is now concrete, so it is measurable.**
- [x] CHK009 Is the duplicate test specified to operate on the **normalised** id rather than the literal string? [Ambiguity, Spec §FR-004 + §FR-008] — if `a45dk` and `A45DK` sit in two cards, FR-004 implies they collide but FR-008 never says the comparison is normalised first.
      → **Resolved 2026-08-21 (Phase 6) — FR-008 now says sharing is judged on the normalised id, so `a45dk` and `A45DK` are a duplicate.**
- [x] CHK010 Is "the writing path" defined by enumeration rather than by description? [Clarity, Spec §FR-013a] — the split between writing and validating paths is load-bearing for SC-009, so which commands belong to each must be listed, not inferred.
      → **Resolved 2026-08-21 (Phase 6) — FR-013a enumerates both paths and places `lernkarten build` in neither.**

## Requirement Consistency

- [ ] CHK011 Do FR-008 (report duplicates, exit non-zero) and FR-013 (reassign automatically) stay non-contradictory across every command? [Consistency, Spec §FR-008/§FR-013/§FR-013a] — FR-013a is the reconciling clause; confirm no other requirement re-crosses that line.
- [ ] CHK012 Is the uniqueness **scope** stated identically in spec, contract and data model? [Consistency] — all three must say per-project, never global, with no registry.
- [ ] CHK013 Is the `id` key's position stated consistently as a *writing convention* rather than a *parse requirement*? [Consistency, Contract §The change] — a reader must accept `id` anywhere; only the writer places it first.

## Acceptance Criteria Quality

- [ ] CHK014 Does SC-003's "same page count as before the feature" name a concrete baseline an implementer can compute? [Measurability, Spec §SC-003] — `2 × ⌈cards ÷ 8⌉` appears in `quickstart.md` but not in the criterion.
- [ ] CHK015 Is SC-008's "swapping the arguments reassigns the other card" stated as a requirement (FR) and not only as a success criterion? [Traceability, Spec §SC-008 → §FR-013b] — the steerability claim is the justification for first-occurrence-wins, so it needs a home in the requirements.

## Scope Boundaries

- [ ] CHK016 Are the four exclusions — `--card` selection, global registry, encoded meaning, `@version` suffix — stated where an implementer will actually encounter them? [Coverage, Spec §FR-014, Contract §Explicitly not in this contract] — an exclusion recorded only in Assumptions is easy to re-add by accident.
- [ ] CHK017 Is it specified whether `lernkarten check` gains any new **flag** as part of this feature? [Gap] — the advisory behaviour is defined but its suppressibility is not.

## Backwards Compatibility

- [ ] CHK018 Are requirements defined for the **mixed** case — some cards with ids, some without — at every touchpoint (build, check, backfill, render), not just at build? [Coverage, Spec §US2 scenario 3] — the spec covers build and backfill; check and render are implied only.
- [x] CHK019 Is the migration path stated as strictly opt-in, with no command that silently backfills as a side effect? [Consistency, Contract §Backwards compatibility] — the read-only guarantee (FR-013a) covers `check`; confirm `build` is equally constrained.
      → **Resolved 2026-08-21 (Phase 6) — the contract's writer table states `lernkarten build` never writes to cards/*.yaml.**

## Notes

- Check items off as completed: `[x]`
- **CHK001, CHK003, CHK004 and CHK007 were the ones that bit**, and all four are now resolved in `spec.md` (FR-005, FR-003b, FR-013d, FR-006a), with CHK008 falling out of the FR-005 fix. The ten still open are consistency and coverage questions rather than gaps — worth a pass in Phase 6 (Analyze), none of them blocking task generation.
- Items here validate *requirements*, not code. Behavioural verification belongs to the 20 red-first assertions in [plan.md](../plan.md) and to [quickstart.md](../quickstart.md).
