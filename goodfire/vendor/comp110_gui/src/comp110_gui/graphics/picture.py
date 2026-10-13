"""Snapshot-based bitmap display control."""

from __future__ import annotations

from typing import Self

from PySide6 import QtGui
from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation
from comp110_gui.bitmap import bitmap as bitmap_module
from comp110_gui.bitmap import sampling as image_sampling
from comp110_gui.bitmap.bitmap import Bitmap
from comp110_gui.bitmap.sampling import Sampling
from comp110_gui.graphics import picture_widget


class Picture(base.Control):
    """Display a snapshot of a bitmap, centered without cropping."""

    def __init__(
        self: Self,
        bitmap: Bitmap,
        *,
        width: int = 320,
        height: int = 240,
        sampling: Sampling = "smooth",
        alt_text: str = "",
    ) -> None:
        """Capture pixels and choose preferred logical viewport dimensions."""
        super().__init__()
        bitmap_module.require_bitmap(bitmap)
        self._width: int = validation.integer(width, "width")
        self._height: int = validation.integer(height, "height")
        self._sampling: Sampling = image_sampling.validate(sampling)
        self._alt_text: str = validation.string(alt_text, "alt_text")
        self._image: QtGui.QImage = QtGui.QImage(bitmap._image)

    def set_bitmap(self: Self, bitmap: Bitmap) -> None:
        """Publish a fresh snapshot, even when reusing the same bitmap."""
        self._check_mutable()
        bitmap_module.require_bitmap(bitmap)
        self._image = QtGui.QImage(bitmap._image)
        if self._widget is not None:
            self._widget.update()

    def set_alt_text(self: Self, text: str) -> None:
        """Set the image's accessible description."""
        self._check_mutable()
        self._alt_text = validation.string(text, "text")
        if self._widget is not None:
            self._widget.setAccessibleDescription(text)

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        return self._attach(picture_widget.PictureWidget(self), dispatch)
