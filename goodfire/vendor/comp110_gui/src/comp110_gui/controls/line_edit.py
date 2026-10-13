"""Normalize native single-line input before Qt records undo history."""

from typing import Self
from typing import override

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from comp110_gui.controls import text_helpers


class LineEdit(QtWidgets.QLineEdit):
    """Normalize pasted and committed text before Qt stores undo history."""

    def _paste(self: Self) -> None:
        self.insert(
            text_helpers.single_line(QtWidgets.QApplication.clipboard().text())
        )

    @override
    def keyPressEvent(self: Self, event: QtGui.QKeyEvent) -> None:
        if event.matches(QtGui.QKeySequence.StandardKey.Paste):
            self._paste()
        else:
            super().keyPressEvent(event)

    def _context_menu(self: Self) -> QtWidgets.QMenu:
        menu: QtWidgets.QMenu = self.createStandardContextMenu()
        action: QtGui.QAction
        for action in menu.actions():
            if action.objectName() == "edit-paste":
                action.triggered.disconnect()
                action.triggered.connect(self._paste)
        return menu

    @override
    def contextMenuEvent(self: Self, event: QtGui.QContextMenuEvent) -> None:
        menu: QtWidgets.QMenu = self._context_menu()
        menu.setParent(self, QtCore.Qt.WindowType.Popup)
        menu.aboutToHide.connect(menu.deleteLater)
        menu.popup(event.globalPos())

    @override
    def inputMethodEvent(self: Self, event: QtGui.QInputMethodEvent) -> None:
        normalized: QtGui.QInputMethodEvent = QtGui.QInputMethodEvent(
            event.preeditString(), event.attributes()
        )
        normalized.setCommitString(
            text_helpers.single_line(event.commitString()),
            event.replacementStart(),
            event.replacementLength(),
        )
        super().inputMethodEvent(normalized)
