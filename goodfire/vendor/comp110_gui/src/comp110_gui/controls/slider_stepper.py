"""Edit float values while stepping through exact integer positions."""

from __future__ import annotations

import decimal
from typing import TYPE_CHECKING
from typing import Self
from typing import cast

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

if TYPE_CHECKING:
    from comp110_gui.controls import slider


class SliderStepper(QtWidgets.QSpinBox):
    """Keep stepper arrows exact even when the displayed fraction is rounded."""

    def __init__(self: Self, control: slider.Slider) -> None:
        """Use integer positions internally and numeric text for the user."""
        super().__init__()
        self._control: slider.Slider = control
        self._validator: QtGui.QDoubleValidator = QtGui.QDoubleValidator(
            control._minimum, control._maximum, 323, self
        )
        self._validator.setLocale(QtCore.QLocale.c())
        self.setLocale(QtCore.QLocale.c())
        self.setRange(0, control._steps)
        self.setKeyboardTracking(False)

    def textFromValue(self: Self, value: int) -> str:  # noqa: N802
        """Show the floating-point value with just the useful decimal places."""
        return self._control._display(value)

    def sizeHint(self: Self) -> QtCore.QSize:  # noqa: N802
        """Reserve space for fractional text, not just the range endpoints."""
        size: QtCore.QSize = super().sizeHint()
        metrics: QtGui.QFontMetrics = self.fontMetrics()
        endpoint_width: int = max(
            metrics.horizontalAdvance(self.textFromValue(self.minimum())),
            metrics.horizontalAdvance(self.textFromValue(self.maximum())),
        )
        extra: int = max(
            0, metrics.horizontalAdvance(self.text()) - endpoint_width
        )
        return size + QtCore.QSize(extra + 8, 0)

    def minimumSizeHint(self: Self) -> QtCore.QSize:  # noqa: N802
        """Keep the complete value visible even in a narrow layout."""
        return self.sizeHint()

    def valueFromText(self: Self, text: str) -> int:  # noqa: N802
        """Snap numeric input; keep the old value for invalid input."""
        try:
            return self._control._index_for(float(text))
        except (ValueError, OverflowError, decimal.InvalidOperation):
            return self.value()

    def validate(
        self: Self, text: str, position: int
    ) -> tuple[QtGui.QValidator.State, str, int]:
        """Validate numeric input and partial edits against the float range."""
        return cast(
            tuple[QtGui.QValidator.State, str, int],
            self._validator.validate(text, position),
        )
