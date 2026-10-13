"""Native Qt painting adapter for the picture control."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from comp110_gui.graphics import rendering

if TYPE_CHECKING:
    from comp110_gui.graphics.picture import Picture


class PictureWidget(QtWidgets.QWidget):
    """Native paint adapter; no widgets are allocated until mounting."""

    def __init__(self: Self, picture: Picture) -> None:
        """Connect native painting to a mounted picture's snapshot."""
        super().__init__()
        self._picture: Picture = picture
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.setAccessibleDescription(picture._alt_text)
        self.setAutoFillBackground(True)

    def sizeHint(self: Self) -> QtCore.QSize:  # noqa: N802
        """Return the student's preferred logical viewport size."""
        return QtCore.QSize(self._picture._width, self._picture._height)

    def paintEvent(self: Self, event: QtGui.QPaintEvent) -> None:  # noqa: N802
        """Draw only during the native paint event."""
        painter: QtGui.QPainter = QtGui.QPainter(self)
        try:
            rendering.paint_image(
                painter,
                self._picture._image,
                QtCore.QRectF(self.contentsRect()),
                self._picture._sampling,
            )
        finally:
            painter.end()
