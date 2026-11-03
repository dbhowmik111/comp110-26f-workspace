"""PROVIDED: small tools from the crew's field kit.

Every place on the map is a Square (see grid.py). Squares can go in sets
and be dictionary keys, because two Squares with the same row and column
are equal and hash the same way. Kinds of land are the strings that
appearance() returns: "pine", "grass", "hardwood", "home", "water", "road",
and "cleared".
"""

import math

from goodfire import looks
from goodfire import terrain
from goodfire.dice import Dice
from goodfire.grid import Square
from goodfire.part2_protocols import FireGround
from goodfire.part2_protocols import Rendered
from goodfire.protocols import Feature
from goodfire.protocols import Land
from goodfire.weather import Wind

looks.install()  # every square answers appearance() from here on


def on_map(row: int, col: int) -> bool:
    """Return True if (row, col) is inside the map."""
    return 0 <= row < terrain.GRID_SIZE and 0 <= col < terrain.GRID_SIZE


def side_neighbors(square: Square) -> list[Square]:
    """Return the squares directly north, south, west, and east.

    Squares on the edge of the map have fewer neighbors. Fire in this model
    spreads only to these four squares.
    """
    result: list[Square] = []
    candidates: list[Square] = [
        Square(square.row - 1, square.col),
        Square(square.row + 1, square.col),
        Square(square.row, square.col - 1),
        Square(square.row, square.col + 1),
    ]
    candidate: Square
    for candidate in candidates:
        if on_map(candidate.row, candidate.col):
            result.append(candidate)
    return result


def kind_at(ground: FireGround, square: Square) -> str:
    """Return what kind of land is on a square, like "pine" or "home"."""
    cell: Land = ground.cell_at(square.row, square.col)
    if isinstance(cell, Rendered):
        return cell.appearance()
    return "unknown"


def land_map(ground: FireGround) -> dict[Square, str]:
    """Return what kind of land is on every square of the map."""
    result: dict[Square, str] = {}
    for row in range(terrain.GRID_SIZE):
        for col in range(terrain.GRID_SIZE):
            square: Square = Square(row, col)
            result[square] = kind_at(ground, square)
    return result


def neighbor_map() -> dict[Square, list[Square]]:
    """Return the side neighbors of every square of the map."""
    result: dict[Square, list[Square]] = {}
    for row in range(terrain.GRID_SIZE):
        for col in range(terrain.GRID_SIZE):
            square: Square = Square(row, col)
            result[square] = side_neighbors(square)
    return result


def squares_of(feature: Feature) -> set[Square]:
    """Return the squares a drawn shape covers, as a set."""
    return set(feature.squares())


def ember_jump(wind: Wind) -> int:
    """Return how many squares an ember flies: 3-10 squares (90-300 m).

    Spot fires 100-300 m ahead of a fire are common; stronger wind carries
    embers farther.
    """
    return min(max(round(wind.speed * 0.8), 3), 10)


def ember_landing(row: int, col: int, wind: Wind, dice: Dice) -> Square:
    """Return where an ember from (row, col) lands; it may be off the map.

    It flies ember_jump(wind) squares in the direction the wind blows
    toward, then drifts up to one square either way.
    """
    jump: int = ember_jump(wind)
    heading: float = math.radians(wind.toward)
    land_row: int = row - round(math.cos(heading) * jump)
    land_col: int = col + round(math.sin(heading) * jump)
    return Square(
        land_row + dice.rng.randint(-1, 1), land_col + dice.rng.randint(-1, 1)
    )
