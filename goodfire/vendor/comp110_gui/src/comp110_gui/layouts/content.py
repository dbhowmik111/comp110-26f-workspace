"""The controls, layouts, and views accepted as child content."""

from comp110_gui import controls
from comp110_gui import graphics
from comp110_gui.layouts import column
from comp110_gui.layouts import row
from comp110_gui.layouts import view

type Content = (
    controls.Label
    | controls.Button
    | controls.TextBox
    | controls.Checkbox
    | controls.Choice
    | controls.TextArea
    | controls.Slider
    | graphics.Picture
    | graphics.Canvas
    | row.Row
    | column.Column
    | view.View
)
