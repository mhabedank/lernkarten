# Testability Checklist: A short, stable card id

**Purpose**: Validate that every requirement is written sharply enough to become a **failing assertion before implementation**. Constitution Principle XI is non-waivable and states the standard directly: *"If no failing check can be written, the requirement is not yet specified sharply enough — go back to the spec, do not go forward to the prompt."* This checklist is that gate.
**Created**: 2026-08-21
**Feature**: [spec.md](../spec.md) · [plan.md § Test plan first](../plan.md) · [docs/testing.md](../../../docs/testing.md)

**How to use**: each item asks whether a requirement *can be made red on its assertion*. An unchecked box means the requirement is too vague to implement, not that a test is missing.

## Assertion Sharpness

- [ ] CHK031 Does every FR map to at least one of the 17 red-first assertions, with none orphaned? [Traceability, Spec §FR-001–§FR-014 → plan §Test plan first] — FR-002 and FR-005 are the ones most at risk of having no assertion of their own.
- [ ] CHK032 Is FR-006's assertion specified as the **round-trip** `remove_ids(insert_ids(src)) == src`, rather than the naive strip-and-compare? [Clarity, Spec §FR-006, plan assertion 4] — the naive form fails for a non-defect reason, so a requirement that does not name the right property invites a wrong test.
- [ ] CHK033 Is `remove_ids` specified as **public API** so the round-trip is assertable at all? [Completeness, plan §Module placement] — a property that can only be checked against a private helper is not a testable requirement.
- [ ] CHK034 Can FR-005 ("well-formed footer" with no id) be expressed as an assertion, or only as visual review? [Measurability, Spec §FR-005] — if only visual, it must be named on the manual checklist rather than counted as automated coverage.
- [ ] CHK035 Is FR-013c's "report states the consequence" assertable on message content, or is it a wording requirement? [Measurability, Spec §FR-013c] — per Principle XI's run-output carve-out, wording requirements must be named on the manual checklist explicitly, never left implicit.

## Red-First Ordering

- [ ] CHK036 Is it specified that the `skills/cards` prompt change is gated by a `check_project.py` check that fails **against what the current prompt produces**? [Completeness, Spec §FR-002, plan assertion 15] — this is the only mechanism that makes a prompt change verifiable; a check written after the prompt proves nothing.
- [ ] CHK037 Do the requirements make it possible to confirm the red-first ordering **was honoured**, rather than merely claimed? [Gap] — nothing in spec or plan requires evidence that each assertion was seen failing first; consider whether commit ordering is the artifact.
- [ ] CHK038 Is "fails on the assertion, not on ImportError" stated as a condition the new `scripts/cardid.py` tests must meet? [Clarity, Constitution §XI] — a brand-new module makes ImportError the default failure mode, so this needs saying for this feature specifically.

## Test Level Placement

- [ ] CHK039 Is each new assertion assigned to the correct level per `docs/testing.md` — unit, contract, e2e? [Consistency, plan §The two halves] — misplacement matters: an e2e-level assertion skips silently without `LERNKARTEN_E2E=1`.
- [ ] CHK040 Is it specified which assertions are allowed to **skip** without the engine, and confirmed that no backwards-compatibility or byte-fidelity assertion is among them? [Coverage, Spec §FR-012] — the P1 guarantees must run in the default suite.

## Test Material

- [ ] CHK041 Are the four new failure fixtures specified by **name and content shape**, so two implementers would build the same corpus? [Completeness, research §R-4] — duplicate, bad alphabet, bad length, non-string id.
- [ ] CHK042 Is it specified that all new fixtures are **text** files requiring no generator, and therefore no committed binaries? [Consistency, Constitution §VIII] — this feature has no reason to touch `make_testdata.py`.
- [ ] CHK043 Is it stated that fixtures extend `tests/fixtures/demo-project/` rather than introducing a new corpus? [Consistency, Constitution §XI, docs/testing.md] — a second corpus would be a Complexity Tracking entry.
- [ ] CHK044 Are the fixture requirements subject-agnostic and free of user content? [Coverage, Constitution §VII] — this is a public repo holding tools, not knowledge.

## Cross-Platform Requirements

- [ ] CHK045 Is CRLF preservation stated as a **requirement** rather than only as a research finding? [Traceability, Spec §Edge Cases → research §R-1] — this feature writes files and Windows blocks a merge, so the line-ending guarantee needs to be a requirement an assertion can cite.
- [ ] CHK046 Is it specified whether the byte-fidelity assertions must run on all three platforms, or whether a Linux/macOS run is sufficient? [Gap] — CI has Windows legs; the requirement should say whether they are load-bearing here.

## Manual-Checklist Requirements

- [ ] CHK047 Are the two Principle XI manual items named explicitly in the requirements — SC-007, and the missing-id advisory wording? [Completeness, Spec §SC-007, §US2 scenario 2] — the constitution requires these be *named* in `docs/testing.md`, never left implicit.

## Notes

- Check items off as completed: `[x]`
- **CHK032, CHK036 and CHK037 are the ones most likely to bite.** CHK032 guards against a test that asserts less than FR-006 states; CHK036 is the only thing making the prompt change verifiable at all; CHK037 asks the uncomfortable question of whether "test-first" can be *audited* rather than trusted.
- This checklist validates requirement testability. The assertions themselves are enumerated in [plan.md](../plan.md); running them is Phase 8 and beyond.
