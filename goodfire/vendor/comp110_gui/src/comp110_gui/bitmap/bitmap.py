"""Headless mutable bitmap storage with exact RGBA pixels."""

from __future__ import annotations

import pathlib
from typing import Self

from PySide6 import QtCore
from PySide6 import QtGui

from comp110_gui import validation
from comp110_gui.bitmap import color as colors
from comp110_gui.bitmap.color import Color
from comp110_gui.bitmap.color import ColorValue


def new_image(width: int, height: int) -> QtGui.QImage:
    """Allocate straight-alpha pixels and report allocation failures."""
    image: QtGui.QImage = QtGui.QImage(
        width, height, QtGui.QImage.Format.Format_RGBA8888
    )
    if image.isNull():
        raise MemoryError(f"Could not allocate a {width} by {height} bitmap.")
    return image


class Bitmap:
    """Mutable RGBA image data usable without a GUI application."""

    def __init__(
        self: Self, *, width: int, height: int, fill: ColorValue = "white"
    ) -> None:
        """Create a bitmap with positive integer dimensions and a fill color."""
        validation.integer(width, "width")
        validation.integer(height, "height")
        color: Color = colors.resolve(fill)
        self._image: QtGui.QImage = new_image(width, height)
        self._image.fill(colors.to_qt_color(color))

    def get_width(self: Self) -> int:
        """Return the number of pixel columns."""
        return self._image.width()

    def get_height(self: Self) -> int:
        """Return the number of pixel rows."""
        return self._image.height()

    def _check_pixel(self: Self, x: object, y: object) -> None:
        """Reject noninteger and out-of-range coordinates before access."""
        # Negative integers use IndexError rather than dimension validation.
        if isinstance(x, bool) or not isinstance(x, int):
            raise TypeError("Pixel x must be an integer, excluding booleans.")
        if isinstance(y, bool) or not isinstance(y, int):
            raise TypeError("Pixel y must be an integer, excluding booleans.")
        if not (0 <= x < self.get_width() and 0 <= y < self.get_height()):
            raise IndexError(
                f"Pixel ({x}, {y}) is outside a {self.get_width()} by "
                f"{self.get_height()} bitmap."
            )

    def get_pixel(self: Self, x: int, y: int) -> Color:
        """Return one pixel's exact RGBA channels.

        Raises:
            TypeError: Coordinates are not integers or are booleans.
            IndexError: The pixel is outside the image.
        """
        self._check_pixel(x, y)
        color: QtGui.QColor = self._image.pixelColor(x, y)
        return Color(
            color.red(), color.green(), color.blue(), alpha=color.alpha()
        )

    def set_pixel(self: Self, x: int, y: int, color: ColorValue) -> None:
        """Replace one pixel, preserving all channels even at zero alpha."""
        self._check_pixel(x, y)
        resolved: Color = colors.resolve(color)
        self._image.setPixelColor(x, y, colors.to_qt_color(resolved))

    def fill(self: Self, color: ColorValue) -> None:
        """Replace all pixels with a color without alpha blending."""
        resolved: Color = colors.resolve(color)
        self._image.fill(colors.to_qt_color(resolved))

    def copy(self: Self) -> Bitmap:
        """Return independent mutable image data."""
        return from_image(QtGui.QImage(self._image))

    def save(self: Self, path: str) -> None:
        """Save original pixels as PNG, overwriting an existing file.

        Args:
            path: Local filename ending in .png, relative to the working
                directory or absolute.

        Raises:
            ValueError: The filename does not end in .png.
            OSError: The file cannot be written or encoded.
        """
        validation.string(path, "path")
        if pathlib.Path(path).suffix.lower() != ".png":
            raise ValueError("Bitmap.save() requires a .png filename.")
        writer: QtGui.QImageWriter = QtGui.QImageWriter(
            path, QtCore.QByteArray(b"png")
        )
        if not writer.write(self._image):
            raise OSError(f"Could not save {path!r}: {writer.errorString()}")


def from_image(image: QtGui.QImage) -> Bitmap:
    """Wrap known valid RGBA image data without allocating it a second time."""
    bitmap: Bitmap = Bitmap.__new__(Bitmap)
    bitmap._image = image
    return bitmap


def require_bitmap(bitmap: object) -> None:
    """Validate facade image inputs before replacing stored snapshots."""
    if not isinstance(bitmap, Bitmap):
        raise TypeError("bitmap must be a Bitmap.")
