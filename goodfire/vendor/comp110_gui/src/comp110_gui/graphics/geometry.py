"""Geometry validation and proportional image positioning."""

from __future__ import annotations

from PySide6 import QtCore

from comp110_gui import validation


def contain(width: float, height: float, box: QtCore.QRectF) -> QtCore.QRectF:
    """Fit source dimensions uniformly and centrally into a destination."""
    scale: float = min(box.width() / width, box.height() / height)
    return QtCore.QRectF(
        box.x() + (box.width() - scale * width) / 2,
        box.y() + (box.height() - scale * height) / 2,
        scale * width,
        scale * height,
    )


def point(x: float, y: float) -> QtCore.QPointF:
    """Validate finite drawing coordinates before constructing Qt geometry."""
    return QtCore.QPointF(validation.number(x, "x"), validation.number(y, "y"))
