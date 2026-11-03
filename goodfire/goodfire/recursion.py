"""PROVIDED: embers, a worked example of recursion.

An ember that starts a spot fire can throw another ember from there, and
that one can throw another. spot_fire follows that chain by calling
itself. It uses only the Simulation protocol, so it works on Part 1's
Landscape as well as Part 2's Wildfire.
"""

from goodfire.dice import Dice
from goodfire.fieldkit import ember_landing
from goodfire.fieldkit import on_map
from goodfire.grid import Square
from goodfire.part2_protocols import Simulation
from goodfire.protocols import Land
from goodfire.weather import Wind


def spot_fire(
    sim: Simulation, row: int, col: int, wind: Wind, dice: Dice, depth: int
) -> int:
    """Carry a burning ember downwind; where it starts a fire, it may throw
    another ember.

    Base cases: no hops left, calm air, the ember lands off the map, or it
    lands on something that does not catch.

    Args:
        sim: The simulation the ember lands in.
        row: The row the ember leaves from.
        col: The column the ember leaves from.
        wind: The wind carrying the ember.
        dice: The simulation's dice.
        depth: How many more hops embers may make.

    Returns:
        How many new fires this ember and its descendants started.
    """
    if depth <= 0 or wind.speed <= 0.0:
        return 0
    landing: Square = ember_landing(row, col, wind, dice)
    if not on_map(landing.row, landing.col):
        return 0
    target: Land = sim.cell_at(landing.row, landing.col)
    if not target.can_ignite():
        return 0
    if dice.roll() >= target.ignition_chance():
        return 0
    sim.ignite(landing.row, landing.col)
    return 1 + spot_fire(sim, landing.row, landing.col, wind, dice, depth - 1)
