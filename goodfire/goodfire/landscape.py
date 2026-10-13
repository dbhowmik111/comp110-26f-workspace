"""STUDENT: the whole map, built from the terrain plus your sketched features.

A Landscape owns a grid of Land objects. It never asks what class a square
is; it asks what the square can do (the Land protocol).

Methods that already have code are provided: read them, they are worked
examples. Replace each raise NotImplementedError("TODO: ...") with your
own code.
"""

__author__: str = ""  # TODO: your 9-digit PID, like "730123456"

from comp110_gui import Canvas

from goodfire import science
from goodfire import terrain
from goodfire.dice import Dice
from goodfire.grid import Square
from goodfire.grow import make_cover
from goodfire.protocols import Feature
from goodfire.protocols import Land


class Landscape:
    """A 30 x 30 grid of 30 m squares that steps a fire forward in time."""

    seed: int
    features: list[Feature]
    dice: Dice
    grid: list[list[Land]]
    steps: int

    def __init__(self, seed: int, features: list[Feature]):
        """Grow the base land cover, then apply each sketched feature.

        Args:
            seed: The random seed. The same seed and features always grow
                the same landscape and, with the same ignitions, the same
                fire.
            features: Sketched shapes, applied in order; later shapes are
                drawn over earlier ones.
        """
        self.seed = seed
        self.features = features
        self.dice = Dice(seed)
        self.grid = []
        self.steps = 0
        row: int = 0
        while row < terrain.GRID_SIZE:
            cells: list[Land] = []
            col: int = 0
            while col < terrain.GRID_SIZE:
                kind: str = terrain.base_cover(row, col)
                cells.append(make_cover(kind, row, col, self.dice))
                col += 1
            self.grid.append(cells)
            row += 1
        index: int = 0
        while index < len(features):
            self.apply(features[index])
            index += 1

    def apply(self, feature: Feature) -> None:
        """Replace every square a feature covers with that feature's cover."""
        squares: list[Square] = feature.squares()
        index: int = 0
        while index < len(squares):
            square: Square = squares[index]
            self.grid[square.row][square.col] = make_cover(
                feature.cover, square.row, square.col, self.dice
            )
            index += 1

    def __str__(self) -> str:
        """Summarize the fire and the homes for the status line."""
        return (
            f"Step {self.steps}: {self.count_burning()} burning, "
            f"{science.percent(self.burned_fraction())}% of fuel burned, "
            f"{self.homes_safe()} of {self.homes_total()} homes safe"
        )

    def __repr__(self) -> str:
        """Show the code that would rebuild this landscape."""
        return f"Landscape(seed={self.seed}, features={self.features})"

    def cell_at(self, row: int, col: int) -> Land:
        """Return the object on one square."""
        return self.grid[row][col]

    def neighbors(self, row: int, col: int) -> list[Land]:
        """Return the squares directly north, south, west, and east.

        Squares on the edge of the map have fewer neighbors.
        """
        result: list[Land] = []
        if row > 0:
            result.append(self.grid[row - 1][col])
        if row < terrain.GRID_SIZE - 1:
            result.append(self.grid[row + 1][col])
        # TODO: add west and east the same way, then return result.
        raise NotImplementedError("TODO: Landscape.neighbors")

    def ignite(self, row: int, col: int) -> bool:
        """Set one square on fire if it can burn.

        Returns:
            True if the square caught fire.
        """
        raise NotImplementedError("TODO: Landscape.ignite")

    def step(self) -> None:
        """Advance the fire by one step.

        Every burning square tries once to light each neighbor that can burn,
        then burns for one step. Squares lit during this step start burning
        only after every square has had its turn.
        """
        to_ignite: list[Land] = []
        row: int = 0
        while row < len(self.grid):
            col: int = 0
            while col < len(self.grid[row]):
                cell: Land = self.grid[row][col]
                if cell.is_burning():
                    neighbors: list[Land] = self.neighbors(row, col)
                    index: int = 0
                    while index < len(neighbors):
                        if self.catches(neighbors[index]):
                            to_ignite.append(neighbors[index])
                        index += 1
                    cell.burn()
                col += 1
            row += 1
        index = 0
        while index < len(to_ignite):
            if to_ignite[index].can_ignite():
                to_ignite[index].ignite()
            index += 1
        self.steps += 1

    def catches(self, neighbor: Land) -> bool:
        """Roll the dice for one neighbor of a burning square."""
        if not neighbor.can_ignite():
            return False
        return self.dice.roll() < neighbor.ignition_chance()

    def count_burning(self) -> int:
        """Return how many squares are on fire right now."""
        count: int = 0
        row: int = 0
        while row < len(self.grid):
            col: int = 0
            while col < len(self.grid[row]):
                if self.grid[row][col].is_burning():
                    count += 1
                col += 1
            row += 1
        return count

    def burned_fraction(self) -> float:
        """Return the fraction of fuel squares that have caught fire."""
        burnable: int = 0
        touched: int = 0
        row: int = 0
        while row < len(self.grid):
            col: int = 0
            while col < len(self.grid[row]):
                cell: Land = self.grid[row][col]
                if cell.is_fuel():
                    burnable += 1
                    if not cell.can_ignite():
                        touched += 1
                col += 1
            row += 1
        if burnable == 0:
            return 0.0
        return touched / burnable

    def homes(self) -> list[Land]:
        """Return every Home on the map."""
        raise NotImplementedError("TODO: Landscape.homes")

    def homes_total(self) -> int:
        """Return how many homes are on the map."""
        return len(self.homes())

    def homes_safe(self) -> int:
        """Return how many homes have not caught fire."""
        raise NotImplementedError("TODO: Landscape.homes_safe")

    def draw(self, canvas: Canvas) -> None:
        """Draw every square (this makes Landscape a comp110_gui.Drawable)."""
        row: int = 0
        while row < len(self.grid):
            col: int = 0
            while col < len(self.grid[row]):
                canvas.draw(self.grid[row][col])
                col += 1
            row += 1
