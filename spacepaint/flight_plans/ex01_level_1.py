"""Making art... in space!"""

from spacepaint import Ship, start_spacepaint

__author__: str = "730986400"


def main(aura: Ship) -> None:
    """Paint a 2-by-2 grid of squares, one in each quadrant."""
    aura.beam(on=True)
    square(ship=aura)
    square(ship=aura)
    square(ship=aura)
    square(ship=aura)
    return None


def square(ship: Ship) -> None:
    """Paint a 6.0-side square to the ship's forward left.

    Starts and ends at the ship's current position. Finishes facing
    90 degrees clockwise from the heading it started with.
    """
    ship.turn(degrees=90.0)
    ship.forward(units=6.0)
    ship.turn(degrees=-90.0)
    ship.forward(units=6.0)
    ship.turn(degrees=-90.0)
    ship.forward(units=6.0)
    ship.turn(degrees=-90.0)
    ship.forward(units=6.0)
    ship.turn(degrees=90.0)
    return None


if __name__ == "__main__":
    start_spacepaint()
