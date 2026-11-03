import pytest


def min(vals: list[int]) -> int:
    """Returns minimum int in the input list."""
    assert len(vals) > 0
    smallest: int = vals[0]
    i: int = 0
    while i < len(vals):
        if vals[i] < smallest:
            smallest = vals[i]
        i += 1
    return smallest


min(vals=[0, 0, 0, 0])


def test_min_zero() -> None:
    """Testif 0 is returned!"""
    assert min([0, 0, 0, 0]) == 0


def test_min_neg() -> None:
    assert min([-1, -3, -4, -18]) == -18


def test_min_empty() -> None:
    with pytest.raises(AssertionError):
        min([])
