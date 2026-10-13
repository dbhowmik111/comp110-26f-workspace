"""Immutable RGBA colors and the supported color vocabulary."""

from __future__ import annotations

import dataclasses
import re
from typing import Self

from PySide6 import QtGui

from comp110_gui import validation


@dataclasses.dataclass(frozen=True, init=False)
class Color:
    """An immutable red, green, blue, and alpha value."""

    _red: int
    _green: int
    _blue: int
    _alpha: int

    def __init__(
        self: Self, red: int, green: int, blue: int, *, alpha: int = 255
    ) -> None:
        """Create a color with integer channels between zero and 255.

        Raises:
            TypeError: A channel is not an integer, or is a boolean.
            ValueError: A channel is outside the allowed range.
        """
        channels: dict[str, int] = {
            "red": red,
            "green": green,
            "blue": blue,
            "alpha": alpha,
        }
        name: str
        value: int
        for name, value in channels.items():
            validation.integer(value, name, minimum=0)
            if value > 255:
                raise ValueError(f"{name} must be between 0 and 255.")
            object.__setattr__(self, "_" + name, value)

    def get_red(self: Self) -> int:
        """Return the red channel."""
        return self._red

    def get_green(self: Self) -> int:
        """Return the green channel."""
        return self._green

    def get_blue(self: Self) -> int:
        """Return the blue channel."""
        return self._blue

    def get_alpha(self: Self) -> int:
        """Return opacity, from zero (transparent) to 255 (opaque)."""
        return self._alpha


type ColorValue = Color | str


_NAMED_COLORS: dict[str, Color] = {
    "black": Color(0, 0, 0),
    "white": Color(255, 255, 255),
    "red": Color(255, 0, 0),
    "green": Color(0, 128, 0),
    "blue": Color(0, 0, 255),
    "yellow": Color(255, 255, 0),
    "gray": Color(128, 128, 128),
    "transparent": Color(0, 0, 0, alpha=0),
}


def resolve(value: ColorValue) -> Color:
    """Resolve only the documented named and hexadecimal color syntax."""
    if isinstance(value, Color):
        return value
    validation.string(value, "color")
    text: str = value.lower()
    if text in _NAMED_COLORS:
        return _NAMED_COLORS[text]
    if re.fullmatch(r"#[0-9a-f]{6}([0-9a-f]{2})?", text) is None:
        raise ValueError(f"Unrecognized color: {value!r}.")
    red: int = int(text[1:3], 16)
    green: int = int(text[3:5], 16)
    blue: int = int(text[5:7], 16)
    alpha: int = int(text[7:9], 16) if len(text) == 9 else 255
    return Color(red, green, blue, alpha=alpha)


def to_qt_color(value: Color) -> QtGui.QColor:
    """Translate the facade color into the private Qt representation."""
    return QtGui.QColor(
        value.get_red(), value.get_green(), value.get_blue(), value.get_alpha()
    )
