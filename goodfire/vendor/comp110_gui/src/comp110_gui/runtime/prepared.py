"""The objects and ownership paths retained for one mounted window."""

from typing import Self

from comp110_gui.runtime import types


class Prepared:
    """Keep the resolved tree and ownership identities until session cleanup."""

    def __init__(self: Self) -> None:
        """Start an empty record of a window's resolved objects."""
        self.objects: list[object] = []
        self.layouts: list[types.Layout] = []
        self.controls: list[types.Leaf] = []
        self.paths: dict[int, str] = {}

    def freeze(self: Self) -> None:
        """Prevent structural edits when this tree begins mounting."""
        layout: types.Layout
        for layout in self.layouts:
            layout._mounted = True

    def rollback(self: Self) -> None:
        """Release failed mount state so this tree can be tried again."""
        layout: types.Layout
        for layout in self.layouts:
            layout._mounted = False
        control: types.Leaf
        for control in self.controls:
            control._detach()

    def dispose(self: Self) -> None:
        """Mark mounted objects as disposed before deleting native widgets."""
        layout: types.Layout
        for layout in self.layouts:
            layout._disposed = True
        control: types.Leaf
        for control in self.controls:
            control._dispose()
