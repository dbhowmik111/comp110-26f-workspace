"""PROVIDED: turn the name of a land cover into the object for one square.

The terrain and your sketched features name covers with strings like
"pine" or "homes". make_cover() builds the matching object.
"""

from goodfire.cover import Home
from goodfire.cover import Road
from goodfire.cover import Water
from goodfire.dice import Dice
from goodfire.plants import Grass
from goodfire.plants import Hardwood
from goodfire.plants import Pine
from goodfire.protocols import Land

COVERS: list[str] = [
    "pine",
    "grass",
    "hardwood",
    "homes",
    "river",
    "pond",
    "road",
]
"""Every cover a Feature may ask for."""


def make_cover(kind: str, row: int, col: int, dice: Dice) -> Land:
    """Create the object for one square of a given cover.

    Args:
        kind: One of the names in COVERS.
        row: The square's row.
        col: The square's column.
        dice: The landscape's dice, for each plant's random fuel load.

    Returns:
        A new Land object for that square.

    Raises:
        ValueError: If ``kind`` is not a known cover.
    """
    if kind == "pine":
        return Pine(row, col, dice.fuel_load(0.6, 1.0))
    if kind == "grass":
        return Grass(row, col, dice.fuel_load(0.3, 0.6))
    if kind == "hardwood":
        return Hardwood(row, col, dice.fuel_load(0.4, 0.8))
    if kind == "homes":
        return Home(row, col, False)
    if kind == "river" or kind == "pond":
        return Water(row, col)
    if kind == "road":
        return Road(row, col)
    raise ValueError(f"unknown cover {kind!r}; expected one of {COVERS}")
