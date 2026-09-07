"""The Leitner data: what a divider says, and how big it is.

A leaf. It imports nothing local, because two modules need the same strings
and neither should have to reach through the other for them:

    scripts/build_pdf.py   writes them into the divider records
    scripts/check_docs.py  asserts docs/leitner.html carries exactly these

That second reader is the whole reason this file exists rather than a few
constants inside build_pdf: the docs gate runs without ever touching the
typesetting engine, and importing build_pdf would drag it in.

Everything here is derived rather than chosen; the derivations live in
specs/008-leitner-compartments/research.md, R1 and R6.
"""

# The compartment colours, in the brand order of docs/design.md. Colour never
# carries meaning alone here — the oversized numeral does that, and survives a
# black-only photocopy. Colour only makes a compartment quick to find.
COLOURS = ("#c2251b", "#f0c000", "#0a3f8f", "#141414")

# The two interval sets, authored rather than derived from one another.
#
# Sebastian Leitner's 1972 box had no intervals at all: five compartments of
# 1/2/5/8/14 cm, worked through when full, so the spacing came from capacity.
# That does not fit a 24 mm deep box — compartment 1 would hold five cards — so
# these are a calendar simplification, and docs/leitner.html says so.
#
# Both sets end at the same longest rest. Choosing three compartments buys
# fewer sessions, not shorter gaps for material already known, so the
# three-set is NOT the four-set truncated.
INTERVALS = {
    3: ("daily", "every 3 days", "every 2 weeks"),
    4: ("daily", "every 2 days", "weekly", "every 2 weeks"),
}

COMPARTMENT_COUNTS = tuple(sorted(INTERVALS))

# Millimetres.
#
# GROWTH  the box is 52 mm inside against a 50 mm card, so 51.5 mm still slides
#         and still sits below the rim. Never wider: cards stand on their long
#         edge and the box is looked into from above, so the side edges are
#         never seen — and a wider divider would not go in at all.
# BAND    the colour band, measured inward from the cut line. With a 2 mm
#         front-to-back registration error under hand-fed simplex and a 1 mm
#         cut error, the floor is 3 mm; 4 mm buys a millimetre of headroom for
#         a 1 mm cost on a 50 mm face.
# BLEED   how far the band runs past the cut line. Same arithmetic, same floor.
# GAP     two bleeds facing each other plus the cut tolerance, measured cut
#         line to cut line — so the middle 2 mm of a gap is unprinted.
GROWTH_MM = 1.5
BAND_MM = 4.0
BLEED_MM = 3.0
GAP_MM = 2 * BLEED_MM + 2.0

# How many dividers sit in each row. A table, not a maximum: four dividers at
# card width total 4 x 71.75 = 287.00 mm, which is exactly the A8 print width,
# so any gap at all overflows it. Three fit one row with 35 mm to spare.
LAYOUT = {3: (3,), 4: (2, 2)}


def rules(count):
    """The rule line for each compartment: what enters it, and what leaves.

    Never a weekday. The interval already says *when*, and a weekday printed on
    paper would fix a start day the user never chose and cannot change after
    cutting — the same reason a compartment number is never printed on a card.
    """
    if count not in INTERVALS:
        raise ValueError(f"{count} compartments: expected one of {list(COMPARTMENT_COUNTS)}")
    return tuple(
        "new + wrong cards"
        if n == 1
        else "right -> retire"
        if n == count
        else f"moved up from {n - 1}"
        for n in range(1, count + 1)
    )
