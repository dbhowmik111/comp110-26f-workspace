"""STUDENT: shapes you sketch on the map to try out "what if?" ideas.

A Polygon marks an area (homes, a meadow, a pond) and a Polyline marks a
line (a river, a road). Both fit the Feature protocol: a ``cover`` and a
``squares()`` method, which lists the map squares the shape covers.

Shapes are drawn through Points (see grid.py), measured in squares from the
north-west corner. Square(r, c) spans rows r to r + 1 and columns c to
c + 1, so its center is Point(r + 0.5, c + 0.5).

Methods that already have code are provided: read them, they are worked
examples. Replace each raise NotImplementedError("TODO: ...") with your
own code.
"""

__author__: str = ""  # TODO: your 9-digit PID, like "730123456"

from goodfire import science
from goodfire import terrain
from goodfire.grid import Point
from goodfire.grid import Square


def already_listed(squares: list[Square], row: int, col: int) -> bool:
    """Return True if a square with this row and column is in the list."""
    index: int = 0
    while index < len(squares):
        if squares[index].row == row and squares[index].col == col:
            return True
        index += 1
    return False


def on_map(row: int, col: int) -> bool:
    """Return True if a row and column name a square on the map."""
    return (
        row >= 0
        and row < terrain.GRID_SIZE
        and col >= 0
        and col < terrain.GRID_SIZE
    )


class Polygon:
    """A closed area, listed corner by corner."""

    corners: list[Point]
    cover: str

    def __init__(self, corners: list[Point], cover: str):
        """Create a polygon.

        Args:
            corners: The corners, in order around the shape.
            cover: What the area becomes, like "homes" or "pond".
        """
        self.corners = corners
        self.cover = cover

    def __str__(self) -> str:
        """Describe the shape for the sketch list."""
        return (
            f"{self.cover} area with {len(self.corners)} corners "
            f"covering {len(self.squares())} squares"
        )

    def __repr__(self) -> str:
        """Show the code that rebuilds this shape (used by saved sketches)."""
        return f"Polygon({self.corners}, cover='{self.cover}')"

    def contains(self, row: float, col: float) -> bool:
        """Return True if a point is inside the polygon (ray casting).

        Imagine a ray from the point toward the east. Each time it crosses
        an edge, it passes between inside and outside, so an odd number of
        crossings means the point is inside.
        """
        inside: bool = False
        count: int = len(self.corners)
        index: int = 0
        while index < count:
            a: Point = self.corners[index]
            b: Point = self.corners[(index + 1) % count]
            straddles: bool = (a.row > row) != (b.row > row)
            if straddles:
                crossing_col: float = a.col + (row - a.row) * (
                    b.col - a.col
                ) / (b.row - a.row)
                if col < crossing_col:
                    inside = not inside
            index += 1
        return inside

    def squares(self) -> list[Square]:
        """Return every square whose center is inside, in row order."""
        result: list[Square] = []
        row: int = 0
        while row < terrain.GRID_SIZE:
            col: int = 0
            while col < terrain.GRID_SIZE:
                if self.contains(row + 0.5, col + 0.5):
                    result.append(Square(row, col))
                col += 1
            row += 1
        return result


class Polyline:
    """A line drawn point to point, like a river or a road."""

    points: list[Point]
    cover: str

    def __init__(self, points: list[Point], cover: str):
        """Create a line.

        Args:
            points: The points, in drawing order.
            cover: What the line becomes, like "river" or "road".
        """
        raise NotImplementedError("TODO: Polyline.__init__")

    def __str__(self) -> str:
        """Describe the line for the sketch list, in meters."""
        return (
            f"{self.cover} line {science.meters(self.length())} m long "
            f"covering {len(self.squares())} squares"
        )

    def __repr__(self) -> str:
        """Show the code that rebuilds this line (used by saved sketches)."""
        raise NotImplementedError("TODO: Polyline.__repr__")

    def length(self) -> float:
        """Return the total length, measured in squares."""
        raise NotImplementedError("TODO: Polyline.length")

    def squares(self) -> list[Square]:
        """Return the squares the line passes through, in drawing order.

        Walk each segment in small steps (a quarter of a square) and record
        each new on-map square the walk enters.
        """
        result: list[Square] = []
        index: int = 0
        while index < len(self.points) - 1:
            a: Point = self.points[index]
            b: Point = self.points[index + 1]
            distance: float = (
                (b.row - a.row) ** 2 + (b.col - a.col) ** 2
            ) ** 0.5
            # Take at least one step, and enough that no step is longer
            # than a quarter of a square.
            steps: int = int(distance * 4 // 1)
            if steps < distance * 4:
                steps += 1
            if steps < 1:
                steps = 1
            step: int = 0
            while step <= steps:
                fraction: float = step / steps
                # x // 1 rounds down, even below zero (off the map).
                row: int = int((a.row + (b.row - a.row) * fraction) // 1)
                col: int = int((a.col + (b.col - a.col) * fraction) // 1)
                if on_map(row, col) and not already_listed(result, row, col):
                    result.append(Square(row, col))
                step += 1
            index += 1
        return result
