"""Painting a beach scene in space with water, sand, palm trees, a boat, and a sun."""

from math import atan2, degrees, sqrt

from spacepaint import Ship, start_spacepaint

__author__: str = "730986400"


def main(aura: Ship) -> None:
    """Arrange the components of my beach scene."""
    draw_border(ship=aura)
    draw_beach(ship=aura, x=0.0, y=0.0)

    draw_sun(ship=aura, x=5.5, y=4.2, size=1.0)
    draw_boat(ship=aura, x=2.5, y=1)
    draw_palm(ship=aura, x=-4.5, y=-2.5, height=4.0)
    draw_palm(ship=aura, x=-2.5, y=-2.5, height=3.2)
    draw_palm(ship=aura, x=-0.5, y=-2.5, height=3.5)

    draw_starfish(ship=aura, x=3.0, y=-3.0, size=0.5)
    draw_starfish(ship=aura, x=4.5, y=-3.2, size=0.2)

    return None


def angle_between(ship: Ship, x: float, y: float) -> float:
    """Compute the shortest turn from the ship's heading toward an X/Y point."""
    turn: float = degrees(atan2(y - ship.y, x - ship.x)) - ship.heading_x_y

    if turn > 180:
        turn -= 360
    elif turn < -180:
        turn += 360

    return turn


def distance_between(ship: Ship, x: float, y: float) -> float:
    """Compute the distance from the ship to an X/Y point."""
    return sqrt((y - ship.y) ** 2 + (x - ship.x) ** 2)


def move_to(ship: Ship, x: float, y: float) -> None:
    """Move the ship from its current position to an X/Y point."""
    ship.turn(degrees=angle_between(ship, x, y))
    ship.forward(units=distance_between(ship, x, y))
    return None


def draw_beach(ship: Ship, x: float, y: float) -> None:
    """Paint blue water and red sand separated by a downward-sloping zigzag."""
    ship.beam(on=False)
    ship.beam_width(width=0.08)

    # Blue water
    ship.beam_color(value="blue")
    move_to(ship, x - 6.0, y - 0.5)
    ship.fill(on=True, opacity=0.6)
    ship.beam(on=True)

    move_to(ship, x - 5.5, y - 0.8)
    move_to(ship, x - 5.0, y - 0.5)
    move_to(ship, x - 4.5, y - 1.0)
    move_to(ship, x - 4.0, y - 0.7)
    move_to(ship, x - 3.5, y - 1.2)
    move_to(ship, x - 3.0, y - 0.9)
    move_to(ship, x - 2.5, y - 1.4)
    move_to(ship, x - 2.0, y - 1.1)
    move_to(ship, x - 1.5, y - 1.6)
    move_to(ship, x - 1.0, y - 1.3)
    move_to(ship, x - 0.5, y - 1.8)
    move_to(ship, x, y - 1.5)
    move_to(ship, x + 0.5, y - 2.0)
    move_to(ship, x + 1.0, y - 1.7)
    move_to(ship, x + 1.5, y - 2.2)
    move_to(ship, x + 2.0, y - 1.9)
    move_to(ship, x + 2.5, y - 2.4)
    move_to(ship, x + 3.0, y - 2.1)
    move_to(ship, x + 3.5, y - 2.6)
    move_to(ship, x + 4.0, y - 2.3)
    move_to(ship, x + 4.5, y - 2.8)
    move_to(ship, x + 5.0, y - 2.5)
    move_to(ship, x + 5.5, y - 3.0)
    move_to(ship, x + 6.0, y - 2.7)
    move_to(ship, x + 6.5, y - 3.2)
    move_to(ship, x + 7.0, y - 2.9)
    move_to(ship, x + 7.5, y - 3.4)
    move_to(ship, x + 8.0, y - 3.1)

    move_to(ship, x + 8.0, y + 7.0)
    move_to(ship, x - 6.0, y + 7.0)
    move_to(ship, x - 6.0, y - 0.5)

    ship.beam(on=False)
    ship.fill(on=False)

    # Red sand
    ship.beam_color(value="red")
    move_to(ship, x - 6.0, y - 0.5)
    ship.fill(on=True, opacity=0.6)
    ship.beam(on=True)

    move_to(ship, x - 5.5, y - 0.8)
    move_to(ship, x - 5.0, y - 0.5)
    move_to(ship, x - 4.5, y - 1.0)
    move_to(ship, x - 4.0, y - 0.7)
    move_to(ship, x - 3.5, y - 1.2)
    move_to(ship, x - 3.0, y - 0.9)
    move_to(ship, x - 2.5, y - 1.4)
    move_to(ship, x - 2.0, y - 1.1)
    move_to(ship, x - 1.5, y - 1.6)
    move_to(ship, x - 1.0, y - 1.3)
    move_to(ship, x - 0.5, y - 1.8)
    move_to(ship, x, y - 1.5)
    move_to(ship, x + 0.5, y - 2.0)
    move_to(ship, x + 1.0, y - 1.7)
    move_to(ship, x + 1.5, y - 2.2)
    move_to(ship, x + 2.0, y - 1.9)
    move_to(ship, x + 2.5, y - 2.4)
    move_to(ship, x + 3.0, y - 2.1)
    move_to(ship, x + 3.5, y - 2.6)
    move_to(ship, x + 4.0, y - 2.3)
    move_to(ship, x + 4.5, y - 2.8)
    move_to(ship, x + 5.0, y - 2.5)
    move_to(ship, x + 5.5, y - 3.0)
    move_to(ship, x + 6.0, y - 2.7)
    move_to(ship, x + 6.5, y - 3.2)
    move_to(ship, x + 7.0, y - 2.9)
    move_to(ship, x + 7.5, y - 3.4)
    move_to(ship, x + 8.0, y - 3.1)

    move_to(ship, x + 8.0, y - 4.0)
    move_to(ship, x - 6.0, y - 4.0)
    move_to(ship, x - 6.0, y - 0.5)

    ship.beam(on=False)
    ship.fill(on=False)

    # Red outline along the shoreline
    ship.beam_color(value="red")
    ship.beam_width(width=0.1)
    move_to(ship, x - 6.0, y - 0.5)
    ship.beam(on=True)

    move_to(ship, x - 5.5, y - 0.8)
    move_to(ship, x - 5.0, y - 0.5)
    move_to(ship, x - 4.5, y - 1.0)
    move_to(ship, x - 4.0, y - 0.7)
    move_to(ship, x - 3.5, y - 1.2)
    move_to(ship, x - 3.0, y - 0.9)
    move_to(ship, x - 2.5, y - 1.4)
    move_to(ship, x - 2.0, y - 1.1)
    move_to(ship, x - 1.5, y - 1.6)
    move_to(ship, x - 1.0, y - 1.3)
    move_to(ship, x - 0.5, y - 1.8)
    move_to(ship, x, y - 1.5)
    move_to(ship, x + 0.5, y - 2.0)
    move_to(ship, x + 1.0, y - 1.7)
    move_to(ship, x + 1.5, y - 2.2)
    move_to(ship, x + 2.0, y - 1.9)
    move_to(ship, x + 2.5, y - 2.4)
    move_to(ship, x + 3.0, y - 2.1)
    move_to(ship, x + 3.5, y - 2.6)
    move_to(ship, x + 4.0, y - 2.3)
    move_to(ship, x + 4.5, y - 2.8)
    move_to(ship, x + 5.0, y - 2.5)
    move_to(ship, x + 5.5, y - 3.0)
    move_to(ship, x + 6.0, y - 2.7)
    move_to(ship, x + 6.5, y - 3.2)
    move_to(ship, x + 7.0, y - 2.9)
    move_to(ship, x + 7.5, y - 3.4)
    move_to(ship, x + 8.0, y - 3.1)

    ship.beam(on=False)

    # Waves
    ship.beam_color(value="cyan")
    ship.beam_width(width=0.06)

    move_to(ship, x, y)
    ship.beam(on=True)
    move_to(ship, x + 0.5, y + 0.2)
    move_to(ship, x + 1.0, y)
    move_to(ship, x + 1.5, y + 0.2)
    move_to(ship, x + 2.0, y)
    move_to(ship, x + 2.5, y + 0.2)
    move_to(ship, x + 3.0, y)
    move_to(ship, x + 3.5, y + 0.2)
    move_to(ship, x + 4.0, y)
    ship.beam(on=False)

    move_to(ship, x + 0.7, y - 0.6)
    ship.beam(on=True)
    move_to(ship, x + 1.2, y - 0.4)
    move_to(ship, x + 1.7, y - 0.6)
    move_to(ship, x + 2.2, y - 0.4)
    move_to(ship, x + 2.7, y - 0.6)
    move_to(ship, x + 3.2, y - 0.4)
    move_to(ship, x + 3.7, y - 0.6)
    move_to(ship, x + 4.2, y - 0.4)
    ship.beam(on=False)

    return None


def draw_boat(ship: Ship, x: float, y: float) -> None:
    """Draw a purple sailboat above the waves."""
    ship.beam(on=False)

    # Purple boat
    ship.beam_color(value="purple")
    ship.beam_width(width=0.08)

    move_to(ship, x - 1.2, y)
    ship.fill(on=True, opacity=0.7)
    ship.beam(on=True)

    move_to(ship, x + 1.2, y)
    move_to(ship, x + 0.7, y - 0.8)
    move_to(ship, x - 0.8, y - 0.8)
    move_to(ship, x - 1.2, y)

    ship.beam(on=False)
    ship.fill(on=False)

    # Mast
    ship.beam_color(value="orange")
    ship.beam_width(width=0.06)
    move_to(ship, x, y)
    ship.beam(on=True)
    move_to(ship, x, y + 2.3)
    ship.beam(on=False)

    # Sail
    ship.beam_color(value="white")
    move_to(ship, x, y + 2.3)
    ship.fill(on=True, opacity=0.7)
    ship.beam(on=True)
    move_to(ship, x + 1.0, y + 0.1)
    move_to(ship, x, y + 0.1)
    move_to(ship, x, y + 2.3)

    ship.beam(on=False)
    ship.fill(on=False)

    return None


def draw_sun(ship: Ship, x: float, y: float, size: float) -> None:
    """Draw a yellow sun with rays."""
    ship.beam(on=False)
    ship.beam_color(value="orange")
    ship.beam_width(width=0.07)

    # Filled sun
    move_to(ship, x + size, y)
    ship.fill(on=True, opacity=0.7)
    ship.beam(on=True)
    ship.arc(radius=size, degrees=360.0)
    ship.beam(on=False)
    ship.fill(on=False)

    # Rays
    move_to(ship, x + 1.5, y + 0.2)
    ship.beam(on=True)
    move_to(ship, x + 2.3, y + 0.2)
    ship.beam(on=False)

    move_to(ship, x + 0.2, y + 1.5)
    ship.beam(on=True)
    move_to(ship, x + 0.2, y + 2.2)
    ship.beam(on=False)

    move_to(ship, x + 1.1, y + 1.1)
    ship.beam(on=True)
    move_to(ship, x + 1.7, y + 1.7)
    ship.beam(on=False)

    move_to(ship, x + 1.1, y - 0.7)
    ship.beam(on=True)
    move_to(ship, x + 1.7, y - 1.3)
    ship.beam(on=False)

    move_to(ship, x - 1.1, y + 0.2)
    ship.beam(on=True)
    move_to(ship, x - 1.9, y + 0.2)
    ship.beam(on=False)

    move_to(ship, x - 0.7, y + 1.1)
    ship.beam(on=True)
    move_to(ship, x - 1.3, y + 1.7)
    ship.beam(on=False)

    move_to(ship, x - 0.7, y - 0.7)
    ship.beam(on=True)
    move_to(ship, x - 1.3, y - 1.3)
    ship.beam(on=False)

    move_to(ship, x + 0.2, y - 1.1)
    ship.beam(on=True)
    move_to(ship, x + 0.2, y - 1.8)
    ship.beam(on=False)

    return None


def draw_palm(ship: Ship, x: float, y: float, height: float) -> None:
    """Draw a palm tree with a straight trunk and green leaves."""
    ship.beam(on=False)

    # Trunk
    ship.beam_color(value="orange")
    ship.beam_width(width=0.07)
    move_to(ship, x, y)
    ship.beam(on=True)
    move_to(ship, x, y + height)
    ship.beam(on=False)

    # Leaves
    draw_palm_leaves(ship=ship, x=x, y=y + height)

    return None


def draw_palm_leaves(ship: Ship, x: float, y: float) -> None:
    """Draw four narrow, long diamond-shaped palm leaves."""
    ship.beam_color(value="green")
    ship.beam_width(width=0.05)

    # Left leaf
    move_to(ship, x, y)
    ship.beam(on=True)
    move_to(ship, x - 1.3, y + 0.5)
    move_to(ship, x - 0.7, y)
    move_to(ship, x - 1.3, y - 0.5)
    move_to(ship, x, y)
    ship.beam(on=False)

    # Right leaf
    move_to(ship, x, y)
    ship.beam(on=True)
    move_to(ship, x + 1.3, y + 0.5)
    move_to(ship, x + 0.7, y)
    move_to(ship, x + 1.3, y - 0.5)
    move_to(ship, x, y)
    ship.beam(on=False)

    # Top leaf
    move_to(ship, x, y)
    ship.beam(on=True)
    move_to(ship, x - 0.35, y + 1.3)
    move_to(ship, x, y + 0.7)
    move_to(ship, x + 0.35, y + 1.3)
    move_to(ship, x, y)
    ship.beam(on=False)

    # Bottom leaf
    move_to(ship, x, y)
    ship.beam(on=True)
    move_to(ship, x - 0.35, y - 1.3)
    move_to(ship, x, y - 0.7)
    move_to(ship, x + 0.35, y - 1.3)
    move_to(ship, x, y)
    ship.beam(on=False)

    return None


def draw_starfish(ship: Ship, x: float, y: float, size: float) -> None:
    """Draw a simple orange starfish."""
    ship.beam(on=False)
    ship.beam_color(value="orange")
    ship.beam_width(width=0.06)

    move_to(ship, x, y + size)
    ship.fill(on=True, opacity=0.7)
    ship.beam(on=True)
    move_to(ship, x + size * 0.3, y + size * 0.3)
    move_to(ship, x + size, y + size * 0.3)
    move_to(ship, x + size * 0.5, y - size * 0.1)
    move_to(ship, x + size * 0.7, y - size)
    move_to(ship, x, y - size * 0.4)
    move_to(ship, x - size * 0.7, y - size)
    move_to(ship, x - size * 0.5, y - size * 0.1)
    move_to(ship, x - size, y + size * 0.3)
    move_to(ship, x - size * 0.3, y + size * 0.3)
    move_to(ship, x, y + size)
    ship.beam(on=False)
    ship.fill(on=False)

    return None


def draw_border(ship: Ship) -> None:
    """Draw a black box around the entire beach scene."""
    ship.beam(on=False)
    ship.beam_color(value="#000000")
    ship.beam_width(width=0.1)

    move_to(ship, -6.0, -4.0)

    ship.beam(on=True)
    move_to(ship, 8.0, -4.0)
    move_to(ship, 8.0, 7.0)
    move_to(ship, -6.0, 7.0)
    move_to(ship, -6.0, -4.0)
    ship.beam(on=False)

    return None


if __name__ == "__main__":
    start_spacepaint()
