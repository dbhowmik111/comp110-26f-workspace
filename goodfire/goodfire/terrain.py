"""PROVIDED: the shape of the land and what grows there before you sketch.

The map is a 30 x 30 grid of 30 m squares (900 m on a side), loosely modeled
on a North Carolina Sandhills watershed: longleaf pine on the uplands,
bottomland hardwoods along the river, and an old field of grass. Row 0 is the
north edge, which is also the high side of the hill.
"""

import math

GRID_SIZE: int = 30
"""The map is GRID_SIZE rows by GRID_SIZE columns."""

CELL_SIZE: int = 20
"""Each square is CELL_SIZE by CELL_SIZE units on the 2D canvas."""


def river_row(col: float) -> float:
    """Return the row where the valley floor runs at a given column."""
    return 9.0 + 1.5 * math.sin(col / 5.0)


def elevation(row: int, col: int) -> float:
    """Return the height of the land, in meters, at the center of a square.

    Args:
        row: The square's row, from 0 (north) to GRID_SIZE - 1 (south).
        col: The square's column, from 0 (west) to GRID_SIZE - 1 (east).

    Returns:
        Meters above the lowest point of the valley.
    """
    slope: float = 1.2 * (GRID_SIZE - row)
    ridge: float = 14.0 * math.exp(-((col - 24) ** 2) / 18.0)
    valley: float = 6.0 * math.exp(-((row - river_row(col)) ** 2) / 4.0)
    return slope + ridge - valley + 6.0


def base_cover(row: int, col: int) -> str:
    """Return what grows on a square before any sketching.

    Args:
        row: The square's row.
        col: The square's column.

    Returns:
        One of "hardwood", "grass", or "pine".
    """
    if abs(row - river_row(col)) <= 2.2:
        return "hardwood"
    if math.hypot(row - 22, col - 7) < 5.5:
        return "grass"
    return "pine"


def shade(base: tuple[int, int, int], row: int, col: int) -> str:
    """Lighten a color on high ground so the hill shows from above.

    Args:
        base: The red, green, and blue channels of the color in the valley.
        row: The square's row.
        col: The square's column.

    Returns:
        A "#RRGGBB" color string.
    """
    lift: float = min(max(elevation(row, col), 0.0) / 60.0, 1.0) * 0.35
    channels: list[int] = []
    channel: int
    for channel in base:
        channels.append(round(channel + (255 - channel) * lift))
    return f"#{channels[0]:02X}{channels[1]:02X}{channels[2]:02X}"
