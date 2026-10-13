"""Retained text drawing data."""

from __future__ import annotations

import dataclasses

from PySide6 import QtCore

from comp110_gui.bitmap.color import Color


@dataclasses.dataclass
class Text:
    """Store one retained text drawing command."""

    text: str
    position: QtCore.QPointF
    color: Color
    font_size: int
