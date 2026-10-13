"""Display wrapping plain text."""

from typing import Self

from PySide6 import QtCore
from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation


class Label(base.Control):
    """Display wrapping plain text, including literal markup and newlines."""

    def __init__(self: Self, text: str = "") -> None:
        """Create a label without opening a window.

        Args:
            text: The text to display.
        """
        super().__init__()
        self._text: str = validation.string(text, "text")
        self._label: QtWidgets.QLabel | None = None

    def get_text(self: Self) -> str:
        """Return the displayed text."""
        self._check_readable()
        return self._text

    def set_text(self: Self, text: str) -> None:
        """Replace the displayed plain text.

        Args:
            text: The new text, which may be empty.
        """
        self._check_mutable()
        self._text = validation.string(text, "text")
        if self._label is not None:
            self._label.setText(self._text)

    def _detach(self: Self) -> None:
        self._label = None
        super()._detach()

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        label: QtWidgets.QLabel = QtWidgets.QLabel(self._text)
        label.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        self._label = label
        return self._attach(label, dispatch)
