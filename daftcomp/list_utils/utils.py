"""Implement the six list functions described in README.md using while loops."""

__author__: str = "730986400"


def scale_range(start: int, stop: int, step: int) -> list[int]:
    """Build a range with an exclusive stop; assert that step is nonzero."""
    assert step != 0

    i: int = start
    range_list: list[int] = []

    if step > 0:
        while i < stop:
            range_list.append(i)
            i += step

    elif step < 0:
        while i > stop:
            range_list.append(i)
            i += step

    return range_list


def shift_mutate(original: list[int], offset: int) -> None:
    """Add offset to every integer in the original list."""
    i: int = 0
    while i < len(original):
        original[i] = original[i] + offset
        i += 1


def shift_pure(original: list[int], offset: int) -> list[int]:
    """Return a new list with offset added to EVERY integer; preserve original."""
    i: int = 0
    shifted: list[int] = []

    while i < len(original):
        shifted.append(original[i] + offset)
        i += 1
    return shifted


def reverse(original: list[int]) -> list[int]:
    """Return the integers in reverse order in a new list; preserve original."""
    raise NotImplementedError("Start at the final index and work backward.")


def halftime(original: list[int]) -> list[int]:
    """Return a new list with each step extended to twice its duration."""
    raise NotImplementedError("Append each original entry, then an extra HOLD or REST.")


def caesar(original: list[int]) -> list[int]:
    """Rotate values 0..127 by 64, preserving REST/HOLD, in a new list."""
    raise NotImplementedError("Wrap shifted values using the remainder operator.")
