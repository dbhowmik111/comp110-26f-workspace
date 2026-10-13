"""The supported retained drawing command types."""

from comp110_gui.graphics.commands import image
from comp110_gui.graphics.commands import line
from comp110_gui.graphics.commands import shape
from comp110_gui.graphics.commands import text

type Command = line.Line | shape.Shape | text.Text | image.Image

__all__: list[str] = ["Command"]
