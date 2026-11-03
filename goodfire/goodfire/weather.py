"""PROVIDED: weather and terrain effects. Each fits the WeatherEffect protocol.

The simulation keeps a list of effects and asks each one, in order, to
adjust the spread chance. Adding a new kind of weather means writing a new
class; the simulation itself never changes. The formulas follow
Alexandridis et al. (2008) and Rothermel (1972); see science.py.
"""

import math

from goodfire import science
from goodfire import terrain
from goodfire.protocols import Land

COMPASS: list[str] = [
    "north",
    "northeast",
    "east",
    "southeast",
    "south",
    "southwest",
    "west",
    "northwest",
]


def bearing(source: Land, target: Land) -> float:
    """Return the compass bearing from source to target, in degrees.

    0 is north (toward row 0), 90 is east, 180 is south, 270 is west.
    """
    degrees: float = math.degrees(
        math.atan2(target.col - source.col, source.row - target.row)
    )
    return degrees % 360.0


class Slope:
    """Fire races uphill: flames lean over and preheat the fuel above them."""

    def __init__(self):
        """Create a slope effect (the terrain itself never changes)."""

    def __repr__(self) -> str:
        """Show the code that would rebuild this effect."""
        return "Slope()"

    def describe(self) -> str:
        """Return a short description for the weather report."""
        return "slope"

    def slope_degrees(self, source: Land, target: Land) -> float:
        """Return the rise from source to target in degrees (down is < 0)."""
        rise: float = terrain.elevation(
            target.row, target.col
        ) - terrain.elevation(source.row, source.col)
        return math.degrees(math.atan(rise / science.CELL_METERS))

    def adjust(self, source: Land, target: Land, chance: float) -> float:
        """Multiply by p_slope = exp(a * slope in degrees)."""
        return chance * math.exp(
            science.SLOPE_A * self.slope_degrees(source, target)
        )

    def advance(self) -> None:
        """The hill does not change over time."""


class Wind:
    """Wind pushes flames and embers downwind."""

    speed: float
    toward: float

    def __init__(self, speed: float, toward: float):
        """Create a steady wind.

        Args:
            speed: Wind speed in meters per second (6 m/s is a fresh breeze).
            toward: The compass bearing the wind blows toward, in degrees.
                A south wind blows toward the north: toward=0.
        """
        self.speed = speed
        self.toward = toward

    def __repr__(self) -> str:
        """Show the code that would rebuild this wind."""
        return f"Wind(speed={self.speed}, toward={self.toward})"

    def heading(self) -> str:
        """Return the nearest of 8 compass names for the wind's direction."""
        index: int = round((self.toward % 360.0) / 45.0) % 8
        return COMPASS[index]

    def describe(self) -> str:
        """Return a short description for the weather report."""
        return f"wind {self.speed:.1f} m/s toward {self.heading()}"

    def adjust(self, source: Land, target: Land, chance: float) -> float:
        """Multiply by p_wind = exp(V * (c1 + c2 * (cos(theta) - 1)))."""
        theta: float = math.radians(bearing(source, target) - self.toward)
        return chance * math.exp(
            self.speed * (science.C1 + science.C2 * (math.cos(theta) - 1.0))
        )

    def advance(self) -> None:
        """This wind stays steady."""


class FuelMoisture:
    """Damp fuel resists fire; drought-dry fuel carries it."""

    moisture: float

    def __init__(self, moisture: float):
        """Create a fuel-moisture effect.

        Args:
            moisture: Dead-fuel moisture as a fraction of dry weight; 0.06
                is drought-dry, 0.12 is typical, 0.30 stops these fuels.
        """
        self.moisture = moisture

    def __repr__(self) -> str:
        """Show the code that would rebuild this effect."""
        return f"FuelMoisture(moisture={self.moisture})"

    def describe(self) -> str:
        """Return a short description for the weather report."""
        return f"fuel moisture {round(self.moisture * 100)}%"

    def adjust(self, source: Land, target: Land, chance: float) -> float:
        """Multiply by max(0, 1 - M / M_x), M_x = moisture of extinction."""
        damping: float = 1.0 - self.moisture / science.MOISTURE_OF_EXTINCTION
        return chance * max(damping, 0.0)

    def advance(self) -> None:
        """Fuel moisture stays steady during one fire."""
