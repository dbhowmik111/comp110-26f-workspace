"""Build a persistent visible label around an input widget."""

from PySide6 import QtCore
from PySide6 import QtWidgets

from comp110_gui.controls import text_helpers


def labeled_field(label: str, editor: QtWidgets.QWidget) -> QtWidgets.QWidget:
    """Give an editor a persistent label and accessible name."""
    container: QtWidgets.QWidget = QtWidgets.QWidget()
    layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    caption: QtWidgets.QLabel = QtWidgets.QLabel(label)
    caption.setTextFormat(QtCore.Qt.TextFormat.PlainText)
    caption.setWordWrap(True)
    # QLabel interprets ampersands when it has a buddy, even in plain text.
    caption.setText(text_helpers.caption(label))
    caption.setBuddy(editor)
    editor.setAccessibleName(label)
    container.setFocusProxy(editor)
    container.setSizePolicy(editor.sizePolicy())
    layout.addWidget(caption)
    layout.addWidget(editor)
    return container
