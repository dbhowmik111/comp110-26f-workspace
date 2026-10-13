"""A fixed logical drawing space with retained drawing commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Self

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation
from comp110_gui.bitmap import bitmap as bitmap_module
from comp110_gui.bitmap import color as colors
from comp110_gui.bitmap import sampling as image_sampling
from comp110_gui.bitmap.bitmap import Bitmap
from comp110_gui.bitmap.color import ColorValue
from comp110_gui.bitmap.sampling import Sampling
from comp110_gui.graphics import canvas_widget
from comp110_gui.graphics import commands
from comp110_gui.graphics import geometry
from comp110_gui.graphics import rendering
from comp110_gui.graphics.commands import image
from comp110_gui.graphics.commands import line
from comp110_gui.graphics.commands import shape
from comp110_gui.graphics.commands import text as text_command
from comp110_gui.graphics.drawable import Drawable

type PointCallback = Callable[[float, float], None]
type DragCallback = Callable[[float, float, float, float], None]


class Canvas(base.Control):
    """A fixed logical drawing space with persistent drawing commands."""

    def __init__(
        self: Self,
        *,
        width: int = 400,
        height: int = 300,
        background: ColorValue = "white",
        alt_text: str = "",
    ) -> None:
        """Create a headless drawing description with preferred dimensions."""
        super().__init__()
        self._width: int = validation.integer(width, "width")
        self._height: int = validation.integer(height, "height")
        self._background: colors.Color = colors.resolve(background)
        self._alt_text: str = validation.string(alt_text, "alt_text")
        self._commands: list[commands.Command] = []
        self._callback: PointCallback | None = None
        self._press_callback: PointCallback | None = None
        self._drag_callback: DragCallback | None = None
        self._enabled: bool = True

    def get_width(self: Self) -> int:
        """Return the declared logical width, regardless of viewport size."""
        self._check_readable()
        return self._width

    def get_height(self: Self) -> int:
        """Return the declared logical height, regardless of viewport size."""
        self._check_readable()
        return self._height

    def _update(self: Self) -> None:
        if self._widget is not None:
            self._widget.update()

    def clear(self: Self) -> None:
        """Release all commands and restore the original background."""
        self._check_mutable()
        self._commands.clear()
        self._update()

    def draw(self: Self, drawable: Drawable) -> None:
        """Call an object's draw method once, immediately.

        Drawing exceptions propagate; commands already recorded remain.
        """
        self._check_mutable()
        draw: object = getattr(drawable, "draw", None)
        if not callable(draw):
            raise TypeError(
                "Canvas.draw() expects an object with draw(canvas)."
            )
        draw(self)

    def draw_line(
        self: Self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        color: ColorValue = "black",
        width: float = 1.0,
    ) -> None:
        """Record a line between two endpoints with a positive stroke width."""
        self._check_mutable()
        start: QtCore.QPointF = geometry.point(x1, y1)
        end: QtCore.QPointF = geometry.point(x2, y2)
        resolved: colors.Color = colors.resolve(color)
        stroke: float = validation.number(width, "width", positive=True)
        self._commands.append(line.Line(start, end, resolved, stroke))
        self._update()

    def draw_rectangle(
        self: Self,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        fill: ColorValue | None = None,
        outline: ColorValue | None = "black",
        outline_width: float = 1.0,
    ) -> None:
        """Record a rectangle using its top-left corner and positive size."""
        self._check_mutable()
        position: QtCore.QPointF = geometry.point(x, y)
        width = validation.number(width, "width", positive=True)
        height = validation.number(height, "height", positive=True)
        self._shape(
            QtCore.QRectF(position, QtCore.QSizeF(width, height)),
            False,
            fill,
            outline,
            outline_width,
        )

    def draw_circle(
        self: Self,
        x: float,
        y: float,
        radius: float,
        *,
        fill: ColorValue | None = None,
        outline: ColorValue | None = "black",
        outline_width: float = 1.0,
    ) -> None:
        """Record a circle with a center and positive radius."""
        self._check_mutable()
        position: QtCore.QPointF = geometry.point(x, y)
        radius = validation.number(radius, "radius", positive=True)
        self._shape(
            QtCore.QRectF(
                position.x() - radius,
                position.y() - radius,
                radius * 2,
                radius * 2,
            ),
            True,
            fill,
            outline,
            outline_width,
        )

    def _shape(
        self: Self,
        bounds: QtCore.QRectF,
        ellipse: bool,
        fill: ColorValue | None,
        outline: ColorValue | None,
        outline_width: float,
    ) -> None:
        resolved_fill: colors.Color | None = (
            None if fill is None else colors.resolve(fill)
        )
        resolved_outline: colors.Color | None = (
            None if outline is None else colors.resolve(outline)
        )
        stroke: float = validation.number(
            outline_width, "outline_width", positive=True
        )
        self._commands.append(
            shape.Shape(
                bounds, ellipse, resolved_fill, resolved_outline, stroke
            )
        )
        self._update()

    def draw_text(
        self: Self,
        text: str,
        x: float,
        y: float,
        *,
        color: ColorValue = "black",
        font_size: int = 16,
    ) -> None:
        """Record plain, unwrapped text positioned by its top-left corner."""
        self._check_mutable()
        text = validation.string(text, "text")
        normalized: str = text.replace("\r\n", "\n").replace("\r", "\n")
        position: QtCore.QPointF = geometry.point(x, y)
        resolved: colors.Color = colors.resolve(color)
        size: int = validation.integer(font_size, "font_size")
        self._commands.append(
            text_command.Text(normalized, position, resolved, size)
        )
        self._update()

    def draw_image(
        self: Self,
        bitmap: Bitmap,
        x: float,
        y: float,
        *,
        width: float | None = None,
        height: float | None = None,
        sampling: Sampling = "smooth",
    ) -> None:
        """Snapshot pixels and fit them within a box without distortion.

        Omitting one dimension preserves the bitmap's aspect ratio. Omitting
        both uses one drawing unit per bitmap pixel.
        """
        self._check_mutable()
        bitmap_module.require_bitmap(bitmap)
        position: QtCore.QPointF = geometry.point(x, y)
        sampling = image_sampling.validate(sampling)
        if width is not None:
            width = validation.number(width, "width", positive=True)
        if height is not None:
            height = validation.number(height, "height", positive=True)
        if width is None and height is None:
            width = float(bitmap.get_width())
            height = float(bitmap.get_height())
        elif width is None:
            assert height is not None
            width = height * bitmap.get_width() / bitmap.get_height()
        elif height is None:
            height = width * bitmap.get_height() / bitmap.get_width()
        bounds: QtCore.QRectF = QtCore.QRectF(
            position, QtCore.QSizeF(width, height)
        )
        self._commands.append(
            image.Image(QtGui.QImage(bitmap._image), bounds, sampling)
        )
        self._update()

    def to_bitmap(self: Self) -> Bitmap:
        """Export independent pixels at the declared drawing dimensions.

        Raises:
            RuntimeError: No active session is ready to dispatch callbacks.
        """
        from comp110_gui.runtime import state

        self._check_mutable()
        state.require_session("Canvas.to_bitmap()")
        image: QtGui.QImage = bitmap_module.new_image(self._width, self._height)
        image.fill(QtCore.Qt.GlobalColor.transparent)
        painter: QtGui.QPainter = QtGui.QPainter(image)
        try:
            rendering.render(painter, self)
        finally:
            painter.end()
        return bitmap_module.from_image(image)

    def on_click(self: Self, callback: PointCallback | None) -> None:
        """Replace the callback receiving release coordinates, or remove it."""
        self._check_mutable()
        validation.callback(callback, "Canvas.on_click accepting x and y")
        self._callback = callback

    def on_press(self: Self, callback: PointCallback | None) -> None:
        """Handle a primary-button press inside the artwork, or remove it.

        The callback receives logical x and y coordinates before any drag or
        click callbacks. Use this to save the state before a drawing gesture.
        """
        self._check_mutable()
        validation.callback(callback, "Canvas.on_press accepting x and y")
        self._press_callback = callback

    def on_drag(self: Self, callback: DragCallback | None) -> None:
        """Handle drawing segments while the primary button is held.

        The callback receives logical x1, y1, x2, y2 coordinates for each
        segment, including the final movement on release. Leaving the drawing
        area breaks the line; reentering starts a new segment. A gesture that
        emits a drag does not also emit on_click. None removes the handler.
        """
        self._check_mutable()
        validation.callback(callback, "Canvas.on_drag accepting x1, y1, x2, y2")
        self._drag_callback = callback

    def set_alt_text(self: Self, text: str) -> None:
        """Set the accessible description of the artwork."""
        self._check_mutable()
        self._alt_text = validation.string(text, "text")
        if self._widget is not None:
            self._widget.setAccessibleDescription(text)

    def is_enabled(self: Self) -> bool:
        """Return whether pointer gestures can invoke callbacks."""
        self._check_readable()
        return self._enabled

    def set_enabled(self: Self, enabled: bool) -> None:
        """Enable or disable pointer callbacks; drawing remains available."""
        self._check_mutable()
        self._enabled = validation.boolean(enabled, "enabled")
        if self._widget is not None:
            self._widget.setEnabled(enabled)
            assert isinstance(self._widget, canvas_widget.CanvasWidget)
            self._widget._press = None
            self._widget._last_drag_point = None

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        return self._attach(canvas_widget.CanvasWidget(self), dispatch)
