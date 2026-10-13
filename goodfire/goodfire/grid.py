"""PROVIDED: points and squares on the 30 x 30 map.

A Point is a spot you sketch at, measured in squares: Point(2.5, 11.0) is
two and a half squares down from the north edge and eleven squares in from
the west edge. A Square is one whole 30 m square of the grid: Square(2, 11)
spans rows 2 to 3 and columns 11 to 12, and its center is Point(2.5, 11.5).
"""


class Point:
    """A spot on the map, in squares from the north-west corner."""

    row: float
    col: float

    def __init__(self, row: float, col: float):
        """Create a point.

        Args:
            row: How far down from the north edge, in squares.
            col: How far in from the west edge, in squares.
        """
        self.row = row
        self.col = col

    def __str__(self) -> str:
        """Describe the point for people."""
        return f"({self.row}, {self.col})"

    def __repr__(self) -> str:
        """Show the code that rebuilds this point."""
        return f"Point({self.row}, {self.col})"

    def __eq__(self, other: object) -> bool:
        """Two points are equal when their rows and columns match."""
        if not isinstance(other, Point):
            return NotImplemented
        return self.row == other.row and self.col == other.col


class Square:
    """One 30 m square of the map, by its whole-number row and column."""

    row: int
    col: int

    def __init__(self, row: int, col: int):
        """Create a square.

        Args:
            row: The square's row, from 0 (north) to 29 (south).
            col: The square's column, from 0 (west) to 29 (east).
        """
        self.row = row
        self.col = col

    def __str__(self) -> str:
        """Describe the square for people."""
        return f"row {self.row}, column {self.col}"

    def __repr__(self) -> str:
        """Show the code that rebuilds this square."""
        return f"Square({self.row}, {self.col})"

    def __eq__(self, other: object) -> bool:
        """Two squares are equal when their rows and columns match."""
        if not isinstance(other, Square):
            return NotImplemented
        return self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        """Let squares go in sets, like the (row, col) pairs they replace."""
        return hash((self.row, self.col))
