"""A push button with one replaceable click callback."""

from typing import Self

from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation
from comp110_gui.controls import callbacks
from comp110_gui.controls import enabled_control
from comp110_gui.controls import text_helpers


class Button(enabled_control.EnabledControl):
    """A push button that calls one registered function when activated."""

    def __init__(self: Self, text: str) -> None:
        """Create a button.

        Args:
            text: A nonblank caption, with literal ampersands.
        """
        super().__init__()
        self._text: str = validation.string(text, "text", nonblank=True)
        self._callback: callbacks.Callback | None = None
        self._button: QtWidgets.QPushButton | None = None

    def get_text(self: Self) -> str:
        """Return the button's caption."""
        self._check_readable()
        return self._text

    def set_text(self: Self, text: str) -> None:
        """Replace the button caption.

        Args:
            text: A nonblank caption.
        """
        self._check_mutable()
        self._text = validation.string(text, "text", nonblank=True)
        if self._button is not None:
            self._button.setText(text_helpers.caption(self._text))
            self._button.setAccessibleName(self._text)

    def on_click(self: Self, callback: callbacks.Callback | None) -> None:
        """Replace the click handler, or remove it with None.

        Args:
            callback: A function or bound method taking no arguments.
        """
        self._check_mutable()
        validation.callback(callback, "on_click")
        self._callback = callback

    def _clicked(self: Self) -> None:
        self._emit("on_click", self._callback)

    def _detach(self: Self) -> None:
        self._button = None
        super()._detach()

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            text_helpers.caption(self._text)
        )
        button.setAccessibleName(self._text)
        button.setAutoDefault(False)
        button.setDefault(False)
        button.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        button.setEnabled(self._enabled)
        button.clicked.connect(self._clicked)
        self._button = button
        return self._attach(button, dispatch)
