"""A labeled dropdown with distinct text options."""

from typing import Self

from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation
from comp110_gui.controls import callbacks
from comp110_gui.controls import enabled_control
from comp110_gui.controls import field


class Choice(enabled_control.EnabledControl):
    """A labeled dropdown of distinct nonblank strings."""

    def __init__(
        self: Self,
        options: list[str],
        *,
        label: str,
        selected: str | None = None,
    ) -> None:
        """Create a noneditable dropdown, copying the supplied options.

        Args:
            options: A nonempty list of unique, nonblank strings.
            label: The persistent visible label and accessible name.
            selected: Initial selection, or None for the first option.

        Raises:
            ValueError: Options are empty, repeated, blank, or lack selected.
        """
        super().__init__()
        self._label: str = validation.string(label, "label", nonblank=True)
        if not isinstance(options, list):
            raise TypeError("options must be a list of strings.")
        if not options:
            raise ValueError("Choice requires at least one option.")
        self._options: list[str] = []
        option: str
        for option in options:
            validation.string(option, "option", nonblank=True)
            if option in self._options:
                raise ValueError("Choice options must be unique.")
            self._options.append(option)
        self._value: str = self._options[0]
        self._callback: callbacks.Callback | None = None
        self._editor: QtWidgets.QComboBox | None = None
        if selected is not None:
            self.set_value(selected)

    def get_value(self: Self) -> str:
        """Return the selected string."""
        self._check_readable()
        return self._value

    def set_value(self: Self, value: str) -> None:
        """Select an option without calling the change handler.

        Args:
            value: A string exactly matching an existing option.

        Raises:
            ValueError: The value is not one of this choice's options.
        """
        self._check_mutable()
        validation.string(value, "value")
        if value not in self._options:
            raise ValueError(
                f"{value!r} is not an option for Choice {self._label!r}."
            )
        self._value = value
        if self._editor is not None:
            self._editor.setCurrentIndex(self._options.index(value))

    def on_change(self: Self, callback: callbacks.Callback | None) -> None:
        """Replace the user-change handler, or remove it with None.

        Args:
            callback: A function or bound method taking no arguments.
        """
        self._check_mutable()
        validation.callback(callback, "on_change")
        self._callback = callback

    def _activated(self: Self, index: int) -> None:
        value: str = self._options[index]
        if value != self._value:
            self._value = value
            self._emit("on_change", self._callback)

    def _detach(self: Self) -> None:
        self._editor = None
        super()._detach()

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        editor: QtWidgets.QComboBox = QtWidgets.QComboBox()
        editor.setEditable(False)
        editor.addItems(self._options)
        editor.setCurrentIndex(self._options.index(self._value))
        editor.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        editor.activated.connect(self._activated)
        self._editor = editor
        container: QtWidgets.QWidget = field.labeled_field(self._label, editor)
        container.setEnabled(self._enabled)
        return self._attach(container, dispatch)
