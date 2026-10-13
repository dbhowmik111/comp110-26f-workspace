"""Internal types for resolved controls and layouts."""

from comp110_gui import controls
from comp110_gui import graphics
from comp110_gui import layouts

type Leaf = (
    controls.Label
    | controls.Button
    | controls.TextBox
    | controls.Checkbox
    | controls.Choice
    | controls.TextArea
    | controls.Slider
    | graphics.Picture
    | graphics.Canvas
)
type Layout = layouts.Row | layouts.Column
