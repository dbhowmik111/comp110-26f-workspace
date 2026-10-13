"""A native window containing student controls and callback diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Self

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from comp110_gui.runtime import mounting

if TYPE_CHECKING:
    from comp110_gui.runtime import node as node_module
    from comp110_gui.runtime import session as session_module
    from comp110_gui.runtime import window as window_module


class WindowWidget(QtWidgets.QWidget):
    """A scrollable content window with a nonmodal traceback panel."""

    def __init__(
        self: Self,
        session: session_module.Session,
        descriptor: window_module.Window | None,
        title: str,
        width: int,
        height: int,
    ) -> None:
        """Create the native shell with scrolling and a hidden error panel."""
        super().__init__()
        self.session: session_module.Session = session
        self.descriptor: window_module.Window | None = descriptor
        self.setWindowTitle(title)
        self.resize(width, height)
        outer: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.content_scroll: QtWidgets.QScrollArea = QtWidgets.QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        outer.addWidget(self.content_scroll)
        self.error_panel: QtWidgets.QPlainTextEdit = QtWidgets.QPlainTextEdit()
        self.error_panel.setReadOnly(True)
        self.error_panel.setTabChangesFocus(True)
        self.error_panel.setAccessibleName("Callback error and traceback")
        self.error_panel.setMaximumHeight(180)
        self.error_panel.hide()
        outer.addWidget(self.error_panel)

    def mount(self: Self, node: node_module.Node) -> None:
        """Place a resolved tree in this window's scrollable content area."""
        body: QtWidgets.QWidget = QtWidgets.QWidget(self)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(body)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        def dispatch(event: str, callback: Callable[[], None]) -> None:
            self.session.dispatch(self, event, callback)

        content: QtWidgets.QWidget = mounting.mount_node(node, body, dispatch)
        layout.addWidget(content)
        if not (
            content.sizePolicy().expandingDirections()
            & QtCore.Qt.Orientation.Vertical
        ):
            layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.content_scroll.setWidget(body)

    def closeEvent(self: Self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        """Hide a secondary window or stop the session for the main window."""
        if self.descriptor is None:
            self.session.stop()
        else:
            self.descriptor._open = False
        event.accept()

    def show_error(self: Self, message: str) -> None:
        """Display a readable traceback without opening a modal dialog."""
        self.error_panel.setPlainText(message)
        self.error_panel.show()
