"""PROVIDED: five season plans for the crew to compare.

Each plan is a burn plan for good fire (or none) plus tactics for the
wildfire season, all within one $40,000 budget. Run
``uv run python compare_plans.py`` to see how each one does over ten seasons
in both climates, then choose the best one in plan.py.

Map reminders: row 0 is north and uphill, and burn-day winds blow toward
the north. The river runs east-west across rows 8-10 and the county road
runs north-south near column 15. The wildfires start at row 23, column 8
(the meadow) and row 21, column 17 (the pines). One neighborhood sits at
rows 2-4, columns 11-18; another is in the pines at rows 14-16, columns
21-25.
"""

from goodfire.burnplan import BurnPlan
from goodfire.grid import Point
from goodfire.grid import Square
from goodfire.part2_protocols import FireGround
from goodfire.sketch import Polygon
from goodfire.sketch import Polyline
from goodfire.tactics import DefensibleSpace
from goodfire.tactics import FuelBreak
from goodfire.tactics import Tactic

PLANS: dict[str, str] = {
    "A": "a small backing burn southeast of the road, and one fuel break",
    "B": "burn everything south of the river in strips on any day with wind "
    "up to 9 m/s, and Firewise the homes in the pines",
    "C": "burn everything south of the river in strips on a calm, damp day, "
    "with no Firewise work",
    "D": "burn everything south of the river in strips on a calm, damp day, "
    "and Firewise the homes in the pines",
    "E": "no burn: Firewise both neighborhoods and cut a fuel break",
}
"""Each plan's name and what it does."""

CAREFUL: dict[str, list[float]] = {"wind": [1.0, 4.0], "moisture": [0.08, 0.20]}
"""A careful prescription: light wind, fuel damp enough to burn gently."""

ANY_DAY: dict[str, list[float]] = {"wind": [1.0, 9.0], "moisture": [0.04, 0.22]}
"""A wide prescription that fits almost any day in the burn window."""


class SeasonPlan:
    """One of the plans in PLANS: a burn plan and tactics for a season."""

    name: str

    def __init__(self, name: str):
        """Choose a plan by name.

        Raises:
            ValueError: If name is not one of the plans in PLANS.
        """
        if name not in PLANS:
            raise ValueError(
                f"no plan named {name!r}; choose one of {list(PLANS)}"
            )
        self.name = name

    def __str__(self) -> str:
        """Describe the plan."""
        return f"Plan {self.name}: {PLANS[self.name]}"

    def __repr__(self) -> str:
        """Show the code that would rebuild this plan."""
        return f"SeasonPlan({self.name!r})"

    def burn_plan(self) -> BurnPlan | None:
        """Return this season's burn plan, or None for no burn."""
        if self.name == "A":
            return backing_burn()
        if self.name == "B":
            return strip_burn(ANY_DAY)
        if self.name in ("C", "D"):
            return strip_burn(CAREFUL)
        return None

    def tactics(self, ground: FireGround, starts: list[Square]) -> list[Tactic]:
        """Return the tactics for the wildfire season, most important first.

        Tactics that do not fit in what is left of the budget are skipped.
        """
        if self.name == "A":
            return [FuelBreak(south_break())]
        if self.name in ("B", "D"):
            return [DefensibleSpace(pine_homes())]
        if self.name == "E":
            return [
                DefensibleSpace(pine_homes()),
                DefensibleSpace(north_homes()),
                FuelBreak(south_break()),
            ]
        return []


def backing_burn() -> BurnPlan:
    """A backing fire in the pines southeast of the road.

    The crew lights only the north edge, so the fire backs south into the
    wind. A backing fire is slow and easy to hold, but on a damp day it
    may go out before it crosses the unit.
    """
    southeast_pines: Polygon = Polygon(
        [
            Point(21.0, 15.0),
            Point(21.0, 30.0),
            Point(30.0, 30.0),
            Point(30.0, 15.0),
        ],
        "pine",
    )
    north_edge: Polyline = Polyline(
        [Point(21.5, 15.0), Point(21.5, 30.0)], "road"
    )
    return BurnPlan(southeast_pines, {"pine", "grass"}, north_edge, CAREFUL)


def strip_burn(prescription: dict[str, list[float]]) -> BurnPlan:
    """Burn every pine and grass square south of the river, lit in strips.

    The river and the road are anchors, so the control line is short.
    Strips two rows apart mean no strip of fire has far to go.
    """
    everything_south: Polygon = Polygon(
        [
            Point(11.0, 0.0),
            Point(11.0, 30.0),
            Point(30.0, 30.0),
            Point(30.0, 0.0),
        ],
        "pine",
    )
    return BurnPlan(
        everything_south, {"pine", "grass"}, strips(11, 29, 2), prescription
    )


def strips(top: int, bottom: int, gap: int) -> Polyline:
    """Return a back-and-forth ignition line across the whole map."""
    points: list[Point] = []
    row: int = top
    west_to_east: bool = True
    while row <= bottom:
        if west_to_east:
            points.append(Point(row + 0.5, 0.0))
            points.append(Point(row + 0.5, 29.9))
        else:
            points.append(Point(row + 0.5, 29.9))
            points.append(Point(row + 0.5, 0.0))
        west_to_east = not west_to_east
        row += gap
    return Polyline(points, "road")


def pine_homes() -> Polygon:
    """The neighborhood in the pines, with room for its defensible space."""
    return Polygon(
        [
            Point(13.5, 20.5),
            Point(13.5, 26.5),
            Point(17.5, 26.5),
            Point(17.5, 20.5),
        ],
        "homes",
    )


def north_homes() -> Polygon:
    """The neighborhood north of the river, uphill."""
    return Polygon(
        [
            Point(1.5, 10.5),
            Point(1.5, 19.5),
            Point(5.5, 19.5),
            Point(5.5, 10.5),
        ],
        "homes",
    )


def south_break() -> Polyline:
    """A fuel break south of the neighborhood in the pines."""
    return Polyline([Point(18.5, 16.0), Point(18.5, 30.0)], "road")
