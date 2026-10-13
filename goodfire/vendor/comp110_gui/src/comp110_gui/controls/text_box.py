"""A labeled single-line text editor."""

from typing import Self

from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import validation
from comp110_gui.controls import callbacks
from comp110_gui.controls import enabled_control
from comp110_gui.controls import field
from comp110_gui.controls import line_edit
from comp110_gui.controls import text_helpers


class TextBox(enabled_control.EnabledControl):
    """A labeled single-line editor with change and Enter callbacks."""

    def __init__(
        self: Self, *, label: str, text: str = "", placeholder: str = ""
    ) -> None:
        """Create a single-line text input.

        Args:
            label: A nonblank, persistent visible field label.
            text: Initial text; each newline becomes a space.
            placeholder: Optional guidance shown while the editor is empty.
        """
        super().__init__()
        self._label: str = validation.string(label, "label", nonblank=True)
        self._text: str = text_helpers.single_line(
            validation.string(text, "text")
        )
        self._placeholder: str = validation.string(placeholder, "placeholder")
        self._change: callbacks.Callback | None = None
        self._submit: callbacks.Callback | None = None
        self._editor: line_edit.LineEdit | None = None

    def get_text(self: Self) -> str:
        """Return current text, without stripping or converting it."""
        self._check_readable()
        return self._text

    def set_text(self: Self, text: str) -> None:
        """Replace text silently, converting each newline to a space.

        Args:
            text: The replacement text.
        """
        self._check_mutable()
        normalized: str = text_helpers.single_line(
            validation.string(text, "text")
        )
        if normalized != self._text:
            self._text = normalized
            if self._editor is not None:
                self._editor.setText(normalized)

    def on_change(self: Self, callback: callbacks.Callback | None) -> None:
        """Replace the user-edit handler, or remove it with None.

        Args:
            callback: A function or bound method taking no arguments.
        """
        self._check_mutable()
        validation.callback(callback, "on_change")
        self._change = callback

    def on_submit(self: Self, callback: callbacks.Callback | None) -> None:
        """Replace the Enter/Return handler, or remove it with None.

        Args:
            callback: A function or bound method taking no arguments.
        """
        self._check_mutable()
        validation.callback(callback, "on_submit")
        self._submit = callback

    def _edited(self: Self, text: str) -> None:
        normalized: str = text_helpers.single_line(text)
        # Also cover native paste routes outside key and context-menu events.
        if normalized != text and self._editor is not None:
            cursor: int = len(
                text_helpers.single_line(text[: self._editor.cursorPosition()])
            )
            self._editor.setText(normalized)
            self._editor.setCursorPosition(cursor)
        if normalized != self._text:
            self._text = normalized
            self._emit("on_change", self._change)

    def _submitted(self: Self) -> None:
        self._emit("on_submit", self._submit)

    def _detach(self: Self) -> None:
        self._editor = None
        super()._detach()

    def _mount(self: Self, dispatch: base.Dispatch) -> QtWidgets.QWidget:
        editor: line_edit.LineEdit = line_edit.LineEdit()
        editor.setMaxLength(2_147_483_647)
        editor.setText(self._text)
        editor.setPlaceholderText(self._placeholder)
        editor.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        editor.textEdited.connect(self._edited)
        editor.returnPressed.connect(self._submitted)
        self._editor = editor
        container: QtWidgets.QWidget = field.labeled_field(self._label, editor)
        container.setEnabled(self._enabled)
        return self._attach(container, dispatch)
