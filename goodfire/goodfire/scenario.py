"""PROVIDED: the standard fire season used by the 3D app and the grader.

Two climates share one landscape. "historical" fire weather is a moderate
south breeze over typically damp fuel. "hotter_drier" is the kind of day a
warming climate makes more common: a stronger wind over drought-dry fuel.
Before the season, the crew has a two-week burn window; each climate has
its own run of daily forecasts, and drier, windier climates offer fewer
days that fit a careful prescription.
"""

import random

from goodfire.burnplan import BurnPlan
from goodfire.grid import Point
from goodfire.grid import Square
from goodfire.landscape import Landscape
from goodfire.part2_protocols import WeatherEffect
from goodfire.plans import SeasonPlan
from goodfire.protocols import Feature
from goodfire.simulation import Wildfire
from goodfire.sketch import Polygon
from goodfire.sketch import Polyline
from goodfire.tactics import Tactic
from goodfire.weather import FuelMoisture
from goodfire.weather import Slope
from goodfire.weather import Wind

RIVER: Polyline = Polyline(
    [
        Point(8.9, -0.5),
        Point(9.7, 2.5),
        Point(10.3, 5.5),
        Point(10.5, 8.5),
        Point(10.1, 11.5),
        Point(9.4, 14.5),
        Point(8.5, 17.5),
        Point(7.8, 20.5),
        Point(7.5, 23.5),
        Point(7.8, 26.5),
        Point(8.4, 29.5),
        Point(8.7, 30.5),
    ],
    "river",
)
ROAD: Polyline = Polyline(
    [Point(30.0, 14.6), Point(19.0, 14.6), Point(12.0, 15.6), Point(5.0, 15.6)],
    "road",
)
NORTH_HOMES: Polygon = Polygon(
    [Point(2.0, 11.0), Point(2.0, 19.0), Point(5.0, 19.0), Point(5.0, 11.0)],
    "homes",
)
PINE_HOMES: Polygon = Polygon(
    [
        Point(14.0, 21.0),
        Point(14.0, 26.0),
        Point(17.0, 26.0),
        Point(17.0, 21.0),
    ],
    "homes",
)

FIRE_STARTS: list[Square] = [Square(23, 8), Square(21, 17)]
"""Where the season's two fires start: the meadow, and the pines east of it."""

BUDGET: int = 40_000
"""Dollars available for tactics each season."""

MAX_STEPS: int = 200
"""A season stops after this many steps even if something still burns."""

CLIMATES: list[str] = ["historical", "hotter_drier"]

BURN_WINDOW_DAYS: int = 14
"""How many days of forecasts the crew may choose a burn day from."""


def features() -> list[Feature]:
    """Return the season's sketch: river, road, and two neighborhoods."""
    return [RIVER, ROAD, NORTH_HOMES, PINE_HOMES]


def weather(climate: str) -> list[WeatherEffect]:
    """Return fresh weather effects for a climate scenario.

    Args:
        climate: "historical" or "hotter_drier".

    Raises:
        ValueError: For an unknown climate name.
    """
    if climate == "historical":
        return [Slope(), Wind(4.0, 0.0), FuelMoisture(0.12)]
    if climate == "hotter_drier":
        return [Slope(), Wind(7.0, 0.0), FuelMoisture(0.06)]
    raise ValueError(f"unknown climate {climate!r}; expected one of {CLIMATES}")


def forecasts(climate: str, seed: int) -> list[dict[str, float]]:
    """Return one forecast per day of the burn window.

    Each forecast holds "wind" (m/s, blowing toward the north) and
    "moisture" (dead-fuel moisture as a fraction of dry weight).

    Args:
        climate: "historical" or "hotter_drier".
        seed: The season's random seed; the same seed gives the same days.
    """
    winds: list[float] = [1.0, 7.0]
    moistures: list[float] = [0.06, 0.22]
    if climate == "hotter_drier":
        winds = [1.5, 9.0]
        moistures = [0.04, 0.16]
    days: random.Random = random.Random(seed * 1000 + len(climate))
    result: list[dict[str, float]] = []
    while len(result) < BURN_WINDOW_DAYS:
        result.append(
            {
                "wind": round(days.uniform(winds[0], winds[1]), 1),
                "moisture": round(days.uniform(moistures[0], moistures[1]), 2),
            }
        )
    return result


def build(seed: int, climate: str, plan: SeasonPlan | None) -> Wildfire:
    """Set up one season: grow the land, schedule the plan, light the fires.

    The burn plan is charged first, then the tactics. If a burn day is set,
    the season's fires start when the burn is out.

    Args:
        seed: The random seed for the landscape and the fire.
        climate: "historical" or "hotter_drier".
        plan: The season plan to schedule, or None for no plan.

    Returns:
        A Wildfire ready to step.
    """
    landscape: Landscape = Landscape(seed, features())
    sim: Wildfire = Wildfire(landscape, weather(climate), BUDGET, seed)
    sim.fire_starts = list(FIRE_STARTS)
    burning: bool = False
    if plan is not None:
        burn: BurnPlan | None = plan.burn_plan()
        if burn is not None:
            try:
                burning = sim.plan_burn(burn, forecasts(climate, seed))
            except NotImplementedError as unfinished:
                sim.note = f"No burn day yet: {unfinished}"
        tactic: Tactic
        for tactic in plan.tactics(sim, list(FIRE_STARTS)):
            sim.schedule(tactic)
    if not burning:
        sim.begin_season()
    return sim


def run_to_end(sim: Wildfire) -> Wildfire:
    """Step until the fire is out or MAX_STEPS have passed."""
    while not sim.is_over() and sim.steps < MAX_STEPS:
        sim.step()
    return sim
