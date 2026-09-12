"""Making art... in space!"""

from spacepaint import Ship, start_spacepaint

__author__: str = "730986400"


def main(aura: Ship) -> None:
    """Your Space Paint program's entrypoint."""
    # Step 1: reach the first corner without painting
    aura.beam(on=False)
    aura.turn(degrees=45.0)
    aura.forward(units=4.242640687119285)  # (3.0, 3.0)

    # Step 2: face the second corner and begin painting
    aura.turn(degrees=135.0)
    aura.beam(on=True)
    aura.forward(units=6.0)  # (-3.0, 3.0)

    # Step 3: visit the remaining corners in order
    aura.turn(degrees=90.0)
    aura.forward(units=6.0)  # (-3.0, -3.0)

    aura.turn(degrees=90.0)
    aura.forward(units=6.0)  # (3.0, -3.0)

    # Step 4: return to the first corner, closing the square.
    aura.turn(degrees=90.0)
    aura.forward(units=6.0)  # back at (3.0, 3.0)
    aura.beam(on=False)

    return None


if __name__ == "__main__":
    start_spacepaint()
