"""STUDENT: plan a prescribed burn with sets and dictionaries.

A burn boss writes a burn plan before lighting good fire: the burn unit,
the fuels the fire is meant to burn, control lines wherever the fire could
leave those fuels, and a prescription (the weather the burn may happen
in). The first five functions below are yours. Each one works only on the
lists, sets, and dictionaries it is given. fire_reach(), control_line(),
and BurnPlan, after them, are worked examples that put your functions to
work on the map.

A Square is a label for one place on the map. You never need to look
inside one: put Squares in sets, use them as dictionary keys, and compare
them with == and in.

Methods that already have code are provided: read them, they are worked
examples. Replace each raise NotImplementedError("TODO: ...") with your
own code.
"""

__author__: str = ""  # TODO: your 9-digit PID, like "730123456"

from goodfire.fieldkit import land_map
from goodfire.fieldkit import neighbor_map
from goodfire.fieldkit import squares_of
from goodfire.grid import Square
from goodfire.part2_protocols import FireGround
from goodfire.sketch import Polygon
from goodfire.sketch import Polyline

KEEP_FIRE_AWAY_FROM: str = "home"
"""The kind of land a burn must not touch, or even stand next to."""

BURNABLE: set[str] = {"pine", "grass", "hardwood", "home"}
"""Kinds of land fire can spread into."""

BURN_COST: int = 25
"""Dollars to burn one 30 m square with good fire."""

LINE_COST: int = 250
"""Dollars to mow or disk one square of control line."""


def count(kinds: list[str]) -> dict[str, int]:
    """Count how many times each kind of land appears in a list.

    Example: count(["pine", "pine", "home"]) is {"pine": 2, "home": 1}.
    """
    raise NotImplementedError("TODO: count")


def group_by_kind(land: dict[Square, str]) -> dict[str, set[Square]]:
    """Group squares by the kind of land on them.

    Example: if land is {a: "pine", b: "home", c: "pine"}, the result is
    {"pine": {a, c}, "home": {b}}.
    """
    raise NotImplementedError("TODO: group_by_kind")


def in_prescription(
    forecast: dict[str, float], prescription: dict[str, list[float]]
) -> bool:
    """Return True if a day's forecast fits every range in a prescription.

    Each value in prescription is a [low, high] range; both ends are
    allowed. The forecast must have every condition the prescription
    names. Example: {"wind": 2.5, "moisture": 0.14} fits
    {"wind": [1.0, 4.0]}, but {"moisture": 0.14} does not.
    """
    raise NotImplementedError("TODO: in_prescription")


def first_burn_day(
    forecasts: list[dict[str, float]], prescription: dict[str, list[float]]
) -> int:
    """Return the index of the first forecast that fits the prescription.

    Return -1 if no forecast fits. Use in_prescription.
    """
    raise NotImplementedError("TODO: first_burn_day")


def spread_once(
    burning: set[Square],
    fuel: set[Square],
    neighbors: dict[Square, list[Square]],
) -> set[Square]:
    """Return the squares fire spreads to in one step.

    These are the neighbors of burning squares (neighbors[square]) that
    are fuel and are not burning yet.
    """
    raise NotImplementedError("TODO: spread_once")


def fire_reach(
    start: set[Square], fuel: set[Square], neighbors: dict[Square, list[Square]]
) -> set[Square]:
    """Worked example: every fuel square fire could reach from the start.

    Fire starts at the start squares that are fuel. Then it spreads one
    step at a time (your spread_once) until a step catches nothing new.
    """
    reached: set[Square] = set()
    square: Square
    for square in start:
        if square in fuel:
            reached.add(square)
    caught: set[Square] = spread_once(reached, fuel, neighbors)
    while len(caught) > 0:
        reached = reached | caught
        caught = spread_once(reached, fuel, neighbors)
    return reached


def control_line(
    burn: set[Square],
    burnable: set[Square],
    neighbors: dict[Square, list[Square]],
) -> set[Square]:
    """Worked example: where fire would escape the burn, so a line goes there.

    Returns every neighbor of a burn square that is burnable but not in the
    burn. Fire can leave the burn only through these squares.
    """
    line: set[Square] = set()
    square: Square
    for square in burn:
        neighbor: Square
        for neighbor in neighbors[square]:
            if neighbor in burnable and neighbor not in burn:
                line.add(neighbor)
    return line


class BurnPlan:
    """Worked example: a burn plan built from the functions above."""

    unit: Polygon
    species: set[str]
    ignition: Polyline
    prescription: dict[str, list[float]]

    def __init__(
        self,
        unit: Polygon,
        species: set[str],
        ignition: Polyline,
        prescription: dict[str, list[float]],
    ):
        """Write a burn plan.

        Args:
            unit: The burn unit, drawn as a polygon.
            species: The kinds of land to burn, like {"pine", "grass"}.
            ignition: The line the crew lights fire along.
            prescription: The allowed [low, high] range for each weather
                condition, like {"wind": [1.0, 4.0], "moisture": [...]}.
        """
        self.unit = unit
        self.species = species
        self.ignition = ignition
        self.prescription = prescription

    def area(self, ground: FireGround) -> set[Square]:
        """Return the squares this burn should blacken.

        Start with the unit's squares of the species to burn, take away
        every home and every square next to a home, then keep what fire
        can reach from the ignition line.
        """
        groups: dict[str, set[Square]] = group_by_kind(land_map(ground))
        neighbors: dict[Square, list[Square]] = neighbor_map()
        fuel: set[Square] = set()
        kind: str
        for kind in self.species:
            if kind in groups:
                fuel = fuel | groups[kind]
        too_close: set[Square] = set()
        if KEEP_FIRE_AWAY_FROM in groups:
            home: Square
            for home in groups[KEEP_FIRE_AWAY_FROM]:
                too_close.add(home)
                neighbor: Square
                for neighbor in neighbors[home]:
                    too_close.add(neighbor)
        fuel = (fuel & squares_of(self.unit)) - too_close
        return fire_reach(squares_of(self.ignition), fuel, neighbors)

    def line(self, ground: FireGround) -> set[Square]:
        """Return the control line that holds the burn in its area."""
        land: dict[Square, str] = land_map(ground)
        burnable: set[Square] = set()
        square: Square
        for square in land:
            if land[square] in BURNABLE:
                burnable.add(square)
        return control_line(self.area(ground), burnable, neighbor_map())

    def cost(self, ground: FireGround) -> int:
        """Return the dollars to build the line and burn the area."""
        return BURN_COST * len(self.area(ground)) + LINE_COST * len(
            self.line(ground)
        )
