"""Replay canvas commands for widget painting and bitmap export."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from comp110_gui.bitmap import color as colors
from comp110_gui.bitmap.color import Color
from comp110_gui.bitmap.sampling import Sampling
from comp110_gui.graphics import commands
from comp110_gui.graphics import geometry
from comp110_gui.graphics.commands import line
from comp110_gui.graphics.commands import shape
from comp110_gui.graphics.commands import text

if TYPE_CHECKING:
    from comp110_gui.graphics.canvas import Canvas


def paint_image(
    painter: QtGui.QPainter,
    image: QtGui.QImage,
    box: QtCore.QRectF,
    sampling: Sampling,
) -> None:
    """Draw from the original snapshot at the current presentation scale."""
    painter.setRenderHint(
        QtGui.QPainter.RenderHint.SmoothPixmapTransform, sampling == "smooth"
    )
    target: QtCore.QRectF = geometry.contain(image.width(), image.height(), box)
    painter.drawImage(target, image)


def _pen(color: Color | None, width: float) -> QtGui.QPen:
    """Create a logical-width outline, or omit it."""
    if color is None:
        return QtGui.QPen(QtCore.Qt.PenStyle.NoPen)
    pen: QtGui.QPen = QtGui.QPen(colors.to_qt_color(color))
    pen.setWidthF(width)
    return pen


def render(painter: QtGui.QPainter, canvas: Canvas) -> None:
    """Replay commands identically for native paint events and image export."""
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    bounds: QtCore.QRectF = QtCore.QRectF(0, 0, canvas._width, canvas._height)
    painter.setClipRect(bounds)
    painter.fillRect(bounds, colors.to_qt_color(canvas._background))
    command: commands.Command
    for command in canvas._commands:
        if isinstance(command, line.Line):
            painter.setPen(_pen(command.color, command.width))
            painter.drawLine(command.start, command.end)
        elif isinstance(command, shape.Shape):
            painter.setPen(_pen(command.outline, command.outline_width))
            if command.fill is None:
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            else:
                painter.setBrush(colors.to_qt_color(command.fill))
            if command.ellipse:
                painter.drawEllipse(command.bounds)
            else:
                painter.drawRect(command.bounds)
        elif isinstance(command, text.Text):
            font: QtGui.QFont = QtWidgets.QApplication.font()
            font.setPixelSize(command.font_size)
            painter.setFont(font)
            painter.setPen(colors.to_qt_color(command.color))
            metrics: QtGui.QFontMetricsF = QtGui.QFontMetricsF(font)
            baseline: float = command.position.y() + metrics.ascent()
            text_line: str
            for text_line in command.text.split("\n"):
                painter.drawText(
                    QtCore.QPointF(command.position.x(), baseline), text_line
                )
                baseline += metrics.lineSpacing()
        else:
            paint_image(
                painter, command.image, command.bounds, command.sampling
            )
