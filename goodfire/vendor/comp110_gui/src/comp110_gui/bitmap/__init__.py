"""Headless RGBA colors, bitmap storage, and local image files."""

from comp110_gui.bitmap.bitmap import Bitmap
from comp110_gui.bitmap.color import Color
from comp110_gui.bitmap.color import ColorValue
from comp110_gui.bitmap.io import load_bitmap
from comp110_gui.bitmap.picker import choose_bitmap
from comp110_gui.bitmap.sampling import Sampling

__all__: list[str] = [
    "Bitmap",
    "Color",
    "ColorValue",
    "Sampling",
    "choose_bitmap",
    "load_bitmap",
]
