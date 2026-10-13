"""One node in a resolved composition tree."""

from typing import Self

from comp110_gui.runtime import types


class Node:
    """A resolved layout or control, with custom views already expanded."""

    def __init__(self: Self, content: types.Leaf | types.Layout) -> None:
        """Store one resolved object, ready to receive its child nodes."""
        self.content: types.Leaf | types.Layout = content
        self.children: list[Node] = []
