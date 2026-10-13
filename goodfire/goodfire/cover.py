"""STUDENT: homes, water, and roads: what people add to the map.

Every square of the map holds one object. The plants (grass, longleaf pine,
and hardwoods) are provided in plants.py. Here are the other three kinds of
square. Home, Water, and Road share no code with the plants or with each
other, yet the app and the Landscape treat them all alike, because every
one fits the Land protocol (see protocols.py).

Methods that already have code are provided: read them, they are worked
examples. Replace each raise NotImplementedError("TODO: ...") with your
own code.
"""

__author__: str = ""  # TODO: your 9-digit PID, like "730123456"

from comp110_gui import Canvas

from goodfire import paint
from goodfire import science

BURNING_COLOR: str = "#8A3A16"
BURNED_COLOR: str = "#2E2A26"


def steps_left(count: int) -> str:
    """Return "1 step left" or "3 steps left"."""
    if count == 1:
        return "1 step left"
    return f"{count} steps left"


class Home:
    """A home at the wildland-urban interface.

    Fire can reach a home, just as it reaches the plants. A hardened home
    (Firewise: ember-resistant vents, a clear 0-5 ft zone) is much harder
    to ignite.
    """

    row: int
    col: int
    hardened: bool
    fuel: float
    state: str
    time_left: int

    def __init__(self, row: int, col: int, hardened: bool):
        """Create a safe home.

        Args:
            row: The home's row on the map.
            col: The home's column on the map.
            hardened: True if the home has Firewise ember protection.
        """
        self.row = row
        self.col = col
        self.hardened = hardened
        self.fuel = 1.0
        self.state = "safe"
        self.time_left = 0

    def __str__(self) -> str:
        """Describe the home for a person using the app."""
        where: str = f"Home at row {self.row}, column {self.col}"
        if self.hardened:
            where += " (Firewise)"
        if self.state == "burning":
            return f"{where}: on fire ({steps_left(self.time_left)})"
        return f"{where}: {self.state}"

    def __repr__(self) -> str:
        """Show the code that would rebuild this home."""
        return f"Home(row={self.row}, col={self.col}, hardened={self.hardened})"

    def is_fuel(self) -> bool:
        """A home can burn."""
        return True

    def is_home(self) -> bool:
        """Return True: this square is a home."""
        raise NotImplementedError("TODO: Home.is_home")

    def can_ignite(self) -> bool:
        """Return True while the home is safe."""
        raise NotImplementedError("TODO: Home.can_ignite")

    def ignition_chance(self) -> float:
        """Homes resist ignition; Firewise homes resist much more."""
        chance: float = science.P_H * (1.0 - 0.2)
        if self.hardened:
            chance = chance * 0.3
        return chance

    def ignite(self) -> None:
        """Catch fire; a home burns for four steps."""
        raise NotImplementedError("TODO: Home.ignite")

    def burn(self) -> None:
        """Burn for one step."""
        self.time_left -= 1
        if self.time_left <= 0:
            self.state = "damaged"

    def is_burning(self) -> bool:
        """Return True while the home is on fire."""
        raise NotImplementedError("TODO: Home.is_burning")

    def color(self) -> str:
        """Return a yard color for the home's square."""
        if self.state == "burning":
            return BURNING_COLOR
        if self.state == "damaged":
            return BURNED_COLOR
        return "#9DB07A"

    def draw(self, canvas: Canvas) -> None:
        """Draw the home, its yard, and any fire (see paint.py)."""
        paint.home(
            canvas,
            self.row,
            self.col,
            self.color(),
            self.state,
            self.hardened,
            self.time_left,
        )


class Water:
    """A river or pond. Fire cannot cross it: a natural anchor point."""

    row: int
    col: int

    def __init__(self, row: int, col: int):
        """Create a water square.

        Args:
            row: The square's row on the map.
            col: The square's column on the map.
        """
        self.row = row
        self.col = col

    def __str__(self) -> str:
        """Describe the square for a person using the app."""
        return f"Water at row {self.row}, column {self.col}: cannot burn"

    def __repr__(self) -> str:
        """Show the code that would rebuild this square."""
        return f"Water(row={self.row}, col={self.col})"

    def is_fuel(self) -> bool:
        """Water never burns."""
        return False

    def is_home(self) -> bool:
        """Return False: this square is not a home."""
        raise NotImplementedError("TODO: Water.is_home")

    def can_ignite(self) -> bool:
        """Water never catches fire."""
        raise NotImplementedError("TODO: Water.can_ignite")

    def ignition_chance(self) -> float:
        """Water never catches fire."""
        return 0.0

    def ignite(self) -> None:
        """Do nothing: water never catches fire."""

    def burn(self) -> None:
        """Do nothing: water never burns."""

    def is_burning(self) -> bool:
        """Water is never on fire."""
        raise NotImplementedError("TODO: Water.is_burning")

    def color(self) -> str:
        """Return a river blue."""
        return "#3F8FC9"

    def draw(self, canvas: Canvas) -> None:
        """Draw open water (see paint.py)."""
        paint.water(canvas, self.row, self.col, self.color())


class Road:
    """Pavement. Crews use roads as ready-made fuel breaks."""

    row: int
    col: int

    def __init__(self, row: int, col: int):
        """Create a road square.

        Args:
            row: The square's row on the map.
            col: The square's column on the map.
        """
        self.row = row
        self.col = col

    def __str__(self) -> str:
        """Describe the square for a person using the app."""
        return f"Road at row {self.row}, column {self.col}: cannot burn"

    def __repr__(self) -> str:
        """Show the code that would rebuild this square."""
        return f"Road(row={self.row}, col={self.col})"

    def is_fuel(self) -> bool:
        """Pavement never burns."""
        return False

    def is_home(self) -> bool:
        """Return False: this square is not a home."""
        return False

    def can_ignite(self) -> bool:
        """Pavement never catches fire."""
        return False

    def ignition_chance(self) -> float:
        """Pavement never catches fire."""
        return 0.0

    def ignite(self) -> None:
        """Do nothing: pavement never catches fire."""

    def burn(self) -> None:
        """Do nothing: pavement never burns."""

    def is_burning(self) -> bool:
        """Pavement is never on fire."""
        return False

    def color(self) -> str:
        """Return an asphalt gray."""
        return "#6E6A66"

    def draw(self, canvas: Canvas) -> None:
        """Draw pavement (see paint.py)."""
        paint.road(canvas, self.row, self.col, self.color())
