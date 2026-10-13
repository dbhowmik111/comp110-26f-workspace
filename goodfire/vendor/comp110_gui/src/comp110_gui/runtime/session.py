"""Retain native windows and coordinate dispatch and session cleanup."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Self
from typing import cast

import shiboken6
from PySide6 import QtWidgets

from comp110_gui import layouts
from comp110_gui.runtime import composition
from comp110_gui.runtime import window_widget

if TYPE_CHECKING:
    from comp110_gui.runtime import node as node_module
    from comp110_gui.runtime import prepared as prepared_module
    from comp110_gui.runtime import types
    from comp110_gui.runtime import window as window_module


class Session:
    """Privately retain all mounted objects and coordinate their lifecycle."""

    def __init__(self: Self, application: QtWidgets.QApplication) -> None:
        """Retain the application and connect its shutdown notification."""
        self.application: QtWidgets.QApplication = application
        self.main: window_widget.WindowWidget | None = None
        self.ready: bool = False
        self.building: bool = False
        self.stopping: bool = False
        self.disposed: bool = False
        self.pending_exception: KeyboardInterrupt | SystemExit | None = None
        self._reserved: dict[int, str] = {}
        self._windows: list[window_widget.WindowWidget] = []
        self._trees: list[prepared_module.Prepared] = []
        self.application.setQuitOnLastWindowClosed(False)
        self.application.aboutToQuit.connect(self.stop)

    def mount(
        self: Self,
        content: layouts.Content,
        title: str,
        width: int,
        height: int,
        descriptor: window_module.Window | None = None,
        prepared_tree: tuple[node_module.Node, prepared_module.Prepared]
        | None = None,
    ) -> window_widget.WindowWidget:
        """Validate and mount one window, rolling back any failed attempt."""
        self.building = True
        node: node_module.Node
        prepared: prepared_module.Prepared | None = None
        widget: window_widget.WindowWidget | None = None
        try:
            if prepared_tree is None:
                node, prepared = composition.prepare(
                    content, self._reserved, title
                )
            else:
                node, prepared = prepared_tree
            prepared.freeze()
            widget = window_widget.WindowWidget(
                self, descriptor, title, width, height
            )
            widget.mount(node)
        except BaseException:
            if prepared is not None:
                # A failed adapter may have attached an unparented widget.
                control: types.Leaf
                for control in prepared.controls:
                    native: QtWidgets.QWidget | None = control._widget
                    if native is not None and native.parent() is None:
                        shiboken6.delete(native)
                prepared.rollback()
            if widget is not None:
                shiboken6.delete(widget)
            raise
        finally:
            self.building = False
        self._reserved.update(prepared.paths)
        self._trees.append(prepared)
        self._windows.append(widget)
        return widget

    def dispatch(
        self: Self,
        origin: window_widget.WindowWidget,
        event: str,
        callback: Callable[[], None],
    ) -> None:
        """Invoke a callback and contain failures at the Qt signal boundary."""
        if not self.ready or self.building or self.stopping:
            return
        error: BaseException
        try:
            callback()
        except (KeyboardInterrupt, SystemExit) as error:
            self.pending_exception = error
            self.stop()
        except Exception as error:
            header: str = f"Error in {event}:"
            print(header, file=sys.stderr)
            traceback.print_exception(error)
            text: str = (
                header + "\n" + "".join(traceback.format_exception(error))
            )
            target: window_widget.WindowWidget = origin
            if origin.descriptor is not None and not origin.descriptor._open:
                target = cast(window_widget.WindowWidget, self.main)
            target.show_error(text)

    def stop(self: Self) -> None:
        """Stop callback dispatch, hide all windows, and exit the event loop."""
        if self.stopping:
            return
        self.stopping = True
        self.ready = False
        widget: window_widget.WindowWidget
        for widget in self._windows:
            if widget.descriptor is not None:
                widget.descriptor._open = False
            widget.hide()
        self.application.quit()

    def dispose(self: Self) -> None:
        """Clear facade handles and delete every native session window."""
        if self.disposed:
            return
        self.stop()
        self.application.aboutToQuit.disconnect(self.stop)
        tree: prepared_module.Prepared
        for tree in self._trees:
            tree.dispose()
        widget: window_widget.WindowWidget
        for widget in self._windows:
            if widget.descriptor is not None:
                widget.descriptor._widget = None
                widget.descriptor._disposed = True
            shiboken6.delete(widget)
        self._windows.clear()
        self._trees.clear()
        self._reserved.clear()
        self.main = None
        self.disposed = True
