"""Native Qt painting adapter for the canvas control."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from comp110_gui.graphics import geometry
from comp110_gui.graphics import rendering

if TYPE_CHECKING:
    from comp110_gui.graphics.canvas import Canvas
    from comp110_gui.graphics.canvas import DragCallback
    from comp110_gui.graphics.canvas import PointCallback


class CanvasWidget(QtWidgets.QWidget):
    """Native painting and click-gesture adaptation for a logical canvas."""

    def __init__(self: Self, canvas: Canvas) -> None:
        """Connect native painting and pointer events to a mounted canvas."""
        super().__init__()
        self._canvas: Canvas = canvas
        self._press: QtCore.QPointF | None = None
        self._last_drag_point: QtCore.QPointF | None = None
        self._dragged: bool = False
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.setAccessibleDescription(canvas._alt_text)
        self.setEnabled(canvas._enabled)
        self.setAutoFillBackground(True)

    def sizeHint(self: Self) -> QtCore.QSize:  # noqa: N802
        """Return the preferred drawing dimensions."""
        return QtCore.QSize(self._canvas._width, self._canvas._height)

    def _drawing_rect(self: Self) -> QtCore.QRectF:
        return geometry.contain(
            self._canvas._width,
            self._canvas._height,
            QtCore.QRectF(self.contentsRect()),
        )

    def _map_point(
        self: Self, position: QtCore.QPointF
    ) -> QtCore.QPointF | None:
        bounds: QtCore.QRectF = self._drawing_rect()
        if bounds.isEmpty() or not bounds.contains(position):
            return None
        scale: float = bounds.width() / self._canvas._width
        return QtCore.QPointF(
            (position.x() - bounds.x()) / scale,
            (position.y() - bounds.y()) / scale,
        )

    def paintEvent(self: Self, event: QtGui.QPaintEvent) -> None:  # noqa: N802
        """Scale vector commands at actual output resolution on each paint."""
        bounds: QtCore.QRectF = self._drawing_rect()
        if bounds.isEmpty():
            return
        painter: QtGui.QPainter = QtGui.QPainter(self)
        try:
            painter.translate(bounds.x(), bounds.y())
            scale: float = bounds.width() / self._canvas._width
            painter.scale(scale, scale)
            rendering.render(painter, self._canvas)
        finally:
            painter.end()

    def mousePressEvent(self: Self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Start only a primary-button gesture originating in the artwork."""
        self._press = None
        self._last_drag_point = None
        self._dragged = False
        point: QtCore.QPointF | None = self._map_point(event.position())
        if (
            self.isEnabled()
            and event.button() == QtCore.Qt.MouseButton.LeftButton
            and point is not None
        ):
            self._press = event.position()
            self._last_drag_point = point
            callback: PointCallback | None = self._canvas._press_callback
            if callback is not None:

                def notify_press() -> None:
                    callback(point.x(), point.y())

                self._canvas._emit("on_press", notify_press)

    def mouseDoubleClickEvent(  # noqa: N802
        self: Self, event: QtGui.QMouseEvent
    ) -> None:
        """Treat the second primary-button press as another ordinary click."""
        self.mousePressEvent(event)

    def mouseMoveEvent(self: Self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Deliver held-button movements in logical drawing coordinates."""
        if self._press is not None:
            if (
                not self.isEnabled()
                or not event.buttons() & QtCore.Qt.MouseButton.LeftButton
            ):
                self._press = None
                self._last_drag_point = None
                return
            distance: float = (event.position() - self._press).manhattanLength()
            if distance > QtWidgets.QApplication.startDragDistance():
                self._dragged = True
            self._drag_to(event.position())

    def _drag_to(self: Self, position: QtCore.QPointF) -> None:
        """Join consecutive points, breaking the stroke outside the artwork."""
        point: QtCore.QPointF | None = self._map_point(position)
        previous: QtCore.QPointF | None = self._last_drag_point
        self._last_drag_point = point
        callback: DragCallback | None = self._canvas._drag_callback
        if (
            point is not None
            and previous is not None
            and point != previous
            and callback is not None
        ):
            self._dragged = True

            def notify_drag() -> None:
                callback(previous.x(), previous.y(), point.x(), point.y())

            self._canvas._emit("on_drag", notify_drag)

    def mouseReleaseEvent(self: Self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        """Dispatch one qualifying gesture with logical release coordinates."""
        press: QtCore.QPointF | None = self._press
        self._press = None
        if (
            press is None
            or not self.isEnabled()
            or event.button() != QtCore.Qt.MouseButton.LeftButton
        ):
            self._last_drag_point = None
            return
        self._drag_to(event.position())
        self._last_drag_point = None
        if self._dragged:
            return
        distance: float = (event.position() - press).manhattanLength()
        if distance > QtWidgets.QApplication.startDragDistance():
            return
        point: QtCore.QPointF | None = self._map_point(event.position())
        callback: PointCallback | None = self._canvas._callback
        if point is not None and callback is not None:

            def notify_click() -> None:
                callback(point.x(), point.y())

            self._canvas._emit("on_click", notify_click)
