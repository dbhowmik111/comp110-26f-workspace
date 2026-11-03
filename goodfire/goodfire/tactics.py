"""PROVIDED: fire-management tactics for the wildfire season.

Tactic is a base class. It owns the parts every tactic shares (its name,
its cost, applying itself square by square, and counting what it treated).
Each subclass overrides squares() to say WHERE it acts and treat() to say
WHAT it does to one square. Tactics reach the simulation only
through the FireGround protocol.
"""

import math

from comp110_gui import Canvas

from goodfire import paint
from goodfire import terrain
from goodfire.cover import Home
from goodfire.grid import Point
from goodfire.grid import Square
from goodfire.part2_protocols import FireGround
from goodfire.plants import Vegetation
from goodfire.protocols import Burnable
from goodfire.protocols import Land
from goodfire.sketch import Polygon
from goodfire.sketch import Polyline


def pairs(squares: list[Square]) -> list[tuple[int, int]]:
    """Return squares as (row, col) pairs."""
    return [(square.row, square.col) for square in squares]


FUEL_KEPT: float = 0.3
"""Fraction of fuel left after good fire or Firewise clearing."""

WET_STEPS: int = 8
"""How many steps a water drop keeps squares too wet to burn."""


class Cleared:
    """A mowed or disked fuel break: bare soil that cannot burn."""

    row: int
    col: int

    def __init__(self, row: int, col: int):
        """Create a cleared square.

        Args:
            row: The square's row on the map.
            col: The square's column on the map.
        """
        self.row = row
        self.col = col

    def __str__(self) -> str:
        """Describe the square for a person using the app."""
        return f"Fuel break at row {self.row}, column {self.col}: cleared soil"

    def __repr__(self) -> str:
        """Show the code that would rebuild this square."""
        return f"Cleared(row={self.row}, col={self.col})"

    def color(self) -> str:
        """Return the color of bare, disked soil."""
        return "#8A6A48"

    def draw(self, canvas: Canvas) -> None:
        """Draw the cleared square."""
        paint.ground(canvas, self.row, self.col, self.color())

    def is_fuel(self) -> bool:
        """Bare soil never burns."""
        return False

    def is_home(self) -> bool:
        """Return False: this square is not a home."""
        return False

    def can_ignite(self) -> bool:
        """Bare soil never catches fire."""
        return False

    def ignition_chance(self) -> float:
        """Bare soil never catches fire."""
        return 0.0

    def ignite(self) -> None:
        """Do nothing: bare soil never catches fire."""

    def burn(self) -> None:
        """Do nothing: bare soil never burns."""

    def is_burning(self) -> bool:
        """Bare soil is never on fire."""
        return False

    def appearance(self) -> str:
        """Draw bare soil in 3D."""
        return "cleared"


class Tactic:
    """One fire-management action with a cost per square it covers.

    Tactic is never used on its own. Each subclass overrides the three
    methods below that raise NotImplementedError. Leave those three as they
    are here.
    """

    name: str
    cost_per_square: int
    treated: int

    def __init__(self, name: str, cost_per_square: int):
        """Set up the parts every tactic shares.

        Args:
            name: A name for people, like "Prescribed burn".
            cost_per_square: Dollars to treat one 30 m square.
        """
        self.name = name
        self.cost_per_square = cost_per_square
        self.treated = 0

    def squares(self, ground: FireGround) -> list[tuple[int, int]]:
        """Return the (row, col) squares this tactic covers."""
        raise NotImplementedError("each kind of tactic overrides squares()")

    def treat(self, ground: FireGround, row: int, col: int) -> bool:
        """Act on one square; return True if anything changed there."""
        raise NotImplementedError("each kind of tactic overrides treat()")

    def __repr__(self) -> str:
        """Show the code that would rebuild this tactic."""
        raise NotImplementedError("each kind of tactic overrides __repr__()")

    def when(self) -> int:
        """Return the step this tactic acts at; 0 means before the fire."""
        return 0

    def cost(self, ground: FireGround) -> int:
        """Return the dollars this tactic will cost on this ground."""
        return self.cost_per_square * len(self.squares(ground))

    def apply(self, ground: FireGround) -> int:
        """Treat every square this tactic covers; return how many changed."""
        count: int = 0
        row: int
        col: int
        for row, col in self.squares(ground):
            if self.treat(ground, row, col):
                count += 1
        self.treated = count
        return count

    def __str__(self) -> str:
        """Describe the tactic for the plan summary."""
        text: str = f"{self.name} (${self.cost_per_square:,} per square)"
        if self.treated > 0:
            text += f": {self.treated} squares treated"
        return text


class FuelBreak(Tactic):
    """A strip mowed or disked down to bare soil."""

    line: Polyline

    def __init__(self, line: Polyline):
        """Plan a fuel break along a line."""
        super().__init__("Fuel break", 250)
        self.line = line

    def __repr__(self) -> str:
        """Show the code that would rebuild this tactic."""
        return f"FuelBreak({self.line!r})"

    def squares(self, ground: FireGround) -> list[tuple[int, int]]:
        """Return the squares along the line."""
        return pairs(self.line.squares())

    def treat(self, ground: FireGround, row: int, col: int) -> bool:
        """Clear vegetation (never homes, never active fire) to bare soil."""
        cell: Land = ground.cell_at(row, col)
        if not isinstance(cell, Burnable) or isinstance(cell, Home):
            return False
        if cell.is_burning():
            return False
        ground.replace(row, col, Cleared(row, col))
        return True


class DefensibleSpace(Tactic):
    """Firewise: harden homes and clear fuel within 30 m (about 100 ft)."""

    area: Polygon

    def __init__(self, area: Polygon):
        """Plan defensible space for the homes inside an area."""
        super().__init__("Defensible space", 300)
        self.area = area

    def __repr__(self) -> str:
        """Show the code that would rebuild this tactic."""
        return f"DefensibleSpace({self.area!r})"

    def squares(self, ground: FireGround) -> list[tuple[int, int]]:
        """Return each home in the area plus the squares beside it."""
        result: list[tuple[int, int]] = []
        row: int
        col: int
        for row, col in pairs(self.area.squares()):
            if not isinstance(ground.cell_at(row, col), Home):
                continue
            spots: list[tuple[int, int]] = [
                (row, col),
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ]
            spot: tuple[int, int]
            for spot in spots:
                on_map: bool = (
                    0 <= spot[0] < terrain.GRID_SIZE
                    and 0 <= spot[1] < terrain.GRID_SIZE
                )
                if on_map and spot not in result:
                    result.append(spot)
        return result

    def treat(self, ground: FireGround, row: int, col: int) -> bool:
        """Harden a home, or thin the vegetation beside it."""
        cell: Land = ground.cell_at(row, col)
        if isinstance(cell, Home):
            cell.hardened = True
            return True
        if isinstance(cell, Vegetation) and cell.can_ignite():
            cell.fuel = round(cell.fuel * FUEL_KEPT, 2)
            return True
        return False


class WaterDrop(Tactic):
    """A helicopter bucket drop: direct attack at a chosen moment."""

    center: Point
    radius: float
    at_step: int

    def __init__(self, center: Point, radius: float, at_step: int):
        """Plan a water drop.

        Args:
            center: The point the helicopter aims at.
            radius: How many squares the water reaches from the center.
            at_step: The step when the drop happens (1 or later).
        """
        super().__init__("Water drop", 1500)
        self.center = center
        self.radius = radius
        self.at_step = at_step

    def __repr__(self) -> str:
        """Show the code that would rebuild this tactic."""
        return (
            f"WaterDrop(center={self.center!r}, radius={self.radius}, "
            f"at_step={self.at_step})"
        )

    def when(self) -> int:
        """A water drop happens during the fire, not before it."""
        return self.at_step

    def squares(self, ground: FireGround) -> list[tuple[int, int]]:
        """Return squares whose centers are within the radius."""
        result: list[tuple[int, int]] = []
        row: int
        for row in range(terrain.GRID_SIZE):
            col: int
            for col in range(terrain.GRID_SIZE):
                distance: float = math.hypot(
                    row + 0.5 - self.center.row, col + 0.5 - self.center.col
                )
                if distance <= self.radius:
                    result.append((row, col))
        return result

    def treat(self, ground: FireGround, row: int, col: int) -> bool:
        """Knock down any flames, then soak the square."""
        cell: Land = ground.cell_at(row, col)
        if isinstance(cell, Burnable):
            while cell.is_burning():
                cell.burn()
        ground.wet(row, col, WET_STEPS)
        return True
