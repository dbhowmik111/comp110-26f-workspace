"""A two-state checkbox with a literal text caption."""

from typing import Self

from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation
from comp110_gui.controls import callbacks
from comp110_gui.controls import enabled_control
from comp110_gui.controls import text_helpers


class Checkbox(enabled_control.EnabledControl):
    """A two-state checkbox with a literal text caption."""

    def __init__(self: Self, text: str, *, checked: bool = False) -> None:
        """Create a checkbox.

        Args:
            text: The nonblank caption and accessible name.
            checked: Whether the checkbox starts checked.
        """
        super().__init__()
        self._text: str = validation.string(text, "text", nonblank=True)
        self._checked: bool = validation.boolean(checked, "checked")
        self._callback: callbacks.Callback | None = None
        self._checkbox: QtWidgets.QCheckBox | None = None

    def is_checked(self: Self) -> bool:
        """Return whether the checkbox is checked."""
        self._check_readable()
        return self._checked

    def set_checked(self: Self, checked: bool) -> None:
        """Set the state without calling the change handler.

        Args:
            checked: The new checked state.
        """
        self._check_mutable()
        self._checked = validation.boolean(checked, "checked")
        if self._checkbox is not None:
            self._checkbox.setChecked(self._checked)

    def on_change(self: Self, callback: callbacks.Callback | None) -> None:
        """Replace the user-change handler, or remove it with None.

        Args:
            callback: A function or bound method taking no arguments.
        """
        self._check_mutable()
        validation.callback(callback, "on_change")
        self._callback = callback

    def _clicked(self: Self, checked: bool) -> None:
        self._checked = checked
        self._emit("on_change", self._callback)

    def _detach(self: Self) -> None:
        self._checkbox = None
        super()._detach()

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        checkbox: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            text_helpers.caption(self._text)
        )
        checkbox.setAccessibleName(self._text)
        checkbox.setTristate(False)
        checkbox.setChecked(self._checked)
        checkbox.setEnabled(self._enabled)
        checkbox.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        checkbox.clicked.connect(self._clicked)
        self._checkbox = checkbox
        return self._attach(checkbox, dispatch)
