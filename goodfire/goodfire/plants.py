"""PROVIDED: the plants that grow on the map, and how they burn.

Vegetation holds what every plant shares: its fuel load, its burning
state, and the Alexandridis ignition chance. Grass, Pine, and Hardwood each
supply only what makes that fuel different (its name, how easily it burns,
how long it burns, and its color). They fit the same Land and Burnable
protocols as your Home, Water, and Road.
"""

from comp110_gui import Canvas

from goodfire import paint
from goodfire import science
from goodfire import terrain
from goodfire.cover import BURNED_COLOR
from goodfire.cover import BURNING_COLOR
from goodfire.cover import steps_left


class Vegetation:
    """Shared behavior for every kind of plant fuel.

    Vegetation is never used on its own, because it does not say what kind
    of plant it is. Each subclass overrides the four methods below that
    raise NotImplementedError.
    """

    row: int
    col: int
    fuel: float
    state: str
    time_left: int

    def __init__(self, row: int, col: int, fuel: float):
        """Create unburned vegetation.

        Args:
            row: The square's row on the map.
            col: The square's column on the map.
            fuel: How much there is to burn, from 0.0 to 1.0.
        """
        self.row = row
        self.col = col
        self.fuel = fuel
        self.state = "unburned"
        self.time_left = 0

    def name(self) -> str:
        """Return the plant's name for people, like "Longleaf pine"."""
        raise NotImplementedError("each kind of plant overrides name()")

    def spread_bonus(self) -> float:
        """Return p_veg: how much easier (+) or harder (-) this fuel burns."""
        raise NotImplementedError("each kind of plant overrides spread_bonus()")

    def burn_time(self) -> int:
        """Return how many steps this fuel keeps burning once lit."""
        raise NotImplementedError("each kind of plant overrides burn_time()")

    def base_color(self) -> tuple[int, int, int]:
        """Return the plant's color in the valley, as red, green, blue."""
        raise NotImplementedError("each kind of plant overrides base_color()")

    def __str__(self) -> str:
        """Describe the square for a person using the app."""
        text: str = (
            f"{self.name()} at row {self.row}, column {self.col}: "
            f"{round(self.fuel * 100)}% fuel, {self.state}"
        )
        if self.state == "burning":
            text += f" ({steps_left(self.time_left)})"
        return text

    def __repr__(self) -> str:
        """Show the code that would rebuild this square, for debugging."""
        kind: str = type(self).__name__
        return f"{kind}(row={self.row}, col={self.col}, fuel={self.fuel})"

    def is_fuel(self) -> bool:
        """Every plant is fuel, even one with no fuel load left."""
        return True

    def is_home(self) -> bool:
        """Return False: this square is a plant, not a home."""
        return False

    def can_ignite(self) -> bool:
        """Return True if the plant has fuel and has not burned yet."""
        return self.state == "unburned" and self.fuel > 0.0

    def ignition_chance(self) -> float:
        """Return P_H * (1 + p_veg) * (1 + p_den), before any weather."""
        return (
            science.P_H
            * (1.0 + self.spread_bonus())
            * science.density_factor(self.fuel)
        )

    def ignite(self) -> None:
        """Start burning for this fuel's burn time."""
        self.state = "burning"
        self.time_left = self.burn_time()

    def burn(self) -> None:
        """Burn for one step."""
        self.time_left -= 1
        if self.time_left <= 0:
            self.state = "burned"

    def is_burning(self) -> bool:
        """Return True while the plant is on fire."""
        return self.state == "burning"

    def color(self) -> str:
        """Return the square's color for its current state."""
        if self.state == "burning":
            return BURNING_COLOR
        if self.state == "burned":
            return BURNED_COLOR
        return terrain.shade(self.base_color(), self.row, self.col)

    def draw(self, canvas: Canvas) -> None:
        """Draw the plant, its flames, or its ashes (see paint.py)."""
        paint.plant(
            canvas,
            self.name(),
            self.row,
            self.col,
            self.color(),
            self.state,
            self.time_left,
            self.fuel,
        )


class Grass(Vegetation):
    """Old-field grass and wiregrass: catches fast, burns out fast."""

    def name(self) -> str:
        """Return "Grass"."""
        return "Grass"

    def spread_bonus(self) -> float:
        """Fine, dry grass carries fire easily."""
        return 0.4

    def burn_time(self) -> int:
        """Grass flames pass in about one step."""
        return 1

    def base_color(self) -> tuple[int, int, int]:
        """Return a straw color."""
        return (176, 168, 86)


class Pine(Vegetation):
    """Longleaf pine savanna: a fire-adapted forest."""

    def name(self) -> str:
        """Return "Longleaf pine"."""
        return "Longleaf pine"

    def spread_bonus(self) -> float:
        """Pine needles and wiregrass carry an average surface fire."""
        return 0.0

    def burn_time(self) -> int:
        """A surface fire under longleaf burns for about two steps."""
        return 2

    def base_color(self) -> tuple[int, int, int]:
        """Return a pine green."""
        return (52, 98, 46)

    def __str__(self) -> str:
        """Mature longleaf usually survives a surface fire; say so."""
        text: str = super().__str__()
        if self.state == "burned":
            text += " (the longleaf survived)"
        return text


class Hardwood(Vegetation):
    """Bottomland hardwoods along the river: moist, slow, long-burning."""

    def name(self) -> str:
        """Return "Hardwood"."""
        return "Hardwood"

    def spread_bonus(self) -> float:
        """Moist leaf litter resists fire."""
        return -0.4

    def burn_time(self) -> int:
        """Heavy litter smolders for about three steps."""
        return 3

    def base_color(self) -> tuple[int, int, int]:
        """Return a leafy green."""
        return (70, 120, 60)
