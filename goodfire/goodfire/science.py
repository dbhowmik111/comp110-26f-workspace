"""PROVIDED: the published numbers behind the simulation.

Fire spread follows the cellular-automaton model of Alexandridis et al.
(2008), which reproduced the 1990 Spetses Island wildfire:

    p_burn = P_H * (1 + p_veg) * (1 + p_den) * p_wind * p_slope

Part 1 uses P_H, each fuel's p_veg, and p_den from each square's fuel
load. Part 2 adds wind, slope, and fuel moisture. See docs/DESIGN.md for
sources and simplifications.
"""

P_H: float = 0.58
"""Base chance that a burning square ignites a neighbor in one step."""

C1: float = 0.045
"""Wind coefficient c1 (per m/s), Alexandridis et al. (2008)."""

C2: float = 0.131
"""Wind coefficient c2 (per m/s), Alexandridis et al. (2008)."""

SLOPE_A: float = 0.078
"""Slope coefficient a (per degree), Alexandridis et al. (2008)."""

CELL_METERS: float = 30.0
"""Each square is 30 m across, the resolution of the US LANDFIRE fuel maps."""

DENSITY_LOW: float = -0.4
"""p_den for the sparsest fuel (fuel load 0.0), as in Alexandridis et al."""

DENSITY_HIGH: float = 0.3
"""p_den for the densest fuel (fuel load 1.0), as in Alexandridis et al."""

MOISTURE_OF_EXTINCTION: float = 0.30
"""Dead-fuel moisture (30%) above which these fuels stop carrying fire."""


def density_factor(fuel: float) -> float:
    """Return (1 + p_den) for a fuel load from 0.0 (sparse) to 1.0 (dense)."""
    return 1.0 + DENSITY_LOW + (DENSITY_HIGH - DENSITY_LOW) * fuel


def percent(fraction: float) -> int:
    """Return a fraction from 0.0 to 1.0 as a whole percent (0.256 -> 26)."""
    return round(fraction * 100)


def meters(squares: float) -> int:
    """Return a distance measured in squares as whole meters."""
    return round(squares * CELL_METERS)
