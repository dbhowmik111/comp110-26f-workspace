"""Private lifecycle state shared by the facade's controls."""

from collections.abc import Callable
from typing import Self

from PySide6 import QtWidgets

from comp110_gui import validation

type Dispatch = Callable[[str, Callable[[], None]], None]


class Control:
    """Keep native handles private and discard them before Qt destruction."""

    def __init__(self: Self) -> None:
        """Create a control with no native widget or active dispatch target."""
        self._widget: QtWidgets.QWidget | None = None
        self._dispatch: Dispatch | None = None
        self._disposed: bool = False

    def _check_readable(self: Self) -> None:
        if self._widget is not None:
            validation.main_thread()

    def _check_mutable(self: Self) -> None:
        self._check_readable()
        if self._disposed:
            raise RuntimeError(
                f"This {type(self).__name__} belongs to an ended application. "
                "Launch your script again to create a new session."
            )

    def _attach(
        self: Self, widget: QtWidgets.QWidget, dispatch: Dispatch
    ) -> QtWidgets.QWidget:
        self._widget = widget
        self._dispatch = dispatch
        return widget

    def _emit(
        self: Self, event: str, callback: Callable[[], None] | None
    ) -> None:
        if self._dispatch is not None and callback is not None:
            self._dispatch(f"{type(self).__name__}.{event}", callback)

    def _detach(self: Self) -> None:
        """Undo a failed mount so the same controls can be tried again."""
        self._widget = None
        self._dispatch = None

    def _dispose(self: Self) -> None:
        self._detach()
        self._disposed = True
