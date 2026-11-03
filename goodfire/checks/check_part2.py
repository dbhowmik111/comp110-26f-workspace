"""Checks for Part 2: burn plans, embers, the burn day, and the season.

Run with:  uv run python -m pytest checks
The Gradescope autograder checks the same behavior (and a little more).
"""

import pytest

from goodfire import plan as chosen
from goodfire import scenario
from goodfire.burnplan import BurnPlan
from goodfire.burnplan import control_line
from goodfire.burnplan import count
from goodfire.burnplan import fire_reach
from goodfire.burnplan import first_burn_day
from goodfire.burnplan import group_by_kind
from goodfire.burnplan import in_prescription
from goodfire.burnplan import spread_once
from goodfire.cover import Home
from goodfire.cover import Road
from goodfire.cover import Water
from goodfire.dice import Dice
from goodfire.fieldkit import kind_at
from goodfire.grid import Point
from goodfire.grid import Square
from goodfire.landscape import Landscape
from goodfire.part2_protocols import HasWeather
from goodfire.part2_protocols import Rendered
from goodfire.plans import CAREFUL
from goodfire.plans import PLANS
from goodfire.plans import SeasonPlan
from goodfire.plans import backing_burn
from goodfire.plans import strip_burn
from goodfire.plants import Grass
from goodfire.plants import Hardwood
from goodfire.plants import Pine
from goodfire.protocols import Land
from goodfire.recursion import spot_fire
from goodfire.simulation import Wildfire
from goodfire.sketch import Polygon
from goodfire.sketch import Polyline
from goodfire.tactics import Cleared
from goodfire.tactics import DefensibleSpace
from goodfire.tactics import FuelBreak
from goodfire.tactics import WaterDrop
from goodfire.weather import Wind


class Field:
    """A tiny FireGround drawn as a picture; off the picture is water.

    Letters: P pine, , grass, h hardwood, H home, ~ water, = road.
    """

    grid: list[list[Land]]

    def __init__(self, picture: list[str]):
        """Build a 30 x 30 map with the picture in its north-west corner."""
        self.grid = []
        row: int
        for row in range(30):
            cells: list[Land] = []
            col: int
            for col in range(30):
                letter: str = "~"
                if row < len(picture) and col < len(picture[row]):
                    letter = picture[row][col]
                cells.append(make_cell(letter, row, col))
            self.grid.append(cells)

    def cell_at(self, row: int, col: int) -> Land:
        """Return the object on one square."""
        return self.grid[row][col]

    def replace(self, row: int, col: int, cell: Land) -> None:
        """Put a new object on one square."""
        self.grid[row][col] = cell

    def wet(self, row: int, col: int, steps: int) -> None:
        """Ignore water in these checks."""


def make_cell(letter: str, row: int, col: int) -> Land:
    """Return the land a picture letter stands for."""
    if letter == "P":
        return Pine(row, col, 0.8)
    if letter == ",":
        return Grass(row, col, 0.5)
    if letter == "h":
        return Hardwood(row, col, 0.6)
    if letter == "H":
        return Home(row, col, False)
    if letter == "=":
        return Road(row, col)
    return Water(row, col)


def block(top: int, left: int, bottom: int, right: int) -> set[Square]:
    """Return every square from (top, left) to (bottom, right), inclusive."""
    return {
        Square(r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
    }


def calm(seed: int) -> Wildfire:
    """Return a season with no weather, no homes, and a big budget."""
    sim: Wildfire = Wildfire(Landscape(seed, []), [], 1_000_000, seed)
    sim.begin_season()
    return sim


# ----------------------------------------------------------- burn plans

A: Square = Square(0, 0)
B: Square = Square(0, 1)
C: Square = Square(1, 0)
D: Square = Square(1, 1)


def test_count_each_kind() -> None:
    """A dictionary from each kind to how many times it appears."""
    assert count(["pine", "pine", "home"]) == {"pine": 2, "home": 1}
    assert count(["grass"]) == {"grass": 1}
    assert count([]) == {}


def test_group_by_kind() -> None:
    """A dictionary from each kind to the set of squares that hold it."""
    land: dict[Square, str] = {A: "pine", B: "home", C: "pine"}
    assert group_by_kind(land) == {"pine": {A, C}, "home": {B}}
    assert group_by_kind({D: "water"}) == {"water": {D}}
    assert group_by_kind({}) == {}
    assert land == {A: "pine", B: "home", C: "pine"}  # unchanged


def test_in_prescription_checks_every_range() -> None:
    """Every condition must be present and inside its range, ends included."""
    rx: dict[str, list[float]] = {"wind": [1.0, 4.0], "moisture": [0.08, 0.2]}
    assert in_prescription({"wind": 2.5, "moisture": 0.12}, rx)
    assert in_prescription({"wind": 4.0, "moisture": 0.08}, rx)
    assert not in_prescription({"wind": 4.1, "moisture": 0.12}, rx)
    assert not in_prescription({"wind": 2.5, "moisture": 0.05}, rx)
    assert not in_prescription({"wind": 2.5}, rx)
    assert in_prescription({"wind": 9.0}, {})


def test_first_burn_day() -> None:
    """The index of the first day that fits, or -1."""
    rx: dict[str, list[float]] = {"wind": [1.0, 4.0]}
    days: list[dict[str, float]] = [{"wind": 6.0}, {"wind": 2.0}, {"wind": 3.0}]
    assert first_burn_day(days, rx) == 1
    assert first_burn_day(days[:1], rx) == -1
    assert first_burn_day([], rx) == -1


def grid_neighbors(squares: set[Square]) -> dict[Square, list[Square]]:
    """Return the side neighbors of each square, within the given squares."""
    result: dict[Square, list[Square]] = {}
    for square in squares:
        result[square] = [
            other
            for other in squares
            if abs(other.row - square.row) + abs(other.col - square.col) == 1
        ]
    return result


def test_spread_once_is_one_step() -> None:
    """Fuel neighbors of the fire that are not burning yet."""
    near: dict[Square, list[Square]] = grid_neighbors(block(0, 0, 3, 3))
    fuel: set[Square] = block(0, 0, 3, 3) - {Square(1, 2)}
    assert spread_once({Square(1, 1)}, fuel, near) == {
        Square(0, 1),
        Square(2, 1),
        Square(1, 0),
    }
    assert spread_once({Square(0, 0), Square(0, 1)}, fuel, near) == {
        Square(1, 0),
        Square(1, 1),
        Square(0, 2),
    }
    assert spread_once(set(), fuel, near) == set()


def test_fire_reach_walks_through_fuel_only() -> None:
    """A flood fill from the start squares, through fuel squares only."""
    everything: set[Square] = block(0, 0, 9, 9)
    near: dict[Square, list[Square]] = grid_neighbors(everything)
    fuel: set[Square] = {
        Square(5, 5),
        Square(5, 6),
        Square(6, 6),
        Square(8, 8),
    }
    reach: set[Square] = fire_reach({Square(5, 5)}, fuel, near)
    assert reach == {Square(5, 5), Square(5, 6), Square(6, 6)}
    assert fire_reach({Square(0, 0)}, fuel, near) == set()
    assert fire_reach({Square(5, 5), Square(8, 8)}, fuel, near) == fuel
    winding: set[Square] = block(0, 0, 9, 0) | block(9, 0, 9, 9)
    assert fire_reach({Square(0, 0)}, winding, near) == winding
    ring: dict[Square, list[Square]] = {A: [B], B: [C], C: [A], D: []}
    assert fire_reach({A}, {A, B, C, D}, ring) == {A, B, C}


def test_control_line_surrounds_the_burn() -> None:
    """Burnable neighbors outside the burn."""
    near: dict[Square, list[Square]] = grid_neighbors(block(0, 0, 3, 3))
    burn: set[Square] = {Square(1, 1)}
    burnable: set[Square] = {Square(0, 1), Square(1, 2), Square(3, 3)}
    assert control_line(burn, burnable, near) == {Square(0, 1), Square(1, 2)}


PICTURE: list[str] = [
    "PPPPhh",
    "PPHPhh",
    "PP,Phh",
    "PPPP==",
]


def test_burn_plan_puts_it_together() -> None:
    """Pull back from homes, keep the species, flood, then line."""
    field: Field = Field(PICTURE)
    unit: Polygon = Polygon(
        [Point(0.0, 0.0), Point(0.0, 6.0), Point(4.0, 6.0), Point(4.0, 0.0)],
        "pine",
    )
    north: Polyline = Polyline([Point(0.5, 0.0), Point(0.5, 6.0)], "road")
    plan: BurnPlan = BurnPlan(unit, {"pine", "grass"}, north, {})
    area: set[Square] = plan.area(field)
    assert Square(1, 1) not in area  # beside the home
    assert Square(0, 4) not in area  # hardwood
    assert Square(3, 0) in area
    line: set[Square] = plan.line(field)
    assert Square(1, 2) not in line  # the home itself never needs a line
    assert Square(0, 4) in line  # hardwood beside the burn
    assert plan.cost(field) == 25 * len(area) + 250 * len(line)


# ----------------------------------------------------------- embers


def test_spot_fire_base_cases() -> None:
    """Calm air, no hops left, or landing off the map start nothing."""
    sim: Wildfire = calm(110)
    assert spot_fire(sim, 20, 15, Wind(6.0, 0.0), Dice(1), 0) == 0
    assert spot_fire(sim, 20, 15, Wind(0.0, 0.0), Dice(1), 3) == 0
    assert spot_fire(sim, 1, 15, Wind(10.0, 0.0), Dice(1), 3) == 0


def test_spot_fire_lands_downwind() -> None:
    """Embers carried by a north wind start fires to the north."""
    sim: Wildfire = calm(110)
    started: int = 0
    for seed in range(20):
        started += spot_fire(sim, 28, 20, Wind(8.0, 0.0), Dice(seed), 2)
    assert started > 0
    for row in range(30):
        for col in range(30):
            if sim.cell_at(row, col).is_burning():
                assert row < 28


# ----------------------------------------------------------- the burn day


def test_burn_day_waits_for_the_prescription() -> None:
    """The burn happens on the first day in prescription, or not at all."""
    plan: BurnPlan = backing_burn()
    days: list[dict[str, float]] = [
        {"wind": 8.0, "moisture": 0.1},
        {"wind": 2.0, "moisture": 0.1},
    ]
    sim: Wildfire = scenario.build(1, "historical", None)
    sim.phase = "waiting"
    assert sim.plan_burn(plan, days)
    assert sim.burn_day == 1
    assert sim.phase == "burn day"
    assert sim.weather_report() == (
        "Weather: slope, wind 2.0 m/s toward north, fuel moisture 10%"
    )
    never: Wildfire = scenario.build(1, "historical", None)
    assert not never.plan_burn(plan, days[:1])


def test_burn_day_builds_the_line_and_stays_inside_it() -> None:
    """The line is cleared, fire stays in its area, then the season starts."""
    plan: BurnPlan = strip_burn(CAREFUL)
    sim: Wildfire = scenario.build(2, "historical", None)
    line: set[Square] = plan.line(sim)
    assert sim.plan_burn(plan, [{"wind": 2.0, "moisture": 0.12}])
    for square in line:
        assert kind_at(sim, square) in {"cleared", "home"}
    assert str(sim).startswith("Burn day (day 1 of the window), step 0:")
    while sim.phase == "burn day":
        sim.step()
    assert len(sim.good_fire) > 300
    assert sim.good_fire <= sim.burn_area
    assert sim.homes_safe() == sim.homes_total()
    burned: Land = sim.cell_at(25, 20)
    assert isinstance(burned, Pine) and burned.can_ignite()  # it greened up
    assert burned.fuel < 0.35
    assert sim.cell_at(21, 17).is_burning()  # the wildfire season began


def test_holding_crew_catches_spot_fires_in_calm_air() -> None:
    """On a burn day, new fires outside the area are usually put out."""
    sim: Wildfire = scenario.build(1, "historical", None)
    sim.phase = "burn day"
    sim.effects = [Wind(0.0, 0.0)]
    assert sim.holding_catch() == 1.0
    assert not sim.ignite(25, 20)
    sim.effects = [Wind(6.0, 0.0)]
    assert sim.holding_catch() == pytest.approx(0.6)


# ----------------------------------------------------------- tactics


def test_fuel_break_and_budget() -> None:
    """A fuel break clears soil; plans past the budget are refused."""
    sim: Wildfire = Wildfire(Landscape(110, []), [], 1_000, 110)
    line: Polyline = Polyline([Point(20.5, 18.0), Point(20.5, 24.0)], "road")
    assert not sim.schedule(FuelBreak(line))  # 7 squares x $250 = $1,750
    small: Polyline = Polyline([Point(20.5, 18.0), Point(20.5, 21.5)], "road")
    assert sim.schedule(FuelBreak(small))
    assert isinstance(sim.cell_at(20, 18), Cleared)


def test_defensible_space_hardens_homes() -> None:
    """Firewise treatment hardens every home in the area."""
    homes: Polygon = Polygon(
        [
            Point(2.0, 11.0),
            Point(2.0, 19.0),
            Point(5.0, 19.0),
            Point(5.0, 11.0),
        ],
        "homes",
    )
    sim: Wildfire = Wildfire(Landscape(110, [homes]), [], 1_000_000, 110)
    assert sim.schedule(DefensibleSpace(homes))
    for home in sim.landscape.homes():
        assert isinstance(home, Home) and home.hardened


def test_water_drop_happens_during_the_fire() -> None:
    """A drop waits for its step, puts fire out, and soaks the ground."""
    sim: Wildfire = calm(110)
    drop: WaterDrop = WaterDrop(Point(22.5, 7.5), 1.0, 2)
    assert sim.schedule(drop)
    sim.ignite(22, 7)
    sim.step()
    sim.step()
    assert sim.water_drops() == []
    sim.step()
    assert sim.water_drops() == [(22.5, 7.5, 1.0)]
    assert not sim.cell_at(22, 7).is_burning()


# ----------------------------------------------------------- the season


def test_squares_say_what_they_look_like() -> None:
    """Every kind of square fits Rendered, so the viewer can draw it."""
    sim: Wildfire = scenario.build(1, "hotter_drier", None)
    assert isinstance(sim, HasWeather)
    assert sim.weather_report() == (
        "Weather: slope, wind 7.0 m/s toward north, fuel moisture 6%"
    )
    looks: dict[str, Land] = {
        "home": Home(0, 0, False),
        "water": Water(0, 0),
        "road": Road(0, 0),
        "pine": Pine(0, 0, 1.0),
        "cleared": Cleared(0, 0),
    }
    for name in looks:
        cell: Land = looks[name]
        assert isinstance(cell, Rendered) and cell.appearance() == name


def test_same_seed_same_season() -> None:
    """Runs are repeatable, so every plan faces the same fires."""
    plan: SeasonPlan = SeasonPlan("D")
    first: Wildfire = scenario.run_to_end(scenario.build(2, "historical", plan))
    second: Wildfire = scenario.run_to_end(
        scenario.build(2, "historical", plan)
    )
    assert str(first) == str(second)
    assert first.good_fire == second.good_fire


def test_every_plan_runs() -> None:
    """Each plan in plans.py runs a season; only E skips the burn."""
    for name in PLANS:
        sim: Wildfire = scenario.run_to_end(
            scenario.build(1, "historical", SeasonPlan(name))
        )
        assert (sim.burn_day >= 0) == (name != "E")
        assert sim.spent <= scenario.BUDGET
    assert repr(SeasonPlan("D")) == "SeasonPlan('D')"
    with pytest.raises(ValueError):
        SeasonPlan("Z")


def test_chosen_plan_is_a_plan() -> None:
    """plan.py names one of the plans in plans.py."""
    assert chosen.CHOSEN_PLAN in PLANS
