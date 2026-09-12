"""Making art in space!"""

from math import atan2, degrees, sqrt

from spacepaint import Ship, start_spacepaint

__author__: str = "730986400"


def main(aura: Ship) -> None:
    """Paint five concentric squares centered at the origin."""
    square_at(ship=aura, center_x=0.0, center_y=0.0, length=5.0)
    square_at(ship=aura, center_x=0.0, center_y=0.0, length=4.0)
    square_at(ship=aura, center_x=0.0, center_y=0.0, length=3.0)
    square_at(ship=aura, center_x=0.0, center_y=0.0, length=2.0)
    square_at(ship=aura, center_x=0.0, center_y=0.0, length=1.0)
    return None


def angle_between(ship: Ship, x: float, y: float) -> float:
    """Compute the turn from the ship's heading toward an X/Y point."""
    return degrees(atan2(y - ship.y, x - ship.x)) - ship.heading_x_y


def distance_between(ship: Ship, x: float, y: float) -> float:
    """Compute the distance from the ship to an X/Y point."""
    return sqrt((y - ship.y) ** 2 + (x - ship.x) ** 2)


def move_to(ship: Ship, x: float, y: float) -> None:
    """Move the ship from its current position to an X/Y point."""
    ship.turn(degrees=angle_between(ship, x, y))
    ship.forward(units=distance_between(ship, x, y))
    return None


def square_at(ship: Ship, center_x: float, center_y: float, length: float) -> None:
    """Paint a square centered at an X/Y point."""
    half: float = length / 2.0

    ship.beam(on=False)
    move_to(ship, center_x + half, center_y + half)  # upper right

    ship.beam(on=True)
    move_to(ship, center_x - half, center_y + half)  # upper left
    move_to(ship, center_x - half, center_y - half)  # lower left
    move_to(ship, center_x + half, center_y - half)  # lower right
    move_to(ship, center_x + half, center_y + half)  # back to upper right
    ship.beam(on=False)

    return None


if __name__ == "__main__":
    start_spacepaint()
