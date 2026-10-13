"""Share enabled-state behavior among interactive controls."""

from typing import Self

from comp110_gui import base
from comp110_gui import validation


class EnabledControl(base.Control):
    """Share the same enabled-state contract among interactive controls."""

    def __init__(self: Self) -> None:
        """Start enabled without constructing a native widget."""
        super().__init__()
        self._enabled: bool = True

    def is_enabled(self: Self) -> bool:
        """Return whether user interaction is enabled."""
        self._check_readable()
        return self._enabled

    def set_enabled(self: Self, enabled: bool) -> None:
        """Enable or disable user interaction, retaining the control's value.

        Args:
            enabled: Whether the user can interact with the control.
        """
        self._check_mutable()
        enabled = validation.boolean(enabled, "enabled")
        self._enabled = enabled
        if self._widget is not None:
            self._widget.setEnabled(enabled)
