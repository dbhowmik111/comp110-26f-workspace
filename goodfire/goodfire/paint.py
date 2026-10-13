"""PROVIDED: how each kind of square looks on the 2D sketch table.

Your classes' draw() methods call these functions, so you never have to
work out pixel positions. Each function paints one 30 m square seen from
above: a ground color, then details such as tree crowns, a roof, ripples, or
flames. Small differences between squares (where a tuft of grass sits, how
big a crown is) come from the square's row and column, so the map looks
natural yet is drawn the same way every time.
"""

from comp110_gui import Canvas

from goodfire import terrain

SIZE: int = terrain.CELL_SIZE

PINE_CROWN: str = "#24502A"
PINE_LIGHT: str = "#3E7440"
SCORCHED_CROWN: str = "#96582C"
SURVIVING_TOP: str = "#5C6830"
HARDWOOD_CROWN: str = "#4C8A3E"
HARDWOOD_LIGHT: str = "#6AA652"
GRASS_TUFT: str = "#8C8440"
WALL: str = "#EDE3CF"
ROOF: str = "#A4553C"
METAL_ROOF: str = "#5A6B7A"
GRAVEL: str = "#B8B2A6"
CHAR: str = "#1E1A18"
ASH: str = "#57504A"
EMBER: str = "#C8401A"
FLAME_OUTER: str = "#E8481C"
FLAME_MIDDLE: str = "#FF8A2A"
FLAME_INNER: str = "#FFD24A"
FLAME_CORE: str = "#FFF4C2"
GLOW: str = "#FF8A2A55"
RIPPLE: str = "#D8ECFA88"


def jitter(row: int, col: int, salt: int) -> float:
    """Return a repeatable number from -1 to 1 for one square."""
    value: int = (row * 7919 + col * 104729 + salt * 15485863) % 1000
    return value / 500 - 1


def center(row: int, col: int) -> tuple[float, float]:
    """Return the canvas position of the middle of a square."""
    return (col * SIZE + SIZE / 2, row * SIZE + SIZE / 2)


def ground(canvas: Canvas, row: int, col: int, color: str) -> None:
    """Fill one square with a flat color."""
    canvas.draw_rectangle(
        col * SIZE, row * SIZE, SIZE, SIZE, fill=color, outline=None
    )


def flames(canvas: Canvas, row: int, col: int, time_left: int) -> None:
    """Draw a fire: a soft glow, then layered flames; new fires burn hottest."""
    x, y = center(row, col)
    heat: float = min(time_left, 4) / 4
    canvas.draw_circle(x, y, SIZE * 0.62, fill=GLOW, outline=None)
    for dx, dy, scale in (
        (-0.18, 0.1, 0.62),
        (0.2, 0.06, 0.55),
        (0, -0.08, 0.8),
    ):
        fx: float = x + dx * SIZE
        fy: float = y + dy * SIZE
        radius: float = SIZE * 0.3 * scale * (0.7 + 0.5 * heat)
        canvas.draw_circle(fx, fy, radius, fill=FLAME_OUTER, outline=None)
        canvas.draw_circle(
            fx,
            fy - radius * 0.25,
            radius * 0.7,
            fill=FLAME_MIDDLE,
            outline=None,
        )
        canvas.draw_circle(
            fx, fy - radius * 0.4, radius * 0.4, fill=FLAME_INNER, outline=None
        )
    if heat > 0.5:
        canvas.draw_circle(
            x, y - SIZE * 0.12, SIZE * 0.08, fill=FLAME_CORE, outline=None
        )


def ash(canvas: Canvas, row: int, col: int) -> None:
    """Speckle a burned square with ash and a few glowing embers."""
    for salt in range(3):
        x: float = col * SIZE + SIZE * (0.5 + 0.38 * jitter(row, col, salt))
        y: float = row * SIZE + SIZE * (0.5 + 0.38 * jitter(row, col, salt + 7))
        canvas.draw_circle(x, y, SIZE * 0.07, fill=ASH, outline=None)
    if jitter(row, col, 3) > 0.6:
        x, y = center(row, col)
        canvas.draw_circle(x, y, SIZE * 0.05, fill=EMBER, outline=None)


def crown(
    canvas: Canvas, x: float, y: float, radius: float, dark: str, light: str
) -> None:
    """Draw a tree crown from above: a shadow, the crown, a sunlit side."""
    canvas.draw_circle(
        x + radius * 0.25,
        y + radius * 0.3,
        radius,
        fill="#00000033",
        outline=None,
    )
    canvas.draw_circle(x, y, radius, fill=dark, outline=None)
    canvas.draw_circle(
        x - radius * 0.3,
        y - radius * 0.3,
        radius * 0.55,
        fill=light,
        outline=None,
    )


def plant(
    canvas: Canvas,
    kind: str,
    row: int,
    col: int,
    color: str,
    state: str,
    time_left: int,
    fuel: float,
) -> None:
    """Draw grass, a longleaf pine, or a hardwood in any state.

    Args:
        canvas: The canvas that shows the whole map.
        kind: The plant's name(): "Grass", "Longleaf pine", or "Hardwood".
        row: The square's row.
        col: The square's column.
        color: The square's color() (already shows burning and burned).
        state: "unburned", "burning", or "burned".
        time_left: Steps of fire left while burning.
        fuel: How much fuel is left, from 0.0 to 1.0.
    """
    ground(canvas, row, col, color)
    x, y = center(row, col)
    x += jitter(row, col, 1) * SIZE * 0.08
    y += jitter(row, col, 2) * SIZE * 0.08
    size: float = 0.75 + 0.35 * fuel
    if state == "burning":
        flames(canvas, row, col, time_left)
        return
    if state == "burned":
        ash(canvas, row, col)
        if kind == "Longleaf pine":
            # Longleaf usually survive: a scorched crown, green at the top.
            radius: float = SIZE * 0.3 * size
            crown(canvas, x, y, radius, SCORCHED_CROWN, SURVIVING_TOP)
        return
    if kind == "Grass":
        for salt in range(4):
            tx: float = col * SIZE + SIZE * (
                0.5 + 0.36 * jitter(row, col, salt)
            )
            ty: float = row * SIZE + SIZE * (
                0.55 + 0.3 * jitter(row, col, salt + 4)
            )
            canvas.draw_line(
                tx - 2, ty + 2, tx, ty - 3, color=GRASS_TUFT, width=1.2
            )
            canvas.draw_line(
                tx + 2, ty + 2, tx, ty - 3, color=GRASS_TUFT, width=1.2
            )
    elif kind == "Longleaf pine":
        crown(canvas, x, y, SIZE * 0.33 * size, PINE_CROWN, PINE_LIGHT)
    else:
        crown(
            canvas,
            x - SIZE * 0.1,
            y + SIZE * 0.05,
            SIZE * 0.3 * size,
            HARDWOOD_CROWN,
            HARDWOOD_LIGHT,
        )
        crown(
            canvas,
            x + SIZE * 0.12,
            y - SIZE * 0.08,
            SIZE * 0.26 * size,
            HARDWOOD_CROWN,
            HARDWOOD_LIGHT,
        )


def home(
    canvas: Canvas,
    row: int,
    col: int,
    color: str,
    state: str,
    hardened: bool,
    time_left: int,
) -> None:
    """Draw a home from above: a yard, a gabled roof, and its condition.

    Firewise (hardened) homes have a metal roof and a gravel strip.
    """
    ground(canvas, row, col, color)
    left: float = col * SIZE
    top: float = row * SIZE
    if hardened:
        canvas.draw_rectangle(
            left + 1.5, top + 2.5, SIZE - 3, SIZE - 4, fill=GRAVEL, outline=None
        )
    if state == "burning":
        canvas.draw_rectangle(
            left + 3.5, top + 4.5, SIZE - 7, SIZE - 8, fill=CHAR, outline=None
        )
        flames(canvas, row, col, time_left)
        return
    if state == "damaged":
        canvas.draw_rectangle(
            left + 3.5,
            top + 4.5,
            SIZE - 7,
            SIZE - 8,
            fill=CHAR,
            outline=ASH,
            outline_width=1.5,
        )
        ash(canvas, row, col)
        return
    roof: str = METAL_ROOF if hardened else ROOF
    canvas.draw_rectangle(
        left + 4.5,
        top + 6.5,
        SIZE - 9,
        SIZE - 9,
        fill="#00000030",
        outline=None,
    )
    canvas.draw_rectangle(
        left + 3.5, top + 4.5, SIZE - 7, SIZE - 8, fill=roof, outline=None
    )
    # The ridge line and the sunlit half of the gabled roof.
    canvas.draw_rectangle(
        left + 3.5,
        top + 4.5,
        SIZE - 7,
        (SIZE - 8) / 2,
        fill="#FFFFFF2A",
        outline=None,
    )
    canvas.draw_line(
        left + 3.5,
        top + SIZE / 2 + 0.5,
        left + SIZE - 3.5,
        top + SIZE / 2 + 0.5,
        color="#00000055",
        width=1.0,
    )
    canvas.draw_rectangle(
        left + SIZE - 7, top + 3, 2.5, 3, fill="#7A5A4C", outline=None
    )


def water(canvas: Canvas, row: int, col: int, color: str) -> None:
    """Draw open water; some squares catch a glint of light."""
    ground(canvas, row, col, color)
    if jitter(row, col, 5) > 0.1:
        x, y = center(row, col)
        x += jitter(row, col, 6) * SIZE * 0.2
        y += jitter(row, col, 7) * SIZE * 0.2
        canvas.draw_line(
            x - SIZE * 0.12, y, x + SIZE * 0.12, y, color=RIPPLE, width=1.0
        )


def road(canvas: Canvas, row: int, col: int, color: str) -> None:
    """Draw pavement."""
    ground(canvas, row, col, color)
