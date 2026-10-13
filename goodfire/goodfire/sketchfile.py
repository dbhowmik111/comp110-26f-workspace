"""PROVIDED: save and load sketches as text, one repr() per line.

This is why __repr__ matters: a saved sketch is just each feature's repr,
and loading runs that code to rebuild the same objects. You can open a
sketch file in VS Code, read it, and even edit the numbers by hand.
"""

from goodfire.grid import Point
from goodfire.photo import PhotoSketch
from goodfire.protocols import Feature
from goodfire.sketch import Polygon
from goodfire.sketch import Polyline

KNOWN_SHAPES: dict[str, object] = {
    "Point": Point,
    "Polygon": Polygon,
    "Polyline": Polyline,
    "PhotoSketch": PhotoSketch,
}


def save_sketch(path: str, features: list[Feature]) -> None:
    """Write one repr() per line, with a comment header.

    Args:
        path: The text file to write.
        features: The shapes to save, in order.
    """
    lines: list[str] = ["# Good Fire sketch: one shape per line, as repr()"]
    feature: Feature
    for feature in features:
        lines.append(repr(feature))
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def sketch_lines(path: str) -> list[str]:
    """Return the shape lines of a sketch file (no blanks or comments)."""
    lines: list[str] = []
    with open(path, encoding="utf-8") as file:
        line: str
        for line in file:
            text: str = line.strip()
            if text != "" and not text.startswith("#"):
                lines.append(text)
    return lines


def read_feature(text: str) -> Feature:
    """Rebuild one shape from its repr().

    Only Polygon, Polyline, PhotoSketch, and their Points may appear, so a
    sketch file cannot run other code.

    Raises:
        ValueError: If the text is not the repr of a known shape.
    """
    name: str = text.split("(", 1)[0]
    if name not in KNOWN_SHAPES:
        raise ValueError(f"unknown shape {name!r}")
    shape: object = eval(text, {"__builtins__": {}}, KNOWN_SHAPES)  # noqa: S307
    if not isinstance(shape, Feature):
        raise ValueError(f"not a sketch feature: {text[:40]}")
    return shape


def load_sketch(path: str) -> list[Feature]:
    """Read a sketch file back into objects, in file order.

    Args:
        path: The text file to read.

    Returns:
        The shapes, in file order.

    Raises:
        ValueError: If a line is not the repr of a known shape.
    """
    features: list[Feature] = []
    text: str
    for text in sketch_lines(path):
        features.append(read_feature(text))
    return features
