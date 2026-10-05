"""Write at least two expected-case tests and one edge-case test per function."""

__author__: str = "730986400"

import pytest

from list_utils.utils import scale_range


def test_scale_range_ascending() -> None:
    """An ascending scale includes start and excludes stop."""
    assert scale_range(60, 67, 2) == [60, 62, 64, 66]


def test_scale_range_descending() -> None:
    """A descending scale includes start and excludes stop."""
    assert scale_range(67, 60, -2) == [67, 65, 63, 61]


def test_scale_range_empty_result() -> None:
    """A step in the wrong direction produces an empty list."""
    assert scale_range(60, 67, -1) == []


def test_scale_range_zero_step() -> None:
    """A zero step raises an assertion error."""
    with pytest.raises(AssertionError):
        scale_range(60, 72, 0)


# Add your tests here. The supplied example does not count toward your 18 tests.
# Test values, unchanged inputs and fresh lists, or mutation through an alias.
