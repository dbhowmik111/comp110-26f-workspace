"""Write at least two expected-case tests and one edge-case test per function."""

__author__: str = "730986400"

import pytest

from daftcomp import HOLD, REST
from list_utils.utils import caesar, halftime, reverse, scale_range, shift_mutate, shift_pure


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
    """A positive offset returns shifted values without changing the original."""
    original = [60, 64, 67]
    result: list[int] = shift_pure(original, 12)
    assert result == [72, 76, 79]
    assert original == [60, 64, 67]
    assert result is not original


def test_shift_pure_negative_offset() -> None:
    """A negative offset returns lower values without changing the original."""
    original = [60, 64, 67]
    result: list[int] = shift_pure(original, -12)
    assert result == [48, 52, 55]
    assert original == [60, 64, 67]
    assert result is not original


def test_shift_pure_zero_offset() -> None:
    """A zero offset returns an unchanged but separate copy."""
    original = [60, 64, 67]
    result: list[int] = shift_pure(original, 0)
    assert result == [60, 64, 67]
    assert original == [60, 64, 67]
    assert result is not original


def test_shift_pure_empty_list() -> None:
    """An empty input returns a new empty list."""
    original = []
    result: list[int] = shift_pure(original, 5)
    assert result == []
    assert original == []
    assert result is not original


# reverse tests


def test_reverse_long_list() -> None:
    """A longer list is returned in reverse order."""
    original: list[int] = [60, 64, 67, 72]
    result: list[int] = reverse(original)

    assert result == [72, 67, 64, 60]
    assert original == [60, 64, 67, 72]
    assert result is not original


def test_reverse_repeated_values() -> None:
    """Repeated values are preserved in reverse order."""
    original: list[int] = [1, 2, 2, 3]
    result: list[int] = reverse(original)
    assert result == [3, 2, 2, 1]
    assert original == [1, 2, 2, 3]
    assert result is not original


def test_reverse_one_item() -> None:
    """A one-item list returns a new list with the same item."""
    original: list[int] = [60]
    result: list[int] = reverse(original)
    assert result == [60]
    assert original == [60]
    assert result is not original


def test_reverse_empty_list() -> None:
    """An empty list returns a new empty list."""
    original: list[int] = []
    result: list[int] = reverse(original)
    assert result == []
    assert original == []
    assert result is not original


# halftime tests
def test_halftime_notes() -> None:
    """Each note is followed by a hold."""
    original: list[int] = [60, 64]
    result: list[int] = halftime(original)

    assert result == [60, HOLD, 64, HOLD]
    assert original == [60, 64]
    assert result is not original


def test_halftime_rests() -> None:
    """A rest is followed by another rest."""
    original: list[int] = [60, REST, 64]
    result: list[int] = halftime(original)

    assert result == [60, HOLD, REST, REST, 64, HOLD]
    assert original == [60, REST, 64]
    assert result is not original


def test_halftime_existing_holds() -> None:
    """An existing hold is followed by another hold."""
    original: list[int] = [60, HOLD]
    result: list[int] = halftime(original)

    assert result == [60, HOLD, HOLD, HOLD]
    assert original == [60, HOLD]
    assert result is not original


def test_halftime_repeated_pitches() -> None:
    """Repeated pitches each receive a hold."""
    original: list[int] = [60, 60]
    result: list[int] = halftime(original)

    assert result == [60, HOLD, 60, HOLD]
    assert original == [60, 60]
    assert result is not original


def test_halftime_empty_list() -> None:
    """An empty input returns a new empty list."""
    original: list[int] = []
    result: list[int] = halftime(original)

    assert result == []
    assert original == []
    assert result is not original


# caeser tests
def test_caesar_wraps_at_boundary() -> None:
    """Values wrap around after reaching 127."""
    original: list[int] = [0, 1, 63, 64, 127]
    result: list[int] = caesar(original)

    assert result == [64, 65, 127, 0, 63]
    assert original == [0, 1, 63, 64, 127]
    assert result is not original


def test_caesar_preserves_rest_and_hold() -> None:
    """REST and HOLD stay unchanged while pitches are shifted."""
    original: list[int] = [60, HOLD, REST, 67]
    result: list[int] = caesar(original)

    assert result == [124, HOLD, REST, 3]
    assert original == [60, HOLD, REST, 67]
    assert result is not original


def test_caesar_empty_list() -> None:
    """An empty input returns a new empty list."""
    original: list[int] = []
    result: list[int] = caesar(original)

    assert result == []
    assert original == []
    assert result is not original


def test_caesar_applied_twice() -> None:
    """Applying Caesar twice restores values in a separate list."""
    original: list[int] = [60, HOLD, REST, 67]
    once: list[int] = caesar(original)
    twice: list[int] = caesar(once)

    assert twice == [60, HOLD, REST, 67]
    assert original == [60, HOLD, REST, 67]
    assert once is not original
    assert twice is not original
    assert twice is not once


# Test values, unchanged inputs and fresh lists, or mutation through an alias.
