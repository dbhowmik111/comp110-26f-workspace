"""Describe student-defined components that build a row or column."""

from __future__ import annotations

from typing import Protocol
from typing import Self

from comp110_gui.layouts import column
from comp110_gui.layouts import row


class View(Protocol):
    """A student-defined component that supplies a Row or Column."""

    def build(self: Self) -> row.Row | column.Column:
        """Return this component's layout when its window first mounts."""
        ...
