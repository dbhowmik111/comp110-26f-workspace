"""Write at least two expected-case tests and one edge-case test per function."""

__author__: str = "730986400"

import pytest

from list_utils.utils import scale_range, shift_mutate, shift_pure


# scale_range tests
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


# shift_mutate tests


def test_shift_mutate_positive_offset() -> None:
    """A positive offset changes every value and returns None."""
    notes: list[int] = [60, 64, 67]
    alias: list[int] = notes

    result: None = shift_mutate(notes, 12)
    assert notes == [72, 76, 79]
    assert alias == [72, 76, 79]
    assert result is None


def test_shift_mutate_negative_offset() -> None:
    """A negative offset decreases every value and returns None."""
    notes: list[int] = [2, 5, 10]

    result: None = shift_mutate(notes, -2)
    assert notes == [0, 3, 8]
    assert result is None


def test_shift_mutate_empty_list() -> None:
    """An empty list stays empty and the function returns None."""
    notes: list[int] = []

    result: None = shift_mutate(notes, 5)
    assert notes == []
    assert result is None


# shift_pure tests


def test_shift_pure_positive_offset() -> None:
    original = [60, 64, 67]
    assert shift_pure(original, 12) == [72, 76, 79]
    assert original == [60, 64, 67]


def test_shift_pure_negative_offset() -> None:
    original = [60, 64, 67]
    assert shift_pure(original, -12) == [48, 52, 55]
    assert original == [60, 64, 67]


def test_shift_pure_zero_offset() -> None:
    original = [60, 64, 67]
    assert shift_pure(original, 0) == [60, 64, 67]
    assert original == [60, 64, 67]


def test_shift_pure_empty_list() -> None:
    original = []
    assert shift_pure(original, 5) == []
    assert original == []


# Add your tests here. The supplied example does not count toward your 18 tests.
# Test values, unchanged inputs and fresh lists, or mutation through an alias.
