"""PROVIDED: the protocols (interfaces) the app and simulator depend on.

A protocol lists the attributes and methods an object must have. A class
satisfies a protocol just by having them; it never inherits from it. The app
never imports your classes by name. It only needs objects with these shapes,
plus comp110_gui's own Drawable protocol (any object with draw(canvas)).
"""

from typing import Protocol
from typing import runtime_checkable

from comp110_gui import Canvas

from goodfire.grid import Square


class Land(Protocol):
    """Anything that can occupy one 30 m square of the map.

    Every square answers the same questions about fire, even squares that
    can never burn: Water and Road simply answer False (or 0.0). That way
    the Landscape can ask any square what it can do without caring which
    class it is.
    """

    row: int
    col: int

    def is_fuel(self) -> bool:
        """Return True for plants and homes: things that could ever burn."""
        ...

    def is_home(self) -> bool:
        """Return True only for a Home."""
        ...

    def can_ignite(self) -> bool:
        """Return True if this square could catch fire right now."""
        ...

    def ignition_chance(self) -> float:
        """Return the chance, from 0.0 to 1.0, that one burning neighbor
        sets this square on fire during one step (before weather)."""
        ...

    def ignite(self) -> None:
        """Start burning (squares that cannot burn do nothing)."""
        ...

    def burn(self) -> None:
        """Burn for one step (squares that cannot burn do nothing)."""
        ...

    def is_burning(self) -> bool:
        """Return True while this square is on fire."""
        ...

    def color(self) -> str:
        """Return the "#RRGGBB" color used to draw this square."""
        ...

    def draw(self, canvas: Canvas) -> None:
        """Record this square's artwork on the canvas (comp110_gui.Drawable).

        Args:
            canvas: The canvas that shows the whole map.
        """
        ...


@runtime_checkable
class Burnable(Protocol):
    """Anything with a fuel load that fire can spread into: plants and homes.

    Because this protocol is runtime checkable, ``isinstance(cell, Burnable)``
    asks whether an object has these attributes and methods, whatever class
    it belongs to.
    """

    fuel: float

    def can_ignite(self) -> bool:
        """Return True if this object could catch fire right now."""
        ...

    def ignition_chance(self) -> float:
        """Return the chance, from 0.0 to 1.0, that one burning neighbor
        sets this object on fire during one step (before weather)."""
        ...

    def ignite(self) -> None:
        """Start burning."""
        ...

    def burn(self) -> None:
        """Burn for one step, and burn out when no time is left."""
        ...

    def is_burning(self) -> bool:
        """Return True while this object is on fire."""
        ...


@runtime_checkable
class Feature(Protocol):
    """A shape sketched on the map, like a marker stroke on a sand table.

    Your Polygon and Polyline classes fit this protocol, and so does the
    provided PhotoSketch, which reads shapes from a photo of a drawing.
    """

    cover: str

    def squares(self) -> list[Square]:
        """Return every square this shape covers, on the map."""
        ...
