"""Launch a single facade application in a fresh desktop Python process."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PySide6 import QtCore
from PySide6 import QtWidgets

from comp110_gui import layouts
from comp110_gui import validation
from comp110_gui.runtime import composition
from comp110_gui.runtime import session as session_module
from comp110_gui.runtime import state

if TYPE_CHECKING:
    from comp110_gui.runtime import node as node_module
    from comp110_gui.runtime import prepared as prepared_module


def run(
    content: layouts.Content,
    *,
    title: str = "COMP110",
    width: int = 480,
    height: int = 320,
) -> None:
    """Run one desktop application until its main window closes.

    Args:
        content: A control, layout, or object implementing View.build().
        title: The main window's title.
        width: Its positive initial width in logical pixels.
        height: Its positive initial height in logical pixels.

    Raises:
        RuntimeError: Called off the main thread, twice, or in an existing Qt
            host. Run the application as a script in a fresh local process.
        TypeError: An argument or view result has the wrong type.
        ValueError: Dimensions or the composition graph are invalid.
    """
    validation.main_thread()
    if state._launching or state._has_run:
        raise RuntimeError(
            "Only one run() session is supported per process. "
            "Launch your .py file again in a fresh local process."
        )
    if QtCore.QCoreApplication.instance() is not None:
        raise RuntimeError(
            "A Qt application already exists. Run your .py file in a fresh "
            "local process, outside notebooks or other Qt hosts."
        )
    title = validation.string(title, "Window title")
    width = validation.integer(width, "Window width")
    height = validation.integer(height, "Window height")
    state._launching = True
    prepared: prepared_module.Prepared | None = None
    try:
        tree: tuple[node_module.Node, prepared_module.Prepared] = (
            composition.prepare(content, {}, "main")
        )
        prepared = tree[1]
        prepared.freeze()
        application: QtWidgets.QApplication = QtWidgets.QApplication(
            [sys.argv[0]]
        )
        state._has_run = True
        session: session_module.Session = session_module.Session(application)
        state._session = session
        try:
            session.main = session.mount(
                content, title, width, height, prepared_tree=tree
            )
            session.main.show()
            session.ready = True
            application.exec()
        finally:
            session.dispose()
        if session.pending_exception is not None:
            raise session.pending_exception
    finally:
        if prepared is not None and not state._has_run:
            prepared.rollback()
        state._session = None
        state._launching = False
