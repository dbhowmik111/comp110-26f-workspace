"""PROVIDED: turn a photo of a hand-drawn map into sketch features.

Instead of clicking on the map, you can draw on paper. Use markers on white
paper: blue for rivers and ponds, red for
homes, black or dark gray for roads, and yellow for meadows. Photograph the
whole page, then choose "Sketch from photo" in the app.

PhotoSketch is not a Polygon or a Polyline, but it fits the same Feature
protocol, so Landscape.apply() works with it unchanged.
"""

from comp110_gui import Bitmap
from comp110_gui import Color

from goodfire import terrain
from goodfire.grid import Square

# Reference marker colors (red, green, blue) and the cover each one means.
MARKERS: list[tuple[tuple[int, int, int], str]] = [
    ((40, 90, 200), "river"),
    ((200, 40, 40), "homes"),
    ((40, 40, 40), "road"),
    ((230, 200, 40), "grass"),
]


class PhotoSketch:
    """The squares of one marker color found in a photo."""

    found: list[tuple[int, int]]
    cover: str

    def __init__(self, found: list[tuple[int, int]], cover: str):
        """Create a photo sketch.

        Args:
            found: The (row, col) squares where the marker appeared.
            cover: The cover those squares become.
        """
        self.found = found
        self.cover = cover

    def __str__(self) -> str:
        """Describe the shape for the sketch list."""
        return f"{self.cover} from a photo covering {len(self.found)} squares"

    def __repr__(self) -> str:
        """Show the code that rebuilds this shape (used by saved sketches)."""
        return f"PhotoSketch({self.found!r}, cover={self.cover!r})"

    def squares(self) -> list[Square]:
        """Return the squares the marker covered."""
        return [Square(row, col) for row, col in self.found]


def closest_marker(color: Color) -> str | None:
    """Return the cover for the nearest marker color, or None for paper."""
    red: int = color.get_red()
    green: int = color.get_green()
    blue: int = color.get_blue()
    if min(red, green, blue) > 170:
        return None  # white or light paper
    best: str | None = None
    best_distance: float = 120.0**2
    reference: tuple[int, int, int]
    cover: str
    for reference, cover in MARKERS:
        distance: float = (
            (red - reference[0]) ** 2
            + (green - reference[1]) ** 2
            + (blue - reference[2]) ** 2
        )
        if distance < best_distance:
            best = cover
            best_distance = distance
    return best


def features_from_photo(image: Bitmap) -> list[PhotoSketch]:
    """Sample the middle of each grid square of a photo and group by color.

    Args:
        image: A photo of the drawing; it is stretched to fit the grid.

    Returns:
        One PhotoSketch per marker color that appears.
    """
    found: dict[str, list[tuple[int, int]]] = {}
    width: int = image.get_width()
    height: int = image.get_height()
    row: int
    for row in range(terrain.GRID_SIZE):
        col: int
        for col in range(terrain.GRID_SIZE):
            x: int = int((col + 0.5) * width / terrain.GRID_SIZE)
            y: int = int((row + 0.5) * height / terrain.GRID_SIZE)
            cover: str | None = closest_marker(image.get_pixel(x, y))
            if cover is not None:
                if cover not in found:
                    found[cover] = []
                found[cover].append((row, col))
    result: list[PhotoSketch] = []
    name: str
    for name in found:
        result.append(PhotoSketch(found[name], name))
    return result
