"""Making art... in space!"""

from spacepaint import Ship, start_spacepaint

__author__: str = "730986400"


def main(aura: Ship) -> None:
    """Paint four squares of decreasing size around the shared origin."""
    aura.beam(on=True)
    square(ship=aura, length=4.0)
    square(ship=aura, length=3.0)
    square(ship=aura, length=2.0)
    square(ship=aura, length=1.0)
    return None


def square(ship: Ship, length: float) -> None:
    """Paint a square of the given side length to the ship's forward left.

    Starts and ends at the ship's current position. Finishes facing
    90 degrees clockwise from the heading it started with.
    """
    ship.turn(degrees=90.0)
    ship.forward(units=length)
    ship.turn(degrees=-90.0)
    ship.forward(units=length)
    ship.turn(degrees=-90.0)
    ship.forward(units=length)
    ship.turn(degrees=-90.0)
    ship.forward(units=length)
    ship.turn(degrees=90.0)
    return None


if __name__ == "__main__":
    start_spacepaint()
