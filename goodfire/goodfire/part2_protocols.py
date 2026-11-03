"""PROVIDED: the protocols Part 2 adds.

Part 1's Land, Burnable, and Feature protocols still describe the map.
These new protocols describe weather, the simulations the 3D viewer can
run, and an optional way for a square to say what it looks like in 3D.
"""

from typing import Protocol
from typing import runtime_checkable

from goodfire.protocols import Land


class WeatherEffect(Protocol):
    """Anything that changes how easily fire spreads between two squares."""

    def adjust(self, source: Land, target: Land, chance: float) -> float:
        """Return a new ignition chance for fire spreading source -> target.

        Args:
            source: The burning square.
            target: The neighboring square that might catch fire.
            chance: The chance so far, after earlier effects.

        Returns:
            The adjusted chance. The simulation clamps it to 0.0-1.0.
        """
        ...

    def advance(self) -> None:
        """Update this effect once per step (most weather stays steady)."""
        ...

    def describe(self) -> str:
        """Return a short description for the weather report."""
        ...


class Simulation(Protocol):
    """Anything the 3D viewer can show and run.

    Part 1's Landscape fits this protocol, and so does Part 2's Wildfire.
    """

    def cell_at(self, row: int, col: int) -> Land:
        """Return the object on one square."""
        ...

    def ignite(self, row: int, col: int) -> bool:
        """Set one square on fire if it can burn."""
        ...

    def step(self) -> None:
        """Advance the fire by one step."""
        ...


@runtime_checkable
class HasWeather(Protocol):
    """A simulation that can also report its weather and water drops."""

    def weather_report(self) -> str:
        """Return one line describing the current weather."""
        ...

    def water_drops(self) -> list[tuple[float, float, float]]:
        """Return (row, col, radius) for each water drop made this step."""
        ...


@runtime_checkable
class Rendered(Protocol):
    """A square that tells the 3D viewer which model to draw.

    The viewer understands "pine", "hardwood", "grass", "home", "water",
    "road", and "cleared". Squares without appearance() are drawn as plain
    colored ground.
    """

    def appearance(self) -> str:
        """Return the name of the 3D model for this square."""
        ...


class FireGround(Protocol):
    """What a management tactic may do to the simulation.

    Tactics depend on this small interface, not on the Wildfire class, so
    they can be tested on any object that offers these three methods. Burn
    plans use it too.
    """

    def cell_at(self, row: int, col: int) -> Land:
        """Return the object on one square."""
        ...

    def replace(self, row: int, col: int, cell: Land) -> None:
        """Put a new object on one square (for example, a cleared break)."""
        ...

    def wet(self, row: int, col: int, steps: int) -> None:
        """Soak one square: no fire spreads into it for ``steps`` steps."""
        ...
