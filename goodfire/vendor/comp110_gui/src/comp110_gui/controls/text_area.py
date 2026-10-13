"""A labeled multiline plain-text editor."""

from typing import Self

from PySide6 import QtCore
from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation
from comp110_gui.controls import callbacks
from comp110_gui.controls import enabled_control
from comp110_gui.controls import field
from comp110_gui.controls import text_helpers


class TextArea(enabled_control.EnabledControl):
    """A labeled plain-text editor or selectable multiline output area."""

    def __init__(
        self: Self, *, label: str, text: str = "", read_only: bool = False
    ) -> None:
        """Create a multiline editor.

        Args:
            label: The nonblank persistent label and accessible name.
            text: Initial plain text; CRLF and CR become LF.
            read_only: Whether editing is disabled but copying remains possible.
        """
        super().__init__()
        self._label: str = validation.string(label, "label", nonblank=True)
        self._text: str = text_helpers.multiline(
            validation.string(text, "text")
        )
        self._read_only: bool = validation.boolean(read_only, "read_only")
        self._callback: callbacks.Callback | None = None
        self._editor: QtWidgets.QPlainTextEdit | None = None

    def get_text(self: Self) -> str:
        """Return the plain text with LF line endings."""
        self._check_readable()
        return self._text

    def set_text(self: Self, text: str) -> None:
        """Replace text silently, retaining the selection when unchanged.

        Args:
            text: New plain text, including any desired newlines.
        """
        self._check_mutable()
        normalized: str = text_helpers.multiline(
            validation.string(text, "text")
        )
        if normalized != self._text:
            self._text = normalized
            if self._editor is not None:
                with QtCore.QSignalBlocker(self._editor):
                    self._editor.setPlainText(normalized)

    def on_change(self: Self, callback: callbacks.Callback | None) -> None:
        """Replace the user-edit handler, or remove it with None.

        Args:
            callback: A function or bound method taking no arguments.
        """
        self._check_mutable()
        validation.callback(callback, "on_change")
        self._callback = callback

    def _edited(self: Self) -> None:
        assert self._editor is not None
        # toPlainText() also replaces nonbreaking spaces and line separators.
        # Raw text preserves them; document paragraph breaks represent LF.
        text: str = self._editor.document().toRawText().replace("\u2029", "\n")
        if text != self._text:
            self._text = text
            self._emit("on_change", self._callback)

    def _detach(self: Self) -> None:
        self._editor = None
        super()._detach()

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        editor: QtWidgets.QPlainTextEdit = QtWidgets.QPlainTextEdit()
        editor.setPlainText(self._text)
        editor.setReadOnly(self._read_only)
        editor.setTabChangesFocus(True)
        editor.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        editor.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        editor.textChanged.connect(self._edited)
        self._editor = editor
        container: QtWidgets.QWidget = field.labeled_field(self._label, editor)
        container.setEnabled(self._enabled)
        return self._attach(container, dispatch)
