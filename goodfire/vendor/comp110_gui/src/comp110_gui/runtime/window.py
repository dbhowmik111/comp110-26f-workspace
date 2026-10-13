"""The modeless secondary-window facade."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

from comp110_gui import layouts
from comp110_gui import validation
from comp110_gui.runtime import composition
from comp110_gui.runtime import state

if TYPE_CHECKING:
    from comp110_gui.runtime import session as session_module
    from comp110_gui.runtime import window_widget


class Window:
    """A modeless secondary window that can be closed and reopened."""

    def __init__(
        self: Self,
        content: layouts.Content,
        *,
        title: str = "COMP110",
        width: int = 480,
        height: int = 320,
    ) -> None:
        """Store content and initial size without creating native widgets.

        Args:
            content: A control, layout, or object implementing View.build().
            title: The window's title.
            width: The positive initial width in logical pixels.
            height: The positive initial height in logical pixels.
        """
        composition.check_content(content)
        self._title: str = validation.string(title, "Window title")
        self._width: int = validation.integer(width, "Window width")
        self._height: int = validation.integer(height, "Window height")
        self._content: layouts.Content = content
        self._widget: window_widget.WindowWidget | None = None
        self._open: bool = False
        self._disposed: bool = False

    def show(self: Self) -> None:
        """Mount once, then show or restore this window during run().

        Raises:
            RuntimeError: There is no active session ready for callbacks.
            TypeError: A view returns something other than Row or Column.
            ValueError: Content is reused or contains a composition cycle.
        """
        session: session_module.Session = state.require_session("Window.show()")
        if self._widget is None:
            self._widget = session.mount(
                self._content, self._title, self._width, self._height, self
            )
        self._open = True
        if self._widget.isMinimized():
            self._widget.showNormal()
        else:
            self._widget.show()
        self._widget.raise_()
        self._widget.activateWindow()

    def close(self: Self) -> None:
        """Hide this window while retaining its controls for reopening.

        Raises:
            RuntimeError: The window's application session has ended.
        """
        validation.main_thread()
        if self._disposed or (state._has_run and state._session is None):
            raise RuntimeError("This Window belongs to an ended application.")
        if self._widget is not None:
            self._widget.close()

    def is_open(self: Self) -> bool:
        """Return whether this window is shown, including when minimized."""
        validation.main_thread()
        return self._open
