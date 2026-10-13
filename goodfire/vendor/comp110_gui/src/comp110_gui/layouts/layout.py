"""Share ordered composition and validation between rows and columns."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

from comp110_gui import base

if TYPE_CHECKING:
    from comp110_gui.layouts import content


class Layout:
    """Share insertion and early validation between rows and columns."""

    def __init__(self: Self) -> None:
        """Start with an empty, editable sequence of child content."""
        self._children: list[content.Content] = []
        self._mounted: bool = False
        self._disposed: bool = False

    def add(self: Self, child: content.Content) -> None:
        """Append one control, layout, or object with a build method.

        Args:
            child: The content to place after the existing children.

        Raises:
            TypeError: The child is not supported content.
            ValueError: The child creates an apparent duplicate or cycle.
            RuntimeError: This layout has already been mounted.
        """
        if self._mounted or self._disposed:
            raise RuntimeError(
                "This layout has already been mounted. "
                "Update existing controls instead."
            )
        if not isinstance(child, (base.Control, Layout)) and not callable(
            getattr(child, "build", None)
        ):
            raise TypeError(
                "add() expects a control, Row, Column, "
                "or an object with a build() method."
            )
        if child is self:
            raise ValueError(
                "A layout cannot contain itself (composition cycle)."
            )
        existing: content.Content
        for existing in self._children:
            if existing is child:
                raise ValueError(
                    f"This {type(child).__name__} appears in two places. "
                    "Create a second object for the second location."
                )
        if isinstance(child, Layout) and child._contains(self):
            raise ValueError(
                "This child creates a Row/Column composition cycle."
            )
        self._children.append(child)

    def _contains(self: Self, target: Layout) -> bool:
        child: content.Content
        for child in self._children:
            if child is target:
                return True
            if isinstance(child, Layout) and child._contains(target):
                return True
        return False
