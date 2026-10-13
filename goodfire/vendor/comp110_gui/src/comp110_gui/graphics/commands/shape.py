"""Retained shape drawing data."""

from __future__ import annotations

import dataclasses

from PySide6 import QtCore

from comp110_gui.bitmap.color import Color


@dataclasses.dataclass
class Shape:
    """Store one retained shape drawing command."""

    bounds: QtCore.QRectF
    ellipse: bool
    fill: Color | None
    outline: Color | None
    outline_width: float
