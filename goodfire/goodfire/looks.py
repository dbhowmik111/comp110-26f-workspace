"""PROVIDED: what each kind of square looks like in the 3D view.

The 3D viewer and the burn plan ask every square appearance() (the
Rendered protocol). Your Part 1 classes do not have that method, and Part 2
never changes your Part 1 files, so install() adds it to each class when
Part 2 starts (fieldkit.py calls it). A class that already has
appearance() keeps its own.
"""

from collections.abc import Callable

from goodfire.cover import Home
from goodfire.cover import Road
from goodfire.cover import Water
from goodfire.plants import Grass
from goodfire.plants import Hardwood
from goodfire.plants import Pine

LOOKS: dict[type, str] = {
    Home: "home",
    Water: "water",
    Road: "road",
    Grass: "grass",
    Pine: "pine",
    Hardwood: "hardwood",
}
"""The 3D model name for each kind of square."""


def looks_like(kind: str) -> Callable[[object], str]:
    """Return an appearance() method that always answers kind."""

    def appearance(self: object) -> str:
        """Return the name of this square's 3D model."""
        return kind

    return appearance


def install() -> None:
    """Give each class in LOOKS an appearance() if it has none yet."""
    for cls in LOOKS:
        if not hasattr(cls, "appearance"):
            setattr(cls, "appearance", looks_like(LOOKS[cls]))  # noqa: B010
