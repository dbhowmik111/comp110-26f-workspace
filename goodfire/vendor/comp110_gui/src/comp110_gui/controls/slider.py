"""A floating-point slider with a synchronized numeric stepper."""

import decimal
import fractions
import math
from typing import Self

from PySide6 import QtCore
from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation
from comp110_gui.controls import callbacks
from comp110_gui.controls import enabled_control
from comp110_gui.controls import field
from comp110_gui.controls import slider_stepper


class Slider(enabled_control.EnabledControl):
    """Select a float on an evenly spaced grid, with a concise value display."""

    def __init__(
        self: Self,
        *,
        label: str,
        min: float = 0.0,
        max: float = 1.0,
        steps: int = 100,
        value: float | None = None,
    ) -> None:
        """Prepare a labeled slider and editable numeric stepper.

        Args:
            label: A persistent, nonblank visible label.
            min: The smallest allowed value.
            max: The largest allowed value, greater than min.
            steps: The number of equal intervals, giving steps + 1 positions.
            value: Initial value snapped to a position; None uses min.

        Raises:
            TypeError: An argument has the wrong type, including booleans.
            ValueError: Bounds, steps, or value are invalid, or adjacent values
                cannot be represented as distinct floats.
        """
        super().__init__()
        self._label: str = validation.string(label, "label", nonblank=True)
        self._minimum: float = validation.number(min, "min")
        self._maximum: float = validation.number(max, "max")
        self._steps: int = validation.integer(steps, "steps")
        if self._steps > 2_147_483_647:
            raise ValueError("steps must be at most 2147483647.")
        if self._minimum >= self._maximum:
            raise ValueError("max must be greater than min.")
        span: float = self._maximum - self._minimum
        interval: float = span / self._steps
        if (
            not math.isfinite(span)
            or interval < math.ulp(self._minimum)
            or interval < math.ulp(self._maximum)
        ):
            raise ValueError(
                "This range and steps cannot represent distinct floats."
            )
        # Decimal arithmetic avoids accumulated binary rounding errors.
        self._start: decimal.Decimal = decimal.Decimal(str(self._minimum))
        self._end: decimal.Decimal = decimal.Decimal(str(self._maximum))
        self._interval: decimal.Decimal = (
            self._end - self._start
        ) / self._steps
        self._places: int = self._display_places()
        self._index: int = 0
        self._callback: callbacks.Callback | None = None
        self._slider: QtWidgets.QSlider | None = None
        self._editor: slider_stepper.SliderStepper | None = None
        if value is not None:
            self.set_value(value)

    def _display_places(self: Self) -> int:
        """Display exact steps or rounded repeating fractions."""
        step_places: int = -int(self._interval.normalize().as_tuple().exponent)
        exact_step: fractions.Fraction = (
            fractions.Fraction(self._end) - fractions.Fraction(self._start)
        ) / self._steps
        places: int
        if fractions.Fraction(self._interval) == exact_step:
            places = step_places
        else:
            places = 1 - self._interval.adjusted()
        bound: decimal.Decimal
        for bound in (self._start, self._end):
            if bound:
                places = max(
                    places, -int(bound.normalize().as_tuple().exponent)
                )
        return places

    def _value_at(self: Self, index: int) -> float:
        if index == self._steps:
            return self._maximum
        return float(self._start + self._interval * index)

    def _index_for(self: Self, value: float) -> int:
        position: decimal.Decimal = (
            decimal.Decimal(str(value)) - self._start
        ) / self._interval
        nearest: int = int(
            position.to_integral_value(rounding=decimal.ROUND_HALF_UP)
        )
        return max(0, min(self._steps, nearest))

    def _display(self: Self, index: int) -> str:
        rounded: float = round(self._value_at(index), self._places)
        if rounded == 0:
            return "0"
        return str(rounded).removesuffix(".0")

    def get_value(self: Self) -> float:
        """Return the selected float, without the display's rounding."""
        self._check_readable()
        return self._value_at(self._index)

    def set_value(self: Self, value: float) -> None:
        """Snap an in-range value to the nearest step without calling on_change.

        Exact halfway values round toward max. Nonfinite and out-of-range
        values raise ValueError without changing the existing selection.
        """
        self._check_mutable()
        value = validation.number(value, "value")
        if not self._minimum <= value <= self._maximum:
            raise ValueError("value must be between min and max.")
        self._index = self._index_for(value)
        self._sync()

    def on_change(self: Self, callback: callbacks.Callback | None) -> None:
        """Replace the user-change handler, or remove it with None."""
        self._check_mutable()
        validation.callback(callback, "on_change")
        self._callback = callback

    def _sync(self: Self) -> None:
        widget: QtWidgets.QSlider | slider_stepper.SliderStepper | None
        for widget in (self._slider, self._editor):
            if widget is not None:
                with QtCore.QSignalBlocker(widget):
                    widget.setValue(self._index)
                widget.updateGeometry()

    def _changed(self: Self, index: int) -> None:
        if index != self._index:
            self._index = index
            self._sync()
            self._emit("on_change", self._callback)

    def _detach(self: Self) -> None:
        self._slider = None
        self._editor = None
        super()._detach()

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        panel: QtWidgets.QWidget = QtWidgets.QWidget()
        row: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(panel)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        slider: QtWidgets.QSlider = QtWidgets.QSlider(
            QtCore.Qt.Orientation.Horizontal
        )
        slider.setRange(0, self._steps)
        slider.setPageStep(max(1, self._steps // 10))
        slider.setAccessibleName(f"{self._label} slider")
        editor: slider_stepper.SliderStepper = slider_stepper.SliderStepper(
            self
        )
        editor.setAccessibleName(self._label)
        slider.valueChanged.connect(self._changed)
        editor.valueChanged.connect(self._changed)
        self._slider = slider
        self._editor = editor
        self._sync()
        row.addWidget(slider, 1)
        row.addWidget(editor)
        panel.setFocusProxy(editor)
        panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        container: QtWidgets.QWidget = field.labeled_field(self._label, panel)
        container.setEnabled(self._enabled)
        return self._attach(container, dispatch)
