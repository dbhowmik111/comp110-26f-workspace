"""Retained image drawing data."""

from __future__ import annotations

import dataclasses

from PySide6 import QtCore
from PySide6 import QtGui

from comp110_gui.bitmap.sampling import Sampling


@dataclasses.dataclass
class Image:
    """Store one retained image drawing command."""

    image: QtGui.QImage
    bounds: QtCore.QRectF
    sampling: Sampling
