"""Structural contract for objects that draw themselves on a canvas."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Protocol
from typing import Self

if TYPE_CHECKING:
    from comp110_gui.graphics.canvas import Canvas


class Drawable(Protocol):
    """An object that records drawing commands when explicitly drawn."""

    def draw(self: Self, canvas: Canvas) -> None:
        """Record this object's artwork on the supplied canvas."""
        ...
