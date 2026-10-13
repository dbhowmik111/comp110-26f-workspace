"""Retained line drawing data."""

from __future__ import annotations

import dataclasses

from PySide6 import QtCore

from comp110_gui.bitmap.color import Color


@dataclasses.dataclass
class Line:
    """Store one retained line drawing command."""

    start: QtCore.QPointF
    end: QtCore.QPointF
    color: Color
    width: float
