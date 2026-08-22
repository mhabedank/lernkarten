# Print & Design Checklist: A short, stable card id

**Purpose**: Validate the *requirements* governing the one visible change this feature makes — the card id in the footer band, growing from 4.6 pt to 8 pt. Constitution Principle XVI treats visible surface as gated, so the requirements must be specific enough that "does it look right?" is the only judgement left.
**Created**: 2026-08-21
**Feature**: [spec.md](../spec.md) · [research.md § R-2](../research.md) · [docs/design.md](../../../docs/design.md)

**How to use**: each item asks whether the requirement is *specified precisely enough*, not whether the rendering is correct.

## Requirement Completeness

- [x] CHK020 Is the chosen type size stated as a **requirement** with its value, or only as a plan decision? [Traceability, Spec §FR-011 → research §R-2] — FR-011 says only "larger than 4.6 pt"; the concrete 8 pt lives in `research.md`, so the spec permits any size above the floor.
      → **Resolved 2026-08-21 — FR-011 pins 8 pt with its measurement.**
- [ ] CHK021 Are requirements defined for the id's rendering at the **A8 grid**, or is `scale` inheritance assumed? [Coverage, Gap] — research shows the proportion holds automatically; the spec never states A8 as in scope for the rendering requirement.
- [x] CHK022 Is the footer's **internal hierarchy** captured as a requirement — that the id must not overpower the 5 pt wordmark? [Gap, research §R-2] — this is the actual reason 11 pt was rejected, yet it appears nowhere as a constraint an implementer must honour.
      → **Resolved 2026-08-21 — FR-011a records the wordmark-balance constraint as a requirement.**
- [ ] CHK023 Are requirements defined for what happens if a future id were long enough to reach the `cw / 3` cap? [Coverage, Spec §FR-010] — `clip: true` remains in the template; the spec asserts the id fits but not what must happen if it ever does not.

## Requirement Clarity

- [ ] CHK024 Is the measurement basis for FR-010 specified — which string, which font, which engine version, which `cw`? [Clarity, Spec §FR-010] — "the longest possible `<id> · 1/2`" is well-defined only once length and alphabet are fixed; the engine version and `cw = 100 mm` come from research, not the requirement.
- [ ] CHK025 Is "legible without leaning in" (US3) tied to any measurable proxy, or explicitly delegated to manual review? [Measurability, Spec §US3] — if it is a human judgement, the spec should say so rather than imply a testable threshold.

## Requirement Consistency

- [x] CHK026 Does the spec's Print & Design section still assert the id is "below the project's own floor", now that `docs/design.md` is known to exempt it by name? [Conflict, Spec §Print & Design Impact vs research §C-3] — the correction is recorded in research; confirm the spec text does not still carry the superseded premise.
      → **Resolved 2026-08-21 — the superseded 'below the floor' claim is gone; the exemption is stated and protected.**
- [x] CHK027 Is the "no type shrunk to fit" rule (Principle XVI) satisfied *and stated* — the id only ever grows? [Consistency, Spec §FR-011] — direction matters here, not just magnitude.
      → **Resolved 2026-08-21 — the spec now states the direction: the id grows to 8 pt and never shrinks.**
- [ ] CHK028 Are the requirements consistent about **duplex alignment** being unaffected — same id on both faces, so the block width matches front and back? [Consistency, Spec §Print & Design Impact] — front/back symmetry is what keeps the claim true; confirm it is stated rather than assumed.

## Documentation Requirements

- [x] CHK029 Is it specified **which** part of `docs/design.md` must change, and which must deliberately stay? [Clarity, Gap] — the size record changes; the sentence exempting the card id from the 11 pt floor must not be edited, and no requirement currently protects it.
      → **Resolved 2026-08-21 — the spec says the size record changes and the exemption sentence must be left intact.**
- [ ] CHK030 Are the black-only-laser and photocopier constraints restated for the id specifically, given it is muted grey? [Coverage, Spec §Print & Design Impact] — the id gets larger, which helps, but the muted fill against a floor is the property worth naming.

## Notes

- Check items off as completed: `[x]`
- **CHK020, CHK022 and CHK026 were the ones that bit**, and all three are now resolved: FR-011 pins 8 pt, FR-011a records the wordmark-balance constraint that actually bounds it, and the spec's superseded "below the floor" claim is gone. CHK021, CHK023, CHK024, CHK025, CHK028 and CHK030 remain open and are lower-stakes.
- Whether the footer *looks* right is not a pytest question and belongs on the manual checklist in `docs/testing.md` (Constitution XI).
