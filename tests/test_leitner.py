"""The Leitner data: interval sets, rule lines, colours and geometry.

`scripts/leitner.py` is a leaf — it imports nothing local — so this module is
the whole of its contract. What it protects is that the two interval sets are
authored, not derived: a three-compartment box is a box with fewer sessions,
not one with shorter gaps.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import leitner  # noqa: E402


def test_the_interval_sets_are_authored_not_truncated():
    """FR-017a: neither set is a prefix of the other.

    Both end at the same longest rest, because what the far end of the box is
    for does not change with the number of compartments. Truncating the
    four-set would cap three compartments at one week, so well-known cards
    would come back twice as often for choosing the simpler box.
    """
    assert leitner.INTERVALS[3] == ("daily", "every 3 days", "every 2 weeks")
    assert leitner.INTERVALS[4] == ("daily", "every 2 days", "weekly", "every 2 weeks")
    assert leitner.INTERVALS[3] != leitner.INTERVALS[4][:3], "not a truncation"
    assert leitner.INTERVALS[3][-1] == leitner.INTERVALS[4][-1], "same longest rest"


@pytest.mark.parametrize("count", [3, 4])
def test_every_compartment_has_an_interval_and_a_rule(count):
    """FR-017b: the rule line says what enters and what leaves."""
    assert len(leitner.INTERVALS[count]) == count
    rules = leitner.rules(count)
    assert len(rules) == count
    assert rules[0] == "new + wrong cards"
    assert rules[-1] == "right -> retire"
    assert all("day" not in r and "sunday" not in r.lower() for r in rules), (
        "a rule line never names a weekday: the interval already says when, and a "
        "printed weekday would fix a start day the user never chose"
    )


@pytest.mark.parametrize("count", [3, 4])
def test_a_colour_per_compartment_in_the_brand_order(count):
    assert leitner.COLOURS[:count] == ("#c2251b", "#f0c000", "#0a3f8f", "#141414")[:count]


def test_the_geometry_constants_carry_their_derivation():
    """The numbers research.md R1 and R6 derive, in the one place that holds them."""
    assert leitner.GROWTH_MM == 1.5, "52 mm box inside against a 50 mm card"
    assert leitner.BAND_MM == 4.0, "2 mm registration + 1 mm cut, rounded up"
    assert leitner.BLEED_MM == 3.0
    assert leitner.GAP_MM == 2 * leitner.BLEED_MM + 2.0, "two bleeds plus cut tolerance"
    assert leitner.LAYOUT == {3: (3,), 4: (2, 2)}, (
        "a table, not a per-row maximum: 4 x 71.75 = 287.00 is the whole A8 print width"
    )
