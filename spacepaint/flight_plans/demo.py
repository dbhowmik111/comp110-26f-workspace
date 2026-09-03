"""Making art... in space!"""

from spacepaint import Ship, start_spacepaint


def main(aura: Ship) -> None:
    """Your Space Paint program's entrypoint."""
    aura.beam(on=True)
    aura.turn(degrees=90.0)
    aura.forward(units=5.0)
    aura.beam(on=False)
    aura.turn(degrees=-90.0)
    aura.forward(units=2.0)
    aura.turn(degrees=-90.0)
    aura.beam(on=True)
    aura.forward(units=5.0)
    aura.beam(on=False)
    aura.turn(degrees=90.0)
    aura.forward(units=4.0)
    aura.beam(on=True)
    aura.fill(on=True)
    aura.arc(radius=2.5, degrees=360.0)
    return None


if __name__ == "__main__":
    start_spacepaint()
