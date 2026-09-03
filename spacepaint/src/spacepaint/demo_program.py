"""Deterministic built-in program used for documentation and render checks."""

from math import atan2, degrees, sqrt

from spacepaint import Ship


def _xy_offset(ship: Ship, x: float, y: float) -> tuple[float, float]:
    """Return the x/y offset from the ship to a target."""
    return x - ship.x, y - ship.y


def _xy_distance(x: float, y: float) -> float:
    """Return the length of an x/y vector."""
    return sqrt(x**2 + y**2)


def turn_to(ship: Ship, x: float, y: float) -> None:
    """Turn toward an absolute position in the x/y plane."""
    dx, dy = _xy_offset(ship=ship, x=x, y=y)
    if dx == 0 and dy == 0:
        return

    target_heading = degrees(atan2(dy, dx))
    turn_distance = target_heading - ship.heading_x_y

    if turn_distance > 180:
        turn_distance -= 360
    elif turn_distance < -180:
        turn_distance += 360

    ship.turn(degrees=turn_distance)


def move_to(ship: Ship, x: float, y: float) -> None:
    """Move to an absolute position in the x/y plane."""
    dx, dy = _xy_offset(ship=ship, x=x, y=y)
    distance = _xy_distance(x=dx, y=dy)
    if distance == 0:
        return
    turn_to(ship=ship, x=x, y=y)
    ship.forward(units=distance)


def main(ship: Ship) -> None:
    """Paint a multicolor star, then launch a fading beam into depth."""
    ship.speed(multiplier=3)
    ship.beam(on=False)
    move_to(ship=ship, x=-3.8, y=-1.5)
    ship.beam_width(width=0.16)
    ship.beam(on=True)

    colors = ("cyan", "blue", "purple", "pink", "orange")
    for beam_color in colors:
        ship.beam_color(value=beam_color)
        ship.forward(units=6)
        ship.turn(degrees=144)

    ship.beam(on=False)
    move_to(ship=ship, x=-3.8, y=-2.7)
    ship.beam_color(value="#ffb347")
    ship.beam_width(width=0.11)
    ship.beam(on=True, fade_after=7)
    ship.yaw_right(degrees=32)
    ship.forward(units=7)
    ship.pitch_up(degrees=28)
    ship.beam_color(value="#67f5ff")
    ship.forward(units=3)
    ship.beam(on=False)
